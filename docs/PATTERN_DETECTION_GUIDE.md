# Pattern Detection System Guide

Complete guide to NQHUB's ICT (Inner Circle Trader) Pattern Detection System.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Pattern Types](#pattern-types)
- [API Usage](#api-usage)
- [Frontend Integration](#frontend-integration)
- [Timezone Handling](#timezone-handling)
- [Troubleshooting](#troubleshooting)

---

## Overview

NQHUB implements automated detection of three main ICT patterns:

1. **Fair Value Gaps (FVG)** - Price imbalances created by rapid moves
2. **Liquidity Pools (LP)** - Areas where stop-loss orders accumulate
3. **Order Blocks (OB)** - Last candle before institutional moves

All patterns are:
- Stored in PostgreSQL with TimescaleDB
- Auto-detected with dynamic parameters (ATR-based)
- Available via REST API endpoints
- Visualized in the Data Module frontend

---

## Architecture

### Backend Components

```
backend/app/services/pattern_detection/
├── fvg_detector.py       # Fair Value Gap detection
├── lp_detector.py        # Liquidity Pool detection
├── ob_detector.py        # Order Block detection
└── interaction_detector.py  # Pattern interactions (pending)

backend/app/models/patterns.py
├── DetectedFVG
├── DetectedLiquidityPool
├── DetectedOrderBlock
└── PatternInteraction

backend/app/api/v1/endpoints/patterns.py
└── API routes for generation and listing
```

### Database Tables

- `detected_fvgs` - Fair Value Gap records
- `detected_liquidity_pools` - Liquidity Pool records
- `detected_order_blocks` - Order Block records
- `pattern_interactions` - Pattern interaction tracking

**See**: `docs/DATABASE_SCHEMA.md` for complete schema

---

## Pattern Types

### 1. Fair Value Gaps (FVG)

**What it is**: A price gap created by imbalance between buyers and sellers, visible as non-overlapping wicks in a 3-candle pattern.

**Detection Criteria** (see `FVG_CRITERIOS_DETECCION.md`):
```
Bullish FVG: vela1.low > vela3.high
Bearish FVG: vela1.high < vela3.low
Minimum gap size: Auto-calculated from ATR
```

**ICT-Specific Fields**:
- `premium_level`: High boundary (resistance in bullish FVG)
- `discount_level`: Low boundary (support in bullish FVG)
- `consequent_encroachment`: 50% level (most important retracement target)
- `displacement_score`: Energetic movement indicator
- `has_break_of_structure`: Break of Structure (BOS) flag

**Significance Levels** (based on gap size):
- MICRO: < 10 points
- SMALL: 10-20 points
- MEDIUM: 20-40 points
- LARGE: 40-80 points
- EXTREME: > 80 points

**States**:
- **UNMITIGATED**: Gap not yet filled
- **REDELIVERED**: Price returned to 50% (consequent encroachment)
- **REBALANCED**: Gap fully filled

**References**:
- Theory: `docs/FVG_TEORIA_ICT.md`
- Criteria: `docs/FVG_CRITERIOS_DETECCION.md`
- Implementation: `docs/DETECCION_FAIR_VALUE_GAPS.md`

### 2. Liquidity Pools (LP)

**What it is**: Areas where stop-loss orders accumulate, creating pockets of liquidity that price seeks.

**Pool Types**:
- **EQH (Equal Highs)**: 2+ highs within tolerance
- **EQL (Equal Lows)**: 2+ lows within tolerance
- **Session Levels**:
  - NYH/NYL: New York High/Low
  - ASH/ASL: Asian Session High/Low
  - LSH/LSL: London Session High/Low

**Detection Criteria** (see `LIQUIDITY_POOLS_CRITERIOS.md`):
```
Tolerance: Auto-calculated from ATR (default 10 points)
Minimum touches: 2 for EQH/EQL
Rectangle representation: zone_low, zone_high, start_time, end_time
```

**ICT Lifecycle**:
1. **Formation**: Pool detected (EQH/EQL or session level)
2. **Modal Level**: Price level with most touches
3. **Sweep Detection**: 3 criteria check (penetration > 5pts, volume spike, reversal)
4. **State Update**: SWEPT or remains UNMITIGATED

**States**:
- **UNMITIGATED**: Pool not yet swept
- **RESPECTED**: Price bounced without sweeping
- **SWEPT**: Stop-loss orders triggered (liquidity taken)
- **MITIGATED**: Pool no longer relevant

**References**:
- Criteria: `docs/LIQUIDITY_POOLS_CRITERIOS.md`
- Lifecycle: `docs/LIQUIDITY_POOL_STATES.md`
- Examples: `docs/LP_20NOV_CRITICAL_LEVELS.md`

### 3. Order Blocks (OB)

**What it is**: The last candle before a significant impulse move, representing institutional order placement.

**Detection Criteria** (see `ORDER_BLOCKS_CRITERIOS.md`):
```
Minimum impulse: Auto-calculated from ATR (2.5x typical move)
Strong threshold: 1.5x minimum impulse
Candle must precede the impulse (not be part of it)
```

**Classification**:
- **BULLISH OB**: Candle before upward impulse
- **BEARISH OB**: Candle before downward impulse
- **STRONG BULLISH OB**: Impulse > 1.5x minimum
- **STRONG BEARISH OB**: Impulse > 1.5x minimum

**Quality Levels**:
- **HIGH**: Strong impulse + large volume + tight range
- **MEDIUM**: Moderate impulse
- **LOW**: Minimum impulse threshold only

**Key Fields**:
- `ob_body_midpoint`: 50% of candle body = (open + close) / 2
- `ob_range_midpoint`: 50% of candle range = (high + low) / 2
- `impulse_move`: Size of impulse in points
- `impulse_direction`: UP or DOWN

**States**:
- **ACTIVE**: OB not yet tested by price
- **TESTED**: Price returned to OB zone
- **BROKEN**: Price decisively broke through OB

**References**:
- Criteria: `docs/ORDER_BLOCKS_CRITERIOS.md`
- Examples: `docs/OB_24NOV_SAMPLE.md`
- Interactions: `docs/REBOTE_Y_PENETRACION_CRITERIOS.md`

### Pattern Interactions (Pending)

**Location**: `backend/app/services/pattern_detection/interaction_detector.py` (not yet implemented)

**Interaction Types** (see `REBOTE_Y_PENETRACION_CRITERIOS.md`):

**Bounce Levels (R0-R4)**:
- **R0**: Clean bounce (0% penetration)
- **R1**: Shallow touch (0.1-10% penetration)
- **R2**: Moderate retest (10-25% penetration)
- **R3**: Deep retest (25-50% penetration)
- **R4**: Full retest (50-90% penetration)

**Penetration Levels (P1-P5)**:
- **P1**: Minor break (90-110% penetration)
- **P2**: Moderate break (110-150%)
- **P3**: Strong break (150-200%)
- **P4**: False breakout (>200% but reverses)
- **P5**: Clean break (>200% sustained)

---

## API Usage

### Generate Patterns

#### Fair Value Gaps
```bash
curl -X POST http://localhost:8002/api/v1/patterns/fvgs/generate \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NQZ5",
    "start_date": "2025-11-24",
    "end_date": "2025-11-25",
    "timeframe": "5min"
  }'
```

**Response**:
```json
{
  "total": 42,
  "auto_parameters": {
    "min_gap_size": 12.5,
    "timeframe": "5min"
  },
  "state_update_stats": {
    "total_checked": 150,
    "redelivered": 8,
    "rebalanced": 12
  },
  "fvgs": [...],
  "text_report": "## FVG Detection Report\n..."
}
```

#### Liquidity Pools
```bash
curl -X POST http://localhost:8002/api/v1/patterns/liquidity-pools/generate \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NQZ5",
    "date": "2025-11-20",
    "timeframe": "5min",
    "pool_types": ["EQH", "EQL", "NYH", "NYL"]
  }'
```

#### Order Blocks
```bash
curl -X POST http://localhost:8002/api/v1/patterns/order-blocks/generate \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NQZ5",
    "start_date": "2025-11-24",
    "end_date": "2025-11-24",
    "timeframe": "5min"
  }'
```

### List Patterns

#### FVGs with Filters
```bash
curl "http://localhost:8002/api/v1/patterns/fvgs?symbol=NQZ5&timeframe=5min&status=UNMITIGATED&significance=LARGE"
```

#### Liquidity Pools with Filters
```bash
curl "http://localhost:8002/api/v1/patterns/liquidity-pools?symbol=NQZ5&timeframe=5min&pool_type=EQH&status=SWEPT"
```

#### Order Blocks with Filters
```bash
curl "http://localhost:8002/api/v1/patterns/order-blocks?symbol=NQZ5&timeframe=5min&quality=HIGH&status=ACTIVE"
```

---

## Frontend Integration

### Pattern Detection Section

**Location**: `frontend/src/client/components/data-module/PatternDetectionSection.tsx`

**Components**:
- `patterns/FVGGenerator.tsx` - FVG generation UI
- `patterns/LPGenerator.tsx` - LP generation UI
- `patterns/OBGenerator.tsx` - OB generation UI

**Features**:
1. **Date Range Selection**: Calendar picker for start/end dates
2. **Real-time Generation**: Progress tracking with status updates
3. **Markdown Reports**: Formatted reports with statistics
4. **List View**: Filterable table with pattern details
5. **Auto-Parameters**: Display of calculated parameters (min_gap_size, tolerance, min_impulse)

**Usage Flow**:
1. Navigate to Data Module → Pattern Detection tab
2. Select pattern type (FVG, LP, or OB)
3. Choose date range and symbol
4. Click "Generate" button
5. View markdown report and pattern list

---

## Timezone Handling

⚠️ **CRITICAL**: All pattern detection must follow the correct timezone pattern.

### The Problem

SQL queries with `AT TIME ZONE 'America/New_York'` return **naive datetimes in ET**, but PostgreSQL interprets them as **UTC** when saving. This causes 5-hour offset errors.

### The Correct Pattern

```python
import pytz
from datetime import datetime

eastern = pytz.timezone('America/New_York')

# Step 1: Ensure formation_time is timezone-aware (ET)
if formation_time.tzinfo is None:
    formation_time = eastern.localize(formation_time)
else:
    formation_time = formation_time.astimezone(eastern)

# Step 2: Convert to UTC aware
formation_time_utc_aware = formation_time.astimezone(pytz.UTC)

# Step 3: Remove tzinfo for database storage
formation_time_utc_naive = formation_time_utc_aware.replace(tzinfo=None)

# Step 4: Save to database
pattern = DetectedPattern(
    formation_time=formation_time_utc_naive,  # UTC naive
    ...
)
```

### Display Format

Text reports MUST show: `"YYYY-MM-DD HH:MM:SS EST (HH:MM:SS UTC)"`

Example:
```
Formation Time: 2025-11-06 00:20:00 EST (05:20:00 UTC)
```

**See**: `docs/TIMEZONE_HANDLING.md` for complete guide, validation checklist, and troubleshooting.

---

## Troubleshooting

### Issue: FVGs not detected

**Possible causes**:
1. **Min gap size too high**: Check auto-calculated `min_gap_size` in report
2. **Insufficient candle data**: Ensure 3-candle pattern exists
3. **Timezone mismatch**: Verify timestamps are correct (EST vs UTC)

**Solution**:
```bash
# Check ATR calculation
SELECT
  timeframe,
  AVG(high - low) as avg_range,
  PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY high - low) as p90_range
FROM candles_5min
WHERE symbol = 'NQZ5' AND time >= '2025-11-24' AND time < '2025-11-25'
GROUP BY timeframe;

# Adjust min_gap_size manually if needed (not recommended)
```

### Issue: Liquidity Pools too many/too few

**Possible causes**:
1. **Tolerance too wide/narrow**: Default 10 points may not fit all instruments
2. **Min touches threshold**: Default 2 touches may miss subtle levels

**Solution**:
- Increase tolerance for volatile periods
- Decrease tolerance for consolidation periods
- Adjust in detector code: `lp_detector.py` line ~50

### Issue: Order Blocks quality incorrect

**Possible causes**:
1. **Min impulse threshold**: Auto-calculated from ATR (2.5x typical move)
2. **Volume data missing**: Quality score requires volume

**Solution**:
```python
# Check volume availability
SELECT COUNT(*) FROM candles_5min WHERE symbol = 'NQZ5' AND volume IS NULL;

# Verify impulse calculation
SELECT
  formation_time,
  impulse_move,
  ob_type,
  quality
FROM detected_order_blocks
WHERE symbol = 'NQZ5'
ORDER BY impulse_move DESC
LIMIT 10;
```

### Issue: Timezone display incorrect

**Symptoms**:
- Patterns appear 5 hours off from ATAS
- UTC time matches but EST time wrong

**Solution**:
1. Check detector uses correct pattern (see Timezone Handling section)
2. Verify database stores UTC naive (`+00` offset, not `-05`)
3. Confirm display converts UTC → EST correctly

**Validation query**:
```sql
SELECT
  formation_time,
  formation_time AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York' as est_time
FROM detected_order_blocks
WHERE symbol = 'NQZ5'
LIMIT 5;
```

---

## Related Documentation

### Pattern-Specific
- `docs/FVG_TEORIA_ICT.md` - FVG theory and ICT concepts
- `docs/FVG_CRITERIOS_DETECCION.md` - FVG detection criteria
- `docs/DETECCION_FAIR_VALUE_GAPS.md` - FVG implementation
- `docs/ORDER_BLOCKS_CRITERIOS.md` - OB detection criteria
- `docs/LIQUIDITY_POOLS_CRITERIOS.md` - LP detection criteria
- `docs/LIQUIDITY_POOL_STATES.md` - LP lifecycle
- `docs/REBOTE_Y_PENETRACION_CRITERIOS.md` - Interaction classification

### Samples
- `docs/OB_24NOV_SAMPLE.md` - Order Block detection example
- `docs/OB_23NOV_SAMPLE.md` - OB detection example
- `docs/LP_20NOV_CRITICAL_LEVELS.md` - Liquidity Pool example

### Core
- `CLAUDE.md` - Complete architecture guide
- `docs/DATABASE_SCHEMA.md` - Pattern tables schema
- `docs/TIMEZONE_HANDLING.md` - **CRITICAL** timezone best practices
