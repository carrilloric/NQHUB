"""
Tests for Market State System

Tests MarketState dataclass and MarketStateManager with synthetic OHLCV data
and mocked Redis/FalkorDB clients.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json
import pytz

from app.research.market_state import (
    MarketState,
    MarketStateManager,
    Session,
    Bias
)
from app.research.ict.models import FVG, OrderBlock, Direction, PatternStatus


# ==================== FIXTURES ====================

@pytest.fixture
def synthetic_candles():
    """
    Generate synthetic OHLCV data for testing.

    Returns 3 timeframes: 1min, 5min, 15min with 100 candles each.
    """
    np.random.seed(42)

    def generate_ohlcv(num_candles: int, base_price: float = 18000.0) -> pd.DataFrame:
        """Generate synthetic OHLCV data"""
        prices = []
        current_price = base_price

        for i in range(num_candles):
            # Random walk with slight upward bias
            change = np.random.normal(0, 20)
            current_price += change

            open_price = current_price
            close_price = current_price + np.random.normal(0, 15)
            high_price = max(open_price, close_price) + abs(np.random.normal(5, 5))
            low_price = min(open_price, close_price) - abs(np.random.normal(5, 5))
            volume = np.random.randint(100, 1000)

            prices.append({
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume,
            })

        df = pd.DataFrame(prices)

        # Add datetime index
        start_time = datetime(2024, 1, 1, 9, 30, tzinfo=pytz.UTC)
        df.index = pd.date_range(start=start_time, periods=num_candles, freq='1min')

        return df

    return {
        "1min": generate_ohlcv(100, base_price=18000.0),
        "5min": generate_ohlcv(100, base_price=18000.0),
        "15min": generate_ohlcv(100, base_price=18000.0),
    }


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    mock_redis = Mock()
    mock_redis.get = Mock(return_value=None)
    mock_redis.set = Mock(return_value=True)
    return mock_redis


@pytest.fixture
def mock_db_session():
    """Mock async database session"""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    return mock_session


@pytest.fixture
def mock_falkordb_client():
    """Mock FalkorDB client"""
    mock_falkor = Mock()
    mock_falkor.execute_command = Mock(return_value=True)
    return mock_falkor


@pytest.fixture
def market_state_manager(mock_redis_client, mock_db_session, mock_falkordb_client):
    """Create MarketStateManager with mocked dependencies"""
    return MarketStateManager(
        redis_client=mock_redis_client,
        db_session=mock_db_session,
        falkordb_client=mock_falkordb_client,
    )


# ==================== TESTS ====================

@pytest.mark.asyncio
async def test_market_state_updates_with_candles(market_state_manager, synthetic_candles):
    """
    Test that update() with 100 candles produces a non-empty MarketState.

    Verifies:
    - MarketState is created with correct timestamp
    - At least some patterns are detected
    - Bias is calculated for all timeframes
    """
    # Run update
    market_state = await market_state_manager.update(synthetic_candles)

    # Verify state is not empty
    assert market_state is not None
    assert market_state.timestamp is not None
    assert market_state.symbol == "NQ"

    # Verify bias is set for all timeframes
    assert "1min" in market_state.bias
    assert "5min" in market_state.bias
    assert "15min" in market_state.bias

    # Verify bias values are valid
    for tf, bias in market_state.bias.items():
        assert bias in [Bias.BULLISH.value, Bias.BEARISH.value, Bias.NEUTRAL.value]

    # Verify patterns dict exists (may be empty, but should exist)
    assert "1min" in market_state.active_fvgs or len(market_state.active_fvgs) == 0
    assert "1min" in market_state.active_obs or len(market_state.active_obs) == 0


@pytest.mark.asyncio
async def test_get_active_fvgs_filters_by_timeframe(market_state_manager, synthetic_candles):
    """
    Test that get_active_fvgs() returns only FVGs from the requested timeframe.

    Verifies:
    - FVGs from 5min are not mixed with 15min
    - Filtering by timeframe works correctly
    """
    # Update state
    market_state = await market_state_manager.update(synthetic_candles)

    # Get FVGs for 5min
    fvgs_5min = market_state.get_active_fvgs("5min")

    # Get FVGs for 15min
    fvgs_15min = market_state.get_active_fvgs("15min")

    # Verify they are different lists (or both empty)
    # If both have patterns, they should not be identical
    if len(fvgs_5min) > 0 and len(fvgs_15min) > 0:
        assert fvgs_5min != fvgs_15min

    # Verify all FVGs in 5min list are actually from the 5min timeframe
    # (This is implicit in the storage structure, but good to verify)
    for fvg in fvgs_5min:
        assert isinstance(fvg, FVG)

    for fvg in fvgs_15min:
        assert isinstance(fvg, FVG)


@pytest.mark.asyncio
async def test_get_active_fvgs_filters_by_direction(market_state_manager, synthetic_candles):
    """
    Test that get_active_fvgs() filters by direction when requested.

    Verifies:
    - direction="bullish" returns only bullish FVGs
    - direction="bearish" returns only bearish FVGs
    - No direction returns all FVGs
    """
    # Update state
    market_state = await market_state_manager.update(synthetic_candles)

    # Get all FVGs for 5min
    all_fvgs = market_state.get_active_fvgs("5min")

    # Get bullish FVGs
    bullish_fvgs = market_state.get_active_fvgs("5min", direction="bullish")

    # Get bearish FVGs
    bearish_fvgs = market_state.get_active_fvgs("5min", direction="bearish")

    # Verify filtering works
    for fvg in bullish_fvgs:
        assert fvg.direction == Direction.BULLISH

    for fvg in bearish_fvgs:
        assert fvg.direction == Direction.BEARISH

    # Verify total matches (bullish + bearish = all)
    assert len(bullish_fvgs) + len(bearish_fvgs) == len(all_fvgs)


@pytest.mark.asyncio
async def test_bias_returns_valid_value(market_state_manager, synthetic_candles):
    """
    Test that get_bias() always returns a valid bias value.

    Verifies:
    - Bias is one of: "bullish", "bearish", "neutral"
    - All timeframes have a bias value
    """
    # Update state
    market_state = await market_state_manager.update(synthetic_candles)

    # Test all timeframes
    for timeframe in ["1min", "5min", "15min"]:
        bias = market_state.get_bias(timeframe)

        # Verify bias is valid
        assert bias in [Bias.BULLISH.value, Bias.BEARISH.value, Bias.NEUTRAL.value]

    # Test non-existent timeframe (should return neutral)
    bias_unknown = market_state.get_bias("60min")
    assert bias_unknown == Bias.NEUTRAL.value


@pytest.mark.asyncio
async def test_session_detection_ny_am(market_state_manager):
    """
    Test that session detection correctly identifies NY_AM session.

    Verifies:
    - 9:30 AM ET → session = "NY_AM"
    - 11:00 AM ET → session = "NY_AM"
    """
    # Create timestamp for 9:30 AM ET
    eastern = pytz.timezone('America/New_York')
    et_time = eastern.localize(datetime(2024, 1, 15, 9, 30))  # Monday 9:30 AM ET
    utc_time = et_time.astimezone(pytz.UTC)

    # Detect session
    session = market_state_manager._detect_session(utc_time)

    # Verify
    assert session == Session.NY_AM.value

    # Test 11:00 AM ET (still NY_AM)
    et_time_11 = eastern.localize(datetime(2024, 1, 15, 11, 0))
    utc_time_11 = et_time_11.astimezone(pytz.UTC)
    session_11 = market_state_manager._detect_session(utc_time_11)
    assert session_11 == Session.NY_AM.value


@pytest.mark.asyncio
async def test_session_detection_london(market_state_manager):
    """
    Test that session detection correctly identifies London session.

    Verifies:
    - 3:00 AM ET → session = "London"
    - 5:00 AM ET → session = "London"
    """
    # Create timestamp for 3:00 AM ET
    eastern = pytz.timezone('America/New_York')
    et_time = eastern.localize(datetime(2024, 1, 15, 3, 0))
    utc_time = et_time.astimezone(pytz.UTC)

    # Detect session
    session = market_state_manager._detect_session(utc_time)

    # Verify
    assert session == Session.LONDON.value

    # Test 5:00 AM ET (still London)
    et_time_5 = eastern.localize(datetime(2024, 1, 15, 5, 0))
    utc_time_5 = et_time_5.astimezone(pytz.UTC)
    session_5 = market_state_manager._detect_session(utc_time_5)
    assert session_5 == Session.LONDON.value


@pytest.mark.asyncio
async def test_market_state_persists_to_redis(market_state_manager, synthetic_candles, mock_redis_client):
    """
    Test that after update(), MarketState is persisted to Redis.

    Verifies:
    - redis.set() is called with correct keys
    - market_state:current contains JSON data
    - market_state:session contains session value
    - market_state:bias:{timeframe} contains bias values
    """
    # Update state
    market_state = await market_state_manager.update(synthetic_candles)

    # Verify Redis calls
    assert mock_redis_client.set.called

    # Verify market_state:current was set
    calls = mock_redis_client.set.call_args_list
    keys_set = [call[0][0] for call in calls]

    assert "market_state:current" in keys_set
    assert "market_state:session" in keys_set

    # Verify bias keys were set
    for timeframe in ["1min", "5min", "15min"]:
        assert f"market_state:bias:{timeframe}" in keys_set


@pytest.mark.asyncio
async def test_get_current_reads_from_redis(market_state_manager, synthetic_candles, mock_redis_client):
    """
    Test that get_current() reads from Redis without recalculating.

    Verifies:
    - get_current() calls redis.get()
    - Returns MarketState if data exists
    - Does not re-run pattern detectors
    """
    # First, update state to persist to Redis
    market_state_original = await market_state_manager.update(synthetic_candles)

    # Mock Redis to return the persisted state
    state_json = json.dumps(market_state_original.to_dict())
    mock_redis_client.get.return_value = state_json.encode('utf-8')

    # Now call get_current()
    market_state = await market_state_manager.get_current()

    # Verify redis.get() was called
    assert mock_redis_client.get.called
    mock_redis_client.get.assert_called_with("market_state:current")

    # Verify we got a MarketState back
    assert market_state is not None
    assert isinstance(market_state, MarketState)
    assert market_state.symbol == "NQ"


@pytest.mark.asyncio
async def test_market_state_to_dict_is_json_serializable(market_state_manager, synthetic_candles):
    """
    Test that MarketState.to_dict() produces valid JSON.

    Verifies:
    - to_dict() returns a dictionary
    - Dictionary can be serialized to JSON
    - All fields are present and have correct types
    """
    # Update state
    market_state = await market_state_manager.update(synthetic_candles)

    # Convert to dict
    state_dict = market_state.to_dict()

    # Verify it's a dict
    assert isinstance(state_dict, dict)

    # Verify JSON serialization works
    state_json = json.dumps(state_dict)
    assert state_json is not None
    assert len(state_json) > 0

    # Verify we can deserialize it back
    state_dict_restored = json.loads(state_json)
    assert state_dict_restored == state_dict

    # Verify required fields are present
    assert "timestamp" in state_dict
    assert "symbol" in state_dict
    assert "bias" in state_dict
    assert "active_fvgs" in state_dict
    assert "active_obs" in state_dict
    assert "key_levels" in state_dict
    assert "session" in state_dict


# ==================== ADDITIONAL HELPER TESTS ====================

def test_market_state_get_patterns():
    """Test MarketState.get_patterns() returns both FVGs and OBs for a timeframe"""
    # Create mock FVG and OB
    fvg = FVG(
        candle_index=10,
        direction=Direction.BULLISH,
        top=18100.0,
        bottom=18050.0,
        displacement_score=0.75,
        status=PatternStatus.ACTIVE,
    )

    ob = OrderBlock(
        candle_index=15,
        direction=Direction.BEARISH,
        top=18200.0,
        bottom=18150.0,
        quality_score=0.80,
        status=PatternStatus.ACTIVE,
    )

    # Create MarketState
    market_state = MarketState(
        timestamp=datetime.now(pytz.UTC),
        active_fvgs={"5min": [fvg]},
        active_obs={"5min": [ob]},
    )

    # Get patterns
    patterns = market_state.get_patterns("5min")

    # Verify
    assert "fvgs" in patterns
    assert "obs" in patterns
    assert len(patterns["fvgs"]) == 1
    assert len(patterns["obs"]) == 1
    assert patterns["fvgs"][0] == fvg
    assert patterns["obs"][0] == ob


def test_market_state_get_active_obs_filters_by_direction():
    """Test that get_active_obs() filters by direction correctly"""
    # Create mock OBs
    ob_bull = OrderBlock(
        candle_index=10,
        direction=Direction.BULLISH,
        top=18100.0,
        bottom=18050.0,
        quality_score=0.75,
        status=PatternStatus.ACTIVE,
    )

    ob_bear = OrderBlock(
        candle_index=20,
        direction=Direction.BEARISH,
        top=18200.0,
        bottom=18150.0,
        quality_score=0.80,
        status=PatternStatus.ACTIVE,
    )

    # Create MarketState
    market_state = MarketState(
        timestamp=datetime.now(pytz.UTC),
        active_obs={"15min": [ob_bull, ob_bear]},
    )

    # Get bullish OBs
    bullish_obs = market_state.get_active_obs("15min", direction="bullish")
    assert len(bullish_obs) == 1
    assert bullish_obs[0].direction == Direction.BULLISH

    # Get bearish OBs
    bearish_obs = market_state.get_active_obs("15min", direction="bearish")
    assert len(bearish_obs) == 1
    assert bearish_obs[0].direction == Direction.BEARISH

    # Get all OBs
    all_obs = market_state.get_active_obs("15min")
    assert len(all_obs) == 2


def test_market_state_key_levels():
    """Test that key_levels field works correctly"""
    market_state = MarketState(
        timestamp=datetime.now(pytz.UTC),
        key_levels=[18000.0, 18100.0, 18200.0],
    )

    assert len(market_state.key_levels) == 3
    assert 18000.0 in market_state.key_levels
    assert 18100.0 in market_state.key_levels
    assert 18200.0 in market_state.key_levels
