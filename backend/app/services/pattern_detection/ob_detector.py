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
        for row in result:
            if row.ob_type is None:
                continue

            # Determine impulse direction
            impulse_direction = "UP" if row.impulse_move > 0 else "DOWN"

            # Calculate candle range
            candle_range = float(row.ob_high - row.ob_low)

            # Evaluate quality
            quality = self.evaluate_quality(
                impulse_move=float(row.impulse_move),
                ob_volume=float(row.ob_volume),
                avg_session_volume=avg_session_volume,
                candle_range=candle_range,
                strong_threshold=strong_threshold
            )

            ob = DetectedOrderBlock(
                symbol=symbol,
                timeframe=timeframe,
                formation_time=row.formation_time,
                ob_type=row.ob_type,
                ob_high=row.ob_high,
                ob_low=row.ob_low,
                ob_open=row.ob_open,
                ob_close=row.ob_close,
                ob_volume=row.ob_volume,
                impulse_move=row.impulse_move,
                impulse_direction=impulse_direction,
                candle_direction=row.candle_direction,
                quality=quality,
                status="ACTIVE"
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

    def _format_et_time(self, utc_time: datetime) -> str:
        """
        Convert UTC datetime to Eastern Time (EST/EDT) string

        Args:
            utc_time: UTC datetime object

        Returns:
            Formatted time string with timezone (e.g., "14:30 EST" or "15:30 EDT")
        """
        eastern = pytz.timezone('US/Eastern')
        # Ensure utc_time has UTC timezone info
        if utc_time.tzinfo is None:
            utc_time = utc_time.replace(tzinfo=pytz.UTC)

        # Convert to Eastern Time
        et_time = utc_time.astimezone(eastern)

        # Get timezone abbreviation (EST or EDT)
        tz_abbr = et_time.strftime('%Z')

        return et_time.strftime(f'%H:%M {tz_abbr}')

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
