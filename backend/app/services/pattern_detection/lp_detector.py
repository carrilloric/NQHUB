"""
Liquidity Pool Detector Service

Detects Liquidity Pools (Equal Highs/Lows, Triple Patterns, Swing Levels, Session Levels).
Based on LIQUIDITY_POOLS_CRITERIOS.md
"""
from datetime import datetime, date, timedelta, time
from typing import List, Dict, Optional, Tuple
from sqlalchemy import text, func
from sqlalchemy.orm import Session
import pytz

from app.models.patterns import DetectedLiquidityPool
from app.schemas.patterns import LiquidityPoolResponse, LiquidityPoolGenerationResponse


class LiquidityPoolDetector:
    """
    Liquidity Pool Detector

    Detects 5 types of liquidity pools:
    - Equal Highs (EQH) / Equal Lows (EQL)
    - Triple Highs (TH) / Triple Lows (TL)
    - Swing High/Low
    - Session Highs/Lows (ASH, ASL, LSH, LSL, NYH, NYL)
    """

    def __init__(self, db: Session):
        self.db = db

    def auto_calibrate_parameters(
        self,
        symbol: str,
        timeframe: str
    ) -> Dict[str, float]:
        """
        Auto-calibrate tolerance for Equal Highs/Lows clustering

        Args:
            symbol: Trading symbol
            timeframe: Candle timeframe

        Returns:
            Dict with calibrated parameters
        """
        # Base tolerance for NQ
        tolerance = 10.0  # ±10 points for NQ

        # Could adjust based on recent volatility (future enhancement)

        return {
            "tolerance": tolerance,
            "timeframe": timeframe,
            "symbol": symbol,
            "min_touches_eqh_eql": 2,
            "min_touches_triple": 3,
            "swing_lookback": 5,
        }

    def classify_strength(
        self,
        num_touches: int,
        total_volume: Optional[float]
    ) -> str:
        """
        Classify LP strength

        Args:
            num_touches: Number of times level was touched
            total_volume: Total volume at touches

        Returns:
            Strength: STRONG, NORMAL, WEAK
        """
        if num_touches >= 3 and (total_volume is None or total_volume > 10000):
            return "STRONG"
        elif num_touches >= 2 and (total_volume is None or total_volume > 5000):
            return "NORMAL"
        else:
            return "WEAK"

    def detect_equal_highs(
        self,
        symbol: str,
        date_val: date,
        timeframe: str,
        tolerance: float
    ) -> List[DetectedLiquidityPool]:
        """
        Detect Equal Highs

        Args:
            symbol: Trading symbol
            date_val: Date to analyze
            timeframe: Candle timeframe
            tolerance: Tolerance in points (±tolerance)

        Returns:
            List of EQH liquidity pools
        """
        table_name = f"candlestick_{timeframe}"
        query = text(f"""
            WITH candles_with_window AS (
                SELECT
                    time_interval AT TIME ZONE 'America/New_York' as et_time,
                    high,
                    volume,
                    ROW_NUMBER() OVER (ORDER BY time_interval) as rn,
                    LAG(high, 1) OVER (ORDER BY time_interval) as prev_high_1,
                    LAG(high, 2) OVER (ORDER BY time_interval) as prev_high_2,
                    LEAD(high, 1) OVER (ORDER BY time_interval) as next_high_1,
                    LEAD(high, 2) OVER (ORDER BY time_interval) as next_high_2
                FROM {table_name}
                WHERE symbol = :symbol
                  AND DATE(time_interval AT TIME ZONE 'America/New_York') = :date_val
                  AND is_spread = false
            ),
            swing_highs AS (
                SELECT et_time, high, volume, rn
                FROM candles_with_window
                WHERE high > prev_high_1
                  AND high > prev_high_2
                  AND high > next_high_1
                  AND high > next_high_2
            ),
            equal_high_clusters AS (
                SELECT
                    ROUND(a.high / :tolerance) * :tolerance as level_bucket,
                    ARRAY_AGG(a.et_time ORDER BY a.et_time) as touch_times,
                    COUNT(*) as num_touches,
                    AVG(a.high) as avg_level,
                    SUM(a.volume) as total_volume,
                    MIN(a.et_time) as first_touch
                FROM swing_highs a
                JOIN swing_highs b ON b.rn > a.rn
                    AND b.rn >= a.rn + 20  -- Min 20 candles apart (1h40m for 5min)
                    AND b.rn <= a.rn + 50  -- Max 50 candles apart (4h10m for 5min)
                    AND ABS(a.high - b.high) <= :tolerance
                GROUP BY level_bucket
                HAVING COUNT(*) >= 2  -- Min 2 touches for EQH
                   AND MAX(a.high) - MIN(a.high) <= :tolerance
            )
            SELECT * FROM equal_high_clusters
        """)

        result = self.db.execute(query, {
            "symbol": symbol,
            "date_val": date_val,
            "tolerance": tolerance
        })

        pools = []
        for row in result:
            strength = self.classify_strength(row.num_touches, row.total_volume)
            pool = DetectedLiquidityPool(
                symbol=symbol,
                timeframe=timeframe,
                formation_time=row.first_touch,
                pool_type="EQH",
                level=row.avg_level,
                tolerance=tolerance,
                touch_times=row.touch_times,
                num_touches=row.num_touches,
                total_volume=row.total_volume,
                strength=strength,
                status="UNMITIGATED"
            )
            pools.append(pool)

        return pools

    def detect_equal_lows(
        self,
        symbol: str,
        date_val: date,
        timeframe: str,
        tolerance: float
    ) -> List[DetectedLiquidityPool]:
        """Detect Equal Lows - similar logic to EQH but with lows"""
        table_name = f"candlestick_{timeframe}"
        query = text(f"""
            WITH candles_with_window AS (
                SELECT
                    time_interval AT TIME ZONE 'America/New_York' as et_time,
                    low,
                    volume,
                    ROW_NUMBER() OVER (ORDER BY time_interval) as rn,
                    LAG(low, 1) OVER (ORDER BY time_interval) as prev_low_1,
                    LAG(low, 2) OVER (ORDER BY time_interval) as prev_low_2,
                    LEAD(low, 1) OVER (ORDER BY time_interval) as next_low_1,
                    LEAD(low, 2) OVER (ORDER BY time_interval) as next_low_2
                FROM {table_name}
                WHERE symbol = :symbol
                  AND DATE(time_interval AT TIME ZONE 'America/New_York') = :date_val
                  AND is_spread = false
            ),
            swing_lows AS (
                SELECT et_time, low, volume, rn
                FROM candles_with_window
                WHERE low < prev_low_1
                  AND low < prev_low_2
                  AND low < next_low_1
                  AND low < next_low_2
            ),
            equal_low_clusters AS (
                SELECT
                    ROUND(a.low / :tolerance) * :tolerance as level_bucket,
                    ARRAY_AGG(a.et_time ORDER BY a.et_time) as touch_times,
                    COUNT(*) as num_touches,
                    AVG(a.low) as avg_level,
                    SUM(a.volume) as total_volume,
                    MIN(a.et_time) as first_touch
                FROM swing_lows a
                JOIN swing_lows b ON b.rn > a.rn
                    AND b.rn >= a.rn + 20
                    AND b.rn <= a.rn + 50
                    AND ABS(a.low - b.low) <= :tolerance
                GROUP BY level_bucket
                HAVING COUNT(*) >= 2
                   AND MAX(a.low) - MIN(a.low) <= :tolerance
            )
            SELECT * FROM equal_low_clusters
        """)

        result = self.db.execute(query, {
            "symbol": symbol,
            "date_val": date_val,
            "tolerance": tolerance
        })

        pools = []
        for row in result:
            strength = self.classify_strength(row.num_touches, row.total_volume)
            pool = DetectedLiquidityPool(
                symbol=symbol,
                timeframe=timeframe,
                formation_time=row.first_touch,
                pool_type="EQL",
                level=row.avg_level,
                tolerance=tolerance,
                touch_times=row.touch_times,
                num_touches=row.num_touches,
                total_volume=row.total_volume,
                strength=strength,
                status="UNMITIGATED"
            )
            pools.append(pool)

        return pools

    def detect_session_levels(
        self,
        symbol: str,
        date_val: date,
        timeframe: str = "5min"
    ) -> List[DetectedLiquidityPool]:
        """
        Detect Session Highs/Lows

        Detects:
        - ASH/ASL: Asian Session (20:00 prev day - 02:00 ET)
        - LSH/LSL: London Session (03:00 - 08:00 ET)
        - NYH/NYL: NY Session (09:30 - 16:00 ET)

        Args:
            symbol: Trading symbol
            date_val: Date to analyze
            timeframe: Candle timeframe

        Returns:
            List of session level liquidity pools
        """
        table_name = f"candlestick_{timeframe}"

        # Adjust date range to include previous day evening for Asian session
        # Interpret times as Eastern Time
        eastern = pytz.timezone('America/New_York')
        start_time = eastern.localize(datetime.combine(date_val - timedelta(days=1), time(20, 0)))
        end_time = eastern.localize(datetime.combine(date_val, time(23, 59)))

        query = text(f"""
            SELECT
                -- Asian Session
                MAX(CASE WHEN (et_hour >= 20 OR et_hour < 2) THEN high END) as ash,
                MIN(CASE WHEN (et_hour >= 20 OR et_hour < 2) THEN low END) as asl,
                -- London Session
                MAX(CASE WHEN et_hour >= 3 AND et_hour < 8 THEN high END) as lsh,
                MIN(CASE WHEN et_hour >= 3 AND et_hour < 8 THEN low END) as lsl,
                -- NY Session
                MAX(CASE WHEN (et_hour = 9 AND et_minute >= 30) OR (et_hour >= 10 AND et_hour < 16) THEN high END) as nyh,
                MIN(CASE WHEN (et_hour = 9 AND et_minute >= 30) OR (et_hour >= 10 AND et_hour < 16) THEN low END) as nyl
            FROM (
                SELECT
                    high, low,
                    EXTRACT(HOUR FROM time_interval AT TIME ZONE 'America/New_York') as et_hour,
                    EXTRACT(MINUTE FROM time_interval AT TIME ZONE 'America/New_York') as et_minute
                FROM {table_name}
                WHERE symbol = :symbol
                  AND time_interval >= :start_time
                  AND time_interval <= :end_time
                  AND is_spread = false
            ) candles
        """)

        result = self.db.execute(query, {
            "symbol": symbol,
            "start_time": start_time,
            "end_time": end_time
        }).fetchone()

        pools = []
        session_time = datetime.combine(date_val, time(12, 0))  # Noon as reference time

        # Create LP for each session level
        if result:
            session_levels = [
                ("ASH", result.ash),
                ("ASL", result.asl),
                ("LSH", result.lsh),
                ("LSL", result.lsl),
                ("NYH", result.nyh),
                ("NYL", result.nyl),
            ]

            for pool_type, level in session_levels:
                if level is not None:
                    pool = DetectedLiquidityPool(
                        symbol=symbol,
                        timeframe=timeframe,
                        formation_time=session_time,
                        pool_type=pool_type,
                        level=level,
                        tolerance=5.0,  # Tighter tolerance for session levels
                        touch_times=[session_time],
                        num_touches=1,
                        total_volume=None,
                        strength="STRONG",  # Session levels are inherently strong
                        status="UNMITIGATED"
                    )
                    pools.append(pool)

        return pools

    def detect_all_pools(
        self,
        symbol: str,
        date_val: date,
        timeframe: str = "5min",
        pool_types: Optional[List[str]] = None
    ) -> List[DetectedLiquidityPool]:
        """
        Detect all liquidity pool types

        Args:
            symbol: Trading symbol
            date_val: Date to analyze
            timeframe: Candle timeframe
            pool_types: Optional filter (e.g., ["EQH", "SESSION"])

        Returns:
            Combined list of all detected pools
        """
        params = self.auto_calibrate_parameters(symbol, timeframe)
        tolerance = params["tolerance"]

        all_pools = []

        # Determine which types to detect
        detect_eqh_eql = pool_types is None or "EQH" in pool_types or "EQL" in pool_types
        detect_session = pool_types is None or "SESSION" in pool_types

        if detect_eqh_eql:
            eqh_pools = self.detect_equal_highs(symbol, date_val, timeframe, tolerance)
            eql_pools = self.detect_equal_lows(symbol, date_val, timeframe, tolerance)
            all_pools.extend(eqh_pools)
            all_pools.extend(eql_pools)

        if detect_session:
            session_pools = self.detect_session_levels(symbol, date_val, timeframe)
            all_pools.extend(session_pools)

        return all_pools

    def generate_liquidity_pools(
        self,
        symbol: str,
        date_val: date,
        timeframe: str = "5min",
        pool_types: Optional[List[str]] = None,
        save_to_db: bool = True
    ) -> LiquidityPoolGenerationResponse:
        """
        Generate Liquidity Pools and optionally save to database

        Args:
            symbol: Trading symbol
            date_val: Date to analyze
            timeframe: Candle timeframe
            pool_types: Optional filter
            save_to_db: Whether to save to database

        Returns:
            LiquidityPoolGenerationResponse with detected pools and text report
        """
        # Detect pools
        pools = self.detect_all_pools(symbol, date_val, timeframe, pool_types)

        # Save to database if requested
        if save_to_db:
            self.db.add_all(pools)
            self.db.commit()
            for pool in pools:
                self.db.refresh(pool)

        # Calculate breakdown
        breakdown = {}
        for pool in pools:
            breakdown[pool.pool_type] = breakdown.get(pool.pool_type, 0) + 1

        # Get auto parameters
        params = self.auto_calibrate_parameters(symbol, timeframe)

        # Convert to response models
        pool_responses = [LiquidityPoolResponse.from_orm(pool) for pool in pools]

        # Generate text report
        text_report = self.generate_text_report(pools, params, symbol, date_val)

        return LiquidityPoolGenerationResponse(
            total=len(pools),
            breakdown=breakdown,
            auto_parameters=params,
            pools=pool_responses,
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
        pools: List[DetectedLiquidityPool],
        params: Dict,
        symbol: str,
        date_val: date
    ) -> str:
        """Generate markdown text report for detected Liquidity Pools"""
        # Group by type
        pools_by_type = {}
        for pool in pools:
            if pool.pool_type not in pools_by_type:
                pools_by_type[pool.pool_type] = []
            pools_by_type[pool.pool_type].append(pool)

        report = f"""# Liquidity Pools - {symbol}

## Detection Summary

**Date**: {date_val}
**Timeframe**: {params['timeframe']}
**Total Pools Detected**: {len(pools)}

### Breakdown by Type
"""
        for pool_type in sorted(pools_by_type.keys()):
            count = len(pools_by_type[pool_type])
            report += f"- **{pool_type}**: {count}\n"

        report += f"""
### Auto-Calibrated Parameters
- **Tolerance**: ±{params['tolerance']} pts
- **Min Touches (EQH/EQL)**: {params['min_touches_eqh_eql']}

---

## Detected Liquidity Pools

"""
        # Add each pool by type
        for pool_type in ["NYH", "NYL", "LSH", "LSL", "ASH", "ASL", "EQH", "EQL"]:
            if pool_type in pools_by_type:
                report += f"### {pool_type} Pools\n\n"
                for pool in pools_by_type[pool_type]:
                    report += f"""**Level: {pool.level:.2f}** ({pool.strength})
- Touches: {pool.num_touches}
- Status: {pool.status}
- Formation: {self._format_et_time(pool.formation_time) if pool.formation_time else 'N/A'}

"""

        report += """
---

## Trading Implications

### Session Highs (ASH, LSH, NYH)
- **Buy-Side Liquidity** (stops above)
- Likely to be swept before bearish moves
- Watch for false breakouts

### Session Lows (ASL, LSL, NYL)
- **Sell-Side Liquidity** (stops below)
- Likely to be swept before bullish moves
- Watch for false breakouts

### Equal Highs/Lows (EQH, EQL)
- Multiple touches = accumulating liquidity
- 3+ touches = **STRONG** liquidity pool
- High probability sweep candidates

---

*Report Generated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """*
*Source: NQHUB Pattern Detection System*
"""

        return report
