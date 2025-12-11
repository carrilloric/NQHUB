# NQHUB Database Schema Documentation

**Generated**: 2025-11-02
**Database**: nqhub (PostgreSQL 15 + TimescaleDB)
**Port**: 5433

---

## Overview

This document describes the complete database schema for the NQHUB ETL system, designed to store and analyze NQ Futures market data from Databento.

### Table Summary

| Table Name | Type | Primary Purpose | Row Estimate |
|------------|------|-----------------|--------------|
| `market_data_ticks` | Hypertable | Raw tick-by-tick market data | Millions |
| `candlestick_30s` | Standard | 30-second aggregated candles | Thousands |
| `candlestick_1min` | Standard | 1-minute aggregated candles | Thousands |
| `candlestick_5min` | Standard | 5-minute aggregated candles | Thousands |
| `candlestick_15min` | Standard | 15-minute aggregated candles | Thousands |
| `candlestick_1hr` | Standard | 1-hour aggregated candles | Hundreds |
| `candlestick_4hr` | Standard | 4-hour aggregated candles | Hundreds |
| `candlestick_daily` | Standard | Daily aggregated candles | Hundreds |
| `candlestick_weekly` | Standard | Weekly aggregated candles | Tens |
| `rollover_periods` | Standard | Futures contract rollover tracking | Dozens |
| `processed_files` | Standard | ETL duplicate prevention | Hundreds |

---

## Core Tables

### 1. market_data_ticks

**Purpose**: Stores raw tick-by-tick market data from Databento CSV files.

**Type**: TimescaleDB Hypertable (partitioned by `ts_event`, 1-day chunks)

**Schema**:

```sql
CREATE TABLE market_data_ticks (
    -- Primary identification
    id                  BIGINT NOT NULL AUTO_INCREMENT,
    ts_recv             TIMESTAMP WITH TIME ZONE NOT NULL,
    ts_event            TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Symbol tracking
    symbol              VARCHAR(20) NOT NULL,
    is_spread           BOOLEAN DEFAULT false,
    is_rollover_period  BOOLEAN DEFAULT false,

    -- Market data
    price               DOUBLE PRECISION NOT NULL,
    size                INTEGER NOT NULL,
    side                VARCHAR(1) NOT NULL,  -- 'A'=Ask, 'B'=Bid
    action              VARCHAR(1),           -- 'A'=Add, 'C'=Cancel, 'M'=Modify, 'F'=Fill, 'T'=Trade

    -- Order book snapshots
    bid_px              DOUBLE PRECISION,
    ask_px              DOUBLE PRECISION,
    bid_sz              INTEGER,
    ask_sz              INTEGER,
    bid_ct              INTEGER,
    ask_ct              INTEGER,

    -- Databento metadata
    rtype               INTEGER,
    publisher_id        INTEGER,
    instrument_id       INTEGER,
    sequence            BIGINT,
    flags               INTEGER,
    ts_in_delta         INTEGER,
    depth               INTEGER,

    PRIMARY KEY (id, ts_event)
);
```

**Indexes**:
- `idx_ticks_ts_event` (btree on `ts_event`) - Time-based queries
- `idx_ticks_symbol` (btree on `symbol`) - Symbol filtering
- `idx_ticks_rollover` (btree on `is_rollover_period`) - Rollover period queries

**TimescaleDB Configuration**:
- Hypertable: `create_hypertable('market_data_ticks', 'ts_event', chunk_time_interval => '1 day')`
- Primary dimension: `ts_event`
- Chunk size: 1 day

**Column Details**:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | BIGINT | Unique tick identifier | 1234567 |
| `ts_recv` | TIMESTAMPTZ | Reception timestamp (when Databento received) | 2024-07-19 09:30:00.123456+00 |
| `ts_event` | TIMESTAMPTZ | Event timestamp (when trade occurred) | 2024-07-19 09:30:00.123000+00 |
| `symbol` | VARCHAR(20) | Contract symbol | NQU4, NQH4-NQM4 |
| `is_spread` | BOOLEAN | Calendar spread indicator | true/false |
| `is_rollover_period` | BOOLEAN | Rollover period flag | true/false |
| `price` | FLOAT | Trade/quote price | 19875.25 |
| `size` | INTEGER | Contract quantity | 5 |
| `side` | VARCHAR(1) | Market side (A/B) | A, B |
| `action` | VARCHAR(1) | Order action (A/C/M/F/T) | T |
| `bid_px` | FLOAT | Best bid price | 19875.00 |
| `ask_px` | FLOAT | Best ask price | 19875.25 |
| `bid_sz` | INTEGER | Best bid size | 12 |
| `ask_sz` | INTEGER | Best ask size | 8 |
| `bid_ct` | INTEGER | Bid order count | 3 |
| `ask_ct` | INTEGER | Ask order count | 2 |

---

### 2. Candlestick Tables (8 Timeframes)

**Purpose**: Store aggregated OHLCV candles with order flow metrics across 8 timeframes.

**Tables**:
- `candlestick_30s`
- `candlestick_1min`
- `candlestick_5min`
- `candlestick_15min`
- `candlestick_1hr`
- `candlestick_4hr`
- `candlestick_daily`
- `candlestick_weekly`

**Schema** (identical across all 8 tables, 35 columns total):

```sql
CREATE TABLE candlestick_{timeframe} (
    -- Time and symbol identification
    time_interval       TIMESTAMP WITH TIME ZONE NOT NULL,
    symbol              VARCHAR(20) NOT NULL,
    is_spread           BOOLEAN DEFAULT false,
    is_rollover_period  BOOLEAN DEFAULT false,

    -- OHLCV (5 columns)
    open                DOUBLE PRECISION,
    high                DOUBLE PRECISION,
    low                 DOUBLE PRECISION,
    close               DOUBLE PRECISION,
    volume              DOUBLE PRECISION,

    -- Point of Control - Regular (5 columns)
    poc                 DOUBLE PRECISION,
    poc_volume          DOUBLE PRECISION,
    poc_percentage      DOUBLE PRECISION,
    poc_location        TEXT,                   -- 'upper_wick', 'body', 'lower_wick'
    poc_position        DOUBLE PRECISION,

    -- Point of Control - Real (exact 0.25 tick) (4 columns)
    real_poc            DOUBLE PRECISION,
    real_poc_volume     DOUBLE PRECISION,
    real_poc_percentage DOUBLE PRECISION,
    real_poc_location   TEXT,

    -- Candle structure (6 columns)
    upper_wick          DOUBLE PRECISION,
    lower_wick          DOUBLE PRECISION,
    body                DOUBLE PRECISION,
    wick_ratio          DOUBLE PRECISION,
    rel_uw              DOUBLE PRECISION,       -- Relative upper wick
    rel_lw              DOUBLE PRECISION,       -- Relative lower wick

    -- Volume distribution (3 columns)
    upper_wick_volume   DOUBLE PRECISION,
    lower_wick_volume   DOUBLE PRECISION,
    body_volume         DOUBLE PRECISION,

    -- Absorption indicators (4 columns)
    asellers_uwick      DOUBLE PRECISION,       -- Aggressive sellers in upper wick
    asellers_lwick      DOUBLE PRECISION,       -- Aggressive sellers in lower wick
    abuyers_uwick       DOUBLE PRECISION,       -- Aggressive buyers in upper wick
    abuyers_lwick       DOUBLE PRECISION,       -- Aggressive buyers in lower wick

    -- Order flow (3 columns)
    delta               DOUBLE PRECISION,       -- buy_volume - sell_volume
    oflow_detail        JSONB,                  -- 0.25 tick granularity
    oflow_unit          JSONB,                  -- 1.0 point granularity

    -- Metadata (1 column)
    tick_count          INTEGER,                -- Number of ticks in candle

    PRIMARY KEY (time_interval, symbol)
);
```

**Indexes** (per timeframe):
- `idx_{timeframe}_time` (btree on `time_interval`) - Time-based queries
- `idx_{timeframe}_symbol` (btree on `symbol`) - Symbol filtering
- `idx_{timeframe}_rollover` (btree on `is_rollover_period`) - Rollover filtering

**Order Flow JSONB Format**:

```json
// oflow_detail (0.25 tick granularity)
{
  "19875.00": {"asks": 125, "bids": 98},
  "19875.25": {"asks": 87, "bids": 142},
  "19875.50": {"asks": 56, "bids": 203}
}

// oflow_unit (1.0 point granularity)
{
  "19875": {"asks": 268, "bids": 443},
  "19876": {"asks": 156, "bids": 321}
}
```

**Column Groups Explained**:

1. **OHLCV** (5 columns): Standard candlestick price and volume data
2. **POC Regular** (5 columns): Point of control that may be rounded/aggregated
3. **POC Real** (4 columns): Exact 0.25 tick precision POC without any rounding
4. **Candle Structure** (6 columns): Geometric properties of the candle
5. **Volume Distribution** (3 columns): How volume is distributed in the candle
6. **Absorption Indicators** (4 columns): Aggressive buyer/seller detection in wicks
7. **Order Flow** (3 columns): Bid/ask volume tracking at price levels
8. **Metadata** (1 column): Supporting data

---

### 3. rollover_periods

**Purpose**: Track futures contract rollover periods for NQ contracts.

**Detection Method**: Automatic detection from symbol changes in tick stream (e.g., NQU4 → NQH4-NQM4 → NQM4).

**Schema**:

```sql
CREATE TABLE rollover_periods (
    id                  SERIAL PRIMARY KEY,
    contract_old        VARCHAR(10) NOT NULL,      -- e.g., 'NQU4'
    contract_new        VARCHAR(10) NOT NULL,      -- e.g., 'NQM4'
    start_date          TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date            TIMESTAMP WITH TIME ZONE,
    total_spread_ticks  INTEGER,                   -- Count of hybrid symbol ticks
    status              VARCHAR(20) DEFAULT 'active',
    detected_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Example Data**:

| contract_old | contract_new | start_date | end_date | total_spread_ticks | status |
|--------------|--------------|------------|----------|-------------------|---------|
| NQH4 | NQM4 | 2024-03-12 | 2024-03-15 | 157821 | completed |
| NQM4 | NQU4 | 2024-06-11 | 2024-06-14 | 143256 | completed |
| NQU4 | NQZ4 | 2024-09-10 | NULL | 89432 | active |

---

### 4. processed_files

**Purpose**: Track processed ZIP and CSV files to prevent duplicate imports.

**Schema**:

```sql
CREATE TABLE processed_files (
    id              SERIAL PRIMARY KEY,
    zip_filename    VARCHAR(255) NOT NULL,
    csv_filename    VARCHAR(255) NOT NULL,
    row_count       INTEGER,
    start_date      TIMESTAMP WITH TIME ZONE,
    end_date        TIMESTAMP WITH TIME ZONE,
    processed_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT uq_processed_files UNIQUE (zip_filename, csv_filename)
);
```

**Example Data**:

| zip_filename | csv_filename | row_count | start_date | end_date | processed_at |
|--------------|--------------|-----------|------------|----------|--------------|
| GLBX-20240719-W4UAD9HEC5.zip | glbx-mdp3-20240719.mbo.csv | 276543 | 2024-07-19 00:00:00+00 | 2024-07-19 23:59:59+00 | 2024-11-02 10:15:32+00 |

---

## Authentication Tables

The database also includes authentication tables created in earlier migrations:

- `users` - User accounts
- `invitations` - Invitation codes for registration
- `password_reset_tokens` - Password reset functionality
- `alembic_version` - Alembic migration version tracking

See authentication documentation for details on these tables.

---

## Design Decisions

### 1. Spread Handling

**Decision**: Store spread symbols (e.g., NQH4-NQM4) as separate data with `is_spread=true` flag.

**Rationale**:
- Allows filtering spreads from backtesting without data loss
- Enables rollover period analysis
- Supports both series-separated and continuous contract views

**Implementation**:
- All tables have `is_spread` boolean column
- All tables have `is_rollover_period` boolean column
- Queries can filter with: `WHERE is_spread = false` or `WHERE is_rollover_period = false`

### 2. Complete Schema Replication

**Decision**: All 8 candlestick tables have identical 35-column schema including order flow JSONB.

**Rationale**:
- Consistency across timeframes
- Supports advanced analysis at all granularities
- Storage is cheap, flexibility is valuable
- Allows comparing POC, absorption, etc. across timeframes

### 3. TimescaleDB Hypertable

**Decision**: Only `market_data_ticks` uses TimescaleDB hypertable, candlestick tables are standard PostgreSQL.

**Rationale**:
- Tick data is massive (millions of rows), benefits from partitioning
- Candlestick tables are smaller (thousands of rows), standard tables are simpler
- TimescaleDB overhead not needed for aggregated data

### 4. Dual POC Storage

**Decision**: Store both `poc` (may be rounded) and `real_poc` (exact 0.25 tick precision).

**Rationale**:
- `poc`: Flexibility for algorithms that aggregate POC
- `real_poc`: Precision for tick-perfect analysis
- Both are stored to support different trading strategies

---

## Query Examples

### Get All Ticks During Rollover Period

```sql
SELECT ts_event, symbol, price, size, side
FROM market_data_ticks
WHERE is_rollover_period = true
ORDER BY ts_event;
```

### Get 5-Minute Candles Excluding Spreads

```sql
SELECT time_interval, symbol, open, high, low, close, volume, delta
FROM candlestick_5min
WHERE is_spread = false
ORDER BY time_interval DESC
LIMIT 100;
```

### Detect High Volume POC Candles

```sql
SELECT time_interval, symbol, close, real_poc, real_poc_percentage
FROM candlestick_15min
WHERE real_poc_percentage > 30.0  -- POC contains >30% of volume
ORDER BY real_poc_percentage DESC
LIMIT 20;
```

### Get Active Rollover Periods

```sql
SELECT contract_old, contract_new, start_date,
       total_spread_ticks, detected_at
FROM rollover_periods
WHERE status = 'active'
ORDER BY start_date DESC;
```

### Check Processed Files

```sql
SELECT zip_filename, COUNT(*) as csv_count,
       SUM(row_count) as total_rows,
       MIN(start_date) as first_date,
       MAX(end_date) as last_date
FROM processed_files
GROUP BY zip_filename
ORDER BY first_date DESC;
```

---

## Migration History

| Revision | Description | Date | File |
|----------|-------------|------|------|
| e5719b486310 | Create users and invitations tables | 2025-11-01 | (previous migration) |
| 8d5b0d19c24e | Add password reset tokens table | 2025-11-01 | (previous migration) |
| b215073e64fd | Create market_data_ticks table | 2025-11-02 | `20251102_0904-b215073e64fd_create_market_data_ticks_table.py` |
| 0cac37df50d1 | Create candlestick tables | 2025-11-02 | `20251102_0904-0cac37df50d1_create_candlestick_tables.py` |
| c32f6b61196a | Create auxiliary tables | 2025-11-02 | `20251102_0905-c32f6b61196a_create_auxiliary_tables.py` |

---

## Database Statistics

**Connection Details**:
- Host: localhost
- Port: 5433
- Database: nqhub
- Docker Container: nqhub_postgres
- Image: timescale/timescaledb:latest-pg15

**Current State** (as of 2025-11-02):
- Total Tables: 15
- Hypertables: 1 (market_data_ticks)
- Data Size: 0 KB (schema only, no data yet)

---

## Future Enhancements

Planned improvements for future phases:

1. **Continuous Aggregates**: Use TimescaleDB continuous aggregates for candlestick tables
2. **Compression**: Enable compression on old chunks of market_data_ticks
3. **Retention Policies**: Auto-drop old tick data after N months
4. **Additional Indexes**: GiN indexes on JSONB columns for order flow queries
5. **Materialized Views**: Pre-computed continuous contract views

---

## Reference Documentation

For more information, see:

- `_reference/docs/DATA_DICTIONARY.md` - Human-readable data structure guide
- `_reference/docs/database_metadata.json` - Legacy database schema reference
- `_reference/docs/csv_format_metadata.json` - Databento CSV format specifications
- `_reference/docs/LEGACY_DATABASE_SCHEMA.md` - Legacy system analysis

---

**Generated by**: Claude Code
**Last Updated**: 2025-11-02
