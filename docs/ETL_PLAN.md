# NQHUB ETL System - Implementation Plan

**Created**: 2025-11-02
**Status**: Planning Phase
**Database**: PostgreSQL + TimescaleDB (port 5433)

---

## 📋 Overview

Complete ETL (Extract, Transform, Load) pipeline to process Databento ZIP archives containing tick-by-tick NQ Futures market data and populate 8 timeframe candlestick tables with order flow analytics.

### High-Level Flow

```
User Uploads ZIP → Backend API → Extract & Validate → Parse CSV →
→ Insert Ticks → Detect Rollovers → Aggregate Candles (8 timeframes) →
→ Update Frontend Progress → Complete
```

---

## 🎯 System Components

### 1. Backend ETL Engine

**Location**: `backend/app/etl/`

```
backend/app/etl/
├── __init__.py
├── models.py              # SQLAlchemy models for ETL tables
├── schemas.py             # Pydantic schemas for API
├── services/
│   ├── upload_service.py      # File upload handling
│   ├── extraction_service.py  # ZIP extraction
│   ├── parser_service.py      # CSV parsing
│   ├── tick_loader.py         # Tick data insertion
│   ├── candle_builder.py      # Candlestick aggregation
│   ├── rollover_detector.py  # Rollover period detection
│   └── job_manager.py         # Job queue and progress tracking
├── routes.py              # FastAPI routes
├── tasks.py               # Background tasks (Celery/RQ)
└── utils.py               # Helper functions
```

### 2. Frontend ETL Dashboard

**Location**: `frontend/src/client/pages/DataModule.tsx` (existing Data Module)

New components to add:

```
frontend/src/client/components/data-module/etl/
├── FileUploader.tsx           # Drag & drop file upload
├── ETLDashboard.tsx          # Main dashboard component
├── ProcessingStatus.tsx      # Real-time job status
├── ProcessedFilesList.tsx    # History of processed files
├── RolloverPeriodsList.tsx   # Detected rollover periods
├── StatisticsPanel.tsx       # Database statistics
└── ProgressChart.tsx         # Visual progress indicators
```

### 3. Database Tables (Already Created)

- ✅ `market_data_ticks` - Raw tick data (TimescaleDB hypertable)
- ✅ `candlestick_*` - 8 timeframe tables
- ✅ `rollover_periods` - Rollover tracking
- ✅ `processed_files` - Duplicate prevention

### 4. Background Job Queue

**Technology**: Choose one:
- **Option A**: FastAPI BackgroundTasks (simple, no dependencies)
- **Option B**: Celery + Redis (robust, scalable)
- **Option C**: Python RQ (lightweight, Redis-based)

**Recommendation**: Start with **RQ** (lightweight but production-ready)

---

## 🔧 Implementation Phases

## Phase 1: File Upload & Storage (Week 1)

### Backend Tasks

**1.1 File Upload API Endpoint**

```python
# backend/app/etl/routes.py

@router.post("/upload-zip")
async def upload_zip_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """
    Upload a Databento ZIP file for processing.
    Returns: job_id for tracking progress
    """
    # 1. Validate file extension (.zip)
    # 2. Check file size (< 5GB)
    # 3. Generate unique job_id (UUID)
    # 4. Save to temporary storage: /tmp/etl_jobs/{job_id}/
    # 5. Extract metadata.json and manifest.json
    # 6. Validate ZIP structure
    # 7. Create job record in database
    # 8. Queue background task
    # 9. Return job_id and initial status
```

**1.2 Temporary Storage Structure**

```
/tmp/etl_jobs/
└── {job_id}/
    ├── original.zip                    # Uploaded ZIP
    ├── extracted/                      # Extracted contents
    │   ├── metadata.json
    │   ├── manifest.json
    │   ├── symbology.json
    │   └── glbx-mdp3-*.tbbo.csv.zst   # Compressed CSV files
    ├── progress.json                   # Job progress tracking
    └── errors.log                      # Error log
```

**1.3 Job Status Tracking Table**

```sql
CREATE TABLE etl_jobs (
    id              UUID PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id),
    zip_filename    VARCHAR(255) NOT NULL,
    file_size_mb    FLOAT,
    status          VARCHAR(20) DEFAULT 'pending',
    -- Statuses: pending, extracting, parsing, loading_ticks,
    --           building_candles, detecting_rollovers, completed, failed

    total_steps     INTEGER DEFAULT 8,
    current_step    INTEGER DEFAULT 0,
    progress_pct    INTEGER DEFAULT 0,

    -- Statistics
    csv_files_found     INTEGER,
    csv_files_processed INTEGER DEFAULT 0,
    ticks_inserted      BIGINT DEFAULT 0,
    candles_created     INTEGER DEFAULT 0,

    -- Timing
    started_at      TIMESTAMP WITH TIME ZONE,
    completed_at    TIMESTAMP WITH TIME ZONE,

    -- Error handling
    error_message   TEXT,
    error_details   JSONB,

    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**1.4 Frontend File Uploader Component**

```typescript
// frontend/src/client/components/data-module/etl/FileUploader.tsx

export function FileUploader() {
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const handleUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/api/v1/etl/upload-zip', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });

    const { job_id } = await response.json();

    // Redirect to monitoring page
    navigate(`/data/etl/jobs/${job_id}`);
  };

  return (
    <div className="border-2 border-dashed rounded-lg p-8">
      <input type="file" accept=".zip" onChange={...} />
      <p>Drag & drop Databento ZIP files here</p>
      <p className="text-sm">Max size: 5GB</p>
    </div>
  );
}
```

---

## Phase 2: ZIP Extraction & CSV Parsing (Week 1-2)

### Backend Tasks

**2.1 ZIP Extraction Service**

```python
# backend/app/etl/services/extraction_service.py

import zipfile
import zstandard as zstd
from pathlib import Path

class ExtractionService:
    def extract_zip(self, job_id: str, zip_path: Path):
        """
        Extract ZIP archive and decompress .zst files.

        Steps:
        1. Extract ZIP to /tmp/etl_jobs/{job_id}/extracted/
        2. Read metadata.json and manifest.json
        3. Find all *.csv.zst files
        4. Decompress .zst to .csv (using zstandard)
        5. Update job status to 'parsing'
        6. Return list of CSV file paths
        """
        job_dir = Path(f"/tmp/etl_jobs/{job_id}")
        extract_dir = job_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)

        # Extract ZIP
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Find and decompress .zst files
        csv_files = []
        for zst_file in extract_dir.glob("*.csv.zst"):
            csv_file = zst_file.with_suffix('')  # Remove .zst

            with open(zst_file, 'rb') as f_in:
                dctx = zstd.ZstdDecompressor()
                with open(csv_file, 'wb') as f_out:
                    dctx.copy_stream(f_in, f_out)

            csv_files.append(csv_file)
            zst_file.unlink()  # Delete .zst after decompression

        return csv_files
```

**2.2 CSV Parser Service**

```python
# backend/app/etl/services/parser_service.py

import pandas as pd
from datetime import datetime

class CSVParserService:
    def parse_csv(self, csv_path: Path):
        """
        Parse Databento CSV file.

        Columns (20 total):
        0: ts_recv, 1: ts_event, 2: rtype, 3: publisher_id,
        4: instrument_id, 5: action, 6: side, 7: depth,
        8: price, 9: size, 10: flags, 11: ts_in_delta,
        12: sequence, 13: bid_px_00, 14: ask_px_00,
        15: bid_sz_00, 16: ask_sz_00, 17: bid_ct_00,
        18: ask_ct_00, 19: symbol

        Returns: Generator of tick dictionaries for batch insertion
        """
        # Use pandas for efficient CSV parsing
        for chunk in pd.read_csv(csv_path, chunksize=10000):
            for _, row in chunk.iterrows():
                yield {
                    'ts_recv': pd.to_datetime(row['ts_recv']),
                    'ts_event': pd.to_datetime(row['ts_event']),
                    'symbol': row['symbol'],
                    'is_spread': '-' in row['symbol'],  # Detect spreads
                    'is_rollover_period': False,  # Will be updated later
                    'price': float(row['price']),
                    'size': int(row['size']),
                    'side': row['side'],
                    'action': row['action'],
                    'bid_px': float(row['bid_px_00']),
                    'ask_px': float(row['ask_px_00']),
                    'bid_sz': int(row['bid_sz_00']),
                    'ask_sz': int(row['ask_sz_00']),
                    'bid_ct': int(row['bid_ct_00']),
                    'ask_ct': int(row['ask_ct_00']),
                    'rtype': int(row['rtype']),
                    'publisher_id': int(row['publisher_id']),
                    'instrument_id': int(row['instrument_id']),
                    'sequence': int(row['sequence']),
                    'flags': int(row['flags']),
                    'ts_in_delta': int(row['ts_in_delta']),
                    'depth': int(row['depth'])
                }
```

---

## Phase 3: Tick Data Loading (Week 2)

### Backend Tasks

**3.1 Bulk Insert Service**

```python
# backend/app/etl/services/tick_loader.py

from sqlalchemy import insert
from sqlalchemy.dialects.postgresql import insert as pg_insert

class TickLoaderService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_insert_ticks(
        self,
        ticks: List[Dict],
        job_id: str
    ):
        """
        Bulk insert ticks into market_data_ticks table.

        Performance optimizations:
        - Batch size: 5000 ticks per insert
        - Use PostgreSQL COPY for maximum speed
        - Update job progress every 50k ticks
        """
        batch_size = 5000
        batch = []
        total_inserted = 0

        for tick in ticks:
            batch.append(tick)

            if len(batch) >= batch_size:
                # Bulk insert
                stmt = insert(MarketDataTicks).values(batch)
                await self.session.execute(stmt)
                await self.session.commit()

                total_inserted += len(batch)
                batch = []

                # Update job progress
                if total_inserted % 50000 == 0:
                    await self.update_job_progress(
                        job_id,
                        ticks_inserted=total_inserted
                    )

        # Insert remaining batch
        if batch:
            stmt = insert(MarketDataTicks).values(batch)
            await self.session.execute(stmt)
            await self.session.commit()
            total_inserted += len(batch)

        return total_inserted
```

**3.2 Duplicate Detection**

Before inserting, check if CSV file was already processed:

```python
async def check_duplicate(
    zip_filename: str,
    csv_filename: str
) -> bool:
    """
    Check if this CSV was already processed.
    Uses unique constraint on processed_files table.
    """
    result = await session.execute(
        select(ProcessedFiles).where(
            ProcessedFiles.zip_filename == zip_filename,
            ProcessedFiles.csv_filename == csv_filename
        )
    )
    return result.scalar() is not None
```

---

## Phase 3.5: Data Coverage Tracking (Week 2)

### New Table: candle_coverage

**Purpose**: Track which days have been populated in each timeframe for granular control and visibility.

```sql
CREATE TABLE candle_coverage (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,
    symbol          VARCHAR(20) NOT NULL,
    timeframe       VARCHAR(10) NOT NULL,
    -- Timeframe values: '30s', '1min', '5min', '15min', '1hr', '4hr', 'daily', 'weekly'

    -- Status tracking
    status          VARCHAR(20) DEFAULT 'pending',
    -- Status values: pending, processing, completed, failed

    -- Statistics
    candles_count   INTEGER,
    first_candle    TIMESTAMP WITH TIME ZONE,
    last_candle     TIMESTAMP WITH TIME ZONE,

    -- Processing info
    processed_at    TIMESTAMP WITH TIME ZONE,
    error_message   TEXT,

    CONSTRAINT uq_candle_coverage UNIQUE (date, symbol, timeframe),
    CONSTRAINT check_timeframe CHECK (timeframe IN (
        '30s', '1min', '5min', '15min', '1hr', '4hr', 'daily', 'weekly'
    ))
);

CREATE INDEX idx_coverage_date ON candle_coverage(date);
CREATE INDEX idx_coverage_timeframe ON candle_coverage(timeframe);
CREATE INDEX idx_coverage_status ON candle_coverage(status);
```

**Usage Example**:
```sql
-- Insert coverage record after processing
INSERT INTO candle_coverage (date, symbol, timeframe, status, candles_count, processed_at)
VALUES ('2024-07-19', 'NQU4', '5min', 'completed', 288, NOW());

-- Query coverage for a date range
SELECT date, timeframe, status, candles_count
FROM candle_coverage
WHERE date BETWEEN '2024-07-01' AND '2024-07-31'
  AND symbol = 'NQU4'
ORDER BY date, timeframe;
```

---

## Phase 4: Rollover Detection (Week 2)

### Backend Tasks

**4.1 Rollover Detector Service**

```python
# backend/app/etl/services/rollover_detector.py

class RolloverDetectorService:
    async def detect_rollovers(self, session: AsyncSession, job_id: str):
        """
        Detect rollover periods from inserted ticks.

        Logic:
        1. Query for spread symbols (WHERE is_spread = true)
        2. Group by symbol, get date range and tick count
        3. Extract old/new contracts from spread symbols
        4. Insert into rollover_periods table
        5. Update is_rollover_period flag on ticks
        """
        # Find all spread symbols
        result = await session.execute("""
            SELECT
                symbol,
                MIN(ts_event) as start_date,
                MAX(ts_event) as end_date,
                COUNT(*) as tick_count
            FROM market_data_ticks
            WHERE is_spread = true
            GROUP BY symbol
        """)

        for row in result:
            # Parse symbol: "NQH4-NQM4" → old=NQH4, new=NQM4
            old_contract, new_contract = row.symbol.split('-')

            # Insert rollover period
            rollover = RolloverPeriod(
                contract_old=old_contract,
                contract_new=new_contract,
                start_date=row.start_date,
                end_date=row.end_date,
                total_spread_ticks=row.tick_count,
                status='completed'
            )
            session.add(rollover)

        await session.commit()

        # Update is_rollover_period flag
        await session.execute("""
            UPDATE market_data_ticks
            SET is_rollover_period = true
            WHERE ts_event >= (
                SELECT MIN(start_date) FROM rollover_periods
            )
            AND ts_event <= (
                SELECT MAX(end_date) FROM rollover_periods
            )
        """)
        await session.commit()
```

---

## Phase 5: Candlestick Aggregation (Week 3)

### Backend Tasks

**5.1 Candle Builder Service**

```python
# backend/app/etl/services/candle_builder.py

class CandleBuilderService:
    TIMEFRAMES = {
        '30s': '30 seconds',
        '1min': '1 minute',
        '5min': '5 minutes',
        '15min': '15 minutes',
        '1hr': '1 hour',
        '4hr': '4 hours',
        'daily': '1 day',
        'weekly': '1 week'
    }

    async def build_candles(
        self,
        session: AsyncSession,
        job_id: str,
        csv_filename: str,
        selected_timeframes: List[str] = None  # NEW: Allow timeframe selection
    ):
        """
        Build selected timeframes of candlesticks.

        Args:
            selected_timeframes: List of timeframes to build (e.g., ['5min', '1hr'])
                                If None, builds all 8 timeframes

        Strategy: Use TimescaleDB time_bucket() for efficient aggregation
        """
        # Default to all timeframes if none specified
        if selected_timeframes is None:
            selected_timeframes = list(self.TIMEFRAMES.keys())

        # Validate timeframes
        invalid = [tf for tf in selected_timeframes if tf not in self.TIMEFRAMES]
        if invalid:
            raise ValueError(f"Invalid timeframes: {invalid}")

        # Get date range from this CSV file
        result = await session.execute("""
            SELECT
                MIN(ts_event) as start_date,
                MAX(ts_event) as end_date,
                DATE(MIN(ts_event)) as start_day,
                DATE(MAX(ts_event)) as end_day
            FROM market_data_ticks mdt
            JOIN processed_files pf ON pf.csv_filename = :csv_filename
            WHERE mdt.ts_event BETWEEN pf.start_date AND pf.end_date
        """, {'csv_filename': csv_filename})

        date_range = result.first()

        # Build each selected timeframe
        total_timeframes = len(selected_timeframes)
        for idx, timeframe in enumerate(selected_timeframes):
            interval = self.TIMEFRAMES[timeframe]

            # Mark as processing in coverage table
            await self._mark_coverage_status(
                session,
                date_range.start_day,
                date_range.end_day,
                timeframe,
                'processing'
            )

            try:
                # Build the timeframe
                candles_created = await self._build_timeframe(
                    session,
                    timeframe,
                    interval,
                    date_range.start_date,
                    date_range.end_date
                )

                # Mark as completed in coverage table
                await self._mark_coverage_status(
                    session,
                    date_range.start_day,
                    date_range.end_day,
                    timeframe,
                    'completed',
                    candles_count=candles_created
                )

            except Exception as e:
                # Mark as failed in coverage table
                await self._mark_coverage_status(
                    session,
                    date_range.start_day,
                    date_range.end_day,
                    timeframe,
                    'failed',
                    error_message=str(e)
                )
                raise

            # Update job progress
            await self.update_job_progress(
                job_id,
                current_step=idx + 1,
                progress_pct=int(((idx + 1) / total_timeframes) * 100)
            )
```

**5.2 Single Timeframe Builder**

```python
async def _build_timeframe(
    self,
    session: AsyncSession,
    timeframe: str,
    interval: str,
    start_date: datetime,
    end_date: datetime
):
    """
    Build candles for a single timeframe using SQL aggregation.

    This is a COMPLEX query that calculates:
    - OHLCV
    - POC (regular and real)
    - Candle structure
    - Volume distribution
    - Absorption indicators
    - Order flow (delta and JSONB)
    """
    table_name = f'candlestick_{timeframe}'

    # Step 1: Basic OHLCV aggregation
    await session.execute(f"""
        INSERT INTO {table_name} (
            time_interval, symbol, is_spread, is_rollover_period,
            open, high, low, close, volume, tick_count
        )
        SELECT
            time_bucket('{interval}', ts_event) as time_interval,
            symbol,
            is_spread,
            is_rollover_period,
            FIRST(price, ts_event) as open,
            MAX(price) as high,
            MIN(price) as low,
            LAST(price, ts_event) as close,
            SUM(size) as volume,
            COUNT(*) as tick_count
        FROM market_data_ticks
        WHERE ts_event BETWEEN :start_date AND :end_date
        GROUP BY time_interval, symbol, is_spread, is_rollover_period
        ON CONFLICT (time_interval, symbol) DO NOTHING
    """, {'start_date': start_date, 'end_date': end_date})

    # Step 2: Calculate POC, order flow, etc. (separate updates)
    await self._calculate_poc(session, table_name, start_date, end_date)
    await self._calculate_order_flow(session, table_name, start_date, end_date)
    await self._calculate_candle_structure(session, table_name)
    await self._calculate_absorption(session, table_name)
```

**5.3 Coverage Status Helper**

```python
async def _mark_coverage_status(
    self,
    session: AsyncSession,
    start_day: date,
    end_day: date,
    timeframe: str,
    status: str,
    candles_count: int = None,
    error_message: str = None
):
    """
    Mark coverage status for a date range and timeframe.

    Creates or updates coverage records for each day in the range.
    """
    current_day = start_day
    while current_day <= end_day:
        # Get symbols for this day
        result = await session.execute("""
            SELECT DISTINCT symbol
            FROM market_data_ticks
            WHERE DATE(ts_event) = :day
        """, {'day': current_day})

        symbols = [row[0] for row in result]

        for symbol in symbols:
            # Upsert coverage record
            stmt = """
                INSERT INTO candle_coverage (
                    date, symbol, timeframe, status,
                    candles_count, processed_at, error_message
                )
                VALUES (:date, :symbol, :timeframe, :status,
                        :candles_count, :processed_at, :error_message)
                ON CONFLICT (date, symbol, timeframe)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    candles_count = EXCLUDED.candles_count,
                    processed_at = EXCLUDED.processed_at,
                    error_message = EXCLUDED.error_message
            """
            await session.execute(stmt, {
                'date': current_day,
                'symbol': symbol,
                'timeframe': timeframe,
                'status': status,
                'candles_count': candles_count,
                'processed_at': datetime.now() if status == 'completed' else None,
                'error_message': error_message
            })

        current_day += timedelta(days=1)

    await session.commit()
```

**5.4 Order Flow Calculation**

```python
async def _calculate_order_flow(
    self,
    session: AsyncSession,
    table_name: str,
    start_date: datetime,
    end_date: datetime
):
    """
    Calculate order flow JSONB at 0.25 tick and 1.0 point granularity.

    This is the MOST COMPLEX calculation.
    """
    # Build order flow detail (0.25 tick)
    await session.execute(f"""
        UPDATE {table_name} c
        SET
            oflow_detail = subq.oflow_detail,
            oflow_unit = subq.oflow_unit,
            delta = subq.delta
        FROM (
            SELECT
                time_bucket('{self.TIMEFRAMES[table_name.split('_')[1]]}', ts_event) as time_interval,
                symbol,

                -- Build JSONB for 0.25 tick detail
                jsonb_object_agg(
                    price::text,
                    jsonb_build_object(
                        'asks', SUM(CASE WHEN side = 'A' THEN size ELSE 0 END),
                        'bids', SUM(CASE WHEN side = 'B' THEN size ELSE 0 END)
                    )
                ) as oflow_detail,

                -- Build JSONB for 1.0 point unit (floor to nearest point)
                jsonb_object_agg(
                    FLOOR(price)::text,
                    jsonb_build_object(
                        'asks', SUM(CASE WHEN side = 'A' THEN size ELSE 0 END),
                        'bids', SUM(CASE WHEN side = 'B' THEN size ELSE 0 END)
                    )
                ) as oflow_unit,

                -- Calculate delta
                SUM(CASE WHEN side = 'B' THEN size ELSE 0 END) -
                SUM(CASE WHEN side = 'A' THEN size ELSE 0 END) as delta

            FROM market_data_ticks
            WHERE ts_event BETWEEN :start_date AND :end_date
            GROUP BY time_interval, symbol
        ) subq
        WHERE c.time_interval = subq.time_interval
          AND c.symbol = subq.symbol
    """, {'start_date': start_date, 'end_date': end_date})
```

---

## Phase 6: Frontend Monitoring Dashboard (Week 3-4)

### Frontend Components

**6.1 ETL Dashboard Page**

```typescript
// frontend/src/client/pages/ETLDashboard.tsx

export function ETLDashboard() {
  const [selectedTab, setSelectedTab] = useState('upload');

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">ETL Pipeline</h1>

      {/* Tab Navigation */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList>
          <TabsTrigger value="upload">Upload</TabsTrigger>
          <TabsTrigger value="coverage">Data Coverage</TabsTrigger>
          <TabsTrigger value="jobs">Jobs</TabsTrigger>
          <TabsTrigger value="stats">Statistics</TabsTrigger>
        </TabsList>

        {/* Upload Tab */}
        <TabsContent value="upload">
          <Card>
            <CardHeader>
              <CardTitle>Upload Data Files</CardTitle>
            </CardHeader>
            <CardContent>
              <FileUploaderWithTimeframeSelection />
            </CardContent>
          </Card>

          {/* Active Jobs */}
          <Card className="mt-4">
            <CardHeader>
              <CardTitle>Active Processing Jobs</CardTitle>
            </CardHeader>
            <CardContent>
              <ActiveJobsList />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Coverage Tab - NEW */}
        <TabsContent value="coverage">
          <DataCoverageDashboard />
        </TabsContent>

        {/* Jobs Tab */}
        <TabsContent value="jobs">
          <Card>
            <CardHeader>
              <CardTitle>Processing History</CardTitle>
            </CardHeader>
            <CardContent>
              <ProcessedFilesList />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Statistics Tab */}
        <TabsContent value="stats">
          <div className="grid grid-cols-2 gap-4">
            <StatisticsPanel />
            <RolloverPeriodsList />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

**6.2 File Uploader with Timeframe Selection (NEW)**

```typescript
// frontend/src/client/components/data-module/etl/FileUploaderWithTimeframeSelection.tsx

const TIMEFRAMES = [
  { id: '30s', label: '30 seconds', description: 'Ultra-short term' },
  { id: '1min', label: '1 minute', description: 'Scalping' },
  { id: '5min', label: '5 minutes', description: 'Day trading' },
  { id: '15min', label: '15 minutes', description: 'Swing trading' },
  { id: '1hr', label: '1 hour', description: 'Position tracking' },
  { id: '4hr', label: '4 hours', description: 'Swing positions' },
  { id: 'daily', label: 'Daily', description: 'Long-term trends' },
  { id: 'weekly', label: 'Weekly', description: 'Macro analysis' }
];

export function FileUploaderWithTimeframeSelection() {
  const [file, setFile] = useState<File | null>(null);
  const [selectedTimeframes, setSelectedTimeframes] = useState<string[]>([]);
  const [selectAll, setSelectAll] = useState(true);
  const [uploading, setUploading] = useState(false);

  const handleToggleAll = () => {
    if (selectAll) {
      setSelectedTimeframes([]);
    } else {
      setSelectedTimeframes(TIMEFRAMES.map(tf => tf.id));
    }
    setSelectAll(!selectAll);
  };

  const handleToggleTimeframe = (timeframeId: string) => {
    setSelectedTimeframes(prev =>
      prev.includes(timeframeId)
        ? prev.filter(id => id !== timeframeId)
        : [...prev, timeframeId]
    );
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      // Only send selected_timeframes if not all selected
      const timeframesToSend = selectAll ? null : selectedTimeframes;

      const response = await fetch('/api/v1/etl/upload-zip', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          selected_timeframes: timeframesToSend
        })
      });

      const { job_id } = await response.json();
      navigate(`/data/etl/jobs/${job_id}`);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* File Selection */}
      <div className="border-2 border-dashed rounded-lg p-8">
        <input
          type="file"
          accept=".zip"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        <p>Drag & drop Databento ZIP files here</p>
        <p className="text-sm">Max size: 5GB</p>
      </div>

      {/* Timeframe Selection */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Select Timeframes to Process</h3>
          <Button variant="outline" onClick={handleToggleAll}>
            {selectAll ? 'Deselect All' : 'Select All'}
          </Button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {TIMEFRAMES.map(tf => (
            <div
              key={tf.id}
              className={cn(
                "p-4 border rounded-lg cursor-pointer transition-colors",
                selectedTimeframes.includes(tf.id) || selectAll
                  ? "border-primary bg-primary/10"
                  : "border-gray-300 hover:border-gray-400"
              )}
              onClick={() => {
                setSelectAll(false);
                handleToggleTimeframe(tf.id);
              }}
            >
              <div className="flex items-center gap-2">
                <Checkbox
                  checked={selectedTimeframes.includes(tf.id) || selectAll}
                  onCheckedChange={() => handleToggleTimeframe(tf.id)}
                />
                <div>
                  <div className="font-medium">{tf.label}</div>
                  <div className="text-xs text-gray-500">{tf.description}</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {!selectAll && selectedTimeframes.length === 0 && (
          <Alert>
            <AlertDescription>
              Please select at least one timeframe to process
            </AlertDescription>
          </Alert>
        )}
      </div>

      {/* Upload Button */}
      <Button
        onClick={handleUpload}
        disabled={!file || (!selectAll && selectedTimeframes.length === 0) || uploading}
        className="w-full"
      >
        {uploading ? 'Uploading...' : 'Upload and Process'}
      </Button>
    </div>
  );
}
```

**6.3 Data Coverage Dashboard (NEW)**

```typescript
// frontend/src/client/components/data-module/etl/DataCoverageDashboard.tsx

export function DataCoverageDashboard() {
  const [symbol, setSymbol] = useState('NQU4');
  const [dateRange, setDateRange] = useState({ start: null, end: null });

  return (
    <div className="space-y-6">
      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4">
          <Input
            placeholder="Symbol (e.g., NQU4)"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
          />
          <DateRangePicker
            value={dateRange}
            onChange={setDateRange}
          />
        </CardContent>
      </Card>

      {/* Coverage Stats Summary */}
      <CoverageStatsPanel symbol={symbol} dateRange={dateRange} />

      {/* Coverage Matrix (Heatmap) */}
      <Card>
        <CardHeader>
          <CardTitle>Data Coverage Matrix</CardTitle>
          <CardDescription>
            Green = Completed, Yellow = Pending, Red = Failed, Gray = No raw data
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CoverageHeatmap symbol={symbol} dateRange={dateRange} />
        </CardContent>
      </Card>

      {/* Reprocess Section */}
      <ReprocessPanel />
    </div>
  );
}
```

**6.4 Coverage Heatmap Component (NEW)**

```typescript
// frontend/src/client/components/data-module/etl/CoverageHeatmap.tsx

export function CoverageHeatmap({ symbol, dateRange }) {
  const { data: matrix, isLoading } = useQuery({
    queryKey: ['coverage-matrix', symbol, dateRange],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (symbol) params.append('symbol', symbol);
      if (dateRange.start) params.append('start_date', dateRange.start);
      if (dateRange.end) params.append('end_date', dateRange.end);

      const response = await fetch(`/api/v1/etl/coverage/matrix?${params}`);
      return response.json();
    }
  });

  if (isLoading) return <Skeleton className="h-96" />;

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y">
        <thead>
          <tr>
            <th className="px-4 py-2">Date</th>
            <th className="px-4 py-2">Raw</th>
            {['30s', '1min', '5min', '15min', '1hr', '4hr', 'daily', 'weekly'].map(tf => (
              <th key={tf} className="px-4 py-2">{tf}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map(row => (
            <tr key={row.date}>
              <td className="px-4 py-2 font-medium">{row.date}</td>
              <td className="px-4 py-2">
                <StatusBadge status={row.has_raw ? 'completed' : null} />
              </td>
              {['30s', '1min', '5min', '15min', '1hr', '4hr', 'daily', 'weekly'].map(tf => (
                <td key={tf} className="px-4 py-2">
                  <StatusBadge status={row.timeframes[tf]} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StatusBadge({ status }: { status: string | null }) {
  const colors = {
    completed: 'bg-green-500',
    processing: 'bg-blue-500',
    pending: 'bg-yellow-500',
    failed: 'bg-red-500',
    null: 'bg-gray-300'
  };

  return (
    <div className={cn('w-8 h-8 rounded', colors[status || 'null'])} title={status || 'No data'} />
  );
}
```

**6.5 Reprocess Panel (NEW)**

```typescript
// frontend/src/client/components/data-module/etl/ReprocessPanel.tsx

export function ReprocessPanel() {
  const [dateRange, setDateRange] = useState({ start: null, end: null });
  const [selectedTimeframes, setSelectedTimeframes] = useState<string[]>([]);

  const handleReprocess = async () => {
    const response = await fetch('/api/v1/etl/reprocess', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        start_date: dateRange.start,
        end_date: dateRange.end,
        timeframes: selectedTimeframes
      })
    });

    const { job_id } = await response.json();
    navigate(`/data/etl/jobs/${job_id}`);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Reprocess Timeframes</CardTitle>
        <CardDescription>
          Rebuild specific timeframes for a date range. Useful after algorithm updates.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <DateRangePicker value={dateRange} onChange={setDateRange} />

        <TimeframeSelector
          selected={selectedTimeframes}
          onChange={setSelectedTimeframes}
        />

        <Button onClick={handleReprocess} disabled={!dateRange.start || selectedTimeframes.length === 0}>
          Start Reprocessing
        </Button>
      </CardContent>
    </Card>
  );
}
```

**6.2 Real-Time Job Monitoring**

```typescript
// frontend/src/client/components/data-module/etl/JobMonitor.tsx

export function JobMonitor({ jobId }: { jobId: string }) {
  const [job, setJob] = useState<ETLJob | null>(null);

  useEffect(() => {
    // Poll job status every 2 seconds
    const interval = setInterval(async () => {
      const response = await fetch(`/api/v1/etl/jobs/${jobId}`);
      const data = await response.json();
      setJob(data);

      if (data.status === 'completed' || data.status === 'failed') {
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId]);

  return (
    <div className="space-y-4">
      {/* Progress Bar */}
      <Progress value={job?.progress_pct} />

      {/* Current Step */}
      <div className="flex items-center gap-2">
        <Loader2 className="animate-spin" />
        <span>{getStepLabel(job?.status)}</span>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-4 gap-4">
        <Metric label="CSV Files" value={job?.csv_files_processed} />
        <Metric label="Ticks Inserted" value={job?.ticks_inserted?.toLocaleString()} />
        <Metric label="Candles Created" value={job?.candles_created} />
        <Metric label="Progress" value={`${job?.progress_pct}%`} />
      </div>

      {/* Error Display */}
      {job?.status === 'failed' && (
        <Alert variant="destructive">
          <AlertTitle>Processing Failed</AlertTitle>
          <AlertDescription>{job.error_message}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
```

**6.3 Database Statistics Panel**

```typescript
// frontend/src/client/components/data-module/etl/StatisticsPanel.tsx

export function StatisticsPanel() {
  const { data: stats } = useQuery({
    queryKey: ['etl-stats'],
    queryFn: async () => {
      const response = await fetch('/api/v1/etl/statistics');
      return response.json();
    },
    refetchInterval: 10000 // Refresh every 10s
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Database Statistics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <StatRow label="Total Ticks" value={stats?.total_ticks} />
          <StatRow label="Date Range" value={`${stats?.min_date} to ${stats?.max_date}`} />
          <StatRow label="Symbols" value={stats?.unique_symbols} />
          <StatRow label="Spread Ticks" value={stats?.spread_ticks} />
          <StatRow label="Rollover Periods" value={stats?.rollover_count} />

          <Separator />

          <h4 className="font-semibold">Candlesticks by Timeframe</h4>
          {Object.entries(stats?.candles_by_timeframe || {}).map(([tf, count]) => (
            <StatRow key={tf} label={tf} value={count} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

---

## Phase 7: API Endpoints Summary

### Backend API Routes

```python
# backend/app/etl/routes.py

from fastapi import APIRouter, UploadFile, File, Depends, Body
from typing import List, Optional

router = APIRouter(prefix="/api/v1/etl", tags=["ETL"])

# File Upload (UPDATED: with timeframe selection)
@router.post("/upload-zip")
async def upload_zip_file(
    file: UploadFile = File(...),
    selected_timeframes: Optional[List[str]] = Body(None),
    # Examples: ["5min", "1hr"] or None for all timeframes
    user: User = Depends(get_current_user)
):
    """
    Upload a Databento ZIP file for processing.

    Args:
        file: ZIP file to upload
        selected_timeframes: List of timeframes to build (default: all 8)
            Options: '30s', '1min', '5min', '15min', '1hr', '4hr', 'daily', 'weekly'

    Returns:
        job_id: UUID for tracking progress
    """
    pass

# Job Management
@router.get("/jobs")
async def list_jobs(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """List ETL jobs with optional status filtering."""
    pass

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get detailed status of a specific ETL job."""
    pass

@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running ETL job."""
    pass

# Statistics
@router.get("/statistics")
async def get_database_statistics():
    """
    Get overall database statistics.

    Returns:
        - total_ticks: Total tick count
        - date_range: Min/max dates
        - unique_symbols: Count of unique symbols
        - spread_ticks: Count of spread ticks
        - rollover_count: Number of rollover periods
        - candles_by_timeframe: Dict of {timeframe: count}
    """
    pass

# NEW: Data Coverage Endpoints
@router.get("/coverage/summary")
async def get_coverage_summary(
    symbol: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """
    Get coverage summary showing which days have raw data
    and which days have been populated for each timeframe.

    Returns:
        {
            "raw_data_days": ["2024-07-19", "2024-07-20", ...],
            "timeframes": {
                "5min": {
                    "completed_days": ["2024-07-19"],
                    "pending_days": ["2024-07-20"],
                    "failed_days": []
                },
                "1hr": {...},
                ...
            }
        }
    """
    pass

@router.get("/coverage/matrix")
async def get_coverage_matrix(
    symbol: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """
    Get coverage matrix (heatmap data).

    Returns:
        [
            {
                "date": "2024-07-19",
                "has_raw": true,
                "timeframes": {
                    "30s": "completed",
                    "1min": "completed",
                    "5min": "completed",
                    "15min": "pending",
                    "1hr": null,
                    ...
                }
            },
            ...
        ]
    """
    pass

@router.get("/coverage/stats")
async def get_coverage_stats():
    """
    Get coverage statistics.

    Returns:
        {
            "total_days_with_raw": 120,
            "by_timeframe": {
                "5min": {"completed": 100, "pending": 20, "failed": 0},
                "1hr": {"completed": 50, "pending": 70, "failed": 0},
                ...
            }
        }
    """
    pass

# NEW: Reprocess Endpoint
@router.post("/reprocess")
async def reprocess_timeframes(
    start_date: date = Body(...),
    end_date: date = Body(...),
    timeframes: List[str] = Body(...),
    symbol: Optional[str] = Body(None),
    user: User = Depends(get_current_user)
):
    """
    Reprocess specific timeframes for a date range.

    Useful when:
    - Algorithm improvements require recalculation
    - Failed processing needs retry
    - New timeframes added to existing data

    Args:
        start_date: Start date to reprocess
        end_date: End date to reprocess
        timeframes: List of timeframes to rebuild
        symbol: Optional symbol filter

    Returns:
        job_id: UUID for tracking reprocessing job
    """
    pass

# Processed Files
@router.get("/processed-files")
async def list_processed_files(
    skip: int = 0,
    limit: int = 50
):
    """List all processed ZIP/CSV files."""
    pass

# Rollover Periods
@router.get("/rollover-periods")
async def list_rollover_periods():
    """List all detected rollover periods."""
    pass

# Data Query (for charts)
@router.get("/candles/{timeframe}")
async def get_candles(
    timeframe: str,
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    exclude_spreads: bool = True
):
    """Query candlestick data for charts."""
    pass
```

---

## 🔌 Database Connections Documentation

### Connection Details

**Primary Database (NQHUB)**:
```
Host: localhost
Port: 5433
Database: nqhub
User: nqhub
Password: nqhub_password
Container: nqhub_postgres
Image: timescale/timescaledb:latest-pg15

PostgreSQL URL: postgresql://nqhub:nqhub_password@localhost:5433/nqhub
Async URL: postgresql+asyncpg://nqhub:nqhub_password@localhost:5433/nqhub
```

**Legacy Database (Reference Only)**:
```
Host: localhost
Port: 5432
Database: nq_orderflow
User: victor
Password: victor2108
Status: READ-ONLY (different WSL instance)
```

**Redis (Job Queue & Cache)**:
```
Host: localhost
Port: 6379
Container: nqhub_redis
```

### Configuration Files

**Backend**: `backend/.env`
```bash
DATABASE_URL=postgresql://nqhub:nqhub_password@localhost:5433/nqhub
DATABASE_URL_ASYNC=postgresql+asyncpg://nqhub:nqhub_password@localhost:5433/nqhub
REDIS_URL=redis://localhost:6379/0
```

**Docker Compose**: `docker/docker-compose.yml`
```yaml
services:
  postgres:
    container_name: nqhub_postgres
    image: timescale/timescaledb:latest-pg15
    ports:
      - "5433:5432"
    environment:
      POSTGRES_DB: nqhub
      POSTGRES_USER: nqhub
      POSTGRES_PASSWORD: nqhub_password
```

---

## 📊 Performance Targets

### ETL Processing Speed

| File Size | Expected Ticks | Target Processing Time |
|-----------|----------------|------------------------|
| 50 MB | ~250K ticks | < 2 minutes |
| 500 MB | ~2.5M ticks | < 10 minutes |
| 1 GB | ~5M ticks | < 20 minutes |
| 5 GB | ~25M ticks | < 2 hours |

### Optimization Strategies

1. **Batch Inserts**: 5000 ticks per batch
2. **PostgreSQL COPY**: Use for bulk loading
3. **TimescaleDB Compression**: Enable after initial load
4. **Parallel Processing**: Process multiple CSV files in parallel
5. **Index Management**: Disable indexes during bulk insert, rebuild after

---

## 🚨 Error Handling

### Error Categories

1. **Upload Errors**: Invalid file format, size exceeded
2. **Extraction Errors**: Corrupted ZIP, missing files
3. **Parsing Errors**: Invalid CSV format, missing columns
4. **Database Errors**: Connection failures, constraint violations
5. **Processing Errors**: Out of memory, timeout

### Error Recovery

- **Automatic Retry**: Up to 3 retries for transient errors
- **Partial Success**: Mark successfully processed CSV files
- **Rollback Strategy**: Transaction-based insertion
- **User Notification**: Email/notification on failure

---

## 📝 Testing Strategy

### Unit Tests

```python
# backend/tests/test_etl/test_parser.py

def test_csv_parser_valid_file():
    parser = CSVParserService()
    ticks = list(parser.parse_csv('sample.csv'))
    assert len(ticks) == 1000
    assert ticks[0]['symbol'] == 'NQU4'

def test_rollover_detection():
    detector = RolloverDetectorService()
    # Test with mock data containing spreads
```

### Integration Tests

```python
# backend/tests/test_etl/test_integration.py

async def test_full_etl_pipeline():
    """
    Test complete ETL flow:
    1. Upload ZIP
    2. Extract
    3. Parse
    4. Load ticks
    5. Build candles
    6. Verify results
    """
```

### Frontend E2E Tests

```typescript
// frontend/e2e/etl.spec.ts

test('upload and monitor ETL job', async ({ page }) => {
  await page.goto('/data/etl');
  await page.setInputFiles('input[type=file]', 'test-data.zip');
  await expect(page.locator('.progress-bar')).toBeVisible();
  await expect(page.locator('.status-complete')).toBeVisible({ timeout: 60000 });
});
```

---

## 📅 Timeline Summary

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| Phase 1: Upload | 1 week | File upload API + UI |
| Phase 2: Parsing | 1 week | ZIP extraction + CSV parsing |
| Phase 3: Loading | 1 week | Tick data insertion |
| Phase 4: Rollovers | 3 days | Rollover detection |
| Phase 5: Candles | 1 week | Candlestick aggregation (8 timeframes) |
| Phase 6: Frontend | 1 week | Monitoring dashboard |
| Phase 7: Testing | 3 days | Unit + integration tests |
| **Total** | **~6 weeks** | Complete ETL system |

---

## 🎯 Success Criteria

- ✅ Upload and process 6.5GB of reference data
- ✅ Insert ~100M ticks into TimescaleDB
- ✅ Generate 8 timeframes of candlesticks
- ✅ Detect all rollover periods automatically
- ✅ < 5% processing time overhead vs raw insertion
- ✅ Zero data loss or corruption
- ✅ Real-time progress monitoring in frontend
- ✅ Graceful error handling and recovery

---

## 📚 Next Steps

1. **Review and Approve Plan** - User feedback on approach
2. **Setup Background Queue** - Install and configure RQ
3. **Implement Phase 1** - File upload endpoint + UI
4. **Test with Small File** - Validate with GLBX-20241230-PRA7BAY34H.zip (29 MB)
5. **Iterate and Optimize** - Based on performance metrics

---

**Document Location**: `backend/ETL_PLAN.md`
**Related Docs**:
- `backend/DATABASE_SCHEMA.md` - Database schema reference
- `_reference/docs/DATA_DICTIONARY.md` - Data structure guide
- `_reference/docs/csv_format_metadata.json` - CSV format specs

