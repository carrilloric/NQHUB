# GCS Dataset Export Pipeline (AUT-334)

## Overview

This implements a background job system for exporting candlestick datasets from TimescaleDB to Google Cloud Storage (GCS) in Parquet format.

## Implementation

### 1. Database Model
- **File**: `app/models/export_job.py`
- **Table**: `export_jobs`
- **Migration**: `alembic/versions/20260329_2200-add_export_jobs_table.py`

Tracks export job state:
- Job parameters (timeframe, date range, export options)
- Progress tracking (status, progress_pct, current_step)
- Results (files metadata with signed URLs)
- Error handling

### 2. Background Worker
- **File**: `app/workers/export_worker.py`
- **Pattern**: RQ (Redis Queue) async worker
- **Entry point**: `export_candles_to_gcs(job_id: str)`

Features:
- Queries TimescaleDB for candlestick data
- Generates Parquet files with gzip compression
- Auto-partitions files > 500MB
- Uploads to GCS with signed URLs (48h TTL)
- Two export versions:
  - **base**: 33 columns (OHLCV + structural data + orderflow metrics)
  - **oflow**: base + `oflow_detail` + `oflow_unit` (JSONB columns)

### 3. API Endpoints
- **File**: `app/api/v1/endpoints/data_export.py`
- **Base URL**: `/api/v1/exports/`

**POST /exports/export** - Create export job
```json
{
  "timeframe": "1min",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "include_oflow": false,
  "flatten_oflow": false
}
```

**GET /exports/export/{job_id}** - Get job status

**GET /exports/export** - List jobs (admin sees all, users see own)

### 4. Configuration
- **File**: `app/config.py`

New settings:
- `GCS_BUCKET_NAME`: Target GCS bucket (default: "nqhub-datasets")
- `GCS_CREDENTIALS_JSON`: Service account JSON or path to JSON file
- `GCS_PROJECT_ID`: GCP project ID

### 5. Test Suite
- **File**: `tests/test_data_export.py`
- **Status**: ⚠️ Tests written but require database schema setup

13 comprehensive tests covering:
- API endpoint creation and status checking
- Base vs oflow export versions
- Auto-partitioning for large datasets
- Signed URL expiration (48h)
- Error handling and job failures
- Progress updates during processing
- Authorization (users see own jobs, admins see all)

## Router Registration

**NOTE**: The export router is at `/exports` prefix (not `/data`) to avoid conflicts with the existing data_platform export endpoint at `/data/export`.

```python
# app/api/v1/__init__.py
api_router.include_router(data_export.router, prefix="/exports", tags=["data-export"])
```

## Dependencies

### Python Packages
- `pyarrow` - Parquet file generation ✅ Installed
- `pandas` - Data manipulation (already in requirements)
- `google-cloud-storage` - GCS upload (to be installed for production)

### Database Requirements

The worker expects a unified `candles` table with the following schema:

```sql
CREATE TABLE candles (
    time_interval TIMESTAMPTZ NOT NULL,
    timeframe TEXT NOT NULL,
    symbol TEXT NOT NULL,
    -- OHLCV
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume BIGINT,
    tick_count INTEGER,
    -- Structural metrics
    body DOUBLE PRECISION,
    upper_wick DOUBLE PRECISION,
    lower_wick DOUBLE PRECISION,
    wick_ratio DOUBLE PRECISION,
    rel_uw DOUBLE PRECISION,
    rel_lw DOUBLE PRECISION,
    -- POC metrics
    poc DOUBLE PRECISION,
    poc_volume BIGINT,
    poc_percentage DOUBLE PRECISION,
    poc_location TEXT,
    poc_position TEXT,
    real_poc DOUBLE PRECISION,
    real_poc_volume BIGINT,
    real_poc_percentage DOUBLE PRECISION,
    real_poc_location TEXT,
    -- Orderflow metrics
    delta BIGINT,
    upper_wick_volume BIGINT,
    lower_wick_volume BIGINT,
    body_volume BIGINT,
    asellers_uwick INTEGER,
    asellers_lwick INTEGER,
    abuyers_uwick INTEGER,
    abuyers_lwick INTEGER,
    -- Flags
    is_spread BOOLEAN,
    is_rollover_period BOOLEAN,
    -- JSONB columns (oflow version only)
    oflow_detail JSONB,
    oflow_unit TEXT,
    PRIMARY KEY (time_interval, timeframe, symbol)
);
```

**Current State**: Production database has `candlestick_*` tables (candlestick_1min, candlestick_5min, etc.), not a unified `candles` table. The worker will need to be adapted to query the appropriate timeframe-specific table, OR a unified view/table needs to be created.

## Testing

### Run Tests
```bash
cd backend
source .venv/bin/activate
pytest tests/test_data_export.py -v
```

### Test Requirements
1. Test database must have `candles` table schema (see above)
2. OR tests need to mock the database queries

### GCS Mocking
All GCS operations are mocked in tests - no real GCS account required. The `get_gcs_client()` function is patched to return mock objects.

## Production Deployment

### Prerequisites
1. Install `google-cloud-storage`:
   ```bash
   uv pip install google-cloud-storage
   ```

2. Set environment variables:
   ```bash
   export GCS_BUCKET_NAME="your-bucket-name"
   export GCS_PROJECT_ID="your-project-id"
   export GCS_CREDENTIALS_JSON='{"type":"service_account",...}'
   # OR
   export GCS_CREDENTIALS_JSON="/path/to/service-account.json"
   ```

3. Ensure RQ worker is running:
   ```bash
   rq worker --url redis://localhost:6379
   ```

4. Apply database migration:
   ```bash
   alembic upgrade export_jobs_001
   ```

### Usage Example

```python
import httpx

# Create export job
response = httpx.post(
    "http://localhost:8002/api/v1/exports/export",
    json={
        "timeframe": "1min",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "include_oflow": True,
        "flatten_oflow": False
    },
    headers={"Authorization": f"Bearer {token}"}
)

job = response.json()
print(f"Job ID: {job['job_id']}")
print(f"Estimated: {job['estimated_rows']} rows, {job['estimated_size_mb']} MB")

# Check status
status_response = httpx.get(
    f"http://localhost:8002/api/v1/exports/export/{job['job_id']}",
    headers={"Authorization": f"Bearer {token}"}
)

status = status_response.json()
print(f"Status: {status['status']} ({status['progress_pct']}%)")

if status['status'] == 'completed':
    for file in status['files']:
        print(f"File: {file['name']} ({file['size_mb']} MB)")
        print(f"Download: {file['signed_url']}")
        print(f"Expires: {file['expires_at']}")
```

## Architecture Decisions

1. **RQ over Celery**: Project already uses RQ for ETL workers, maintaining consistency

2. **Parquet format**: Columnar storage with compression for efficient ML/analytics

3. **Auto-partitioning**: Prevents memory issues and enables parallel downloads for large datasets

4. **Signed URLs**: Secure, time-limited access without exposing GCS credentials

5. **Two export versions**:
   - Base version for most use cases (smaller files)
   - Oflow version for advanced order flow analysis

6. **Separate router prefix**: `/exports` instead of `/data` to avoid conflicts with existing data_platform export

## Known Issues

1. **Test Database Schema**: Tests require `candles` table to exist in test database. Production has `candlestick_*` tables instead.

   **Resolution Options**:
   - A) Create unified `candles` table/view in production
   - B) Update worker to query appropriate `candlestick_{timeframe}` table
   - C) Create `candles` table in test fixtures only (current approach)

2. **Router Conflict**: Original spec had `/data/export` but conflicts with existing data_platform router. Changed to `/exports/export`.

## Related Files

- Linear Issue: AUT-334
- Contract: F5.3 Dataset Builder & Versioning
- Related: CONTRACT-001 (data_platform export - different system)

## Future Enhancements

- [ ] Support for custom column selection
- [ ] Compression format options (gzip, snappy, brotli)
- [ ] Email notification on completion
- [ ] Incremental exports (only new data since last export)
- [ ] Export to multiple cloud providers (AWS S3, Azure Blob)
- [ ] Export scheduling/recurring jobs
