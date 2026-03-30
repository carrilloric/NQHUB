"""
Export Worker - Background task for exporting datasets to GCS

This worker processes export jobs in the background using RQ.
Follows the same pattern as app/etl/tasks.py.

To run: Make sure the RQ worker is running (app.etl.worker)
"""
import asyncio
import logging
from datetime import datetime, timedelta
from uuid import UUID
from pathlib import Path
import tempfile
import os
from typing import Dict, List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd

from app.db.session import AsyncSessionLocal
from app.models.export_job import ExportJob
from app.config import settings

logger = logging.getLogger(__name__)


# ===========================================
# Column definitions for export versions
# ===========================================

BASE_COLUMNS = [
    "time_interval", "symbol", "open", "high", "low", "close", "volume", "tick_count",
    "body", "upper_wick", "lower_wick", "wick_ratio", "rel_uw", "rel_lw",
    "poc", "poc_volume", "poc_percentage", "poc_location", "poc_position",
    "real_poc", "real_poc_volume", "real_poc_percentage", "real_poc_location",
    "delta", "upper_wick_volume", "lower_wick_volume", "body_volume",
    "asellers_uwick", "asellers_lwick", "abuyers_uwick", "abuyers_lwick",
    "is_spread", "is_rollover_period"
]

OFLOW_COLUMNS = BASE_COLUMNS + ["oflow_detail", "oflow_unit"]


# ===========================================
# GCS Upload Functions
# ===========================================

def get_gcs_client():
    """
    Get Google Cloud Storage client.

    In tests, this will be mocked.
    In production, uses credentials from settings.
    """
    try:
        from google.cloud import storage
        import json

        if settings.GCS_CREDENTIALS_JSON:
            # If credentials_json is a JSON string, parse it
            if settings.GCS_CREDENTIALS_JSON.startswith('{'):
                credentials_info = json.loads(settings.GCS_CREDENTIALS_JSON)
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
                client = storage.Client(credentials=credentials, project=settings.GCS_PROJECT_ID)
            else:
                # If it's a file path
                client = storage.Client.from_service_account_json(settings.GCS_CREDENTIALS_JSON)
        else:
            # Use default credentials (works in GCP environment)
            client = storage.Client()

        return client
    except ImportError:
        logger.warning("google-cloud-storage not installed. GCS uploads will fail in production.")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize GCS client: {e}")
        return None


def upload_to_gcs(local_path: str, gcs_path: str) -> str:
    """
    Upload file to GCS and return signed URL.

    Args:
        local_path: Path to local file
        gcs_path: Destination path in GCS (without gs:// prefix and bucket name)

    Returns:
        Signed URL (valid for 48 hours)
    """
    client = get_gcs_client()
    if not client:
        raise Exception("GCS client not available")

    bucket = client.bucket(settings.GCS_BUCKET_NAME)
    blob = bucket.blob(gcs_path)

    # Upload with gzip compression
    blob.upload_from_filename(local_path, content_type='application/octet-stream')

    logger.info(f"✅ Uploaded {local_path} to gs://{settings.GCS_BUCKET_NAME}/{gcs_path}")

    # Generate signed URL (valid for 48 hours)
    expiration = timedelta(hours=48)
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=expiration,
        method="GET"
    )

    return signed_url


# ===========================================
# Database Query Functions
# ===========================================

async def estimate_export_size(
    session: AsyncSession,
    timeframe: str,
    start_date: str,
    end_date: str
) -> tuple[int, int]:
    """
    Estimate number of rows and size in MB for the export.

    Returns:
        (estimated_rows, estimated_size_mb)
    """
    query = text("""
        SELECT COUNT(*) as row_count
        FROM candles
        WHERE timeframe = :timeframe
        AND time_interval >= :start_date::date
        AND time_interval < :end_date::date + INTERVAL '1 day'
    """)

    result = await session.execute(
        query,
        {"timeframe": timeframe, "start_date": start_date, "end_date": end_date}
    )
    row = result.fetchone()
    row_count = row[0] if row else 0

    # Rough estimate: 2.5 KB per row for base, 3.5 KB for oflow
    estimated_size_mb = int((row_count * 2500) / (1024 * 1024))

    return row_count, estimated_size_mb


async def export_candles_from_db(
    session: AsyncSession,
    timeframe: str,
    start_date: str,
    end_date: str,
    include_oflow: bool = False,
    flatten_oflow: bool = False
) -> pd.DataFrame:
    """
    Query candles from TimescaleDB and return as DataFrame.

    Args:
        session: Async database session
        timeframe: Candle timeframe
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        include_oflow: Include oflow_detail and oflow_unit columns
        flatten_oflow: Flatten JSONB to separate columns (if include_oflow=True)

    Returns:
        pandas DataFrame
    """
    # Select columns based on export version
    columns = OFLOW_COLUMNS if include_oflow else BASE_COLUMNS
    columns_str = ", ".join(columns)

    query = text(f"""
        SELECT {columns_str}
        FROM candles
        WHERE timeframe = :timeframe
        AND time_interval >= :start_date::date
        AND time_interval < :end_date::date + INTERVAL '1 day'
        ORDER BY time_interval
    """)

    result = await session.execute(
        query,
        {"timeframe": timeframe, "start_date": start_date, "end_date": end_date}
    )

    rows = result.fetchall()
    df = pd.DataFrame(rows, columns=columns)

    logger.info(f"Fetched {len(df)} candles from database")

    # If flatten_oflow is True, expand JSONB columns
    if include_oflow and flatten_oflow and 'oflow_detail' in df.columns:
        # TODO: Implement flattening logic if needed
        # For now, we keep JSONB as-is
        pass

    return df


# ===========================================
# Parquet Generation Functions
# ===========================================

def generate_parquet_files(
    df: pd.DataFrame,
    output_dir: Path,
    base_filename: str,
    include_oflow: bool = False,
    max_size_mb: int = 500
) -> List[Dict]:
    """
    Generate Parquet file(s) with auto-partitioning if > 500MB.

    Args:
        df: DataFrame to export
        output_dir: Directory to write files
        base_filename: Base filename (e.g., "NQ_2024_1min_base")
        include_oflow: Whether this is the oflow version
        max_size_mb: Maximum file size before partitioning

    Returns:
        List of file metadata dicts
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    files = []

    # Estimate DataFrame size in memory (rough approximation)
    estimated_size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)

    logger.info(f"DataFrame estimated size: {estimated_size_mb:.2f} MB")

    if estimated_size_mb > max_size_mb:
        # Partition into multiple files
        num_partitions = int(estimated_size_mb / max_size_mb) + 1
        rows_per_partition = len(df) // num_partitions

        logger.info(f"Partitioning into {num_partitions} files ({rows_per_partition} rows each)")

        for i in range(num_partitions):
            start_idx = i * rows_per_partition
            end_idx = (i + 1) * rows_per_partition if i < num_partitions - 1 else len(df)

            partition_df = df.iloc[start_idx:end_idx]
            filename = f"{base_filename}_part{i+1}.parquet"
            filepath = output_dir / filename

            # Write to Parquet
            table = pa.Table.from_pandas(partition_df)
            pq.write_table(table, filepath, compression='gzip')

            size_mb = os.path.getsize(filepath) / (1024 * 1024)

            files.append({
                "name": filename,
                "size_mb": round(size_mb, 2),
                "local_path": str(filepath)
            })

            logger.info(f"✅ Created partition {i+1}/{num_partitions}: {filename} ({size_mb:.2f} MB)")

    else:
        # Single file export
        filename = f"{base_filename}.parquet"
        filepath = output_dir / filename

        # Write to Parquet
        table = pa.Table.from_pandas(df)
        pq.write_table(table, filepath, compression='gzip')

        size_mb = os.path.getsize(filepath) / (1024 * 1024)

        files.append({
            "name": filename,
            "size_mb": round(size_mb, 2),
            "local_path": str(filepath)
        })

        logger.info(f"✅ Created file: {filename} ({size_mb:.2f} MB)")

    return files


# ===========================================
# Job Status Update Functions
# ===========================================

async def update_job_status(
    session: AsyncSession,
    job_id: UUID,
    status: str,
    progress_pct: int = None,
    current_step: str = None,
    **kwargs
):
    """Update export job status in database"""
    result = await session.execute(
        select(ExportJob).where(ExportJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        logger.error(f"Export job {job_id} not found")
        return

    job.status = status
    if progress_pct is not None:
        job.progress_pct = progress_pct
    if current_step is not None:
        job.current_step = current_step

    # Update other fields
    for key, value in kwargs.items():
        if hasattr(job, key):
            setattr(job, key, value)

    await session.commit()
    logger.info(f"Export job {job_id} updated: {status} ({progress_pct}%)")


# ===========================================
# Main Export Task (RQ Entry Point)
# ===========================================

def export_candles_to_gcs(job_id: str):
    """
    Main export task - exports candles to GCS in Parquet format.

    This is the function that RQ will execute in the background.

    Steps:
    1. Mark job as 'running'
    2. Query TimescaleDB
    3. Generate Parquet files (base + oflow versions)
    4. Auto-partition if > 500MB
    5. Upload to GCS with gzip compression
    6. Generate signed URLs (TTL: 48h)
    7. Mark job as 'completed' with file metadata

    Args:
        job_id: UUID string of the export job
    """
    job_uuid = UUID(job_id)
    logger.info(f"🚀 Starting export job: {job_id}")

    # Run async code in sync context
    asyncio.run(_export_with_error_handling(job_uuid))


async def _export_with_error_handling(job_id: UUID):
    """Wrapper that handles errors within a single event loop"""
    try:
        await _export_async(job_id)
        logger.info(f"✅ Export job completed: {job_id}")
    except Exception as e:
        logger.error(f"❌ Export job failed: {job_id} - {str(e)}", exc_info=True)
        await _mark_job_failed(job_id, str(e))


async def _export_async(job_id: UUID):
    """Async implementation of export processing"""

    async with AsyncSessionLocal() as session:
        # Get job details
        result = await session.execute(
            select(ExportJob).where(ExportJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            raise Exception(f"Export job {job_id} not found")

        logger.info(f"Job params: {job.timeframe} {job.start_date} to {job.end_date}")

        # Step 1: Mark as running
        await update_job_status(
            session, job_id, "running",
            progress_pct=10,
            current_step="Querying database",
            started_at=datetime.utcnow()
        )

        # Step 2: Export base version (without JSONB)
        logger.info("📊 Exporting base version (no JSONB)...")
        df_base = await export_candles_from_db(
            session,
            job.timeframe,
            job.start_date,
            job.end_date,
            include_oflow=False
        )

        await update_job_status(
            session, job_id, "running",
            progress_pct=40,
            current_step="Generating base Parquet"
        )

        # Step 3: Generate Parquet files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Base filename pattern: NQ_20240101_20241231_1min_base
            base_filename = f"NQ_{job.start_date.replace('-', '')}_{job.end_date.replace('-', '')}_{job.timeframe}_base"

            files_base = generate_parquet_files(
                df_base,
                temp_path,
                base_filename,
                include_oflow=False
            )

            await update_job_status(
                session, job_id, "running",
                progress_pct=60,
                current_step="Uploading base files to GCS"
            )

            # Step 4: Upload base files to GCS
            all_files = []
            for file_info in files_base:
                gcs_path = file_info["name"]
                signed_url = upload_to_gcs(file_info["local_path"], gcs_path)

                all_files.append({
                    "name": file_info["name"],
                    "size_mb": file_info["size_mb"],
                    "gcs_path": f"gs://{settings.GCS_BUCKET_NAME}/{gcs_path}",
                    "signed_url": signed_url,
                    "expires_at": (datetime.utcnow() + timedelta(hours=48)).isoformat() + "Z"
                })

            # Step 5: Export oflow version if requested
            if job.include_oflow:
                logger.info("📊 Exporting oflow version (with JSONB)...")
                df_oflow = await export_candles_from_db(
                    session,
                    job.timeframe,
                    job.start_date,
                    job.end_date,
                    include_oflow=True,
                    flatten_oflow=job.flatten_oflow
                )

                await update_job_status(
                    session, job_id, "running",
                    progress_pct=75,
                    current_step="Generating oflow Parquet"
                )

                oflow_filename = f"NQ_{job.start_date.replace('-', '')}_{job.end_date.replace('-', '')}_{job.timeframe}_oflow"

                files_oflow = generate_parquet_files(
                    df_oflow,
                    temp_path,
                    oflow_filename,
                    include_oflow=True
                )

                await update_job_status(
                    session, job_id, "running",
                    progress_pct=85,
                    current_step="Uploading oflow files to GCS"
                )

                # Upload oflow files
                for file_info in files_oflow:
                    gcs_path = file_info["name"]
                    signed_url = upload_to_gcs(file_info["local_path"], gcs_path)

                    all_files.append({
                        "name": file_info["name"],
                        "size_mb": file_info["size_mb"],
                        "gcs_path": f"gs://{settings.GCS_BUCKET_NAME}/{gcs_path}",
                        "signed_url": signed_url,
                        "expires_at": (datetime.utcnow() + timedelta(hours=48)).isoformat() + "Z"
                    })

        # Step 6: Mark as completed
        await update_job_status(
            session, job_id, "completed",
            progress_pct=100,
            current_step="Export completed",
            completed_at=datetime.utcnow(),
            files=all_files
        )

        logger.info(f"✅ Exported {len(all_files)} file(s) to GCS")


async def _mark_job_failed(job_id: UUID, error_message: str):
    """Mark job as failed with error message"""
    async with AsyncSessionLocal() as session:
        await update_job_status(
            session, job_id, "failed",
            progress_pct=0,
            current_step="Failed",
            completed_at=datetime.utcnow(),
            error=error_message
        )
