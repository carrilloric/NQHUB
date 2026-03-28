# Timezone Handling - NQHUB Best Practices

**Created**: 2025-12-12
**Last Updated**: 2025-12-12
**Status**: ✅ Active Standard

---

## ⚠️ CRITICAL WARNING

**NEVER** save datetime objects to PostgreSQL without explicitly converting to UTC naive first.

**NEVER** trust SQL `AT TIME ZONE` to return the correct timezone-aware datetime for database storage.

---

## Table of Contents

1. [The Problem](#the-problem)
2. [Architecture](#architecture)
3. [The Correct Pattern](#the-correct-pattern)
4. [Anti-Patterns](#anti-patterns)
5. [Validation Checklist](#validation-checklist)
6. [Reference Code](#reference-code)
7. [Troubleshooting](#troubleshooting)

---

## The Problem

### What Went Wrong

On December 12, 2025, we discovered a critical timezone bug in the Order Blocks and Liquidity Pools detectors:

**Symptom**: Timestamps displayed with incorrect dates (off by 5 hours)
```
Expected: Nov 6, 00:20 EST (vela en ATAS)
Got:      Nov 5, 19:20 EST (reporte de OB)
```

**Root Cause**: SQL query with `AT TIME ZONE 'America/New_York'` returns a **naive datetime in ET**, but PostgreSQL interprets it as **UTC** when saving:

```python
# ❌ INCORRECT FLOW
DB: 2025-11-06 05:20:00+00 UTC
  ↓ SQL: AT TIME ZONE 'America/New_York'
  ↓ Python receives: 2025-11-06 00:20:00 (naive, but in ET)
  ↓ Save to DB: formation_time=row.formation_time
  ↓ PostgreSQL assumes: 2025-11-06 00:20:00+00 UTC ← WRONG!
  ↓ Read from DB: 2025-11-06 00:20:00+00 UTC
  ↓ Convert to EST: 2025-11-05 19:20:00 EST ← INCORRECT (5 hours off)
```

**Impact**: 1,335 Order Blocks and 132 Liquidity Pools had incorrect timestamps.

**Fix Applied**: Copied timezone handling pattern from FVG detector to OB and LP detectors.

---

## Architecture

### Timezone Flow in NQHUB

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INPUT (EST/EDT)                        │
│              "Buscar patrones del 6 de Nov"                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PYTHON BACKEND (FastAPI)                     │
│  • Convert user date to ET aware: eastern.localize()            │
│  • Convert to UTC for DB queries: .astimezone(pytz.UTC)        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   POSTGRESQL DATABASE                           │
│  • Storage: TIMESTAMP WITH TIME ZONE (UTC)                      │
│  • Stored as: UTC naive (e.g., 2025-11-06 05:20:00+00)        │
│  • Query with: AT TIME ZONE converts to specified timezone     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PYTHON PROCESSING                            │
│  1. Receive naive datetime from SQL (in ET if AT TIME ZONE)   │
│  2. Localize to ET: eastern.localize(naive_dt)                 │
│  3. Convert to UTC: et_aware.astimezone(pytz.UTC)              │
│  4. Remove tzinfo: utc_aware.replace(tzinfo=None)              │
│  5. Save to DB: UTC naive                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API RESPONSE (JSON)                        │
│  • Format: ISO 8601 with Z (e.g., "2025-11-06T05:20:00Z")     │
│  • Timezone: UTC                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TEXT REPORTS / DISPLAY                       │
│  • Format: "YYYY-MM-DD HH:MM:SS EST (HH:MM:SS UTC)"           │
│  • Example: "2025-11-06 00:20:00 EST (05:20:00 UTC)"          │
│  • Method: _format_et_time() in each detector                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Database**: Always stores UTC naive (timezone info removed before INSERT)
2. **API**: Always returns ISO 8601 with Z (UTC)
3. **Display**: Always shows EST/EDT with UTC reference
4. **Conversions**: Always explicit with pytz (never implicit)

---

## The Correct Pattern

### ✅ Step-by-Step Guide

When you receive a datetime from SQL with `AT TIME ZONE`:

```python
import pytz
from datetime import datetime

# Step 1: Get datetime from SQL (AT TIME ZONE returns naive in specified timezone)
query = text(f"""
    SELECT time_interval AT TIME ZONE 'America/New_York' as et_time
    FROM candlestick_5min
    WHERE ...
""")
result = db.execute(query).fetchone()
formation_time = result.et_time  # naive datetime in ET

# Step 2: Localize to ET (make timezone-aware)
eastern = pytz.timezone('America/New_York')
if formation_time.tzinfo is None:
    # If naive, assume it's already in ET (from AT TIME ZONE)
    formation_time_aware = eastern.localize(formation_time)
else:
    # If already timezone-aware, convert to ET
    formation_time_aware = formation_time.astimezone(eastern)

# Step 3: Convert to UTC
formation_time_utc = formation_time_aware.astimezone(pytz.UTC)

# Step 4: Remove timezone info (make naive UTC for DB storage)
formation_time_utc_naive = formation_time_utc.replace(tzinfo=None)

# Step 5: Save to database
pattern = DetectedPattern(
    formation_time=formation_time_utc_naive,  # ← UTC naive
    ...
)
db.add(pattern)
db.commit()
```

### ✅ Compact Version (One-Liner)

```python
# Assuming row.et_time is naive ET from AT TIME ZONE
eastern = pytz.timezone('America/New_York')
formation_time_utc_naive = eastern.localize(row.et_time).astimezone(pytz.UTC).replace(tzinfo=None)
```

### ✅ Display Formatting

```python
def _format_et_time(self, utc_time: datetime) -> str:
    """
    Convert UTC datetime to Eastern Time (EST/EDT) string with date and UTC time

    Args:
        utc_time: UTC datetime object

    Returns:
        Formatted time string with date, timezone, and UTC (e.g., "2024-11-06 14:30:00 EST (19:30:00 UTC)")
    """
    eastern = pytz.timezone('US/Eastern')

    # Ensure utc_time has UTC timezone info
    if utc_time.tzinfo is None:
        utc_time = utc_time.replace(tzinfo=pytz.UTC)

    # Convert to Eastern Time
    et_time = utc_time.astimezone(eastern)

    # Get timezone abbreviation (EST or EDT)
    tz_abbr = et_time.strftime('%Z')

    # Format: YYYY-MM-DD HH:MM:SS TZ (HH:MM:SS UTC)
    date_str = et_time.strftime('%Y-%m-%d')
    time_str = et_time.strftime('%H:%M:%S')
    utc_time_str = utc_time.strftime('%H:%M:%S')

    return f"{date_str} {time_str} {tz_abbr} ({utc_time_str} UTC)"
```

---

## Anti-Patterns

### ❌ NEVER Do This

#### 1. Saving Naive ET Datetime Directly
```python
# ❌ WRONG
query = text(f"SELECT time_interval AT TIME ZONE 'America/New_York' as et_time FROM ...")
result = db.execute(query).fetchone()

pattern = DetectedPattern(
    formation_time=result.et_time  # ← PostgreSQL will assume this is UTC!
)
```

**Why Wrong**: PostgreSQL stores `TIMESTAMP WITH TIME ZONE` by converting to UTC. If you pass a naive datetime, it assumes it's already UTC.

#### 2. Trusting Implicit Timezone Conversion
```python
# ❌ WRONG
utc_time = datetime.now()  # No timezone info
db.add(pattern)  # PostgreSQL guesses timezone
```

**Why Wrong**: Implicit conversions are unreliable and vary by database configuration.

#### 3. Mixing Timezone-Aware and Naive Datetimes
```python
# ❌ WRONG
et_time = pytz.timezone('America/New_York').localize(datetime.now())
pattern = DetectedPattern(
    formation_time=et_time  # ← Still timezone-aware!
)
```

**Why Wrong**: Some ORMs will fail, others will silently convert incorrectly.

#### 4. Using Local System Timezone
```python
# ❌ WRONG
from datetime import datetime
now = datetime.now()  # Uses system timezone (could be anything!)
```

**Why Wrong**: System timezone may not be UTC or ET. Always use explicit timezones with pytz.

---

## Validation Checklist

Use this checklist when implementing any feature that involves timestamps:

### Before Committing Code

- [ ] **SQL Queries**: If using `AT TIME ZONE`, am I converting the result to UTC naive?
- [ ] **Database Writes**: Are all timestamps converted to UTC naive before saving?
- [ ] **Explicit Conversion**: Am I using `pytz.timezone().localize()` and `.astimezone()`?
- [ ] **No Implicit Conversions**: Have I avoided `datetime.now()` without timezone?
- [ ] **Display Format**: Do text reports show `"YYYY-MM-DD HH:MM:SS EST (HH:MM:SS UTC)"`?

### Testing

- [ ] **Database Verification**: Query DB directly to confirm timestamps are UTC
  ```sql
  SELECT formation_time FROM detected_order_blocks LIMIT 1;
  -- Should show: 2025-11-06 05:20:00+00
  ```
- [ ] **API Response**: Confirm JSON has ISO 8601 with Z
  ```json
  { "formation_time": "2025-11-06T05:20:00Z" }
  ```
- [ ] **Display Validation**: Confirm text reports show EST with UTC reference
  ```
  2025-11-06 00:20:00 EST (05:20:00 UTC)
  ```
- [ ] **Cross-Reference**: Validate against known candles in ATAS or external source

### Manual Test

Pick a known candle (e.g., Nov 6, 15:55 EST) and verify:

1. You see it at **15:55 EST** in ATAS
2. Database shows **20:55 UTC** (`SELECT * WHERE time_interval = '2025-11-06 20:55:00'`)
3. API returns `"2025-11-06T20:55:00Z"`
4. Display shows `"2025-11-06 15:55:00 EST (20:55:00 UTC)"`

---

## Reference Code

### FVG Detector (Gold Standard)

**File**: `backend/app/services/pattern_detection/fvg_detector.py:240-261`

```python
# Convert to DetectedFVG objects and filter by ET date range
fvgs = []
for row in result:
    # Ensure formation_time is timezone-aware (ET)
    formation_time = row.formation_time
    if formation_time.tzinfo is None:
        # If naive, assume it's already in ET (from AT TIME ZONE)
        formation_time = eastern.localize(formation_time)
    else:
        # If already timezone-aware, convert to ET
        formation_time = formation_time.astimezone(eastern)

    # Filter: only include FVGs where formation_time is within the requested ET range
    if formation_time < start_time_et or formation_time > end_time_et:
        continue

    significance = self.classify_significance(row.gap_size)
    has_break_of_structure = row.displacement_score > 1.5 if row.displacement_score else False

    fvg = DetectedFVG(
        symbol=symbol,
        timeframe=timeframe,
        formation_time=formation_time.astimezone(pytz.UTC).replace(tzinfo=None),  # Convert to UTC naive for DB
        fvg_type=row.fvg_type,
        ...
    )
    fvgs.append(fvg)
```

### Order Blocks Detector (Fixed)

**File**: `backend/app/services/pattern_detection/ob_detector.py:276-324`

```python
# Convert to DetectedOrderBlock objects
obs = []
eastern = pytz.timezone('America/New_York')

for row in result:
    if row.ob_type is None:
        continue

    # Ensure formation_time is timezone-aware (ET)
    formation_time = row.formation_time
    if formation_time.tzinfo is None:
        # If naive, assume it's already in ET (from AT TIME ZONE)
        formation_time = eastern.localize(formation_time)
    else:
        # If already timezone-aware, convert to ET
        formation_time = formation_time.astimezone(eastern)

    # ... quality evaluation ...

    ob = DetectedOrderBlock(
        symbol=symbol,
        timeframe=timeframe,
        formation_time=formation_time.astimezone(pytz.UTC).replace(tzinfo=None),  # Convert to UTC naive for DB
        ob_type=row.ob_type,
        ...
    )
    obs.append(ob)
```

---

## Troubleshooting

### Problem: Display shows wrong date (off by 5 hours)

**Diagnosis**:
```python
# Check database timestamp
SELECT formation_time FROM detected_order_blocks WHERE id = 123;
# Should show: 2025-11-06 05:20:00+00

# If shows: 2025-11-06 00:20:00+00 ← WRONG (should be 05:20 UTC)
```

**Solution**: The datetime was saved as ET naive instead of UTC naive. Apply the correct pattern:
```python
formation_time = eastern.localize(row.et_time).astimezone(pytz.UTC).replace(tzinfo=None)
```

### Problem: "TypeError: can't subtract offset-naive and offset-aware datetimes"

**Diagnosis**: Mixing timezone-aware and naive datetimes.

**Solution**: Ensure all datetimes are consistently aware or naive:
```python
# Make aware
dt_aware = pytz.UTC.localize(naive_dt)

# Make naive
dt_naive = aware_dt.replace(tzinfo=None)
```

### Problem: API returns wrong timezone in JSON

**Diagnosis**: Check response format:
```json
// ❌ WRONG
{ "formation_time": "2025-11-06T00:20:00-05:00" }

// ✅ CORRECT
{ "formation_time": "2025-11-06T05:20:00Z" }
```

**Solution**: Ensure Pydantic model serializes as UTC:
```python
class OrderBlockResponse(BaseModel):
    formation_time: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%dT%H:%M:%SZ') if v else None
        }
```

### Problem: DST transitions cause issues

**Diagnosis**: Datetime falls during Daylight Saving Time transition (spring forward / fall back).

**Solution**: Use `pytz.localize()` with `is_dst=None` to raise error on ambiguous times:
```python
try:
    dt_aware = eastern.localize(naive_dt, is_dst=None)
except pytz.exceptions.AmbiguousTimeError:
    # Handle ambiguous time (fall back)
    pass
except pytz.exceptions.NonExistentTimeError:
    # Handle non-existent time (spring forward)
    pass
```

---

## Quick Reference

### Common Operations

| Operation | Code |
|-----------|------|
| Get current UTC time | `datetime.now(pytz.UTC)` |
| Convert ET to UTC naive | `eastern.localize(et_naive).astimezone(pytz.UTC).replace(tzinfo=None)` |
| Convert UTC naive to ET aware | `pytz.UTC.localize(utc_naive).astimezone(eastern)` |
| Format for display | `_format_et_time(utc_datetime)` |
| Parse user input (ET date) | `eastern.localize(datetime.combine(date_val, datetime.min.time()))` |

### Timezone References

- **Database**: UTC (stored as naive with `+00` offset)
- **API**: UTC (ISO 8601 with `Z`)
- **Display**: Eastern Time (EST -5 / EDT -4)
- **User Input**: Eastern Time (trading hours)

---

## Related Documentation

- `DATABASE_SCHEMA.md` - Database table definitions
- `FVG_CRITERIOS_DETECCION.md` - FVG detection criteria
- `ORDER_BLOCKS_CRITERIOS.md` - Order Blocks detection criteria
- `LIQUIDITY_POOLS_CRITERIOS.md` - Liquidity Pools detection criteria

---

## Change Log

### 2025-12-12 - Initial Creation
- Documented timezone bug found in OB and LP detectors
- Created standard pattern based on FVG detector
- Added validation checklist and troubleshooting guide
