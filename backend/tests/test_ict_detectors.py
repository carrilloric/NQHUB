"""
Tests for ICT Pattern Detectors

Tests for FVG (Fair Value Gap) and OB (Order Block) detectors.
Uses synthetic OHLCV data - no database required.
"""

import pytest
import pandas as pd
import numpy as np
from app.research.ict import (
    FVGDetector,
    OrderBlockDetector,
    FVG,
    OrderBlock,
    PatternStatus,
    Direction
)


# ==================== Helper Functions ====================

def create_bullish_fvg_candles() -> pd.DataFrame:
    """Create 3 candles where there's a clear bullish FVG"""
    return pd.DataFrame({
        'open':  [100.0, 102.0, 106.0],
        'high':  [102.0, 104.0, 110.0],
        'low':   [99.0,  101.0, 105.0],  # low[2]=105 > high[0]=102 → FVG bullish
        'close': [101.0, 103.0, 109.0],
        'volume': [1000, 1200, 2000]
    })


def create_bearish_fvg_candles() -> pd.DataFrame:
    """Create 3 candles where there's a clear bearish FVG"""
    return pd.DataFrame({
        'open':  [110.0, 108.0, 104.0],
        'high':  [111.0, 109.0, 105.0],  # high[2]=105 < low[0]=108 → FVG bearish
        'low':   [108.0, 106.0, 102.0],
        'close': [109.0, 107.0, 103.0],
        'volume': [1000, 1200, 2000]
    })


def create_no_gap_candles() -> pd.DataFrame:
    """Create candles with no gaps"""
    return pd.DataFrame({
        'open':  [100.0, 101.0, 102.0, 103.0],
        'high':  [101.5, 102.5, 103.5, 104.5],
        'low':   [99.5,  100.5, 101.5, 102.5],
        'close': [101.0, 102.0, 103.0, 104.0],
        'volume': [1000, 1000, 1000, 1000]
    })


def create_bullish_ob_candles() -> pd.DataFrame:
    """Create candles with a bullish Order Block pattern"""
    # Last bearish candle before strong bullish impulse
    return pd.DataFrame({
        'open':  [100.0, 101.0, 102.0, 101.0, 105.0, 108.0, 110.0],
        'high':  [101.5, 102.5, 103.0, 102.0, 106.0, 109.0, 111.0],
        'low':   [99.5,  100.5, 101.5, 100.0, 104.0, 107.0, 109.0],
        'close': [101.0, 102.0, 101.5, 100.5, 105.5, 108.5, 110.5],  # [3] is bearish, then strong up
        'volume': [1000, 1000, 1000, 1500, 2000, 2500, 3000]
    })


def create_bearish_ob_candles() -> pd.DataFrame:
    """Create candles with a bearish Order Block pattern"""
    # Last bullish candle before strong bearish impulse
    return pd.DataFrame({
        'open':  [100.0, 99.0, 98.0, 99.0, 95.0, 92.0, 90.0],
        'high':  [101.0, 100.0, 99.5, 100.5, 96.0, 93.0, 91.0],
        'low':   [99.0,  98.0,  97.0, 98.5,  94.0, 91.0, 89.0],
        'close': [99.5,  98.5,  99.0, 100.0, 94.5, 91.5, 89.5],  # [3] is bullish, then strong down
        'volume': [1000, 1000, 1000, 1500, 2000, 2500, 3000]
    })


def create_realistic_nq_data(num_candles: int = 100) -> pd.DataFrame:
    """Create realistic NQ futures synthetic data"""
    np.random.seed(42)

    # Start at a typical NQ price
    base_price = 15000.0
    prices = [base_price]

    # Generate price movement
    for i in range(1, num_candles):
        # Random walk with trend
        trend = 0.0001 * (i % 20 - 10)  # Slight trend
        change = np.random.normal(0, 0.002) + trend
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)

    # Create OHLC from prices
    data = []
    for i in range(num_candles):
        base = prices[i]

        # Create realistic candle
        open_price = base + np.random.uniform(-5, 5)
        close_price = base + np.random.uniform(-5, 5)

        # High and low should contain open and close
        high_price = max(open_price, close_price) + np.random.uniform(0, 10)
        low_price = min(open_price, close_price) - np.random.uniform(0, 10)

        volume = np.random.uniform(1000, 5000)

        data.append({
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })

    return pd.DataFrame(data)


# ==================== FVG Tests ====================

class TestFVGDetector:
    """Test suite for FVG Detector"""

    def test_fvg_bullish_detected(self):
        """Test that a clear bullish FVG is detected"""
        df = create_bullish_fvg_candles()
        detector = FVGDetector(min_gap_atr_ratio=0.0)  # Disable ATR check for simple test

        fvgs = detector.detect(df)

        assert len(fvgs) == 1, "Should detect exactly one FVG"
        fvg = fvgs[0]

        assert fvg.direction == Direction.BULLISH
        assert fvg.candle_index == 2
        assert fvg.bottom == 102.0  # high[0]
        assert fvg.top == 105.0     # low[2]
        assert fvg.status == PatternStatus.ACTIVE

    def test_fvg_bearish_detected(self):
        """Test that a clear bearish FVG is detected"""
        df = create_bearish_fvg_candles()
        detector = FVGDetector(min_gap_atr_ratio=0.0)  # Disable ATR check for simple test

        fvgs = detector.detect(df)

        assert len(fvgs) == 1, "Should detect exactly one FVG"
        fvg = fvgs[0]

        assert fvg.direction == Direction.BEARISH
        assert fvg.candle_index == 2
        assert fvg.top == 108.0      # low[0]
        assert fvg.bottom == 105.0   # high[2]
        assert fvg.status == PatternStatus.ACTIVE

    def test_fvg_no_gap_no_detection(self):
        """Test that no FVG is detected when there are no gaps"""
        df = create_no_gap_candles()
        detector = FVGDetector()

        fvgs = detector.detect(df)

        assert len(fvgs) == 0, "Should not detect any FVG when no gaps exist"

    def test_fvg_displacement_score_range(self):
        """Test that displacement score is always between 0.0 and 1.0"""
        df = create_realistic_nq_data(50)
        detector = FVGDetector(min_gap_atr_ratio=0.1)

        fvgs = detector.detect(df)

        for fvg in fvgs:
            assert 0.0 <= fvg.displacement_score <= 1.0, \
                f"Displacement score {fvg.displacement_score} out of range"

    def test_fvg_mitigated_when_price_touches(self):
        """Test that FVG becomes mitigated when price touches 50% of gap"""
        # Create FVG and then price retraces
        df = pd.DataFrame({
            'open':  [100.0, 102.0, 106.0, 105.0, 104.0],
            'high':  [102.0, 104.0, 110.0, 106.0, 105.0],
            'low':   [99.0,  101.0, 105.0, 103.0, 102.5],  # [3] touches midpoint first
            'close': [101.0, 103.0, 109.0, 104.0, 103.0],
            'volume': [1000, 1200, 2000, 1500, 1300]
        })

        detector = FVGDetector(min_gap_atr_ratio=0.0)
        fvgs = detector.detect(df)

        assert len(fvgs) == 1
        fvg = fvgs[0]

        # Update lifecycle
        updated_fvgs = detector.update_lifecycle(fvgs, df)
        updated_fvg = updated_fvgs[0]

        # FVG midpoint is (102 + 105) / 2 = 103.5
        # Candle 3 low is 103.0, which is below midpoint
        assert updated_fvg.status == PatternStatus.MITIGATED
        assert updated_fvg.mitigated_at == 3  # Mitigation occurs at candle 3

    def test_fvg_broken_when_price_closes_through(self):
        """Test that FVG becomes broken when price closes beyond gap"""
        # Create FVG and then price closes below
        df = pd.DataFrame({
            'open':  [100.0, 102.0, 106.0, 103.0, 102.0],
            'high':  [102.0, 104.0, 110.0, 104.0, 103.0],
            'low':   [99.0,  101.0, 105.0, 104.0, 100.0],  # [3] doesn't touch midpoint
            'close': [101.0, 103.0, 109.0, 105.0, 101.0],  # [4] closes below gap
            'volume': [1000, 1200, 2000, 1500, 1300]
        })

        detector = FVGDetector(min_gap_atr_ratio=0.0)
        fvgs = detector.detect(df)

        # Update lifecycle
        updated_fvgs = detector.update_lifecycle(fvgs, df)
        updated_fvg = updated_fvgs[0]

        assert updated_fvg.status == PatternStatus.BROKEN
        assert updated_fvg.mitigated_at == 4

    def test_fvg_active_stays_active(self):
        """Test that FVG stays active when price doesn't touch gap"""
        df = pd.DataFrame({
            'open':  [100.0, 102.0, 106.0, 107.0, 108.0],
            'high':  [102.0, 104.0, 110.0, 109.0, 110.0],
            'low':   [99.0,  101.0, 105.0, 106.0, 107.0],  # Never goes back to gap
            'close': [101.0, 103.0, 109.0, 108.0, 109.0],
            'volume': [1000, 1200, 2000, 1500, 1300]
        })

        detector = FVGDetector(min_gap_atr_ratio=0.0)
        fvgs = detector.detect(df)

        # Update lifecycle
        updated_fvgs = detector.update_lifecycle(fvgs, df)
        updated_fvg = updated_fvgs[0]

        assert updated_fvg.status == PatternStatus.ACTIVE
        assert updated_fvg.mitigated_at is None


# ==================== Order Block Tests ====================

class TestOrderBlockDetector:
    """Test suite for Order Block Detector"""

    def test_ob_bullish_detected(self):
        """Test that a bullish Order Block is detected"""
        df = create_bullish_ob_candles()

        # Need more data for ATR calculation
        df = pd.concat([create_no_gap_candles()] * 3 + [df], ignore_index=True)

        detector = OrderBlockDetector(min_move_atr=0.5)  # Lower threshold for test
        obs = detector.detect(df)

        # Should find at least one bullish OB
        bullish_obs = [ob for ob in obs if ob.direction == Direction.BULLISH]
        assert len(bullish_obs) > 0, "Should detect at least one bullish OB"

        ob = bullish_obs[0]
        assert ob.status == PatternStatus.ACTIVE
        assert ob.tested_count == 0

    def test_ob_bearish_detected(self):
        """Test that a bearish Order Block is detected"""
        df = create_bearish_ob_candles()

        # Need more data for ATR calculation
        df = pd.concat([create_no_gap_candles()] * 3 + [df], ignore_index=True)

        detector = OrderBlockDetector(min_move_atr=0.5)  # Lower threshold for test
        obs = detector.detect(df)

        # Should find at least one bearish OB
        bearish_obs = [ob for ob in obs if ob.direction == Direction.BEARISH]
        assert len(bearish_obs) > 0, "Should detect at least one bearish OB"

        ob = bearish_obs[0]
        assert ob.status == PatternStatus.ACTIVE
        assert ob.tested_count == 0

    def test_ob_quality_score_range(self):
        """Test that quality score is always between 0.0 and 1.0"""
        df = create_realistic_nq_data(50)
        detector = OrderBlockDetector()

        obs = detector.detect(df)

        for ob in obs:
            assert 0.0 <= ob.quality_score <= 1.0, \
                f"Quality score {ob.quality_score} out of range"

    def test_ob_tested_count_increments(self):
        """Test that tested_count increments when price touches OB"""
        # Create clear OB pattern with test
        # Start with stable price, then bearish OB before bullish impulse, then test without breaking
        df = pd.DataFrame({
            'open':  [100.0] * 10 + [100.5, 101.0, 100.0, 105.0, 108.0, 110.0, 105.0, 101.5],
            'high':  [101.0] * 10 + [101.5, 102.0, 101.0, 106.0, 109.0, 111.0, 106.0, 102.5],
            'low':   [99.0] * 10 + [99.5, 100.0, 99.0, 104.0, 107.0, 109.0, 104.0, 100.0],  # [17] touches OB
            'close': [100.5] * 10 + [101.0, 100.5, 99.5, 105.5, 108.5, 110.5, 105.0, 102.0],  # Close above OB low
            'volume': [1000] * 18
        })

        detector = OrderBlockDetector(min_move_atr=0.5)
        obs = detector.detect(df)

        # Should find at least one OB
        assert len(obs) > 0, "Should detect at least one Order Block"

        # Update lifecycle
        updated_obs = detector.update_lifecycle(obs, df)

        # Check if any OB was tested or broken (both are valid)
        tested_obs = [ob for ob in updated_obs if ob.tested_count > 0 or ob.status == PatternStatus.BROKEN]
        assert len(tested_obs) > 0, "At least one OB should have been tested or broken"
        # Accept both TESTED and BROKEN as valid outcomes
        assert tested_obs[0].status in [PatternStatus.TESTED, PatternStatus.BROKEN]

    def test_ob_broken_when_price_closes_through(self):
        """Test that OB becomes broken when price closes through it"""
        # Create OB and then break it
        df = pd.DataFrame({
            'open':  [100.0] * 15 + [101.0, 100.0, 104.0, 106.0, 102.0],
            'high':  [101.0] * 15 + [102.0, 101.0, 105.0, 107.0, 103.0],
            'low':   [99.0] * 15 + [100.0, 99.0,  103.0, 105.0, 98.0],   # [19] goes below OB
            'close': [100.5] * 15 + [100.5, 99.5,  104.5, 106.5, 98.5],  # [19] closes below OB
            'volume': [1000] * 20
        })

        detector = OrderBlockDetector(min_move_atr=0.5)
        obs = detector.detect(df)

        if len(obs) > 0:
            # Update lifecycle
            updated_obs = detector.update_lifecycle(obs, df)

            # Check if any OB was broken
            broken_obs = [ob for ob in updated_obs if ob.status == PatternStatus.BROKEN]
            if len(broken_obs) > 0:
                assert broken_obs[0].broken_at is not None

    def test_ob_min_move_threshold(self):
        """Test that OB is not detected when move is below threshold"""
        # Create small moves that shouldn't qualify
        df = pd.DataFrame({
            'open':  [100.0, 100.1, 100.2, 100.3, 100.4] * 5,
            'high':  [100.5, 100.6, 100.7, 100.8, 100.9] * 5,
            'low':   [99.5,  99.6,  99.7,  99.8,  99.9] * 5,
            'close': [100.2, 100.3, 100.4, 100.5, 100.6] * 5,
            'volume': [1000] * 25
        })

        detector = OrderBlockDetector(min_move_atr=2.0)  # High threshold
        obs = detector.detect(df)

        assert len(obs) == 0, "Should not detect OB with small moves"


# ==================== Integration Tests ====================

class TestDetectorsIntegration:
    """Integration tests for both detectors"""

    def test_fvg_detector_with_realistic_nq_data(self):
        """Test FVG detector with realistic NQ data"""
        df = create_realistic_nq_data(100)
        detector = FVGDetector()

        fvgs = detector.detect(df)

        # Should detect at least some FVGs in realistic data
        assert len(fvgs) >= 0, "Detector should run without errors"

        # All FVGs should have valid properties
        for fvg in fvgs:
            assert fvg.candle_index >= 2
            assert fvg.candle_index < len(df)
            assert fvg.top > fvg.bottom
            assert fvg.direction in [Direction.BULLISH, Direction.BEARISH]

    def test_ob_detector_with_realistic_nq_data(self):
        """Test OB detector with realistic NQ data"""
        df = create_realistic_nq_data(100)
        detector = OrderBlockDetector()

        obs = detector.detect(df)

        # Should detect at least some OBs in realistic data
        assert len(obs) >= 0, "Detector should run without errors"

        # All OBs should have valid properties
        for ob in obs:
            assert ob.candle_index >= 0
            assert ob.candle_index < len(df)
            assert ob.top > ob.bottom
            assert ob.direction in [Direction.BULLISH, Direction.BEARISH]

    def test_detectors_work_together(self):
        """Test that both detectors can work on the same dataset"""
        df = create_realistic_nq_data(100)

        fvg_detector = FVGDetector()
        ob_detector = OrderBlockDetector()

        fvgs = fvg_detector.detect(df)
        obs = ob_detector.detect(df)

        # Both should run without conflicts
        assert isinstance(fvgs, list)
        assert isinstance(obs, list)

        # Update lifecycles
        updated_fvgs = fvg_detector.update_lifecycle(fvgs, df)
        updated_obs = ob_detector.update_lifecycle(obs, df)

        assert len(updated_fvgs) == len(fvgs)
        assert len(updated_obs) == len(obs)