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
            "min_touches_eqh_eql": 3,  # Changed from 2 to 3 for simplified approach
            "min_touches_triple": 3,
            "swing_lookback": 5,
        }

    def classify_strength(
        self,
        num_touches: int,
        total_volume: Optional[float],
        zone_size: Optional[float] = None
    ) -> str:
        """
        Classify LP strength based on touches, volume, and zone compactness

        Args:
            num_touches: Number of times level was touched
            total_volume: Total volume at touches
            zone_size: Size of the zone in points (smaller = more precise = stronger)

        Returns:
            Strength: STRONG, NORMAL, WEAK

        CRITERIA:
        - More touches = stronger
        - Higher volume = stronger
        - Smaller zone_size = stronger (more precise touches)
        """
        # Base score from touches
        if num_touches >= 5:
            touch_score = 3
        elif num_touches >= 3:
            touch_score = 2
        else:
            touch_score = 1

        # Volume score
        if total_volume is None or total_volume > 10000:
            volume_score = 2
        elif total_volume > 5000:
            volume_score = 1
        else:
            volume_score = 0

        # Zone compactness score (smaller zone = more precise = stronger)
        # For NQ, zones < 5 pts are very tight, 5-10 pts are normal, >10 pts are loose
        if zone_size is not None:
            if zone_size < 5:
                zone_score = 2  # Very compact
            elif zone_size < 10:
                zone_score = 1  # Normal
            else:
                zone_score = 0  # Loose
        else:
            zone_score = 1  # Default if not provided

        # Total score
        total_score = touch_score + volume_score + zone_score

        # Classify based on total score
        if total_score >= 6:
            return "STRONG"
        elif total_score >= 4:
            return "NORMAL"
        else:
            return "WEAK"

    def find_modal_level(
        self,
        prices: List[float],
        sub_tolerance: float = 2.0
    ) -> dict:
        """
        Find the modal (most frequent) level within a cluster using sub-clustering

        Args:
            prices: List of high/low prices from cluster
            sub_tolerance: Tolerance for sub-clustering (default ±2 pts)

        Returns:
            dict with modal_level, modal_count, spread
        """
        if not prices:
            return {"modal_level": 0, "modal_count": 0, "spread": 0}

        # Sort prices for sub-clustering
        sorted_prices = sorted(prices)

        # Sub-cluster with tighter tolerance
        sub_clusters = []
        current_sub = [sorted_prices[0]]
        anchor = sorted_prices[0]

        for i in range(1, len(sorted_prices)):
            if abs(sorted_prices[i] - anchor) <= sub_tolerance:
                current_sub.append(sorted_prices[i])
            else:
                sub_clusters.append(current_sub)
                current_sub = [sorted_prices[i]]
                anchor = sorted_prices[i]

        # Don't forget last sub-cluster
        if current_sub:
            sub_clusters.append(current_sub)

        # Find sub-cluster with most touches (modal)
        modal_sub = max(sub_clusters, key=len)
        modal_level = sum(modal_sub) / len(modal_sub)  # Average of modal sub-cluster
        modal_count = len(modal_sub)

        # Spread = total dispersion of original cluster
        spread = max(prices) - min(prices)

        return {
            "modal_level": modal_level,
            "modal_count": modal_count,
            "spread": spread
        }

    def post_cluster_by_proximity(
        self,
        pools: List[DetectedLiquidityPool],
        proximity_threshold: float = 20.0
    ) -> List[DetectedLiquidityPool]:
        """
        Merge pools that are within proximity_threshold points of each other.

        Algorithm:
        1. Separate EQH and EQL pools
        2. Sort each group by level
        3. For each group, merge pools within proximity_threshold
        4. Combine touch_times from merged pools

        Args:
            pools: List of detected pools
            proximity_threshold: Distance in points to merge (default 20.0)

        Returns:
            List of merged pools
        """
        # Separate by type (don't merge EQH with EQL)
        eqh_pools = [p for p in pools if p.pool_type == "EQH"]
        eql_pools = [p for p in pools if p.pool_type == "EQL"]
        session_pools = [p for p in pools if p.pool_type not in ["EQH", "EQL"]]

        merged_pools = []

        # Process EQH pools
        if eqh_pools:
            merged_pools.extend(self._merge_pool_group(eqh_pools, proximity_threshold))

        # Process EQL pools
        if eql_pools:
            merged_pools.extend(self._merge_pool_group(eql_pools, proximity_threshold))

        # Session pools don't get merged (different criteria)
        merged_pools.extend(session_pools)

        return merged_pools

    def _merge_pool_group(
        self,
        pools: List[DetectedLiquidityPool],
        proximity_threshold: float
    ) -> List[DetectedLiquidityPool]:
        """
        Merge pools within a single group (all EQH or all EQL)

        Uses chain-based clustering: each pool is compared to the PREVIOUS pool,
        not the anchor. This creates a chaining effect where pools within
        proximity_threshold of each other are merged together.

        Args:
            pools: Pools of same type (all EQH or all EQL)
            proximity_threshold: Distance threshold for merging

        Returns:
            Merged pools
        """
        if not pools:
            return []

        # Sort by level
        sorted_pools = sorted(pools, key=lambda p: p.level)

        merged = []
        current_cluster = [sorted_pools[0]]

        for i in range(1, len(sorted_pools)):
            pool = sorted_pools[i]
            prev_pool = current_cluster[-1]  # Last pool in current cluster

            # Check if within proximity of PREVIOUS pool (chain-based)
            if abs(pool.level - prev_pool.level) <= proximity_threshold:
                current_cluster.append(pool)
            else:
                # Finalize current cluster and start new one
                merged.append(self._merge_pools(current_cluster))
                current_cluster = [pool]

        # Don't forget the last cluster
        if current_cluster:
            merged.append(self._merge_pools(current_cluster))

        return merged

    def _merge_pools(
        self,
        pools: List[DetectedLiquidityPool]
    ) -> DetectedLiquidityPool:
        """
        Merge multiple pools into one by combining their touch_times

        Args:
            pools: Pools to merge (all same type)

        Returns:
            Single merged pool
        """
        if len(pools) == 1:
            return pools[0]

        # Use the first pool as base
        merged = pools[0]

        # Combine all touch_times (deduplicate)
        all_touch_times = set(merged.touch_times or [])
        for pool in pools[1:]:
            if pool.touch_times:
                all_touch_times.update(pool.touch_times)

        merged.touch_times = sorted(list(all_touch_times))
        merged.num_touches = len(merged.touch_times)

        # Recalculate zone based on all touches
        # For EQH: zone is range of HIGHs, for EQL: range of LOWs
        # We'll query the actual prices at touch_times and recalculate
        if merged.touch_times:
            # Query to get actual highs/lows at touch_times
            table_name = f"candlestick_{merged.timeframe}"
            price_field = "high" if merged.pool_type == "EQH" else "low"

            from sqlalchemy import text
            query = text(f"""
                SELECT {price_field}
                FROM {table_name}
                WHERE symbol = :symbol
                  AND time_interval = ANY(:touch_times)
            """)

            result = self.db.execute(query, {
                "symbol": merged.symbol,
                "touch_times": merged.touch_times
            })

            prices = [row[0] for row in result]

            if prices:
                merged.zone_low = min(prices)
                merged.zone_high = max(prices)
                merged.level = sum(prices) / len(prices)  # Average level

        # Sum total volume from all merged pools
        merged.total_volume = sum(p.total_volume or 0 for p in pools)

        # Recalculate strength based on new num_touches
        if merged.num_touches >= 8:
            merged.strength = "STRONG"
        elif merged.num_touches >= 5:
            merged.strength = "NORMAL"
        else:
            merged.strength = "WEAK"

        return merged

    def detect_equal_highs(
        self,
        symbol: str,
        date_val: date,
        timeframe: str,
        tolerance: float
    ) -> List[DetectedLiquidityPool]:
        """
        Detect Equal Highs - Correct Clustering Approach

        Groups candle highs that are within ±tolerance of each other.
        Creates zone from MIN(highs) to MAX(highs) of the group (NOT including lows).
        Atemporal: No time limit between touches.

        Args:
            symbol: Trading symbol
            date_val: Date to analyze
            timeframe: Candle timeframe
            tolerance: Tolerance in points (±tolerance from cluster mean)

        Returns:
            List of EQH liquidity pools (zones)
        """
        table_name = f"candlestick_{timeframe}"

        # Get all highs for the day (keep time_interval in UTC, filter by EST date)
        query = text(f"""
            SELECT
                time_interval as utc_time,
                high,
                volume
            FROM {table_name}
            WHERE symbol = :symbol
              AND DATE(time_interval AT TIME ZONE 'America/New_York') = :date_val
              AND is_spread = false
            ORDER BY high ASC
        """)

        result = self.db.execute(query, {
            "symbol": symbol,
            "date_val": date_val
        })

        # Get all candles with their highs (times are in UTC)
        candles = [{"time": row.utc_time, "high": row.high, "volume": row.volume}
                   for row in result]

        if not candles:
            return []

        # Cluster highs that are within ±tolerance of FIRST high (anchor)
        # This prevents "drift" where adding new candles gradually shifts the zone
        clusters = []
        current_cluster = [candles[0]]
        cluster_anchor = candles[0]["high"]  # First high is the anchor level

        for i in range(1, len(candles)):
            # Check if this candle's high is within ±tolerance of anchor
            if abs(candles[i]["high"] - cluster_anchor) <= tolerance:
                current_cluster.append(candles[i])
            else:
                # Start new cluster
                if len(current_cluster) >= 3:  # Save cluster if it has ≥3 touches
                    clusters.append(current_cluster)
                current_cluster = [candles[i]]
                cluster_anchor = candles[i]["high"]  # New anchor for new cluster

        # Don't forget the last cluster
        if len(current_cluster) >= 3:
            clusters.append(current_cluster)

        # Convert clusters to DetectedLiquidityPool objects
        pools = []
        for cluster_idx, cluster in enumerate(clusters):
            highs = [c["high"] for c in cluster]
            touch_times = [c["time"] for c in cluster]
            volumes = [c["volume"] for c in cluster]

            level = sum(highs) / len(highs)  # Average high
            zone_low = min(highs)  # MIN of highs (NOT lows of candles)
            zone_high = max(highs)  # MAX of highs
            zone_size = zone_high - zone_low  # Compactness of the zone
            total_volume = sum(volumes)
            num_touches = len(cluster)
            first_touch = min(touch_times)

            # Normalize first_touch to UTC naive for DB storage
            if first_touch.tzinfo is None:
                # If naive, assume UTC
                first_touch_utc_naive = first_touch
            else:
                # If timezone-aware, convert to UTC and remove tzinfo
                first_touch_utc_naive = first_touch.astimezone(pytz.UTC).replace(tzinfo=None)

            # Normalize all touch_times to UTC naive
            touch_times_utc_naive = []
            for tt in touch_times:
                if tt.tzinfo is None:
                    touch_times_utc_naive.append(tt)
                else:
                    touch_times_utc_naive.append(tt.astimezone(pytz.UTC).replace(tzinfo=None))

            strength = self.classify_strength(num_touches, total_volume, zone_size)

            pool = DetectedLiquidityPool(
                symbol=symbol,
                timeframe=timeframe,
                formation_time=first_touch_utc_naive,
                pool_type="EQH",
                level=level,
                zone_low=zone_low,
                zone_high=zone_high,
                tolerance=tolerance,
                touch_times=touch_times_utc_naive,
                num_touches=num_touches,
                total_volume=total_volume,
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
        """
        Detect Equal Lows - Correct Clustering Approach

        Groups candle lows that are within ±tolerance of each other.
        Creates zone from MIN(lows) to MAX(lows) of the group (NOT including highs).
        Atemporal: No time limit between touches.

        CRITERIA:
        - Lows must be within ±tolerance of the cluster mean
        - Zone = range where lows actually touched (MIN to MAX of lows)
        - Minimum 3 touches to form a valid EQL
        - No time limit between touches

        Args:
            symbol: Trading symbol
            date_val: Date to analyze
            timeframe: Candle timeframe
            tolerance: Tolerance in points (±tolerance)

        Returns:
            List of EQL liquidity pools (zones)
        """
        table_name = f"candlestick_{timeframe}"

        # Get all lows for the day (keep time_interval in UTC, filter by EST date)
        query = text(f"""
            SELECT
                time_interval as utc_time,
                low,
                volume
            FROM {table_name}
            WHERE symbol = :symbol
              AND DATE(time_interval AT TIME ZONE 'America/New_York') = :date_val
              AND is_spread = false
            ORDER BY low ASC
        """)

        result = self.db.execute(query, {"symbol": symbol, "date_val": date_val})
        # Get all candles with their lows (times are in UTC)
        candles = [{"time": row.utc_time, "low": row.low, "volume": row.volume}
                   for row in result]

        if not candles:
            return []

        # Cluster lows that are within ±tolerance of FIRST low (anchor)
        # This prevents "drift" where adding new candles gradually shifts the zone
        clusters = []
        current_cluster = [candles[0]]
        cluster_anchor = candles[0]["low"]  # First low is the anchor level

        for i in range(1, len(candles)):
            # Check if this candle's low is within ±tolerance of anchor
            if abs(candles[i]["low"] - cluster_anchor) <= tolerance:
                current_cluster.append(candles[i])
            else:
                # Start new cluster
                if len(current_cluster) >= 3:  # Save cluster if it has ≥3 touches
                    clusters.append(current_cluster)
                current_cluster = [candles[i]]
                cluster_anchor = candles[i]["low"]  # New anchor for new cluster

        # Don't forget the last cluster
        if len(current_cluster) >= 3:
            clusters.append(current_cluster)

        # Convert clusters to DetectedLiquidityPool objects
        pools = []
        for cluster in clusters:
            lows = [c["low"] for c in cluster]
            touch_times = [c["time"] for c in cluster]
            volumes = [c["volume"] for c in cluster]

            level = sum(lows) / len(lows)  # Average low
            zone_low = min(lows)  # MIN of lows
            zone_high = max(lows)  # MAX of lows (NOT highs of candles)
            zone_size = zone_high - zone_low  # Compactness of the zone
            total_volume = sum(volumes)
            num_touches = len(cluster)
            first_touch = min(touch_times)

            # Normalize first_touch to UTC naive for DB storage
            if first_touch.tzinfo is None:
                # If naive, assume UTC
                first_touch_utc_naive = first_touch
            else:
                # If timezone-aware, convert to UTC and remove tzinfo
                first_touch_utc_naive = first_touch.astimezone(pytz.UTC).replace(tzinfo=None)

            # Normalize all touch_times to UTC naive
            touch_times_utc_naive = []
            for tt in touch_times:
                if tt.tzinfo is None:
                    touch_times_utc_naive.append(tt)
                else:
                    touch_times_utc_naive.append(tt.astimezone(pytz.UTC).replace(tzinfo=None))

            strength = self.classify_strength(num_touches, total_volume, zone_size)

            pool = DetectedLiquidityPool(
                symbol=symbol,
                timeframe=timeframe,
                formation_time=first_touch_utc_naive,
                pool_type="EQL",
                level=level,
                zone_low=zone_low,
                zone_high=zone_high,
                tolerance=tolerance,
                touch_times=touch_times_utc_naive,
                num_touches=num_touches,
                total_volume=total_volume,
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
            WITH candles_with_session AS (
                SELECT
                    time_interval AT TIME ZONE 'America/New_York' as et_time,
                    high, low,
                    EXTRACT(HOUR FROM time_interval AT TIME ZONE 'America/New_York') as et_hour,
                    EXTRACT(MINUTE FROM time_interval AT TIME ZONE 'America/New_York') as et_minute,
                    CASE
                        WHEN (EXTRACT(HOUR FROM time_interval AT TIME ZONE 'America/New_York') >= 20
                              OR EXTRACT(HOUR FROM time_interval AT TIME ZONE 'America/New_York') < 2)
                        THEN 'ASIAN'
                        WHEN EXTRACT(HOUR FROM time_interval AT TIME ZONE 'America/New_York') >= 3
                             AND EXTRACT(HOUR FROM time_interval AT TIME ZONE 'America/New_York') < 8
                        THEN 'LONDON'
                        WHEN (EXTRACT(HOUR FROM time_interval AT TIME ZONE 'America/New_York') = 9
                              AND EXTRACT(MINUTE FROM time_interval AT TIME ZONE 'America/New_York') >= 30)
                             OR (EXTRACT(HOUR FROM time_interval AT TIME ZONE 'America/New_York') >= 10
                                 AND EXTRACT(HOUR FROM time_interval AT TIME ZONE 'America/New_York') < 16)
                        THEN 'NY'
                        ELSE NULL
                    END as session
                FROM {table_name}
                WHERE symbol = :symbol
                  AND time_interval >= :start_time
                  AND time_interval <= :end_time
                  AND is_spread = false
            ),
            session_extremes AS (
                SELECT
                    session,
                    MAX(high) as max_high,
                    MIN(low) as min_low
                FROM candles_with_session
                WHERE session IS NOT NULL
                GROUP BY session
            ),
            session_highs AS (
                SELECT DISTINCT ON (c.session)
                    c.session,
                    'HIGH' as extreme_type,
                    c.et_time,
                    c.high as level
                FROM candles_with_session c
                JOIN session_extremes e ON c.session = e.session AND c.high = e.max_high
                WHERE c.session IS NOT NULL
                ORDER BY c.session, c.et_time
            ),
            session_lows AS (
                SELECT DISTINCT ON (c.session)
                    c.session,
                    'LOW' as extreme_type,
                    c.et_time,
                    c.low as level
                FROM candles_with_session c
                JOIN session_extremes e ON c.session = e.session AND c.low = e.min_low
                WHERE c.session IS NOT NULL
                ORDER BY c.session, c.et_time
            ),
            session_times AS (
                SELECT * FROM session_highs
                UNION ALL
                SELECT * FROM session_lows
            )
            SELECT
                MAX(CASE WHEN session = 'ASIAN' AND extreme_type = 'HIGH' THEN level END) as ash,
                MAX(CASE WHEN session = 'ASIAN' AND extreme_type = 'HIGH' THEN et_time END) as ash_time,
                MAX(CASE WHEN session = 'ASIAN' AND extreme_type = 'LOW' THEN level END) as asl,
                MAX(CASE WHEN session = 'ASIAN' AND extreme_type = 'LOW' THEN et_time END) as asl_time,
                MAX(CASE WHEN session = 'LONDON' AND extreme_type = 'HIGH' THEN level END) as lsh,
                MAX(CASE WHEN session = 'LONDON' AND extreme_type = 'HIGH' THEN et_time END) as lsh_time,
                MAX(CASE WHEN session = 'LONDON' AND extreme_type = 'LOW' THEN level END) as lsl,
                MAX(CASE WHEN session = 'LONDON' AND extreme_type = 'LOW' THEN et_time END) as lsl_time,
                MAX(CASE WHEN session = 'NY' AND extreme_type = 'HIGH' THEN level END) as nyh,
                MAX(CASE WHEN session = 'NY' AND extreme_type = 'HIGH' THEN et_time END) as nyh_time,
                MAX(CASE WHEN session = 'NY' AND extreme_type = 'LOW' THEN level END) as nyl,
                MAX(CASE WHEN session = 'NY' AND extreme_type = 'LOW' THEN et_time END) as nyl_time
            FROM session_times
        """)

        result = self.db.execute(query, {
            "symbol": symbol,
            "start_time": start_time,
            "end_time": end_time
        }).fetchone()

        pools = []
        eastern = pytz.timezone('America/New_York')

        # Create LP for each session level
        if result:
            session_levels = [
                ("ASH", result.ash, result.ash_time),
                ("ASL", result.asl, result.asl_time),
                ("LSH", result.lsh, result.lsh_time),
                ("LSL", result.lsl, result.lsl_time),
                ("NYH", result.nyh, result.nyh_time),
                ("NYL", result.nyl, result.nyl_time),
            ]

            for pool_type, level, level_time in session_levels:
                if level is not None and level_time is not None:
                    # Ensure level_time is timezone-aware (ET) then convert to UTC naive
                    if level_time.tzinfo is None:
                        # If naive, assume it's already in ET (from AT TIME ZONE)
                        level_time_aware = eastern.localize(level_time)
                    else:
                        # If already timezone-aware, convert to ET
                        level_time_aware = level_time.astimezone(eastern)

                    # Convert to UTC naive for DB storage
                    level_time_utc_naive = level_time_aware.astimezone(pytz.UTC).replace(tzinfo=None)

                    pool = DetectedLiquidityPool(
                        symbol=symbol,
                        timeframe=timeframe,
                        formation_time=level_time_utc_naive,  # Store as UTC naive
                        pool_type=pool_type,
                        level=level,
                        tolerance=5.0,  # Tighter tolerance for session levels
                        touch_times=[level_time_utc_naive],  # Store as UTC naive
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
        session_types = {"ASH", "ASL", "LSH", "LSL", "NYH", "NYL", "SESSION"}

        detect_eqh_eql = pool_types is None or "EQH" in pool_types or "EQL" in pool_types
        detect_session = pool_types is None or "SESSION" in pool_types or any(t in session_types for t in pool_types)

        if detect_eqh_eql:
            eqh_pools = self.detect_equal_highs(symbol, date_val, timeframe, tolerance)
            eql_pools = self.detect_equal_lows(symbol, date_val, timeframe, tolerance)
            all_pools.extend(eqh_pools)
            all_pools.extend(eql_pools)

        if detect_session:
            session_pools = self.detect_session_levels(symbol, date_val, timeframe)
            # Filter session pools if specific types were requested
            if pool_types is not None and "SESSION" not in pool_types:
                session_pools = [p for p in session_pools if p.pool_type in pool_types]
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
        # Delete existing pools for this date (to avoid duplicates from algorithm changes)
        if save_to_db:
            self.db.query(DetectedLiquidityPool).filter(
                DetectedLiquidityPool.symbol == symbol,
                DetectedLiquidityPool.timeframe == timeframe,
                func.date(DetectedLiquidityPool.formation_time) == date_val
            ).delete()
            self.db.commit()

        # Detect pools
        pools = self.detect_all_pools(symbol, date_val, timeframe, pool_types)

        # Post-cluster by proximity (merge nearby pools within 20 pts)
        pools = self.post_cluster_by_proximity(pools, proximity_threshold=20.0)

        # Save ALL pools to database (before filtering)
        if save_to_db:
            self.db.add_all(pools)
            self.db.commit()
            for pool in pools:
                self.db.refresh(pool)

        # Filter to only STRONG pools for EQH/EQL (session pools keep all)
        pools_for_response = [
            p for p in pools
            if p.pool_type not in ["EQH", "EQL"] or p.strength == "STRONG"
        ]

        # Calculate breakdown (from filtered pools)
        breakdown = {}
        for pool in pools_for_response:
            breakdown[pool.pool_type] = breakdown.get(pool.pool_type, 0) + 1

        # Get auto parameters
        params = self.auto_calibrate_parameters(symbol, timeframe)

        # Convert to response models (filtered pools only)
        pool_responses = [LiquidityPoolResponse.from_orm(pool) for pool in pools_for_response]

        # Get current price (last close of the day) for distance calculation
        table_name = f"candlestick_{timeframe}"
        from sqlalchemy import text
        query = text(f"""
            SELECT close
            FROM {table_name}
            WHERE symbol = :symbol
              AND DATE(time_interval) = :date_val
            ORDER BY time_interval DESC
            LIMIT 1
        """)
        result = self.db.execute(query, {"symbol": symbol, "date_val": date_val})
        row = result.fetchone()
        current_price = row[0] if row else None

        # Populate rectangle representation fields
        for pool_resp in pool_responses:
            # Start and end time from touch_times (chronologically)
            if pool_resp.touch_times and len(pool_resp.touch_times) > 0:
                pool_resp.start_time = min(pool_resp.touch_times)
                pool_resp.end_time = max(pool_resp.touch_times)

            # Liquidity type based on pool_type
            if pool_resp.pool_type == "EQH":
                pool_resp.liquidity_type = "Buy-Side Liquidity"
            elif pool_resp.pool_type == "EQL":
                pool_resp.liquidity_type = "Sell-Side Liquidity"
            # Session levels don't have liquidity_type (remains None)

            # Zone size
            if pool_resp.zone_low is not None and pool_resp.zone_high is not None:
                pool_resp.zone_size = pool_resp.zone_high - pool_resp.zone_low

            # Calculate modal level for EQH/EQL pools
            if pool_resp.pool_type in ["EQH", "EQL"] and pool_resp.touch_times:
                modal_data = self._calculate_modal_level(
                    symbol=pool_resp.symbol,
                    timeframe=pool_resp.timeframe,
                    pool_type=pool_resp.pool_type,
                    touch_times=pool_resp.touch_times
                )
                pool_resp.modal_level = modal_data["modal_level"]
                pool_resp.modal_touches = modal_data["modal_count"]
                pool_resp.spread = modal_data["spread"]

            # Calculate time freshness and importance score
            if pool_resp.end_time:
                from datetime import datetime, timezone
                time_since_last_touch = (datetime.now(timezone.utc) - pool_resp.end_time).total_seconds() / 3600
                pool_resp.time_freshness = time_since_last_touch

                # Importance score with time decay
                # Recent pools get higher scores via inverse time decay
                time_decay = 1.0 / (1.0 + time_since_last_touch)

                importance_score = (
                    (pool_resp.num_touches * 2.0) +         # Weight touches heavily
                    ((pool_resp.total_volume or 0) / 1000) + # Normalize volume
                    ((pool_resp.spread or 0) * -0.5) +       # Penalize wide spreads
                    (time_decay * 10.0)                      # Reward recent activity (scaled)
                )
                pool_resp.importance_score = importance_score

            # Calculate distance to current price
            if current_price is not None:
                level = pool_resp.modal_level if pool_resp.modal_level is not None else pool_resp.level
                pool_resp.distance_to_current_price = level - current_price

            # Check if pool was swept (FASE 5A: INTACT → SWEPT)
            if pool_resp.pool_type in ["EQH", "EQL"] and pool_resp.modal_level is not None:
                sweep_data = self.check_if_swept(
                    symbol=pool_resp.symbol,
                    timeframe=pool_resp.timeframe,
                    pool_type=pool_resp.pool_type,
                    modal_level=pool_resp.modal_level,
                    formation_time=pool_resp.formation_time,
                    date_val=date_val
                )
                pool_resp.sweep_status = sweep_data["sweep_status"]
                pool_resp.sweep_criteria_met = sweep_data["criteria_met"]

        # Sort pools by importance score (descending)
        pool_responses.sort(key=lambda p: p.importance_score or 0, reverse=True)

        # Generate text report (use response models with calculated fields)
        text_report = self.generate_text_report(pool_responses, params, symbol, date_val)

        return LiquidityPoolGenerationResponse(
            total=len(pools_for_response),
            breakdown=breakdown,
            auto_parameters=params,
            pools=pool_responses,
            text_report=text_report
        )

    def _calculate_modal_level(
        self,
        symbol: str,
        timeframe: str,
        pool_type: str,
        touch_times: List[datetime]
    ) -> dict:
        """
        Calculate modal level by querying highs/lows at touch_times

        Args:
            symbol: Trading symbol
            timeframe: Candle timeframe
            pool_type: EQH or EQL
            touch_times: List of timestamps where pool was touched

        Returns:
            dict with modal_level, modal_count, spread
        """
        if not touch_times:
            return {"modal_level": None, "modal_count": 0, "spread": 0}

        table_name = f"candlestick_{timeframe}"
        price_field = "high" if pool_type == "EQH" else "low"

        # Query to get highs/lows at touch_times
        query = text(f"""
            SELECT {price_field}
            FROM {table_name}
            WHERE symbol = :symbol
              AND time_interval = ANY(:touch_times)
            ORDER BY {price_field} ASC
        """)

        result = self.db.execute(query, {
            "symbol": symbol,
            "touch_times": touch_times
        })

        prices = [row[0] for row in result]

        if not prices:
            return {"modal_level": None, "modal_count": 0, "spread": 0}

        # Use find_modal_level to get modal
        return self.find_modal_level(prices, sub_tolerance=2.0)

    def check_if_swept(
        self,
        symbol: str,
        timeframe: str,
        pool_type: str,
        modal_level: float,
        formation_time: datetime,
        date_val: date
    ) -> dict:
        """
        Check if a liquidity pool was swept using ICT criteria

        A sweep is valid if at least 2 of 3 criteria are met:
        1. Ruptura >1 pt (clean break)
        2. Cierre del lado opuesto (close opposite side)
        3. Vela de intención (body > average)

        Args:
            symbol: Trading symbol
            timeframe: Candle timeframe
            pool_type: EQH or EQL
            modal_level: The modal price level
            formation_time: When pool was formed
            date_val: Date to analyze

        Returns:
            dict with sweep_status (INTACT or SWEPT) and criteria_met count
        """
        table_name = f"candlestick_{timeframe}"

        # Get candles after pool formation (same day only)
        from sqlalchemy import text
        query = text(f"""
            SELECT time_interval, open, high, low, close
            FROM {table_name}
            WHERE symbol = :symbol
              AND DATE(time_interval) = :date_val
              AND time_interval > :formation_time
            ORDER BY time_interval ASC
        """)

        result = self.db.execute(query, {
            "symbol": symbol,
            "date_val": date_val,
            "formation_time": formation_time
        })

        candles = list(result)

        if not candles:
            return {"sweep_status": "INTACT", "criteria_met": 0}

        # Calculate average body size for recent candles (for criterion 3)
        recent_bodies = []
        for row in candles[:20]:  # Use first 20 candles for average
            body = abs(row[4] - row[1])  # close - open
            recent_bodies.append(body)

        avg_body = sum(recent_bodies) / len(recent_bodies) if recent_bodies else 0

        # Check each candle for sweep
        max_criteria_met = 0

        for row in candles:
            time_interval, open_price, high, low, close = row
            criteria_met = 0

            # Criterio 1: Ruptura >1 pt
            if pool_type == "EQH":
                if high > modal_level + 1.0:
                    criteria_met += 1
            else:  # EQL
                if low < modal_level - 1.0:
                    criteria_met += 1

            # Criterio 2: Cierre del lado opuesto
            if pool_type == "EQH":
                # EQH: sweep arriba, cierre abajo
                if high > modal_level and close < modal_level:
                    criteria_met += 1
            else:  # EQL
                # EQL: sweep abajo, cierre arriba
                if low < modal_level and close > modal_level:
                    criteria_met += 1

            # Criterio 3: Vela de intención (cuerpo > promedio)
            candle_body = abs(close - open_price)
            if candle_body > avg_body:
                criteria_met += 1

            # Track maximum criteria met across all candles
            if criteria_met > max_criteria_met:
                max_criteria_met = criteria_met

            # If at least 2 criteria met, it's a sweep
            if criteria_met >= 2:
                return {
                    "sweep_status": "SWEPT",
                    "criteria_met": criteria_met
                }

        # No sweep detected
        return {
            "sweep_status": "INTACT",
            "criteria_met": max_criteria_met
        }

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
        pools: List,  # List of LiquidityPoolResponse models (response models, not DB models)
        params: Dict,
        symbol: str,
        date_val: date
    ) -> str:
        """Generate markdown text report for detected Liquidity Pools (ICT-aligned)"""
        # Separate session levels from EQH/EQL
        session_pools = [p for p in pools if p.pool_type not in ["EQH", "EQL"]]
        eqh_eql_pools = [p for p in pools if p.pool_type in ["EQH", "EQL"]]

        # Sort EQH/EQL by importance_score (should already be sorted, but ensure)
        # Use a temporary score of 0 if importance_score is None
        eqh_eql_pools_sorted = sorted(eqh_eql_pools, key=lambda p: p.importance_score if p.importance_score is not None else 0, reverse=True)

        # Get current price (from first pool's distance calculation)
        current_price = None
        if eqh_eql_pools_sorted:
            first_pool = eqh_eql_pools_sorted[0]
            if first_pool.distance_to_current_price is not None:
                level = first_pool.modal_level if first_pool.modal_level is not None else first_pool.level
                current_price = level - first_pool.distance_to_current_price

        # Format current price
        current_price_str = f"${current_price:.2f}" if current_price is not None else "N/A"

        report = f"""# Liquidity Pool Analysis - {symbol}

## 📊 Detection Summary

**Date**: {date_val}
**Timeframe**: {params['timeframe']}
**Total STRONG Pools**: {len(pools)}
- **EQH/EQL Pools**: {len(eqh_eql_pools)}
- **Session Levels**: {len(session_pools)}

**Current Price** (close): {current_price_str}


### Auto-Calibrated Parameters
- **Clustering Tolerance**: ±{params['tolerance']} pts (intra-cluster)
- **Post-Clustering Distance**: 20 pts (inter-cluster)
- **Min Touches**: {params['min_touches_eqh_eql']} (for STRONG status)

---

"""
        # EQH/EQL Pools (Operational Levels)
        if eqh_eql_pools_sorted:
            report += """## 🎯 EQH/EQL Liquidity Pools (STRONG Only)

*Ordered by Importance Score (touches + volume + freshness - spread)*

"""
            for i, pool in enumerate(eqh_eql_pools_sorted, 1):
                # Calculate derived fields that may not be in DB model
                modal_level = pool.modal_level if pool.modal_level is not None else pool.level
                modal_touches = pool.modal_touches if pool.modal_touches is not None else pool.num_touches
                spread = pool.spread if pool.spread is not None else (pool.zone_high - pool.zone_low if pool.zone_low and pool.zone_high else 0)
                importance = pool.importance_score if pool.importance_score is not None else 0
                distance = pool.distance_to_current_price if hasattr(pool, 'distance_to_current_price') and pool.distance_to_current_price is not None else 0

                # Determine position relative to current price
                position = "ABOVE ⬆️" if distance > 0 else "BELOW ⬇️" if distance < 0 else "AT PRICE"

                # Liquidity type
                liq_type = "Buy-Side Liquidity (BSL)" if pool.pool_type == "EQH" else "Sell-Side Liquidity (SSL)"

                # Time range
                time_range = "N/A"
                if pool.touch_times and len(pool.touch_times) > 0:
                    start_time = self._format_et_time(min(pool.touch_times))
                    end_time = self._format_et_time(max(pool.touch_times))
                    time_range = f"{start_time} → {end_time}"

                # Sweep status with emoji
                sweep_status = pool.sweep_status if hasattr(pool, 'sweep_status') and pool.sweep_status else "INTACT"
                sweep_emoji = "🔴" if sweep_status == "SWEPT" else "🟢"
                criteria_met = pool.sweep_criteria_met if hasattr(pool, 'sweep_criteria_met') and pool.sweep_criteria_met is not None else 0

                # Calculate concentration percentage
                concentration_pct = (modal_touches / pool.num_touches * 100) if pool.num_touches > 0 else 0

                report += f"""### #{i} - {pool.pool_type} at ${modal_level:.2f} ({pool.strength})

**{liq_type}** (Point Level - NOT a zone)

- **Operational Level**: ${modal_level:.2f} (this is the price level to watch)
- **Concentration**: {modal_touches}/{pool.num_touches} touches at modal level ({concentration_pct:.1f}%)
- **Total Touches**: {pool.num_touches} touches distributed across {spread:.2f} pts
- **Importance Score**: {importance:.2f}
- **Distance from Current**: {distance:+.2f} pts ({position})
- **Time Window**: {time_range}
- **Status**: {pool.status}
- **Sweep Status**: {sweep_emoji} **{sweep_status}** ({criteria_met}/3 ICT criteria met)

💡 *Use ${modal_level:.2f} as the precise level. Spread ({spread:.2f} pts) shows cluster dispersion, not an operational zone.*

"""
        else:
            report += """## 🎯 EQH/EQL Liquidity Pools

*No STRONG EQH/EQL pools detected for this date.*

"""

        # Session Levels (if any)
        if session_pools:
            report += """---

## 📍 Session Levels

*Session extremes are tracked separately and not subject to post-clustering.*

"""
            for pool in session_pools:
                report += f"""**{pool.pool_type}: ${pool.level:.2f}** ({pool.strength})
- Touches: {pool.num_touches}
- Status: {pool.status}
- Formation: {self._format_et_time(pool.formation_time) if pool.formation_time else 'N/A'}

"""

        report += """---

## 💡 Trading Implications (ICT Framework)

### Buy-Side Liquidity (EQH)
- **Resting stops** above swing highs
- Prime targets for **liquidity sweeps** before bearish reversals
- Watch for **mitigation** (displacement + FVG formation)

### Sell-Side Liquidity (EQL)
- **Resting stops** below swing lows
- Prime targets for **liquidity sweeps** before bullish reversals
- Watch for **mitigation** (displacement + FVG formation)

### Importance Score Components
- **Touches** (2.0x weight): More touches = stronger pool
- **Volume** (normalized): Institutional participation
- **Spread** (-0.5x penalty): Tighter concentration = higher quality
- **Freshness** (decay factor): Recent activity prioritized

---

*Report Generated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """*
*Source: NQHUB Pattern Detection System*
"""

        return report
