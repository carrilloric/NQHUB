"""
Market State System

Central MarketState object that aggregates all indicators and detected patterns in real-time.
This is the single source of truth that strategies use to make trading decisions.

Persists in:
- Memory (fast access for live trading)
- Redis (O(1) access for current state)
- PostgreSQL market_state_snapshots (historical snapshots for audit)
- FalkorDB (graph relationships between patterns)
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List
import json
import pandas as pd
import pytz
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.research.ict.models import FVG, OrderBlock, Direction
from app.research.ict.fvg_detector import FVGDetector
from app.research.ict.ob_detector import OrderBlockDetector


class Session(str, Enum):
    """Trading session types"""
    NY_AM = "NY_AM"          # New York morning session (9:30 AM - 12:00 PM ET)
    NY_PM = "NY_PM"          # New York afternoon session (12:00 PM - 4:00 PM ET)
    LONDON = "London"        # London session (3:00 AM - 8:00 AM ET)
    ASIA = "Asia"            # Asian session (7:00 PM - 2:00 AM ET)
    AFTER_HOURS = "After_Hours"  # After hours (4:00 PM - 6:00 PM ET)
    UNKNOWN = "unknown"      # Cannot determine session


class Bias(str, Enum):
    """Market bias/sentiment"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class MarketState:
    """
    Market State snapshot at a specific timestamp.

    Aggregates all detected patterns, bias, and key levels across timeframes.
    This is the central object that strategies query to make trading decisions.
    """
    timestamp: datetime
    symbol: str = "NQ"

    # Bias by timeframe: {"1min": "bullish", "5min": "neutral", "15min": "bearish"}
    bias: Dict[str, str] = field(default_factory=dict)

    # Active patterns by timeframe
    active_fvgs: Dict[str, List[FVG]] = field(default_factory=dict)
    active_obs: Dict[str, List[OrderBlock]] = field(default_factory=dict)

    # Key support/resistance levels
    key_levels: List[float] = field(default_factory=list)

    # Current trading session
    session: str = Session.UNKNOWN.value

    def to_dict(self) -> dict:
        """
        Convert MarketState to dictionary for JSON serialization.

        Returns:
            Dictionary with all fields serialized
        """
        # Convert FVGs and OBs to dicts
        active_fvgs_dict = {}
        for tf, fvgs in self.active_fvgs.items():
            active_fvgs_dict[tf] = [self._fvg_to_dict(fvg) for fvg in fvgs]

        active_obs_dict = {}
        for tf, obs in self.active_obs.items():
            active_obs_dict[tf] = [self._ob_to_dict(ob) for ob in obs]

        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "bias": self.bias,
            "active_fvgs": active_fvgs_dict,
            "active_obs": active_obs_dict,
            "key_levels": self.key_levels,
            "session": self.session,
        }

    @staticmethod
    def _fvg_to_dict(fvg: FVG) -> dict:
        """Convert FVG to dict"""
        return {
            "candle_index": fvg.candle_index,
            "direction": fvg.direction.value,
            "top": fvg.top,
            "bottom": fvg.bottom,
            "displacement_score": fvg.displacement_score,
            "status": fvg.status.value,
            "mitigated_at": fvg.mitigated_at,
        }

    @staticmethod
    def _ob_to_dict(ob: OrderBlock) -> dict:
        """Convert OrderBlock to dict"""
        return {
            "candle_index": ob.candle_index,
            "direction": ob.direction.value,
            "top": ob.top,
            "bottom": ob.bottom,
            "quality_score": ob.quality_score,
            "status": ob.status.value,
            "tested_count": ob.tested_count,
            "broken_at": ob.broken_at,
        }

    def get_patterns(self, timeframe: str) -> dict:
        """
        Get all patterns for a specific timeframe.

        Args:
            timeframe: Timeframe string (e.g., "1min", "5min", "15min")

        Returns:
            Dictionary with FVGs and OBs for the timeframe
        """
        return {
            "fvgs": self.active_fvgs.get(timeframe, []),
            "obs": self.active_obs.get(timeframe, []),
        }

    def get_active_fvgs(self, timeframe: str, direction: Optional[str] = None) -> List[FVG]:
        """
        Get active FVGs for a timeframe, optionally filtered by direction.

        Args:
            timeframe: Timeframe string (e.g., "5min")
            direction: Optional direction filter ("bullish" or "bearish")

        Returns:
            List of FVG objects
        """
        fvgs = self.active_fvgs.get(timeframe, [])

        if direction is None:
            return fvgs

        # Filter by direction
        direction_enum = Direction.BULLISH if direction.lower() == "bullish" else Direction.BEARISH
        return [fvg for fvg in fvgs if fvg.direction == direction_enum]

    def get_active_obs(self, timeframe: str, direction: Optional[str] = None) -> List[OrderBlock]:
        """
        Get active Order Blocks for a timeframe, optionally filtered by direction.

        Args:
            timeframe: Timeframe string (e.g., "15min")
            direction: Optional direction filter ("bullish" or "bearish")

        Returns:
            List of OrderBlock objects
        """
        obs = self.active_obs.get(timeframe, [])

        if direction is None:
            return obs

        # Filter by direction
        direction_enum = Direction.BULLISH if direction.lower() == "bullish" else Direction.BEARISH
        return [ob for ob in obs if ob.direction == direction_enum]

    def get_bias(self, timeframe: str) -> str:
        """
        Get bias for a specific timeframe.

        Args:
            timeframe: Timeframe string (e.g., "1min", "5min", "15min")

        Returns:
            Bias string: "bullish", "bearish", or "neutral"
        """
        return self.bias.get(timeframe, Bias.NEUTRAL.value)


class MarketStateManager:
    """
    Manages MarketState lifecycle and persistence.

    Responsibilities:
    1. Update MarketState by running detectors on candle data
    2. Persist state to Redis (fast access), PostgreSQL (historical), FalkorDB (graph)
    3. Provide fast read access from Redis for live trading
    4. Maintain historical snapshots for backtesting and analysis
    """

    def __init__(
        self,
        redis_client: Redis,
        db_session: Optional[AsyncSession] = None,
        falkordb_client: Optional[Redis] = None
    ):
        """
        Initialize MarketStateManager.

        Args:
            redis_client: Redis client for fast state storage
            db_session: Optional async SQLAlchemy session for PostgreSQL
            falkordb_client: Optional FalkorDB client (Redis module)
        """
        self.redis_client = redis_client
        self.db_session = db_session
        self.falkordb_client = falkordb_client

        # Initialize pattern detectors
        self.fvg_detector = FVGDetector(min_gap_atr_ratio=0.5)
        self.ob_detector = OrderBlockDetector(min_move_atr=1.5)

    async def update(self, candles: Dict[str, pd.DataFrame]) -> MarketState:
        """
        Recalculate MarketState from candle data.

        Process:
        1. Run FVGDetector and OBDetector for each timeframe
        2. Update pattern lifecycle (active, mitigated, broken)
        3. Determine bias for each timeframe
        4. Identify key levels
        5. Detect current session
        6. Persist to Redis, PostgreSQL, FalkorDB

        Args:
            candles: Dictionary mapping timeframe to DataFrame
                    Example: {"1min": df_1min, "5min": df_5min, "15min": df_15min}
                    Each DataFrame must have: open, high, low, close, volume

        Returns:
            Updated MarketState object
        """
        # Get timestamp from latest candle (use first available timeframe)
        first_tf = list(candles.keys())[0]
        timestamp = candles[first_tf].index[-1] if hasattr(candles[first_tf].index[-1], 'to_pydatetime') else datetime.now(pytz.UTC)

        # Initialize market state
        market_state = MarketState(timestamp=timestamp)

        # Process each timeframe
        for timeframe, df in candles.items():
            if df.empty:
                continue

            # Detect FVGs
            fvgs = self.fvg_detector.detect(df)
            fvgs = self.fvg_detector.update_lifecycle(fvgs, df)

            # Detect Order Blocks
            obs = self.ob_detector.detect(df)
            obs = self.ob_detector.update_lifecycle(obs, df)

            # Filter only active patterns
            active_fvgs = [fvg for fvg in fvgs if fvg.status.value == "active"]
            active_obs = [ob for ob in obs if ob.status.value == "active"]

            market_state.active_fvgs[timeframe] = active_fvgs
            market_state.active_obs[timeframe] = active_obs

            # Determine bias for this timeframe
            market_state.bias[timeframe] = self._calculate_bias(df, active_fvgs, active_obs)

        # Identify key levels across all timeframes
        market_state.key_levels = self._identify_key_levels(candles)

        # Detect current session
        market_state.session = self._detect_session(timestamp)

        # Persist to Redis
        await self._persist_to_redis(market_state)

        # Persist to PostgreSQL (if session available)
        if self.db_session:
            await self._persist_to_postgres(market_state)

        # Persist to FalkorDB graph (if client available)
        if self.falkordb_client:
            await self._persist_to_falkordb(market_state)

        return market_state

    async def get_current(self) -> Optional[MarketState]:
        """
        Read current MarketState from Redis (O(1) access).

        Returns:
            Current MarketState or None if not found
        """
        # Read from Redis
        state_json = self.redis_client.get("market_state:current")

        if state_json is None:
            return None

        # Deserialize
        return self._deserialize_market_state(json.loads(state_json))

    async def get_snapshot(self, timestamp: datetime) -> Optional[MarketState]:
        """
        Read historical MarketState snapshot from PostgreSQL.

        Args:
            timestamp: Timestamp to retrieve snapshot for

        Returns:
            MarketState snapshot or None if not found
        """
        if self.db_session is None:
            return None

        # Query PostgreSQL for snapshot
        query = text("""
            SELECT snapshot_data
            FROM market_state_snapshots
            WHERE timestamp = :timestamp
            LIMIT 1
        """)

        result = await self.db_session.execute(query, {"timestamp": timestamp})
        row = result.fetchone()

        if row is None:
            return None

        # Deserialize
        return self._deserialize_market_state(row[0])

    def _calculate_bias(
        self,
        df: pd.DataFrame,
        active_fvgs: List[FVG],
        active_obs: List[OrderBlock]
    ) -> str:
        """
        Calculate market bias based on patterns and price action.

        Bias determination logic:
        1. Count bullish vs bearish active patterns
        2. Check recent price trend (last 10 candles)
        3. Combine signals to determine overall bias

        Args:
            df: Candle data
            active_fvgs: Active FVG patterns
            active_obs: Active Order Block patterns

        Returns:
            Bias string: "bullish", "bearish", or "neutral"
        """
        if df.empty:
            return Bias.NEUTRAL.value

        # Count bullish vs bearish patterns
        bullish_fvgs = sum(1 for fvg in active_fvgs if fvg.direction == Direction.BULLISH)
        bearish_fvgs = sum(1 for fvg in active_fvgs if fvg.direction == Direction.BEARISH)

        bullish_obs = sum(1 for ob in active_obs if ob.direction == Direction.BULLISH)
        bearish_obs = sum(1 for ob in active_obs if ob.direction == Direction.BEARISH)

        total_bullish = bullish_fvgs + bullish_obs
        total_bearish = bearish_fvgs + bearish_obs

        # Check recent price trend (last 10 candles)
        recent_candles = df.tail(10)
        if len(recent_candles) >= 2:
            price_change = recent_candles['close'].iloc[-1] - recent_candles['close'].iloc[0]
            trend_bullish = price_change > 0
        else:
            trend_bullish = None

        # Combine signals
        if total_bullish > total_bearish and (trend_bullish or trend_bullish is None):
            return Bias.BULLISH.value
        elif total_bearish > total_bullish and (not trend_bullish or trend_bullish is None):
            return Bias.BEARISH.value
        else:
            return Bias.NEUTRAL.value

    def _identify_key_levels(self, candles: Dict[str, pd.DataFrame]) -> List[float]:
        """
        Identify key support/resistance levels across all timeframes.

        Logic:
        1. Find swing highs/lows in each timeframe
        2. Cluster levels that appear across multiple timeframes
        3. Return sorted list of key levels

        Args:
            candles: Dictionary of timeframe to DataFrame

        Returns:
            List of key price levels
        """
        all_levels = []

        for timeframe, df in candles.items():
            if df.empty or len(df) < 20:
                continue

            # Find swing highs (local maxima)
            for i in range(10, len(df) - 10):
                window = df['high'].iloc[i-10:i+11]
                if df['high'].iloc[i] == window.max():
                    all_levels.append(df['high'].iloc[i])

            # Find swing lows (local minima)
            for i in range(10, len(df) - 10):
                window = df['low'].iloc[i-10:i+11]
                if df['low'].iloc[i] == window.min():
                    all_levels.append(df['low'].iloc[i])

        if not all_levels:
            return []

        # Cluster nearby levels (within 10 points)
        all_levels.sort()
        key_levels = []
        current_cluster = [all_levels[0]]

        for level in all_levels[1:]:
            if level - current_cluster[-1] <= 10:
                current_cluster.append(level)
            else:
                # Take median of cluster
                key_levels.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [level]

        # Add last cluster
        if current_cluster:
            key_levels.append(sum(current_cluster) / len(current_cluster))

        return sorted(key_levels)

    def _detect_session(self, timestamp: datetime) -> str:
        """
        Detect trading session based on timestamp (Eastern Time).

        Sessions (all times in ET):
        - NY_AM: 9:30 AM - 12:00 PM
        - NY_PM: 12:00 PM - 4:00 PM
        - AFTER_HOURS: 4:00 PM - 6:00 PM
        - ASIA: 7:00 PM - 2:00 AM
        - LONDON: 3:00 AM - 8:00 AM
        - UNKNOWN: Other times

        Args:
            timestamp: Current timestamp (UTC or timezone-aware)

        Returns:
            Session string
        """
        # Convert to Eastern Time
        eastern = pytz.timezone('America/New_York')

        if timestamp.tzinfo is None:
            # Assume UTC if naive
            timestamp = pytz.UTC.localize(timestamp)

        et_time = timestamp.astimezone(eastern)
        hour = et_time.hour
        minute = et_time.minute

        # Determine session
        if (hour == 9 and minute >= 30) or (10 <= hour < 12):
            return Session.NY_AM.value
        elif 12 <= hour < 16:
            return Session.NY_PM.value
        elif 16 <= hour < 18:
            return Session.AFTER_HOURS.value
        elif 19 <= hour or hour < 2:
            return Session.ASIA.value
        elif 3 <= hour < 8:
            return Session.LONDON.value
        else:
            return Session.UNKNOWN.value

    async def _persist_to_redis(self, market_state: MarketState):
        """
        Persist MarketState to Redis for fast access.

        Redis keys:
        - market_state:current → JSON of full state
        - market_state:session → current session
        - market_state:bias:{timeframe} → bias value
        """
        # Serialize state
        state_json = json.dumps(market_state.to_dict())

        # Store in Redis
        self.redis_client.set("market_state:current", state_json)
        self.redis_client.set("market_state:session", market_state.session)

        # Store bias by timeframe
        for timeframe, bias in market_state.bias.items():
            self.redis_client.set(f"market_state:bias:{timeframe}", bias)

    async def _persist_to_postgres(self, market_state: MarketState):
        """
        Persist MarketState snapshot to PostgreSQL for historical analysis.

        Table: market_state_snapshots
        Columns: id, timestamp, symbol, snapshot_data (JSONB)
        """
        if self.db_session is None:
            return

        # Insert snapshot
        query = text("""
            INSERT INTO market_state_snapshots (timestamp, symbol, snapshot_data)
            VALUES (:timestamp, :symbol, :snapshot_data::jsonb)
            ON CONFLICT (timestamp, symbol) DO UPDATE
            SET snapshot_data = EXCLUDED.snapshot_data
        """)

        await self.db_session.execute(query, {
            "timestamp": market_state.timestamp,
            "symbol": market_state.symbol,
            "snapshot_data": json.dumps(market_state.to_dict()),
        })
        await self.db_session.commit()

    async def _persist_to_falkordb(self, market_state: MarketState):
        """
        Persist MarketState to FalkorDB graph for pattern relationship queries.

        Creates nodes and relationships:
        - (:MarketState {timestamp, session, bias_*})
        - (:FVG {id, timeframe, direction, top, bottom, ...})
        - (:OrderBlock {id, timeframe, direction, top, bottom, ...})
        - (ms)-[:HAS_FVG]->(fvg)
        - (ms)-[:HAS_OB]->(ob)
        - (fvg)-[:NEAR_OB {distance_ticks}]->(ob)
        """
        if self.falkordb_client is None:
            return

        # FalkorDB commands using Redis Graph module
        # Note: In production, use FalkorDB Python client
        # For now, this is a placeholder that shows the structure

        graph_name = "market_state_graph"

        # Create MarketState node
        ms_node_id = f"ms_{market_state.timestamp.isoformat()}"

        # Build bias properties
        bias_props = ", ".join([f"bias_{tf}: '{bias}'" for tf, bias in market_state.bias.items()])

        # Cypher query to create MarketState node
        cypher_ms = f"""
        CREATE (ms:MarketState {{
            id: '{ms_node_id}',
            timestamp: '{market_state.timestamp.isoformat()}',
            session: '{market_state.session}',
            {bias_props}
        }})
        """

        # In production, execute: self.falkordb_client.execute_command("GRAPH.QUERY", graph_name, cypher_ms)

        # Create FVG nodes and relationships
        for timeframe, fvgs in market_state.active_fvgs.items():
            for i, fvg in enumerate(fvgs):
                fvg_node_id = f"fvg_{timeframe}_{fvg.candle_index}"
                cypher_fvg = f"""
                MATCH (ms:MarketState {{id: '{ms_node_id}'}})
                CREATE (fvg:FVG {{
                    id: '{fvg_node_id}',
                    timeframe: '{timeframe}',
                    direction: '{fvg.direction.value}',
                    top: {fvg.top},
                    bottom: {fvg.bottom},
                    displacement_score: {fvg.displacement_score},
                    status: '{fvg.status.value}'
                }})
                CREATE (ms)-[:HAS_FVG]->(fvg)
                """
                # Execute in production

        # Create OB nodes and relationships
        for timeframe, obs in market_state.active_obs.items():
            for ob in obs:
                ob_node_id = f"ob_{timeframe}_{ob.candle_index}"
                cypher_ob = f"""
                MATCH (ms:MarketState {{id: '{ms_node_id}'}})
                CREATE (ob:OrderBlock {{
                    id: '{ob_node_id}',
                    timeframe: '{timeframe}',
                    direction: '{ob.direction.value}',
                    top: {ob.top},
                    bottom: {ob.bottom},
                    quality_score: {ob.quality_score},
                    status: '{ob.status.value}'
                }})
                CREATE (ms)-[:HAS_OB]->(ob)
                """
                # Execute in production

        # Create NEAR_OB relationships between FVGs and OBs
        # (Find patterns that are close to each other across timeframes)
        for fvg_tf, fvgs in market_state.active_fvgs.items():
            for ob_tf, obs in market_state.active_obs.items():
                for fvg in fvgs:
                    for ob in obs:
                        # Check if FVG and OB are near each other (within 50 ticks)
                        fvg_mid = (fvg.top + fvg.bottom) / 2
                        ob_mid = (ob.top + ob.bottom) / 2
                        distance = abs(fvg_mid - ob_mid)

                        if distance <= 50:
                            cypher_rel = f"""
                            MATCH (fvg:FVG {{id: 'fvg_{fvg_tf}_{fvg.candle_index}'}}),
                                  (ob:OrderBlock {{id: 'ob_{ob_tf}_{ob.candle_index}'}})
                            CREATE (fvg)-[:NEAR_OB {{distance_ticks: {distance:.2f}}}]->(ob)
                            """
                            # Execute in production

    def _deserialize_market_state(self, data: dict) -> MarketState:
        """
        Deserialize MarketState from dictionary.

        Args:
            data: Dictionary with MarketState data

        Returns:
            MarketState object
        """
        from app.research.ict.models import PatternStatus

        # Parse timestamp
        timestamp = datetime.fromisoformat(data["timestamp"])

        # Parse FVGs
        active_fvgs = {}
        for tf, fvg_list in data.get("active_fvgs", {}).items():
            fvgs = []
            for fvg_dict in fvg_list:
                fvg = FVG(
                    candle_index=fvg_dict["candle_index"],
                    direction=Direction(fvg_dict["direction"]),
                    top=fvg_dict["top"],
                    bottom=fvg_dict["bottom"],
                    displacement_score=fvg_dict["displacement_score"],
                    status=PatternStatus(fvg_dict["status"]),
                    mitigated_at=fvg_dict.get("mitigated_at"),
                )
                fvgs.append(fvg)
            active_fvgs[tf] = fvgs

        # Parse OBs
        active_obs = {}
        for tf, ob_list in data.get("active_obs", {}).items():
            obs = []
            for ob_dict in ob_list:
                ob = OrderBlock(
                    candle_index=ob_dict["candle_index"],
                    direction=Direction(ob_dict["direction"]),
                    top=ob_dict["top"],
                    bottom=ob_dict["bottom"],
                    quality_score=ob_dict["quality_score"],
                    status=PatternStatus(ob_dict["status"]),
                    tested_count=ob_dict.get("tested_count", 0),
                    broken_at=ob_dict.get("broken_at"),
                )
                obs.append(ob)
            active_obs[tf] = obs

        return MarketState(
            timestamp=timestamp,
            symbol=data.get("symbol", "NQ"),
            bias=data.get("bias", {}),
            active_fvgs=active_fvgs,
            active_obs=active_obs,
            key_levels=data.get("key_levels", []),
            session=data.get("session", Session.UNKNOWN.value),
        )
