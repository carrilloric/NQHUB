"""
ETL Background Tasks

Tasks that are queued and processed by RQ workers.
"""
from datetime import datetime, timedelta
from uuid import UUID
import asyncio
import logging
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.etl.models import ETLJob
from app.config import settings

logger = logging.getLogger(__name__)


async def update_job_status(
    session: AsyncSession,
    job_id: UUID,
    status: str,
    current_step: int = None,
    progress_pct: int = None,
    **kwargs
):
    """Update ETL job status in database"""
    result = await session.execute(
        select(ETLJob).where(ETLJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        logger.error(f"Job {job_id} not found")
        return

    job.status = status
    if current_step is not None:
        job.current_step = current_step
    if progress_pct is not None:
        job.progress_pct = progress_pct

    # Update other fields
    for key, value in kwargs.items():
        if hasattr(job, key):
            setattr(job, key, value)

    await session.commit()
    logger.info(f"Job {job_id} updated: {status} ({progress_pct}%)")


def process_etl_job(job_id: str):
    """
    Main ETL task - processes a ZIP file and populates database.

    This is the function that RQ will execute in the background.

    Steps:
    1. Extract ZIP file
    2. Decompress .zst files
    3. Parse CSV files
    4. Load ticks into market_data_ticks
    5. Build candles for selected timeframes
    6. Detect rollovers
    7. Update coverage tracking
    8. Mark job as completed

    Args:
        job_id: UUID string of the ETL job
    """
    job_uuid = UUID(job_id)
    logger.info(f"Starting ETL job: {job_id}")

    # Run async code in sync context (single event loop)
    asyncio.run(_process_etl_job_with_error_handling(job_uuid))


async def _process_etl_job_with_error_handling(job_id: UUID):
    """
    Wrapper that handles errors within a single event loop.
    This avoids nested asyncio.run() calls.
    """
    try:
        await _process_etl_job_async(job_id)
        logger.info(f"ETL job completed: {job_id}")
    except Exception as e:
        logger.error(f"ETL job failed: {job_id} - {str(e)}", exc_info=True)
        # Mark job as failed (using await, not asyncio.run)
        await _mark_job_failed(job_id, str(e))


async def _process_etl_job_async(job_id: UUID):
    """Async implementation of ETL processing"""

    async with AsyncSessionLocal() as session:
        # Get job details
        result = await session.execute(
            select(ETLJob).where(ETLJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Initialize ETL logger (FASE 2)
        from app.etl.logger import ETLJobLogger
        etl_logger = ETLJobLogger(job_id, session)

        # Import cleanup function
        from app.etl.services.file_handler import cleanup_job_files

        try:
            # STEP 1: Mark as started
            await etl_logger.info("ETL job starting", filename=job.zip_filename, file_size_mb=job.file_size_mb)

            await update_job_status(
                session,
                job_id,
                status="extracting",
                current_step=1,
                progress_pct=10,
                started_at=datetime.utcnow()
            )

            # Import ETL services
            from app.etl.services.file_handler import get_job_directory
            from app.etl.services.extractor import extract_zip
            from app.etl.services.csv_parser import parse_csv_file, extract_symbol_from_filename, extract_date_from_filename
            from app.etl.services.tick_loader import load_ticks_batch
            from app.etl.services.candle_builder import (
                build_candles_for_day,
                get_available_dates,
                get_unique_symbols_for_date_range,
                is_spread_symbol
            )
            from app.etl.services.active_contract_detector import (
                detect_active_contracts,
                save_active_periods
            )

            # STEP 2: Extract ZIP and decompress .zst files
            await etl_logger.info("Starting ZIP extraction", filename=job.zip_filename)
            logger.info(f"Extracting ZIP: {job.zip_filename}")
            job_dir = get_job_directory(job_id)
            zip_path = job_dir / "uploaded.zip"
            csv_files = extract_zip(zip_path, job_id)
            await etl_logger.info(f"Extracted {len(csv_files)} CSV files", csv_count=len(csv_files))
            logger.info(f"Extracted {len(csv_files)} CSV files")

            # Pre-analysis: estimate total ticks and days
            from app.etl.services.csv_parser import extract_date_from_filename
            import os

            total_days = len(csv_files)
            total_ticks_estimated = 0
            unique_dates = set()

            for csv_file in csv_files:
                # Estimate ticks based on file size (aproximación: ~50 bytes per tick)
                file_size = os.path.getsize(csv_file)
                estimated_ticks = file_size // 50
                total_ticks_estimated += estimated_ticks

                # Extract date from filename
                file_date = extract_date_from_filename(csv_file.name)
                if file_date:
                    unique_dates.add(file_date)

            total_days = len(unique_dates) if unique_dates else len(csv_files)

            await update_job_status(
                session, job_id, status="parsing", current_step=2, progress_pct=30,
                csv_files_found=len(csv_files),
                total_ticks_estimated=total_ticks_estimated,
                total_days=total_days,
                status_detail=f"{len(csv_files)} archivos CSV encontrados ({total_days} días)"
            )

            # STEP 3: Parse CSVs and load ticks
            await etl_logger.info(f"Starting tick loading", csv_count=len(csv_files))
            logger.info(f"Loading ticks from {len(csv_files)} CSV files...")
            await update_job_status(session, job_id, status="loading_ticks", current_step=3, progress_pct=40)

            import time
            import psutil

            total_ticks = 0
            total_duplicates = 0
            days_processed = 0
            start_time = time.time()

            for i, csv_file in enumerate(csv_files, 1):
                await etl_logger.info(f"Processing file {i}/{len(csv_files)}", filename=csv_file.name)
                logger.info(f"Processing: {csv_file.name}")

                # Extract date from filename and build detailed status
                file_date = extract_date_from_filename(csv_file.name)
                if file_date:
                    status_detail = f"Archivo {i}/{len(csv_files)}: {file_date} ({csv_file.name})"
                else:
                    status_detail = f"Archivo {i}/{len(csv_files)}: {csv_file.name}"

                # Calculate processing metrics
                elapsed_time = time.time() - start_time
                ticks_per_second = total_ticks / elapsed_time if elapsed_time > 0 else 0
                process = psutil.Process()
                memory_usage_mb = process.memory_info().rss / 1024 / 1024

                # Estimate completion time
                if ticks_per_second > 0 and total_ticks_estimated > 0:
                    remaining_ticks = total_ticks_estimated - total_ticks
                    seconds_remaining = remaining_ticks / ticks_per_second
                    estimated_completion = datetime.utcnow() + timedelta(seconds=seconds_remaining)
                else:
                    estimated_completion = None

                # Update current file being processed with detailed status
                await update_job_status(
                    session, job_id, "loading_ticks",
                    current_csv_file=csv_file.name,
                    status_detail=status_detail,
                    days_processed=days_processed,
                    duplicates_skipped=total_duplicates,
                    ticks_per_second=ticks_per_second,
                    memory_usage_mb=memory_usage_mb,
                    estimated_completion=estimated_completion,
                    progress_pct=40 + int(20 * (i / len(csv_files)))  # Progress from 40% to 60%
                )

                # Parse CSV in batches
                batch_num = 0
                file_ticks = 0
                file_duplicates = 0

                for batch in parse_csv_file(csv_file):
                    batch_num += 1
                    batch_size = len(batch)
                    logger.info(f"🔍 Processing batch {batch_num}: {batch_size} ticks from {csv_file.name}")

                    # Insert batch - now returns (inserted, duplicates)
                    count, dups = await load_ticks_batch(session, batch)
                    total_ticks += count
                    total_duplicates += dups
                    file_ticks += count
                    file_duplicates += dups
                    logger.info(f"✓ Inserted {count} ticks from batch {batch_num} (total: {total_ticks}, dups: {dups})")

                # Increment days processed after completing a file
                if file_ticks > 0:
                    days_processed += 1

            await etl_logger.info(f"Completed tick loading",
                                  total_ticks=total_ticks,
                                  total_duplicates=total_duplicates,
                                  days_processed=days_processed)
            logger.info(f"Loaded {total_ticks} total ticks (skipped {total_duplicates} duplicates)")
            await update_job_status(
                session, job_id, status="building_candles", current_step=4, progress_pct=60,
                ticks_inserted=total_ticks,
                duplicates_skipped=total_duplicates,
                days_processed=days_processed,
                status_detail=f"Iniciando construcción de velas ({total_ticks:,} ticks procesados, {total_duplicates:,} duplicados omitidos)"
            )

            # STEP 4: Build candles for selected timeframes
            selected_timeframes = job.selected_timeframes or [
                '30s', '1min', '5min', '15min', '1hr', '4hr', 'daily', 'weekly'
            ]
            await etl_logger.info(f"Starting candle building", timeframes=selected_timeframes)
            logger.info(f"Building candles for timeframes: {selected_timeframes}")

            # Get date range from inserted ticks
            date_range_query = text("""
                SELECT MIN(DATE(ts_event)), MAX(DATE(ts_event))
                FROM market_data_ticks
            """)
            result = await session.execute(date_range_query)
            date_range = result.first()

            if not date_range or not date_range[0]:
                logger.warning("No tick data found to build candles")
                total_candles = 0
            else:
                start_date, end_date = date_range[0], date_range[1]
                logger.info(f"Date range for candle building: {start_date} to {end_date}")

                # Get ALL unique symbols in the date range
                symbols = await get_unique_symbols_for_date_range(session, start_date, end_date)
                await etl_logger.info(f"Found symbols to process", symbol_count=len(symbols), symbols=symbols)
                logger.info(f"Will process {len(symbols)} symbols: {symbols}")

                total_candles = 0

                # Process each symbol independently
                for symbol_idx, symbol in enumerate(symbols, 1):
                    is_spread = is_spread_symbol(symbol)
                    await etl_logger.info(f"Processing symbol {symbol}", is_spread=is_spread, index=f"{symbol_idx}/{len(symbols)}")
                    logger.info(f"🔍 Processing symbol {symbol_idx}/{len(symbols)}: {symbol} (is_spread={is_spread})")

                    # Get dates with data for this specific symbol
                    logger.info(f"🔍 Calling get_available_dates() for symbol: {symbol}")
                    available_dates = await get_available_dates(session, symbol)
                    logger.info(f"📅 get_available_dates() returned {len(available_dates)} dates for {symbol}: {available_dates}")

                    if not available_dates:
                        logger.warning(f"⚠️ No dates found for symbol {symbol}, skipping")
                        continue

                    logger.info(f"✅ Symbol {symbol} has {len(available_dates)} days with data - proceeding to build candles")

                    # Build candles for each date
                    for date_idx, date_obj in enumerate(available_dates, 1):
                        date_str = date_obj.strftime("%d-%b-%Y").upper()

                        # Build candles for all timeframes for this symbol+date
                        candle_results = await build_candles_for_day(session, symbol, date_obj, selected_timeframes)

                        # Sum up candles created
                        for tf, count in candle_results.items():
                            total_candles += count
                            logger.info(f"Built {count} {tf} candles for {symbol} on {date_obj}")

                        # Update job status with progress
                        progress_detail = f"{symbol} ({symbol_idx}/{len(symbols)}) - Velas para {date_str}"
                        await update_job_status(
                            session, job_id, "building_candles",
                            status_detail=progress_detail
                        )

            await etl_logger.info(f"Completed candle building", total_candles=total_candles)
            await update_job_status(
                session, job_id, status="detecting_rollovers", current_step=5, progress_pct=85,
                candles_created=total_candles,
                status_detail=f"Detectando rollovers ({total_candles:,} velas creadas)"
            )

            # STEP 5: Detect active contracts
            await etl_logger.info("Starting active contract detection")
            logger.info(f"🔍 Detecting active contracts based on volume analysis...")

            if not date_range or not date_range[0]:
                logger.warning("⚠️ No date range available for contract detection")
                active_periods_count = 0
            else:
                start_date, end_date = date_range[0], date_range[1]

                # Detect active contract periods
                active_periods = await detect_active_contracts(session, start_date, end_date)

                # Save to database
                active_periods_count = await save_active_periods(session, active_periods)

                logger.info(f"✅ Detected and saved {active_periods_count} active contract periods")

            await update_job_status(
                session, job_id, status="finalizing", current_step=6, progress_pct=95,
                status_detail=f"Finalizando ({active_periods_count} períodos de contrato activo detectados)"
            )

            # STEP FINAL: Mark as completed
            await etl_logger.info("ETL job completed successfully",
                                  total_ticks=total_ticks,
                                  total_candles=total_candles,
                                  csv_files=len(csv_files))

            # Build completion status detail
            completion_detail = (
                f"Completado: {len(csv_files)} archivos, "
                f"{total_ticks:,} ticks, {total_candles:,} velas"
            )

            await update_job_status(
                session,
                job_id,
                status="completed",
                current_step=7,
                progress_pct=100,
                completed_at=datetime.utcnow(),
                csv_files_processed=len(csv_files),
                ticks_inserted=total_ticks,
                candles_created=total_candles,
                status_detail=completion_detail
            )

        except Exception as e:
            await etl_logger.error(f"ETL job failed", error=str(e), error_type=type(e).__name__)
            logger.error(f"Error processing job {job_id}: {str(e)}")
            raise

        finally:
            # Always cleanup job files, even on error
            try:
                cleanup_job_files(job_id)
                logger.info(f"✅ Cleaned up job files for {job_id}")
                await etl_logger.info("Job files cleaned up")
            except Exception as cleanup_error:
                # Don't fail the job if cleanup fails, just log it
                logger.warning(f"⚠️ Failed to cleanup job files for {job_id}: {cleanup_error}")
                await etl_logger.warning(f"Cleanup failed: {cleanup_error}")


async def _mark_job_failed(job_id: UUID, error_message: str):
    """Mark job as failed with error details"""
    async with AsyncSessionLocal() as session:
        await update_job_status(
            session,
            job_id,
            status="failed",
            progress_pct=0,
            completed_at=datetime.utcnow(),
            error_message=error_message
        )
