"""
Tests for NQHubStrategy abstract base class
"""
import pytest
import sys
from pathlib import Path
from typing import List
import pandas as pd

# Add nqhub-research to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "nqhub-research"))

from nqhub.strategies.base import NQHubStrategy
from nqhub import TICK_SIZE, TICK_VALUE, POINT_VALUE


class TestNQHubStrategy:
    """Test NQHubStrategy abstract base class."""

    def test_nqhub_strategy_abstract(self):
        """Test that NQHubStrategy cannot be instantiated directly."""
        with pytest.raises(TypeError) as excinfo:
            strategy = NQHubStrategy()

        # Check that the error message indicates it's an abstract class
        assert "Can't instantiate abstract class" in str(excinfo.value)

    def test_nq_constants_hardcoded(self):
        """Test that NQ constants are correctly hardcoded."""
        # Test module-level constants
        assert TICK_SIZE == 0.25, f"TICK_SIZE should be 0.25, got {TICK_SIZE}"
        assert TICK_VALUE == 5.0, f"TICK_VALUE should be 5.0, got {TICK_VALUE}"
        assert POINT_VALUE == 20.0, f"POINT_VALUE should be 20.0, got {POINT_VALUE}"

        # Test class-level constants
        assert NQHubStrategy.TICK_SIZE == 0.25
        assert NQHubStrategy.TICK_VALUE == 5.0
        assert NQHubStrategy.POINT_VALUE == 20.0

    def test_concrete_strategy_implementation(self):
        """Test that a concrete implementation of NQHubStrategy works."""

        class TestStrategy(NQHubStrategy):
            def required_features(self) -> List[str]:
                return ["rsi", "volume"]

            def generate_signals(self, data: pd.DataFrame) -> pd.Series:
                return pd.Series([1, 0, -1], index=data.index[:3])

            def position_size(self, equity: float, risk_pct: float) -> int:
                return 1

        # Should be able to instantiate concrete class
        strategy = TestStrategy(name="TestStrategy")
        assert strategy.name == "TestStrategy"
        assert strategy.TICK_SIZE == 0.25
        assert strategy.TICK_VALUE == 5.0
        assert strategy.POINT_VALUE == 20.0

    def test_constants_cannot_be_modified(self):
        """Test that attempting to modify constants raises an error."""

        class BadStrategy(NQHubStrategy):
            TICK_SIZE = 0.50  # Trying to override constant

            def required_features(self) -> List[str]:
                return []

            def generate_signals(self, data: pd.DataFrame) -> pd.Series:
                return pd.Series()

            def position_size(self, equity: float, risk_pct: float) -> int:
                return 1

        # Should raise RuntimeError when trying to instantiate
        with pytest.raises(RuntimeError) as excinfo:
            strategy = BadStrategy()

        assert "TICK_SIZE must be 0.25" in str(excinfo.value)

    def test_pnl_calculation_methods(self):
        """Test P&L calculation helper methods."""

        class TestStrategy(NQHubStrategy):
            def required_features(self) -> List[str]:
                return []

            def generate_signals(self, data: pd.DataFrame) -> pd.Series:
                return pd.Series()

            def position_size(self, equity: float, risk_pct: float) -> int:
                return 1

        strategy = TestStrategy()

        # Test long trade P&L
        entry = 16800.00
        exit = 16805.00

        # Points calculation
        pnl_points = strategy.calculate_pnl_points(entry, exit, side=1)
        assert pnl_points == 5.0

        # Ticks calculation
        pnl_ticks = strategy.calculate_pnl_ticks(entry, exit, side=1)
        assert pnl_ticks == 20  # 5 points / 0.25 tick_size

        # Dollar calculation
        pnl_dollars = strategy.calculate_pnl_dollars(entry, exit, side=1, contracts=2)
        assert pnl_dollars == 200.0  # 20 ticks * $5 * 2 contracts

        # Test short trade P&L
        pnl_points_short = strategy.calculate_pnl_points(entry, exit, side=-1)
        assert pnl_points_short == -5.0