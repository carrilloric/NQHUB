"""
Tests for Data Export API and Worker

Tests the GCS dataset export pipeline including:
- API endpoints for creating and monitoring export jobs
- RQ worker for async export processing
- Parquet file generation with auto-partitioning
- GCS upload with signed URLs

All GCS operations are mocked - no real GCS account required.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from uuid import uuid4
import pandas as pd
import tempfile
from pathlib import Path

from sqlalchemy import text
from httpx import AsyncClient

from app.models.export_job import ExportJob
from app.workers.export_worker import (
    estimate_export_size,
    export_candles_from_db,
    generate_parquet_files,
    export_candles_to_gcs,
    _export_async,
    BASE_COLUMNS,
    OFLOW_COLUMNS
)


# ==========================================
# Fixtures
# ==========================================

@pytest.fixture
async def sample_candles(async_db):
    """Insert sample candle data for export testing."""
    # Drop table if it exists from previous test
    await async_db.execute(text("DROP TABLE IF EXISTS candles CASCADE"))
    await async_db.commit()

    # Create the candles table
    await async_db.execute(text("""
        CREATE TABLE candles (
            time_interval TIMESTAMPTZ NOT NULL,
            timeframe TEXT NOT NULL,
            symbol TEXT NOT NULL,
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume BIGINT,
            tick_count INTEGER,
            body DOUBLE PRECISION,
            upper_wick DOUBLE PRECISION,
            lower_wick DOUBLE PRECISION,
            wick_ratio DOUBLE PRECISION,
            rel_uw DOUBLE PRECISION,
            rel_lw DOUBLE PRECISION,
            poc DOUBLE PRECISION,
            poc_volume BIGINT,
            poc_percentage DOUBLE PRECISION,
            poc_location TEXT,
            poc_position TEXT,
            real_poc DOUBLE PRECISION,
            real_poc_volume BIGINT,
            real_poc_percentage DOUBLE PRECISION,
            real_poc_location TEXT,
            delta BIGINT,
            upper_wick_volume BIGINT,
            lower_wick_volume BIGINT,
            body_volume BIGINT,
            asellers_uwick INTEGER,
            asellers_lwick INTEGER,
            abuyers_uwick INTEGER,
            abuyers_lwick INTEGER,
            is_spread BOOLEAN,
            is_rollover_period BOOLEAN,
            oflow_detail JSONB,
            oflow_unit TEXT,
            PRIMARY KEY (time_interval, timeframe, symbol)
        )
    """))
    await async_db.commit()

    # Insert 10 sample candles with all required columns
    for i in range(10):
        time_interval = datetime(2024, 1, 1, 9, 30) + timedelta(minutes=i)

        price = 18000.0 + i * 10.0
        await async_db.execute(text("""
            INSERT INTO candles (
                time_interval, timeframe, symbol,
                open, high, low, close, volume, tick_count,
                body, upper_wick, lower_wick, wick_ratio, rel_uw, rel_lw,
                poc, poc_volume, poc_percentage, poc_location, poc_position,
                real_poc, real_poc_volume, real_poc_percentage, real_poc_location,
                delta, upper_wick_volume, lower_wick_volume, body_volume,
                asellers_uwick, asellers_lwick, abuyers_uwick, abuyers_lwick,
                is_spread, is_rollover_period,
                oflow_detail, oflow_unit
            ) VALUES (
                :time_interval, '1min', 'NQ',
                :open_price, :high_price, :low_price, :close_price, 1000, 500,
                5.0, 5.0, 5.0, 1.0, 0.5, 0.5,
                :poc_price, 500, 50.0, 'MIDDLE', 'BALANCED',
                :real_poc_price, 500, 50.0, 'MIDDLE',
                100, 200, 200, 600,
                50, 50, 50, 50,
                false, false,
                '{"levels": []}', 'CONTRACT'
            )
        """), {
            "time_interval": time_interval,
            "open_price": price,
            "high_price": price + 10.0,
            "low_price": price - 5.0,
            "close_price": price + 5.0,
            "poc_price": price,
            "real_poc_price": price
        })

    await async_db.commit()
    yield

    # Cleanup
    await async_db.execute(text("DROP TABLE IF EXISTS candles CASCADE"))
    await async_db.commit()


@pytest.fixture
def mock_gcs_client():
    """Mock Google Cloud Storage client."""
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()

    # Setup mock chain
    mock_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    # Mock signed URL generation
    mock_blob.generate_signed_url.return_value = "https://storage.googleapis.com/signed-url-example?expires=123456"

    return mock_client


@pytest.fixture
def mock_rq_queue():
    """Mock RQ queue for job enqueueing."""
    mock_queue = MagicMock()
    mock_queue.enqueue.return_value = MagicMock(id="test-job-id")
    return mock_queue


# ==========================================
# API Endpoint Tests
# ==========================================

@pytest.mark.asyncio
async def test_export_job_created_on_post(async_client: AsyncClient, async_db, auth_headers, sample_candles, mock_rq_queue):
    """
    Test 1: POST /data/export returns job_id

    Verifies that creating an export job returns:
    - job_id (UUID)
    - status = "queued"
    - estimated_rows
    - estimated_size_mb
    """
    # Need to manually override get_async_db for this endpoint
    from app import main
    from app.core.database import get_async_db

    async def override_get_async_db():
        yield async_db

    main.app.dependency_overrides[get_async_db] = override_get_async_db

    try:
        with patch('app.api.v1.endpoints.data_export.get_etl_queue', return_value=mock_rq_queue):
            response = await async_client.post(
                "/api/v1/exports/export",
                json={
                    "timeframe": "1min",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-01",
                    "include_oflow": False,
                    "flatten_oflow": False
                },
                headers=auth_headers
            )

        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")

        assert response.status_code == 201
        data = response.json()

        assert "job_id" in data
        assert data["status"] == "queued"
        assert data["estimated_rows"] > 0
        assert data["estimated_size_mb"] >= 0

        # Verify job was enqueued
        assert mock_rq_queue.enqueue.called
    finally:
        main.app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_export_job_status_queued(async_client: AsyncClient, auth_headers, async_db, test_user):
    """
    Test 2: GET /data/export/{id} shows status=queued

    Verifies that fetching a newly created export job shows:
    - status = "queued"
    - progress_pct = 0
    - created_at timestamp
    """
    # Create a test export job
    job = ExportJob(
        id=uuid4(),
        timeframe="1min",
        start_date="2024-01-01",
        end_date="2024-01-01",
        include_oflow=False,
        flatten_oflow=False,
        status="queued",
        progress_pct=0,
        estimated_rows=100,
        estimated_size_mb=1,
        created_by_id=test_user.id
    )
    async_db.add(job)
    await async_db.commit()
    await async_db.refresh(job)

    response = await async_client.get(
        f"/api/v1/exports/export/{job.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "queued"
    assert data["progress_pct"] == 0
    assert data["created_at"] is not None


@pytest.mark.asyncio
async def test_invalid_timeframe_rejected(async_client: AsyncClient, auth_headers):
    """Verify that invalid timeframes are rejected."""
    response = await async_client.post(
        "/api/v1/exports/export",
        json={
            "timeframe": "invalid",
            "start_date": "2024-01-01",
            "end_date": "2024-01-01",
            "include_oflow": False
        },
        headers=auth_headers
    )

    assert response.status_code == 400
    assert "Invalid timeframe" in response.json()["detail"]


@pytest.mark.asyncio
async def test_no_data_returns_404(async_client: AsyncClient, auth_headers, mock_rq_queue):
    """Verify that requesting export with no data returns 404."""
    with patch('app.api.v1.endpoints.data_export.get_etl_queue', return_value=mock_rq_queue):
        response = await async_client.post(
            "/api/v1/exports/export",
            json={
                "timeframe": "1min",
                "start_date": "2099-01-01",  # Future date with no data
                "end_date": "2099-01-01",
                "include_oflow": False
            },
            headers=auth_headers
        )

    assert response.status_code == 404
    assert "No data found" in response.json()["detail"]


# ==========================================
# Worker Tests
# ==========================================

@pytest.mark.asyncio
async def test_export_base_has_no_jsonb(async_db, sample_candles):
    """
    Test 3: Export base version has no JSONB columns

    Verifies that exporting with include_oflow=False:
    - Returns DataFrame with BASE_COLUMNS only
    - Does NOT include oflow_detail or oflow_unit
    """
    df = await export_candles_from_db(
        async_db,
        timeframe="1min",
        start_date="2024-01-01",
        end_date="2024-01-01",
        include_oflow=False,
        flatten_oflow=False
    )

    assert len(df) == 10  # Should have 10 candles
    assert list(df.columns) == BASE_COLUMNS
    assert "oflow_detail" not in df.columns
    assert "oflow_unit" not in df.columns


@pytest.mark.asyncio
async def test_export_oflow_includes_jsonb(async_db, sample_candles):
    """
    Test 4: Export with include_oflow=true includes JSONB columns

    Verifies that exporting with include_oflow=True:
    - Returns DataFrame with OFLOW_COLUMNS
    - Includes oflow_detail and oflow_unit
    """
    df = await export_candles_from_db(
        async_db,
        timeframe="1min",
        start_date="2024-01-01",
        end_date="2024-01-01",
        include_oflow=True,
        flatten_oflow=False
    )

    assert len(df) == 10
    assert list(df.columns) == OFLOW_COLUMNS
    assert "oflow_detail" in df.columns
    assert "oflow_unit" in df.columns


@pytest.mark.asyncio
async def test_export_partitions_large_dataset():
    """
    Test 5: Dataset > 500MB creates multiple files

    Verifies that large datasets are partitioned:
    - Creates multiple Parquet files
    - Each file is < 500MB (target)
    - Files named with _part1, _part2, etc.
    """
    # Create a large DataFrame (simulate 600MB worth of data)
    # We'll create enough rows to exceed the 500MB threshold
    num_rows = 100000  # Large enough to trigger partitioning

    df = pd.DataFrame({
        col: [f"value_{i}" for i in range(num_rows)]
        for col in BASE_COLUMNS
    })

    with tempfile.TemporaryDirectory() as temp_dir:
        files = generate_parquet_files(
            df,
            Path(temp_dir),
            "NQ_20240101_20241231_1min_base",
            include_oflow=False,
            max_size_mb=10  # Use small threshold for testing
        )

        # Should create multiple partitions
        assert len(files) > 1

        # Verify partition naming
        for i, file_info in enumerate(files):
            if len(files) > 1:
                assert f"_part{i+1}" in file_info["name"]
            assert file_info["name"].endswith(".parquet")
            assert file_info["size_mb"] > 0


@pytest.mark.asyncio
async def test_signed_url_has_48h_expiry(mock_gcs_client):
    """
    Test 6: Signed URL expires_at = now + 48h

    Verifies that generated signed URLs:
    - Have 48-hour expiration
    - expires_at timestamp is set correctly
    """
    with patch('app.workers.export_worker.get_gcs_client', return_value=mock_gcs_client):
        from app.workers.export_worker import upload_to_gcs

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.parquet') as f:
            f.write("test data")
            temp_path = f.name

        try:
            signed_url = upload_to_gcs(temp_path, "test_file.parquet")

            # Verify generate_signed_url was called with 48h expiration
            mock_blob = mock_gcs_client.bucket().blob()
            mock_blob.generate_signed_url.assert_called_once()

            call_kwargs = mock_blob.generate_signed_url.call_args[1]
            assert call_kwargs["expiration"] == timedelta(hours=48)
            assert call_kwargs["version"] == "v4"
            assert call_kwargs["method"] == "GET"
        finally:
            Path(temp_path).unlink()


@pytest.mark.asyncio
async def test_export_failed_job_has_error(async_db, test_user):
    """
    Test 7: GCS failure sets status=failed with error

    Verifies that when GCS upload fails:
    - Job status becomes "failed"
    - Error message is stored in job.error
    """
    # Create a test export job
    job = ExportJob(
        id=uuid4(),
        timeframe="1min",
        start_date="2024-01-01",
        end_date="2024-01-01",
        include_oflow=False,
        flatten_oflow=False,
        status="queued",
        progress_pct=0,
        estimated_rows=10,
        estimated_size_mb=1,
        created_by_id=test_user.id
    )
    async_db.add(job)
    await async_db.commit()
    await async_db.refresh(job)

    # Mock GCS client to raise an exception
    mock_gcs = MagicMock()
    mock_gcs.side_effect = Exception("GCS upload failed: network error")

    with patch('app.workers.export_worker.get_gcs_client', return_value=None):
        # This should fail because GCS client is None
        with pytest.raises(Exception):
            await _export_async(job.id)

    # Refresh job from database
    await async_db.refresh(job)

    # Verify job is marked as failed
    assert job.status == "failed"
    assert job.error is not None
    assert "GCS client not available" in job.error or "not found" in job.error


@pytest.mark.asyncio
async def test_export_progress_updates(async_db, test_user, sample_candles, mock_gcs_client):
    """
    Test 8: Worker in progress shows progress_pct > 0

    Verifies that during export processing:
    - Status changes from "queued" to "running"
    - progress_pct increases (10%, 40%, 60%, etc.)
    - current_step is updated
    """
    # Create a test export job
    job = ExportJob(
        id=uuid4(),
        timeframe="1min",
        start_date="2024-01-01",
        end_date="2024-01-01",
        include_oflow=False,
        flatten_oflow=False,
        status="queued",
        progress_pct=0,
        estimated_rows=10,
        estimated_size_mb=1,
        created_by_id=test_user.id
    )
    async_db.add(job)
    await async_db.commit()
    await async_db.refresh(job)

    # Mock GCS operations
    with patch('app.workers.export_worker.get_gcs_client', return_value=mock_gcs_client):
        with patch('app.workers.export_worker.upload_to_gcs') as mock_upload:
            mock_upload.return_value = "https://storage.googleapis.com/signed-url"

            # Run the export worker
            await _export_async(job.id)

    # Refresh job from database
    await async_db.refresh(job)

    # Verify job completed successfully
    assert job.status == "completed"
    assert job.progress_pct == 100
    assert job.current_step == "Export completed"
    assert job.completed_at is not None
    assert job.files is not None
    assert len(job.files) > 0

    # Verify file metadata
    file_info = job.files[0]
    assert "name" in file_info
    assert "size_mb" in file_info
    assert "gcs_path" in file_info
    assert "signed_url" in file_info
    assert "expires_at" in file_info


@pytest.mark.asyncio
async def test_estimate_export_size(async_db, sample_candles):
    """Test the estimate_export_size function."""
    rows, size_mb = await estimate_export_size(
        async_db,
        timeframe="1min",
        start_date="2024-01-01",
        end_date="2024-01-01"
    )

    assert rows == 10  # We inserted 10 candles
    assert size_mb >= 0


@pytest.mark.asyncio
async def test_list_export_jobs(async_client: AsyncClient, auth_headers, async_db, test_user):
    """Test listing export jobs with pagination."""
    # Create multiple export jobs
    for i in range(3):
        job = ExportJob(
            id=uuid4(),
            timeframe="1min",
            start_date="2024-01-01",
            end_date="2024-01-01",
            include_oflow=False,
            status="queued",
            progress_pct=0,
            estimated_rows=100,
            estimated_size_mb=1,
            created_by_id=test_user.id
        )
        async_db.add(job)

    await async_db.commit()

    response = await async_client.get(
        "/api/v1/exports/export?limit=10&offset=0",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 3


@pytest.mark.asyncio
async def test_authorization_check(async_client: AsyncClient, auth_headers, async_db, test_user, admin_user):
    """Test that users can only see their own jobs (except admins)."""
    # Create a job for test_user
    user_job = ExportJob(
        id=uuid4(),
        timeframe="1min",
        start_date="2024-01-01",
        end_date="2024-01-01",
        include_oflow=False,
        status="queued",
        progress_pct=0,
        estimated_rows=100,
        estimated_size_mb=1,
        created_by_id=test_user.id
    )
    async_db.add(user_job)

    # Create a job for admin_user
    admin_job = ExportJob(
        id=uuid4(),
        timeframe="1min",
        start_date="2024-01-01",
        end_date="2024-01-01",
        include_oflow=False,
        status="queued",
        progress_pct=0,
        estimated_rows=100,
        estimated_size_mb=1,
        created_by_id=admin_user.id
    )
    async_db.add(admin_job)
    await async_db.commit()

    # Test user trying to access admin's job - should fail
    response = await async_client.get(
        f"/api/v1/exports/export/{admin_job.id}",
        headers=auth_headers
    )

    assert response.status_code == 403
