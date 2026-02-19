"""
Order Block Detector Service

Detects Order Blocks based on impulse movements after specific candle types.
Based on ORDER_BLOCKS_CRITERIOS.md
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from sqlalchemy import text, func
from sqlalchemy.orm import Session
import pytz

from app.models.patterns import DetectedOrderBlock
from app.schemas.patterns import OrderBlockResponse, OrderBlockGenerationResponse


class OrderBlockDetector:
    """
    Order Block Detector

    Detects bullish and bearish order blocks based on:
    - BEARISH candle before bullish impulse = Bullish OB
    - BULLISH candle before bearish impulse = Bearish OB
    """

    def __init__(self, db: Session):
        self.db = db

    def auto_calibrate_parameters(
        self,
        symbol: str,
        timeframe: str
    ) -> Dict[str, float]:
        """
        Auto-calibrate impulse thresholds based on recent volatility

        Args:
            symbol: Trading symbol
            timeframe: Candle timeframe

        Returns:
            Dict with calibrated parameters
        """
        # Base thresholds
        base_min_impulse = {
            "30s": 5.0,
            "1min": 8.0,
            "5min": 15.0,
            "15min": 25.0,
            "1hr": 40.0,
            "4hr": 80.0,
            "daily": 150.0,
            "weekly": 300.0,
        }

        min_impulse = base_min_impulse.get(timeframe, 15.0)
        strong_threshold = min_impulse * 1.8  # Strong OBs: 1.8x min impulse

        # Calculate recent ATR for adjustment
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
            # Adjust: 12-15% of ATR for min impulse
            volatility_adjusted = float(avg_range) * 0.13
            min_impulse = float(max(min_impulse, volatility_adjusted))
            strong_threshold = float(min_impulse * 1.8)

        return {
            "min_impulse": round(min_impulse, 2),
            "strong_threshold": round(strong_threshold, 2),
            "lookforward_candles": 3,
            "timeframe": timeframe,
            "symbol": symbol,
        }

    def evaluate_quality(
        self,
        impulse_move: float,
        ob_volume: float,
        avg_session_volume: float,
        candle_range: float,
        strong_threshold: float
    ) -> str:
        """
        Evaluate Order Block quality

        Scoring system:
        - Impulse size: +1 to +3 points
        - Volume: +1 to +2 points
        - Body ratio: +1 point
        Total >=7: HIGH, >=5: MEDIUM, <5: LOW

        Args:
            impulse_move: Impulse movement in points
            ob_volume: OB candle volume
            avg_session_volume: Average session volume
            candle_range: OB candle range (high - low)
            strong_threshold: Strong impulse threshold

        Returns:
            Quality: HIGH, MEDIUM, LOW
        """
        score = 0

        # Impulse score
        abs_impulse = abs(impulse_move)
        if abs_impulse > strong_threshold:
            score += 3
        elif abs_impulse > strong_threshold * 0.7:
            score += 2
        else:
            score += 1

        # Volume score
        if avg_session_volume > 0:
            vol_ratio = ob_volume / avg_session_volume
            if vol_ratio > 2.0:
                score += 2
            elif vol_ratio > 1.5:
                score += 1

        # Body ratio score (simplified - would need open/close to calculate properly)
        # Assume average body ratio contributes 1 point on average
        score += 1

        # Classify
        if score >= 7:
            return "HIGH"
        elif score >= 5:
            return "MEDIUM"
        else:
            return "LOW"

    def detect_order_blocks(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe: str = "5min"
    ) -> List[DetectedOrderBlock]:
        """
        Detect Order Blocks in date range

        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            timeframe: Candle timeframe

        Returns:
            List of detected Order Blocks
        """
        # Auto-calibrate parameters
        params = self.auto_calibrate_parameters(symbol, timeframe)
        min_impulse = params["min_impulse"]
        strong_threshold = params["strong_threshold"]

        # Calculate average session volume for quality scoring
        table_name = f"candlestick_{timeframe}"
        avg_vol_query = text(f"""
            SELECT AVG(volume) as avg_volume
            FROM {table_name}
            WHERE symbol = :symbol
              AND time_interval >= :start_time
              AND time_interval <= :end_time
              AND is_spread = false
        """)

        # Interpret dates as Eastern Time
        eastern = pytz.timezone('America/New_York')
        start_time = eastern.localize(datetime.combine(start_date, datetime.min.time()))
        end_time = eastern.localize(datetime.combine(end_date, datetime.max.time()))

        avg_vol_result = self.db.execute(avg_vol_query, {
            "symbol": symbol,
            "start_time": start_time,
            "end_time": end_time
        }).fetchone()

        avg_session_volume = float(avg_vol_result[0]) if avg_vol_result and avg_vol_result[0] else 1000.0

        # Main query
        query = text(f"""
            WITH candles_analysis AS (
                SELECT
                    time_interval AT TIME ZONE 'America/New_York' as et_time,
                    open, high, low, close, volume,
                    -- Candle direction
                    CASE
                        WHEN close > open THEN 'BULLISH'
                        WHEN close < open THEN 'BEARISH'
                        ELSE 'DOJI'
                    END as direction,
                    -- Movement in next 3 candles
                    LEAD(close, 3) OVER w - close as move_3candles,
                    -- Max/min of next 3 candles (to check for violation)
                    GREATEST(
                        LEAD(high, 1) OVER w,
                        LEAD(high, 2) OVER w,
                        LEAD(high, 3) OVER w
                    ) as max_next3,
                    LEAST(
                        LEAD(low, 1) OVER w,
                        LEAD(low, 2) OVER w,
                        LEAD(low, 3) OVER w
                    ) as min_next3
                FROM {table_name}
                WHERE symbol = :symbol
                  AND time_interval >= :start_time
                  AND time_interval <= :end_time
                  AND is_spread = false
                WINDOW w AS (ORDER BY time_interval)
            )
            SELECT
                et_time as formation_time,
                direction as candle_direction,
                ROUND(high::numeric, 2) as ob_high,
                ROUND(low::numeric, 2) as ob_low,
                ROUND(open::numeric, 2) as ob_open,
                ROUND(close::numeric, 2) as ob_close,
                ROUND(volume::numeric, 2) as ob_volume,
                ROUND(move_3candles::numeric, 2) as impulse_move,
                -- Classify OB type
                CASE
                    -- STRONG BULLISH OB: Bearish candle + strong bullish impulse
                    WHEN direction = 'BEARISH'
                         AND move_3candles > :strong_threshold
                         AND min_next3 >= low
                         THEN 'STRONG BULLISH OB'
                    -- BULLISH OB: Bearish candle + normal bullish impulse
                    WHEN direction = 'BEARISH'
                         AND move_3candles >= :min_impulse
                         AND move_3candles <= :strong_threshold
                         AND min_next3 >= low
                         THEN 'BULLISH OB'
                    -- STRONG BEARISH OB: Bullish candle + strong bearish impulse
                    WHEN direction = 'BULLISH'
                         AND move_3candles < -:strong_threshold
                         AND max_next3 <= high
                         THEN 'STRONG BEARISH OB'
                    -- BEARISH OB: Bullish candle + normal bearish impulse
                    WHEN direction = 'BULLISH'
                         AND move_3candles <= -:min_impulse
                         AND move_3candles >= -:strong_threshold
                         AND max_next3 <= high
                         THEN 'BEARISH OB'
                    ELSE NULL
                END as ob_type
            FROM candles_analysis
            WHERE ABS(move_3candles) >= :min_impulse
              AND CASE
                    WHEN direction = 'BEARISH' AND move_3candles > 0 THEN min_next3 >= low
                    WHEN direction = 'BULLISH' AND move_3candles < 0 THEN max_next3 <= high
                    ELSE false
                  END
            ORDER BY et_time
        """)

        result = self.db.execute(query, {
            "symbol": symbol,
            "start_time": start_time,
            "end_time": end_time,
            "min_impulse": min_impulse,
            "strong_threshold": strong_threshold
        })

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

            # Determine impulse direction
            impulse_direction = "UP" if row.impulse_move > 0 else "DOWN"

            # Calculate candle range
            candle_range = float(row.ob_high - row.ob_low)

            # Calculate midpoints
            ob_body_midpoint = (float(row.ob_open) + float(row.ob_close)) / 2.0
            ob_range_midpoint = (float(row.ob_high) + float(row.ob_low)) / 2.0

            # Evaluate quality
            quality = self.evaluate_quality(
                impulse_move=float(row.impulse_move),
                ob_volume=float(row.ob_volume),
                avg_session_volume=avg_session_volume,
                candle_range=candle_range,
                strong_threshold=strong_threshold
            )

            # Get current time for lifecycle tracking
            now_utc = datetime.now(pytz.UTC).replace(tzinfo=None)  # UTC naive for DB
            formation_time_utc_naive = formation_time.astimezone(pytz.UTC).replace(tzinfo=None)

            ob = DetectedOrderBlock(
                symbol=symbol,
                timeframe=timeframe,
                formation_time=formation_time_utc_naive,  # Convert to UTC naive for DB
                ob_type=row.ob_type,
                ob_high=row.ob_high,
                ob_low=row.ob_low,
                ob_open=row.ob_open,
                ob_close=row.ob_close,
                ob_volume=row.ob_volume,
                ob_body_midpoint=ob_body_midpoint,
                ob_range_midpoint=ob_range_midpoint,
                impulse_move=row.impulse_move,
                impulse_direction=impulse_direction,
                candle_direction=row.candle_direction,
                quality=quality,
                status="ACTIVE",
                # Initialize lifecycle tracking fields
                last_checked_time=now_utc,  # Time when this OB was generated/last checked
                last_checked_candle_time=formation_time_utc_naive,  # Start checking from formation
                test_count=0,  # No tests yet
                max_penetration_pts=0.0,  # No penetration yet
                max_penetration_pct=0.0  # No penetration yet
            )
            obs.append(ob)

        return obs

    def generate_order_blocks(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe: str = "5min",
        save_to_db: bool = True
    ) -> OrderBlockGenerationResponse:
        """
        Generate Order Blocks and optionally save to database

        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            timeframe: Candle timeframe
            save_to_db: Whether to save to database

        Returns:
            OrderBlockGenerationResponse with detected OBs and text report
        """
        # Detect OBs
        obs = self.detect_order_blocks(symbol, start_date, end_date, timeframe)

        # Save to database if requested
        if save_to_db:
            self.db.add_all(obs)
            self.db.commit()
            for ob in obs:
                self.db.refresh(ob)

            # IMPORTANT: Auto-update lifecycle states after generation
            # This handles the case where OBs are generated for historical data
            # (e.g., generating on Nov 30 for Nov 1-5 range)
            # The update will check ALL price action from formation_time to NOW
            # and populate lifecycle fields (test_count, broken_time, etc.)
            self.update_ob_states(
                symbol=symbol,
                timeframe=timeframe,
                up_to_time=datetime.now(pytz.UTC)
            )

        # Calculate breakdown
        breakdown = {}
        for ob in obs:
            breakdown[ob.ob_type] = breakdown.get(ob.ob_type, 0) + 1

        # Get auto parameters
        params = self.auto_calibrate_parameters(symbol, timeframe)

        # Convert to response models
        ob_responses = [OrderBlockResponse.from_orm(ob) for ob in obs]

        # Generate text report
        text_report = self.generate_text_report(obs, params, symbol, start_date, end_date)

        return OrderBlockGenerationResponse(
            total=len(obs),
            breakdown=breakdown,
            auto_parameters=params,
            order_blocks=ob_responses,
            text_report=text_report
        )

    def update_ob_states(
        self,
        symbol: str,
        timeframe: str,
        up_to_time: datetime
    ) -> Dict[str, int]:
        """
        Update OB states based on price action up to a given time

        Checks ACTIVE Order Blocks and updates their status to TESTED or BROKEN based on:
        - TESTED: Price touches OB zone (3 detection options captured)
        - BROKEN: Price closes beyond OB zone (invalidation)

        Args:
            symbol: Trading symbol
            timeframe: Candle timeframe
            up_to_time: Check price action up to this time (timezone-aware UTC)

        Returns:
            Dict with stats: {total_checked, tested, broken}
        """
        # Query ACTIVE Order Blocks for this symbol and timeframe
        active_obs = self.db.query(DetectedOrderBlock).filter(
            DetectedOrderBlock.symbol == symbol,
            DetectedOrderBlock.timeframe == timeframe,
            DetectedOrderBlock.status == "ACTIVE"
        ).all()

        if not active_obs:
            return {"total_checked": 0, "tested": 0, "broken": 0}

        table_name = f"candlestick_{timeframe}"

        # Track state changes
        stats = {
            "total_checked": len(active_obs),
            "tested": 0,
            "broken": 0
        }

        for ob in active_obs:
            # Determine time range to check
            # Start from last_checked_candle_time or formation_time
            if ob.last_checked_candle_time:
                check_from = ob.last_checked_candle_time
                if check_from.tzinfo is None:
                    check_from = check_from.replace(tzinfo=pytz.UTC)
            else:
                check_from = ob.formation_time
                if check_from.tzinfo is None:
                    check_from = check_from.replace(tzinfo=pytz.UTC)

            # Query candles in the check range
            query = text(f"""
                SELECT time_interval, high, low, close, open
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
                ob.last_checked_time = up_to_time.replace(tzinfo=None)
                continue

            # Check each candle for state transitions
            new_status = ob.status

            for candle in candles:
                # Update last_checked_candle_time
                last_candle_time = candle.time_interval
                if last_candle_time.tzinfo is None:
                    last_candle_time = last_candle_time.replace(tzinfo=pytz.UTC)
                ob.last_checked_candle_time = last_candle_time.replace(tzinfo=None)

                if "BULLISH" in ob.ob_type:
                    # BULLISH OB: zone is [ob_low, ob_high]
                    # Acts as SUPPORT - expecting price to bounce off bottom

                    # Option 1: Edge touch (candle.low touches ob_high)
                    if candle.low <= ob.ob_high and ob.first_touch_edge_time is None:
                        ob.first_touch_edge_time = last_candle_time.replace(tzinfo=None)
                        ob.first_touch_edge_price = candle.low

                    # Option 2: Midpoint touch (candle.low touches ob_body_midpoint)
                    if candle.low <= ob.ob_body_midpoint and ob.first_touch_midpoint_time is None:
                        ob.first_touch_midpoint_time = last_candle_time.replace(tzinfo=None)
                        ob.first_touch_midpoint_price = candle.low

                    # Option 3: Entry without close (candle enters zone but doesn't close inside)
                    if (candle.low < ob.ob_high and
                        candle.close >= ob.ob_low and
                        ob.first_entry_no_close_time is None):
                        ob.first_entry_no_close_time = last_candle_time.replace(tzinfo=None)
                        ob.first_entry_candle_close = candle.close

                    # Update test_count and test_times if any touch occurred
                    if candle.low <= ob.ob_high:
                        if ob.test_times is None:
                            ob.test_times = []
                        if last_candle_time.replace(tzinfo=None) not in ob.test_times:
                            ob.test_times.append(last_candle_time.replace(tzinfo=None))
                            ob.test_count += 1
                            if new_status == "ACTIVE":
                                new_status = "TESTED"

                    # Calculate penetration (how far price went into OB zone)
                    if candle.low < ob.ob_high:
                        penetration_pts = max(0, ob.ob_high - candle.low)
                        ob_range = ob.ob_high - ob.ob_low
                        penetration_pct = (penetration_pts / ob_range * 100) if ob_range > 0 else 0

                        if penetration_pts > ob.max_penetration_pts:
                            ob.max_penetration_pts = penetration_pts
                        if penetration_pct > ob.max_penetration_pct:
                            ob.max_penetration_pct = penetration_pct

                    # BROKEN: Price closes below OB low (invalidation)
                    if candle.close < ob.ob_low:
                        new_status = "BROKEN"
                        if ob.broken_time is None:
                            ob.broken_time = last_candle_time.replace(tzinfo=None)
                            ob.broken_candle_close = candle.close
                        break  # No need to check further candles

                elif "BEARISH" in ob.ob_type:
                    # BEARISH OB: zone is [ob_low, ob_high]
                    # Acts as RESISTANCE - expecting price to bounce off top

                    # Option 1: Edge touch (candle.high touches ob_low)
                    if candle.high >= ob.ob_low and ob.first_touch_edge_time is None:
                        ob.first_touch_edge_time = last_candle_time.replace(tzinfo=None)
                        ob.first_touch_edge_price = candle.high

                    # Option 2: Midpoint touch (candle.high touches ob_body_midpoint)
                    if candle.high >= ob.ob_body_midpoint and ob.first_touch_midpoint_time is None:
                        ob.first_touch_midpoint_time = last_candle_time.replace(tzinfo=None)
                        ob.first_touch_midpoint_price = candle.high

                    # Option 3: Entry without close (candle enters zone but doesn't close inside)
                    if (candle.high > ob.ob_low and
                        candle.close <= ob.ob_high and
                        ob.first_entry_no_close_time is None):
                        ob.first_entry_no_close_time = last_candle_time.replace(tzinfo=None)
                        ob.first_entry_candle_close = candle.close

                    # Update test_count and test_times if any touch occurred
                    if candle.high >= ob.ob_low:
                        if ob.test_times is None:
                            ob.test_times = []
                        if last_candle_time.replace(tzinfo=None) not in ob.test_times:
                            ob.test_times.append(last_candle_time.replace(tzinfo=None))
                            ob.test_count += 1
                            if new_status == "ACTIVE":
                                new_status = "TESTED"

                    # Calculate penetration (how far price went into OB zone)
                    if candle.high > ob.ob_low:
                        penetration_pts = max(0, candle.high - ob.ob_low)
                        ob_range = ob.ob_high - ob.ob_low
                        penetration_pct = (penetration_pts / ob_range * 100) if ob_range > 0 else 0

                        if penetration_pts > ob.max_penetration_pts:
                            ob.max_penetration_pts = penetration_pts
                        if penetration_pct > ob.max_penetration_pct:
                            ob.max_penetration_pct = penetration_pct

                    # BROKEN: Price closes above OB high (invalidation)
                    if candle.close > ob.ob_high:
                        new_status = "BROKEN"
                        if ob.broken_time is None:
                            ob.broken_time = last_candle_time.replace(tzinfo=None)
                            ob.broken_candle_close = candle.close
                        break  # No need to check further candles

            # Update stats only if status actually changed
            if new_status != ob.status:
                if new_status == "TESTED":
                    stats["tested"] += 1
                elif new_status == "BROKEN":
                    stats["broken"] += 1

            # Update OB status and last_checked_time
            ob.status = new_status
            ob.last_checked_time = up_to_time.replace(tzinfo=None)

        # Commit all changes
        self.db.commit()

        return stats

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
        obs: List[DetectedOrderBlock],
        params: Dict,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> str:
        """Generate markdown text report for detected Order Blocks"""
        # Count by type
        type_counts = {}
        for ob in obs:
            type_counts[ob.ob_type] = type_counts.get(ob.ob_type, 0) + 1

        # Count by quality
        quality_counts = {}
        for ob in obs:
            quality_counts[ob.quality] = quality_counts.get(ob.quality, 0) + 1

        report = f"""# Order Blocks - {symbol}

## Detection Summary

**Period**: {start_date} to {end_date}
**Timeframe**: {params['timeframe']}
**Total Order Blocks Detected**: {len(obs)}

### Breakdown by Type
"""
        for ob_type in ["STRONG BULLISH OB", "BULLISH OB", "STRONG BEARISH OB", "BEARISH OB"]:
            count = type_counts.get(ob_type, 0)
            if count > 0:
                report += f"- **{ob_type}**: {count}\n"

        report += """
### Breakdown by Quality
"""
        for quality in ["HIGH", "MEDIUM", "LOW"]:
            count = quality_counts.get(quality, 0)
            if count > 0:
                report += f"- **{quality}**: {count}\n"

        report += f"""
### Auto-Calibrated Parameters
- **Min Impulse**: {params['min_impulse']} pts
- **Strong Threshold**: {params['strong_threshold']} pts
- **Lookforward Candles**: {params['lookforward_candles']}

---

## Detected Order Blocks

"""
        # Add each OB
        for i, ob in enumerate(obs, 1):
            emoji = "⭐" if "STRONG" in ob.ob_type else "✅" if "BULLISH" in ob.ob_type else "❌"

            report += f"""### {i}. {ob.ob_type} {emoji} @ {self._format_et_time(ob.formation_time)}

```
OB Candle:
  Type: {ob.candle_direction}
  Open:  {ob.ob_open:.2f}
  High:  {ob.ob_high:.2f}
  Low:   {ob.ob_low:.2f}
  Close: {ob.ob_close:.2f}
  Range: {ob.ob_high - ob.ob_low:.2f} pts

  Body Midpoint (50%):  {ob.ob_body_midpoint:.2f}
  Range Midpoint (50%): {ob.ob_range_midpoint:.2f}

  Volume: {ob.ob_volume:.0f} contratos

Impulso:
  Direction: {ob.impulse_direction}
  Movement in 3 candles: {ob.impulse_move:+.2f} pts

Quality: {ob.quality}
Status: {ob.status}
```

---

"""

        report += """
## Trading Implications

### Bullish Order Blocks
- **Function**: Act as SUPPORT when price retraces
- **Entry**: Near OB low or midpoint
- **Stop Loss**: Below OB low
- **Invalidation**: Clean break and close below OB low

### Bearish Order Blocks
- **Function**: Act as RESISTANCE when price retraces
- **Entry**: Near OB high or midpoint
- **Stop Loss**: Above OB high
- **Invalidation**: Clean break and close above OB high

### Quality Levels
- **HIGH**: Strong impulse + high volume + good structure
- **MEDIUM**: Moderate impulse or volume
- **LOW**: Weak impulse or low volume (use with caution)

---

*Report Generated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """*
*Source: NQHUB Pattern Detection System*
"""

        return report
