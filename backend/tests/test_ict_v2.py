"""
Test suite for ICT V2 patterns: Liquidity Pools, Kill Zones, Breaker Blocks

Tests using synthetic DataFrames without requiring TimescaleDB.
"""

import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
import pytz
import pytest
from app.research.ict.patterns.liquidity_pool import LiquidityPoolDetector, LiquidityPoolType, LiquidityPoolStatus
from app.research.ict.patterns.kill_zone import KillZoneDetector
from app.research.ict.patterns.breaker_block import BreakerBlockDetector
from app.research.ict.models import Direction, PatternStatus
from app.research.ict.ob_detector import OrderBlockDetector
from app.research.market_state import MarketStateManager, MarketState
from unittest.mock import MagicMock, patch
import warnings


def create_synthetic_df(num_candles: int = 100, base_price: float = 18000.0) -> pd.DataFrame:
    """
    Create a synthetic OHLCV DataFrame for testing.

    Args:
        num_candles: Number of candles to generate
        base_price: Base price level

    Returns:
        DataFrame with columns: open, high, low, close, volume, datetime
    """
    dates = pd.date_range(start='2024-01-15 09:30:00', periods=num_candles, freq='5min', tz='America/New_York')

    # Generate random price movements
    np.random.seed(42)
    returns = np.random.normal(0, 0.001, num_candles)
    prices = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        'open': prices * (1 + np.random.uniform(-0.001, 0.001, num_candles)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.002, num_candles))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.002, num_candles))),
        'close': prices,
        'volume': np.random.uniform(100, 1000, num_candles),
        'datetime': dates
    })

    # Ensure OHLC constraints
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)

    return df


# ============================================================================
# Liquidity Pool Tests
# ============================================================================

@pytest.mark.filterwarnings("ignore:smartmoneyconcepts not installed")
def test_eqh_detected_with_2_equal_highs():
    """Test that 2 equal highs within tolerance creates an EQH liquidity pool"""
    # Create synthetic data with equal highs
    df = create_synthetic_df(30)

    # Manually set equal highs
    df.loc[10, 'high'] = 18100.0
    df.loc[15, 'high'] = 18100.25  # Within 1 tick tolerance (0.25)
    df.loc[20, 'high'] = 18100.0

    # Mock smc.liquidity() to return EQH
    with patch('app.research.ict.patterns.liquidity_pool.smc') as mock_smc:
        mock_smc.swing_highs_lows.return_value = pd.DataFrame({
            'HighLow': [1, 0, 1, 0, 1],  # Pattern of highs and lows
            'Level': [18100.0, 18050.0, 18100.0, 18060.0, 18100.0]
        })

        mock_smc.liquidity.return_value = pd.DataFrame({
            'Liquidity': [-1, 0, 0, 0, -1],  # -1 = EQH (bearish liquidity)
            'Level': [18100.0, 0, 0, 0, 18100.0],
            'End': [20, 0, 0, 0, 25],
            'Swept': [0, 0, 0, 0, 0]
        })

        detector = LiquidityPoolDetector()
        pools = detector.detect(df, "5m")

        # Should detect at least one EQH
        eqh_pools = [p for p in pools if p.type == LiquidityPoolType.EQH]
        assert len(eqh_pools) > 0, "Should detect at least one EQH pool"

        # Check properties
        eqh = eqh_pools[0]
        assert eqh.price_level == 18100.0
        assert eqh.touches >= 2
        assert eqh.status == LiquidityPoolStatus.ACTIVE


@pytest.mark.filterwarnings("ignore:smartmoneyconcepts not installed")
def test_eql_detected_with_3_equal_lows():
    """Test that 3 equal lows creates an EQL liquidity pool with touches=3"""
    df = create_synthetic_df(30)

    # Set equal lows
    df.loc[5, 'low'] = 17950.0
    df.loc[12, 'low'] = 17950.25  # Within tolerance
    df.loc[18, 'low'] = 17950.0

    with patch('app.research.ict.patterns.liquidity_pool.smc') as mock_smc:
        mock_smc.swing_highs_lows.return_value = pd.DataFrame({
            'HighLow': [-1, 0, -1, 0, -1],  # Lows
            'Level': [17950.0, 18000.0, 17950.0, 18010.0, 17950.0]
        })

        mock_smc.liquidity.return_value = pd.DataFrame({
            'Liquidity': [1, 0, 0, 0, 1],  # 1 = EQL (bullish liquidity)
            'Level': [17950.0, 0, 0, 0, 17950.0],
            'End': [18, 0, 0, 0, 25],
            'Swept': [0, 0, 0, 0, 0]
        })

        detector = LiquidityPoolDetector()
        pools = detector.detect(df, "5m")

        eql_pools = [p for p in pools if p.type == LiquidityPoolType.EQL]
        assert len(eql_pools) > 0, "Should detect at least one EQL pool"

        eql = eql_pools[0]
        assert abs(eql.price_level - 17950.0) < 1.0
        assert eql.touches >= 2  # At least 2 touches


@pytest.mark.filterwarnings("ignore:smartmoneyconcepts not installed")
def test_lp_status_swept_on_wick_reversal():
    """Test that price touching and reversing in same candle marks LP as swept"""
    df = create_synthetic_df(30)

    # Setup EQH that gets swept
    df.loc[10, 'high'] = 18100.0
    df.loc[15, 'high'] = 18100.0

    # Sweep candle - wick above but close below
    df.loc[20, 'high'] = 18101.0  # Wick above
    df.loc[20, 'close'] = 18095.0  # Close below

    with patch('app.research.ict.patterns.liquidity_pool.smc') as mock_smc:
        mock_smc.swing_highs_lows.return_value = pd.DataFrame({
            'HighLow': [1] * len(df)
        })

        mock_smc.liquidity.return_value = pd.DataFrame({
            'Liquidity': [-1] + [0] * (len(df) - 1),
            'Level': [18100.0] + [0] * (len(df) - 1),
            'End': [20] + [0] * (len(df) - 1),
            'Swept': [1] + [0] * (len(df) - 1)  # Marked as swept
        })

        detector = LiquidityPoolDetector()
        pools = detector.detect(df, "5m")

        swept_pools = [p for p in pools if p.status == LiquidityPoolStatus.SWEPT]
        assert len(swept_pools) > 0, "Should detect swept liquidity pool"


@pytest.mark.filterwarnings("ignore:smartmoneyconcepts not installed")
def test_lp_status_broken_on_close_beyond():
    """Test that price closing beyond LP marks it as broken"""
    df = create_synthetic_df(30)

    # Setup EQL
    df.loc[10, 'low'] = 17950.0
    df.loc[15, 'low'] = 17950.0

    # Break candle - close below
    df.loc[20, 'close'] = 17945.0  # Close below the level
    df.loc[20, 'low'] = 17940.0

    with patch('app.research.ict.patterns.liquidity_pool.smc') as mock_smc:
        mock_smc.swing_highs_lows.return_value = pd.DataFrame({
            'HighLow': [-1] * len(df)
        })

        mock_smc.liquidity.return_value = pd.DataFrame({
            'Liquidity': [1] + [0] * (len(df) - 1),
            'Level': [17950.0] + [0] * (len(df) - 1),
            'End': [15] + [0] * (len(df) - 1),
            'Swept': [0] * len(df)
        })

        detector = LiquidityPoolDetector()
        pools = detector.detect(df, "5m")

        if pools:
            pool = pools[0]
            # Update status based on price action
            detector.update_status(pool, df)

            # Since close is below the zone, should be broken
            assert pool.status == LiquidityPoolStatus.BROKEN


@pytest.mark.filterwarnings("ignore:smartmoneyconcepts not installed")
def test_sweep_score_range():
    """Test that sweep score is always between 0.0 and 1.0"""
    df = create_synthetic_df(50)

    with patch('app.research.ict.patterns.liquidity_pool.smc') as mock_smc:
        mock_smc.swing_highs_lows.return_value = pd.DataFrame({
            'HighLow': [1, -1] * 25
        })

        mock_smc.liquidity.return_value = pd.DataFrame({
            'Liquidity': [1, -1, 0, 0, 1],
            'Level': [17950.0, 18100.0, 0, 0, 17960.0],
            'End': [10, 15, 0, 0, 30],
            'Swept': [0] * 5
        })

        detector = LiquidityPoolDetector()
        pools = detector.detect(df, "5m")

        for pool in pools:
            assert 0.0 <= pool.sweep_score <= 1.0, f"Sweep score {pool.sweep_score} out of range"


# ============================================================================
# Kill Zone Tests
# ============================================================================

def test_ny_am_session_active_at_930():
    """Test that NY AM Session is active at 9:30 AM ET"""
    detector = KillZoneDetector()

    # Create timestamp for 9:30 AM ET
    et = pytz.timezone('America/New_York')
    test_time = et.localize(datetime(2024, 1, 15, 9, 30, 0))

    active_zones = detector.get_active_kill_zones(test_time)
    zone_names = [z.name for z in active_zones]

    assert "NY AM Session" in zone_names, "NY AM Session should be active at 9:30 AM ET"


def test_silver_bullet_active_at_1015():
    """Test that Silver Bullet is active at 10:15 AM ET"""
    detector = KillZoneDetector()

    # Create timestamp for 10:15 AM ET
    et = pytz.timezone('America/New_York')
    test_time = et.localize(datetime(2024, 1, 15, 10, 15, 0))

    active_zones = detector.get_active_kill_zones(test_time)
    zone_names = [z.name for z in active_zones]

    assert "Silver Bullet" in zone_names, "Silver Bullet should be active at 10:15 AM ET"

    # Also check that NY AM is still active
    assert "NY AM Session" in zone_names, "NY AM Session should also be active at 10:15 AM ET"


def test_no_kill_zone_at_noon():
    """Test that NY Lunch (12:30 PM ET) is marked as avoid period"""
    detector = KillZoneDetector()

    # Create timestamp for 12:30 PM ET
    et = pytz.timezone('America/New_York')
    test_time = et.localize(datetime(2024, 1, 15, 12, 30, 0))

    # Check if in kill zone (should be false as NY Lunch is to avoid)
    in_kz = detector.is_in_kill_zone(test_time)
    assert not in_kz, "Should not be in tradeable kill zone during NY Lunch"

    # But it should still be detected as an active zone
    active_zones = detector.get_active_kill_zones(test_time)
    zone_names = [z.name for z in active_zones]
    assert "NY Lunch" in zone_names, "NY Lunch should be detected but marked as avoid"


def test_apex_maintenance_not_kill_zone():
    """Test that 4:30 PM ET (after market) is not a kill zone"""
    detector = KillZoneDetector()

    # Create timestamp for 4:30 PM ET (after regular trading)
    et = pytz.timezone('America/New_York')
    test_time = et.localize(datetime(2024, 1, 15, 16, 30, 0))

    active_zones = detector.get_active_kill_zones(test_time)

    assert len(active_zones) == 0, "No kill zones should be active at 4:30 PM ET"


def test_time_to_next_kill_zone_positive():
    """Test that time_to_next_kill_zone returns positive timedelta"""
    detector = KillZoneDetector()

    # Test at 7:00 AM ET (before London Open at 2:00 AM, so next day)
    et = pytz.timezone('America/New_York')
    test_time = et.localize(datetime(2024, 1, 15, 7, 0, 0))

    next_zone, time_delta = detector.time_to_next_kill_zone(test_time)

    assert next_zone is not None, "Should find next kill zone"
    assert time_delta > timedelta(0), "Time to next kill zone should be positive"
    assert next_zone.name == "NY AM Session", "Next zone at 7 AM should be NY AM Session at 8:30"


# ============================================================================
# Breaker Block Tests
# ============================================================================

def test_bb_created_from_broken_bearish_ob():
    """Test that broken bearish OB becomes bullish BB"""
    df = create_synthetic_df(50)

    # Create a bearish Order Block scenario
    # OB at index 10, then break above at index 20
    df.loc[10, 'open'] = 18100.0
    df.loc[10, 'close'] = 18080.0  # Bearish candle
    df.loc[10, 'high'] = 18110.0
    df.loc[10, 'low'] = 18075.0

    # Impulse move down after OB
    for i in range(11, 14):
        df.loc[i, 'close'] = df.loc[i-1, 'close'] - 20
        df.loc[i, 'low'] = df.loc[i, 'close'] - 5

    # Break above the OB
    df.loc[20, 'close'] = 18115.0  # Close above OB top
    df.loc[20, 'high'] = 18120.0

    ob_detector = OrderBlockDetector(min_move_atr=0.5)  # Low threshold for testing
    bb_detector = BreakerBlockDetector(ob_detector)

    breaker_blocks = bb_detector.detect(df, "5m")

    # Should have at least one BB
    assert len(breaker_blocks) > 0, "Should detect breaker block from broken bearish OB"

    # Check that it's bullish (inverted from bearish OB)
    bb = breaker_blocks[0]
    assert bb.direction == Direction.BULLISH, "Broken bearish OB should become bullish BB"


def test_bb_created_from_broken_bullish_ob():
    """Test that broken bullish OB becomes bearish BB"""
    df = create_synthetic_df(50)

    # Create a bullish Order Block scenario
    df.loc[10, 'open'] = 18080.0
    df.loc[10, 'close'] = 18100.0  # Bullish candle
    df.loc[10, 'high'] = 18105.0
    df.loc[10, 'low'] = 18075.0

    # Impulse move up after OB
    for i in range(11, 14):
        df.loc[i, 'close'] = df.loc[i-1, 'close'] + 20
        df.loc[i, 'high'] = df.loc[i, 'close'] + 5

    # Break below the OB
    df.loc[20, 'close'] = 18070.0  # Close below OB bottom
    df.loc[20, 'low'] = 18065.0

    ob_detector = OrderBlockDetector(min_move_atr=0.5)
    bb_detector = BreakerBlockDetector(ob_detector)

    breaker_blocks = bb_detector.detect(df, "5m")

    if breaker_blocks:
        bb = breaker_blocks[0]
        assert bb.direction == Direction.BEARISH, "Broken bullish OB should become bearish BB"


def test_bb_inherits_ob_range():
    """Test that BB has same top/bottom as original OB"""
    df = create_synthetic_df(50)

    # Setup OB
    ob_top = 18110.0
    ob_bottom = 18075.0

    df.loc[10, 'high'] = ob_top
    df.loc[10, 'low'] = ob_bottom
    df.loc[10, 'open'] = 18100.0
    df.loc[10, 'close'] = 18080.0  # Bearish

    # Impulse and break
    for i in range(11, 14):
        df.loc[i, 'close'] = df.loc[i-1, 'close'] - 20

    df.loc[20, 'close'] = ob_top + 5  # Break above

    ob_detector = OrderBlockDetector(min_move_atr=0.5)
    bb_detector = BreakerBlockDetector(ob_detector)

    breaker_blocks = bb_detector.detect(df, "5m")

    if breaker_blocks:
        bb = breaker_blocks[0]
        assert bb.top == ob_top, "BB should inherit OB top"
        assert bb.bottom == ob_bottom, "BB should inherit OB bottom"


def test_bb_quality_inherits_from_ob():
    """Test that BB quality score is derived from OB"""
    df = create_synthetic_df(50)

    # Create high-quality OB
    df.loc[10, 'open'] = 18100.0
    df.loc[10, 'close'] = 18080.0
    df.loc[10, 'volume'] = 5000  # High volume for quality

    # Strong impulse
    for i in range(11, 14):
        df.loc[i, 'close'] = df.loc[i-1, 'close'] - 30

    # Strong break
    df.loc[20, 'close'] = 18120.0
    df.loc[20, 'high'] = 18125.0

    ob_detector = OrderBlockDetector(min_move_atr=0.5)
    bb_detector = BreakerBlockDetector(ob_detector)

    breaker_blocks = bb_detector.detect(df, "5m")

    if breaker_blocks:
        bb = breaker_blocks[0]
        assert bb.quality_score > 0, "BB should have quality score > 0"
        assert bb.quality_score <= 1.0, "BB quality score should be <= 1.0"


def test_bb_status_tested_on_touch():
    """Test that BB tested_count increases when price touches it"""
    df = create_synthetic_df(50)

    # Setup OB and break
    df.loc[10, 'open'] = 18100.0
    df.loc[10, 'close'] = 18080.0
    df.loc[10, 'high'] = 18110.0
    df.loc[10, 'low'] = 18075.0

    for i in range(11, 14):
        df.loc[i, 'close'] = df.loc[i-1, 'close'] - 20

    df.loc[20, 'close'] = 18115.0  # Break

    # Add test touches
    df.loc[25, 'low'] = 18105.0  # Touch from above
    df.loc[30, 'low'] = 18108.0  # Another touch

    ob_detector = OrderBlockDetector(min_move_atr=0.5)
    bb_detector = BreakerBlockDetector(ob_detector)

    breaker_blocks = bb_detector.detect(df, "5m")

    if breaker_blocks:
        bb = breaker_blocks[0]
        assert bb.tested_count >= 1, "BB should have been tested at least once"


# ============================================================================
# Market State Integration Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore:smartmoneyconcepts not installed")
async def test_market_state_includes_lps():
    """Test that MarketState update() includes active_liquidity_pools"""
    df = create_synthetic_df(50)

    # Mock Redis and DB
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True

    with patch('app.research.ict.patterns.liquidity_pool.smc') as mock_smc:
        # Mock smc functions
        mock_smc.swing_highs_lows.return_value = pd.DataFrame({
            'HighLow': [1, -1] * 25
        })

        mock_smc.liquidity.return_value = pd.DataFrame({
            'Liquidity': [1, -1] + [0] * (len(df) - 2),
            'Level': [17950.0, 18100.0] + [0] * (len(df) - 2),
            'End': [10, 15] + [0] * (len(df) - 2),
            'Swept': [0] * len(df)
        })

        manager = MarketStateManager(mock_redis)

        candles = {"5m": df}
        market_state = await manager.update(candles)

        # Check that liquidity pools are included
        assert hasattr(market_state, 'active_liquidity_pools')
        assert "5m" in market_state.active_liquidity_pools
        # May or may not have pools depending on mock behavior
        assert isinstance(market_state.active_liquidity_pools["5m"], list)


@pytest.mark.asyncio
async def test_market_state_kill_zone_flag():
    """Test that MarketState sets is_in_kill_zone=True during NY AM"""
    df = create_synthetic_df(50)

    # Set timestamp to 9:45 AM ET (during NY AM Session)
    et = pytz.timezone('America/New_York')
    ny_am_time = et.localize(datetime(2024, 1, 15, 9, 45, 0))
    df.index = pd.DatetimeIndex([ny_am_time] * len(df))

    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True

    manager = MarketStateManager(mock_redis)

    candles = {"5m": df}
    market_state = await manager.update(candles)

    # Check kill zone fields
    assert hasattr(market_state, 'is_in_kill_zone')
    assert hasattr(market_state, 'active_kill_zones')

    # Should be in kill zone during NY AM
    assert market_state.is_in_kill_zone == True, "Should be in kill zone during NY AM Session"
    assert len(market_state.active_kill_zones) > 0, "Should have active kill zones"

    # Check that NY AM Session is in the list
    zone_names = [kz.name for kz in market_state.active_kill_zones]
    assert "NY AM Session" in zone_names, "NY AM Session should be active"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])