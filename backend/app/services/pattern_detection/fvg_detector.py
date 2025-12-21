"""
FVG Detector Service

Detects Fair Value Gaps with auto-parameter calibration and text report generation.
Based on FVG_CRITERIOS_DETECCION.md
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy import text, func
from sqlalchemy.orm import Session
import pytz

from app.models.patterns import DetectedFVG
from app.schemas.patterns import FVGResponse, FVGGenerationResponse


class FVGDetector:
    """
    Fair Value Gap Detector

    Detects FVGs using 3-candle pattern analysis with auto-calibrated parameters.
    """

    def __init__(self, db: Session):
        self.db = db

    def auto_calibrate_parameters(
        self,
        symbol: str,
        timeframe: str
    ) -> Dict[str, float]:
        """
        Auto-calibrate minimum gap size based on timeframe and recent volatility

        Args:
            symbol: Trading symbol (e.g., "NQZ5")
            timeframe: Candle timeframe (e.g., "5min")

        Returns:
            Dict with calibrated parameters

        Strategy:
            - Base thresholds by timeframe
            - Adjust for recent ATR (last 20 trading days)
            - 5min: 1.0-2.0 pts
            - 15min: 2.0-4.0 pts
            - 1hr: 5.0-10.0 pts
        """
        # Base thresholds by timeframe
        base_thresholds = {
            "30s": 0.5,
            "1min": 0.75,
            "5min": 1.0,
            "15min": 2.0,
            "1hr": 5.0,
            "4hr": 10.0,
            "daily": 20.0,
            "weekly": 50.0,
        }

        min_gap_size = base_thresholds.get(timeframe, 1.0)

        # Calculate recent ATR to adjust for volatility
        table_name = f"candlestick_{timeframe}"
        query = text(f"""
            SELECT AVG(high - low) as avg_range
            FROM {table_name}
            WHERE symbol = :symbol
              AND time_interval >= NOW() - INTERVAL '20 days'
            LIMIT 500
        """)

        result = self.db.execute(query, {"symbol": symbol}).fetchone()
        if result and result[0]:
            avg_range = float(result[0])
            # Adjust threshold: 5-8% of average range
            volatility_adjusted = avg_range * 0.06
            min_gap_size = max(min_gap_size, volatility_adjusted)

        return {
            "min_gap_size": round(min_gap_size, 2),
            "timeframe": timeframe,
            "symbol": symbol,
        }

    def classify_significance(self, gap_size: float) -> str:
        """
        Classify FVG significance by gap size

        Args:
            gap_size: Gap size in points

        Returns:
            Significance level: MICRO, SMALL, MEDIUM, LARGE, EXTREME
        """
        if gap_size < 1.0:
            return "MICRO"
        elif gap_size < 5.0:
            return "SMALL"
        elif gap_size < 10.0:
            return "MEDIUM"
        elif gap_size < 20.0:
            return "LARGE"
        else:
            return "EXTREME"

    def detect_fvgs(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe: str = "5min"
    ) -> List[DetectedFVG]:
        """
        Detect Fair Value Gaps in date range

        Args:
            symbol: Trading symbol
            start_date: Start date for detection
            end_date: End date for detection
            timeframe: Candle timeframe

        Returns:
            List of detected FVGs
        """
        # Auto-calibrate parameters
        params = self.auto_calibrate_parameters(symbol, timeframe)
        min_gap_size = params["min_gap_size"]

        # Build query
        table_name = f"candlestick_{timeframe}"
        query = text(f"""
            WITH candles AS (
                SELECT
                    time_interval,
                    time_interval AT TIME ZONE 'America/New_York' as et_time,
                    open, high, low, close, volume,
                    -- Vela 1 (previous)
                    LAG(high, 1) OVER w as prev_high,
                    LAG(low, 1) OVER w as prev_low,
                    LAG(open, 1) OVER w as prev_open,
                    LAG(close, 1) OVER w as prev_close,
                    -- Vela 3 (next)
                    LEAD(high, 1) OVER w as next_high,
                    LEAD(low, 1) OVER w as next_low,
                    LEAD(open, 1) OVER w as next_open,
                    LEAD(close, 1) OVER w as next_close,
                    LEAD(time_interval, 1) OVER w as next_time,
                    -- ATR for displacement calculation (14-period)
                    AVG(high - low) OVER (ORDER BY time_interval ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) as atr
                FROM {table_name}
                WHERE symbol = :symbol
                  AND time_interval >= :start_time
                  AND time_interval <= :end_time
                  AND is_spread = false
                WINDOW w AS (ORDER BY time_interval)
            )
            SELECT
                next_time AT TIME ZONE 'America/New_York' as formation_time,
                -- FVG Type
                CASE
                    WHEN prev_high < next_low THEN 'BULLISH'
                    WHEN prev_low > next_high THEN 'BEARISH'
                END as fvg_type,
                -- FVG Zone
                CASE
                    WHEN prev_high < next_low THEN prev_high
                    WHEN prev_low > next_high THEN next_high
                END as fvg_start,
                CASE
                    WHEN prev_high < next_low THEN next_low
                    WHEN prev_low > next_high THEN prev_low
                END as fvg_end,
                -- Gap Size
                CASE
                    WHEN prev_high < next_low THEN next_low - prev_high
                    WHEN prev_low > next_high THEN prev_low - next_high
                END as gap_size,
                -- Midpoint
                CASE
                    WHEN prev_high < next_low THEN (prev_high + next_low) / 2
                    WHEN prev_low > next_high THEN (prev_low + next_high) / 2
                END as midpoint,
                -- Vela 1 details
                prev_high as vela1_high,
                prev_low as vela1_low,
                -- Vela 3 details
                next_high as vela3_high,
                next_low as vela3_low,
                -- ICT Levels
                CASE
                    WHEN prev_high < next_low THEN next_low  -- BULLISH: Premium = top
                    WHEN prev_low > next_high THEN prev_low  -- BEARISH: Premium = top
                END as premium_level,
                CASE
                    WHEN prev_high < next_low THEN prev_high  -- BULLISH: Discount = bottom
                    WHEN prev_low > next_high THEN next_high  -- BEARISH: Discount = bottom
                END as discount_level,
                CASE
                    WHEN prev_high < next_low THEN (prev_high + next_low) / 2  -- C.E. = midpoint
                    WHEN prev_low > next_high THEN (prev_low + next_high) / 2
                END as consequent_encroachment,
                -- Displacement Score (gap_size / ATR ratio)
                CASE
                    WHEN prev_high < next_low AND atr > 0 THEN (next_low - prev_high) / atr
                    WHEN prev_low > next_high AND atr > 0 THEN (prev_low - next_high) / atr
                    ELSE 0
                END as displacement_score,
                -- ATR for reference
                atr
            FROM candles
            WHERE (prev_high < next_low OR prev_low > next_high)
              AND CASE
                    WHEN prev_high < next_low THEN next_low - prev_high
                    WHEN prev_low > next_high THEN prev_low - next_high
                  END >= :min_gap_size
            ORDER BY et_time
        """)

        # Execute query - interpret dates as Eastern Time
        eastern = pytz.timezone('America/New_York')
        start_time_et = eastern.localize(datetime.combine(start_date, datetime.min.time()))
        end_time_et = eastern.localize(datetime.combine(end_date, datetime.max.time()))

        # Expand range for LAG/LEAD window (add 1 day buffer on each side)
        # Convert to UTC for database query (time_interval column is UTC)
        start_time_utc = (start_time_et - timedelta(days=1)).astimezone(pytz.UTC)
        end_time_utc = (end_time_et + timedelta(days=1)).astimezone(pytz.UTC)

        result = self.db.execute(query, {
            "symbol": symbol,
            "start_time": start_time_utc.replace(tzinfo=None),  # Remove tzinfo for PostgreSQL
            "end_time": end_time_utc.replace(tzinfo=None),
            "min_gap_size": min_gap_size
        })

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

            # Simple BOS detection: if displacement_score > 1.5, likely broke structure
            has_break_of_structure = row.displacement_score > 1.5 if row.displacement_score else False

            fvg = DetectedFVG(
                symbol=symbol,
                timeframe=timeframe,
                formation_time=formation_time.astimezone(pytz.UTC).replace(tzinfo=None),  # Convert to UTC naive for DB
                fvg_type=row.fvg_type,
                fvg_start=row.fvg_start,
                fvg_end=row.fvg_end,
                gap_size=row.gap_size,
                midpoint=row.midpoint,
                vela1_high=row.vela1_high,
                vela1_low=row.vela1_low,
                vela3_high=row.vela3_high,
                vela3_low=row.vela3_low,
                significance=significance,
                # ICT fields
                premium_level=row.premium_level,
                discount_level=row.discount_level,
                consequent_encroachment=row.consequent_encroachment,
                displacement_score=row.displacement_score,
                has_break_of_structure=has_break_of_structure,
                status="UNMITIGATED"
            )
            fvgs.append(fvg)

        return fvgs

    def update_fvg_states(
        self,
        symbol: str,
        timeframe: str,
        up_to_time: Optional[datetime] = None
    ) -> Dict[str, int]:
        """
        Update FVG states based on price action

        Checks all active FVGs (status != REBALANCED) and updates their states:
        - UNMITIGATED → REDELIVERED: Price touched zone but didn't fully close gap
        - REDELIVERED → REBALANCED: Price fully closed gap
        - UNMITIGATED → REBALANCED: Direct transition if fully filled on first touch

        Args:
            symbol: Trading symbol
            timeframe: Candle timeframe
            up_to_time: Check up to this time (default: now)

        Returns:
            Dict with counts of state transitions
        """
        if up_to_time is None:
            up_to_time = datetime.now(pytz.UTC)
        elif up_to_time.tzinfo is None:
            # Assume naive datetime is UTC
            up_to_time = up_to_time.replace(tzinfo=pytz.UTC)

        # Get active FVGs (not REBALANCED) ordered by formation time
        active_fvgs = self.db.query(DetectedFVG).filter(
            DetectedFVG.symbol == symbol,
            DetectedFVG.timeframe == timeframe,
            DetectedFVG.status != "REBALANCED"
        ).order_by(DetectedFVG.formation_time).all()

        if not active_fvgs:
            return {"total_checked": 0, "redelivered": 0, "rebalanced": 0}

        table_name = f"candlestick_{timeframe}"

        # Track state changes
        stats = {
            "total_checked": len(active_fvgs),
            "redelivered": 0,
            "rebalanced": 0
        }

        for fvg in active_fvgs:
            # Determine time range to check
            # Start from last_checked_time or formation_time
            if fvg.last_checked_time:
                check_from = fvg.last_checked_time
                if check_from.tzinfo is None:
                    check_from = check_from.replace(tzinfo=pytz.UTC)
            else:
                check_from = fvg.formation_time
                if check_from.tzinfo is None:
                    check_from = check_from.replace(tzinfo=pytz.UTC)

            # Query candles in the check range
            query = text(f"""
                SELECT time_interval, high, low, close
                FROM {table_name}
                WHERE symbol = :symbol
                  AND time_interval > :check_from
                  AND time_interval <= :up_to_time
                  AND is_spread = false
                ORDER BY time_interval
            """)

            result = self.db.execute(query, {
                "symbol": symbol,
                "check_from": check_from.replace(tzinfo=None),  # PostgreSQL naive
                "up_to_time": up_to_time.replace(tzinfo=None)
            })

            candles = list(result)
            if not candles:
                # No new candles to check, just update last_checked_time
                fvg.last_checked_time = up_to_time.replace(tzinfo=None)
                continue

            # Check each candle for state transitions
            new_status = fvg.status

            for candle in candles:
                if fvg.fvg_type == "BULLISH":
                    # BULLISH FVG: zone is [fvg_start, fvg_end]
                    # fvg_start = Vela 1 High (discount, bottom)
                    # fvg_end = Vela 3 Low (premium, top)

                    # Check if price entered the zone
                    if candle.low <= fvg.fvg_end:
                        # Price touched or entered the FVG zone
                        if candle.close <= fvg.fvg_start:
                            # Fully closed the gap (price closed below bottom)
                            new_status = "REBALANCED"
                            break  # No need to check further candles
                        else:
                            # Partial fill (touched zone but didn't close gap)
                            if fvg.status == "UNMITIGATED":
                                new_status = "REDELIVERED"
                            # Don't break - keep checking for full rebalance

                elif fvg.fvg_type == "BEARISH":
                    # BEARISH FVG: zone is [fvg_end, fvg_start]
                    # fvg_end = Vela 3 High (discount, bottom)
                    # fvg_start = Vela 1 Low (premium, top)

                    # Check if price entered the zone
                    if candle.high >= fvg.fvg_end:
                        # Price touched or entered the FVG zone
                        if candle.close >= fvg.fvg_start:
                            # Fully closed the gap (price closed above top)
                            new_status = "REBALANCED"
                            break  # No need to check further candles
                        else:
                            # Partial fill (touched zone but didn't close gap)
                            if fvg.status == "UNMITIGATED":
                                new_status = "REDELIVERED"
                            # Don't break - keep checking for full rebalance

            # Update stats only if status actually changed
            if new_status != fvg.status:
                if new_status == "REDELIVERED":
                    stats["redelivered"] += 1
                elif new_status == "REBALANCED":
                    stats["rebalanced"] += 1

            # Update FVG status and last_checked_time
            fvg.status = new_status
            fvg.last_checked_time = up_to_time.replace(tzinfo=None)

        # Commit all changes
        self.db.commit()

        return stats

    def generate_fvgs(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe: str = "5min",
        save_to_db: bool = True
    ) -> FVGGenerationResponse:
        """
        Generate FVGs and optionally save to database

        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            timeframe: Candle timeframe
            save_to_db: Whether to save detected FVGs to database

        Returns:
            FVGGenerationResponse with detected FVGs and text report
        """
        # Detect FVGs
        fvgs = self.detect_fvgs(symbol, start_date, end_date, timeframe)

        # Save to database if requested
        if save_to_db:
            self.db.add_all(fvgs)
            self.db.commit()
            for fvg in fvgs:
                self.db.refresh(fvg)

        # Update states of existing FVGs (on-demand approach)
        # Check all previously detected FVGs up to end_date
        eastern = pytz.timezone('America/New_York')
        end_time_et = eastern.localize(datetime.combine(end_date, datetime.max.time()))
        end_time_utc = end_time_et.astimezone(pytz.UTC)

        state_update_stats = self.update_fvg_states(
            symbol=symbol,
            timeframe=timeframe,
            up_to_time=end_time_utc
        )

        # Get auto parameters
        params = self.auto_calibrate_parameters(symbol, timeframe)

        # Convert to response models
        fvg_responses = [FVGResponse.from_orm(fvg) for fvg in fvgs]

        # Generate text report
        text_report = self.generate_text_report(
            fvgs=fvgs,
            params=params,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            state_update_stats=state_update_stats
        )

        return FVGGenerationResponse(
            total=len(fvgs),
            auto_parameters=params,
            state_update_stats=state_update_stats,
            fvgs=fvg_responses,
            text_report=text_report
        )

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

    def generate_text_report(
        self,
        fvgs: List[DetectedFVG],
        params: Dict,
        symbol: str,
        start_date: date,
        end_date: date,
        state_update_stats: Optional[Dict[str, int]] = None
    ) -> str:
        """
        Generate markdown text report for detected FVGs

        Args:
            fvgs: List of detected FVGs
            params: Auto-calibrated parameters
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            state_update_stats: Statistics from state updates

        Returns:
            Markdown formatted report string
        """
        # Count by type
        bullish_count = sum(1 for fvg in fvgs if fvg.fvg_type == "BULLISH")
        bearish_count = sum(1 for fvg in fvgs if fvg.fvg_type == "BEARISH")

        # Count by significance
        significance_counts = {}
        for fvg in fvgs:
            significance_counts[fvg.significance] = significance_counts.get(fvg.significance, 0) + 1

        # Build report
        report = f"""# Fair Value Gaps - {symbol}

## Detection Summary

**Period**: {start_date} to {end_date}
**Timeframe**: {params['timeframe']}
**Total FVGs Detected**: {len(fvgs)}

### Breakdown
- **Bullish FVGs**: {bullish_count}
- **Bearish FVGs**: {bearish_count}

### By Significance
"""
        for sig in ["EXTREME", "LARGE", "MEDIUM", "SMALL", "MICRO"]:
            count = significance_counts.get(sig, 0)
            if count > 0:
                report += f"- **{sig}**: {count}\n"

        # Add state update stats if available
        if state_update_stats:
            report += f"""
### State Updates
- **Total FVGs Checked**: {state_update_stats.get('total_checked', 0)}
- **Newly REDELIVERED**: {state_update_stats.get('redelivered', 0)} (price touched zone)
- **Newly REBALANCED**: {state_update_stats.get('rebalanced', 0)} (gap fully closed)
"""

        report += f"""
### Auto-Calibrated Parameters
- **Min Gap Size**: {params['min_gap_size']} pts

---

## Detected FVGs

"""
        # Add each FVG
        for i, fvg in enumerate(fvgs, 1):
            bos_emoji = "⚡" if fvg.has_break_of_structure else ""
            report += f"""### {i}. {fvg.fvg_type} FVG {bos_emoji} @ {self._format_et_time(fvg.formation_time)}

```
Gap Details:
  Type: {fvg.fvg_type}
  Gap Size: {fvg.gap_size:.2f} pts
  Range: {fvg.fvg_start:.2f} - {fvg.fvg_end:.2f}
  Significance: {fvg.significance}

ICT Levels (3 Key Levels):
  🔴 Premium:     {fvg.premium_level:.2f} pts  (High boundary)
  ⚪ C.E. (50%):  {fvg.consequent_encroachment:.2f} pts  (Midpoint)
  🟢 Discount:    {fvg.discount_level:.2f} pts  (Low boundary)

Displacement Analysis:
  Displacement Score: {fvg.displacement_score:.2f}x ATR
  Break of Structure: {"YES ⚡" if fvg.has_break_of_structure else "NO"}

Vela 1 (Previous):
  High: {fvg.vela1_high:.2f}
  Low: {fvg.vela1_low:.2f}

Vela 3 (Formation Candle):
  High: {fvg.vela3_high:.2f}
  Low: {fvg.vela3_low:.2f}

Status: {fvg.status}
```

---

"""

        report += f"""
## Trading Implications

### ICT 3 Key Levels
- **Premium** (🔴): High boundary - Best for shorts (BEARISH) or profit targets (BULLISH)
- **Consequent Encroachment** (⚪): 50% level - Primary entry zone for high-probability setups
- **Discount** (🟢): Low boundary - Best for longs (BULLISH) or profit targets (BEARISH)

### FVG State Lifecycle
- **UNMITIGATED** 🟢: FVG untouched - Most powerful state, waiting for price to return
- **REDELIVERED** 🟡: Price touched the zone but didn't fully close the gap - Still valid, partial fill
- **REBALANCED** 🔴: Gap fully closed - FVG loses power, no longer valid for trading

**Important**: Only trade UNMITIGATED or REDELIVERED FVGs. REBALANCED FVGs are invalidated.

### For Bullish FVGs (BISI - Buyside Imbalance, Sellside Inefficiency)
- Act as **SUPPORT** when price retraces
- **Best Entry**: Discount level (low boundary) or C.E. (50%)
- **Conservative Entry**: Only at Discount level
- **Stop Loss**: Below Discount level
- **State Transitions**:
  - UNMITIGATED → REDELIVERED: Price touches zone (low <= premium)
  - → REBALANCED: Price closes below discount level

### For Bearish FVGs (SIBI - Sellside Imbalance, Buyside Inefficiency)
- Act as **RESISTANCE** when price retraces
- **Best Entry**: Premium level (high boundary) or C.E. (50%)
- **Conservative Entry**: Only at Premium level
- **Stop Loss**: Above Premium level
- **State Transitions**:
  - UNMITIGATED → REDELIVERED: Price touches zone (high >= discount)
  - → REBALANCED: Price closes above premium level

### Displacement & Break of Structure
- **High Displacement** (>1.5x ATR): Strong institutional activity, higher probability setup
- **Break of Structure** (⚡): Confirms trend change, FVG likely to hold on retest

---

*Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Source: NQHUB Pattern Detection System*
*Enhanced with ICT Smart Money Concepts*
"""

        return report
