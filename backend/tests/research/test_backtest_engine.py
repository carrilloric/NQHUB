"""
Tests for BacktestEngine - VectorBT Pro wrapper for running backtests.

Tests required per AUT-336:
- test_run_backtest_returns_results — con datos sintéticos NQ
- test_backtest_results_include_apex_compliance — ApexValidator integrado
- test_grid_search_returns_multiple_results — N param combos → N results
- test_walk_forward_splits_correctly — n_splits ventanas correctas
- test_celery_task_saves_to_db — mock DB, verificar escritura
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

# Import the classes we'll be testing (will implement after tests)
from app.research.backtesting.engine import BacktestEngine, ApexValidator
from app.research.backtesting.schemas import BacktestConfig, BacktestResults
from app.research.backtesting.optimizer import BacktestOptimizer
from app.research.backtesting.tasks import run_backtest_task
from app.research.strategies.base import NQHubStrategy


# Helper function to create synthetic NQ candle data
def create_synthetic_nq_candles(
    n_bars: int = 1000,
    timeframe: str = "1min",
    start_price: float = 15000.0
) -> pd.DataFrame:
    """
    Create synthetic NQ futures candle data.
    NQ specs: tick_size=0.25, tick_value=$5, point_value=$20
    """
    dates = pd.date_range(
        start=datetime(2024, 1, 1, 9, 30),
        periods=n_bars,
        freq="1min"
    )

    # Generate realistic price movements
    returns = np.random.normal(0.0001, 0.001, n_bars)
    prices = start_price * (1 + returns).cumprod()

    # Round to NQ tick size (0.25)
    prices = np.round(prices * 4) / 4

    # Create OHLCV data
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.uniform(-0.0001, 0.0001, n_bars)),
        'high': prices * (1 + np.abs(np.random.uniform(0, 0.0002, n_bars))),
        'low': prices * (1 - np.abs(np.random.uniform(0, 0.0002, n_bars))),
        'close': prices,
        'volume': np.random.uniform(100, 1000, n_bars).astype(int)
    })

    # Ensure OHLC relationships are valid
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)

    # Round to tick size
    for col in ['open', 'high', 'low', 'close']:
        df[col] = np.round(df[col] * 4) / 4

    df.set_index('timestamp', inplace=True)
    return df


# Mock strategy for testing
class MockStrategy(NQHubStrategy):
    """Mock strategy for testing backtests."""

    def __init__(self, **params):
        self.params = params or {'sma_period': 20}

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate simple SMA crossover signals."""
        sma = df['close'].rolling(self.params['sma_period']).mean()
        signals = pd.Series(0, index=df.index)
        signals[df['close'] > sma] = 1  # Long signal
        signals[df['close'] < sma] = -1  # Exit signal
        return signals

    def position_size(self, df: pd.DataFrame) -> pd.Series:
        """Return fixed position size of 1 contract."""
        return pd.Series(1, index=df.index)

    @property
    def required_features(self) -> list:
        """Return required features for this strategy."""
        return ['close']  # Only needs close price


class TestBacktestEngine:
    """Test suite for BacktestEngine."""

    @pytest.fixture
    def engine(self):
        """Create a BacktestEngine instance."""
        return BacktestEngine()

    @pytest.fixture
    def candles(self):
        """Create synthetic NQ candle data."""
        return create_synthetic_nq_candles(n_bars=500)

    @pytest.fixture
    def config(self):
        """Create a basic BacktestConfig."""
        return BacktestConfig(
            strategy_id="test_strategy_001",
            timeframe="1min",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),
            commission=0.0002,
            slippage=0.0001,
            initial_capital=25000.0  # Apex $25K account
        )

    @pytest.fixture
    def strategy(self):
        """Create a mock strategy instance."""
        return MockStrategy(sma_period=20)

    def test_run_backtest_returns_results(self, engine, strategy, candles, config):
        """Test that run_backtest returns valid BacktestResults with NQ synthetic data."""
        # Run the backtest
        results = engine.run_backtest(
            strategy=strategy,
            candles=candles,
            config=config
        )

        # Verify results is a BacktestResults instance
        assert isinstance(results, BacktestResults)

        # Verify all required fields are present
        assert results.backtest_id is not None
        assert results.strategy_id == config.strategy_id
        assert isinstance(results.total_return, float)
        assert isinstance(results.sharpe_ratio, float)
        assert isinstance(results.sortino_ratio, float)
        assert isinstance(results.max_drawdown, float)
        assert isinstance(results.win_rate, float)
        assert isinstance(results.profit_factor, float)
        assert isinstance(results.total_trades, int)
        assert results.total_trades >= 0
        assert isinstance(results.apex_compliant, bool)
        assert results.params_hash is not None

        # Verify metrics are within reasonable ranges
        assert -1.0 <= results.total_return <= 10.0  # -100% to 1000% return
        assert -10.0 <= results.sharpe_ratio <= 10.0
        assert 0.0 <= results.max_drawdown <= 1.0  # 0% to 100% drawdown
        assert 0.0 <= results.win_rate <= 1.0  # 0% to 100% win rate

    @patch('app.research.backtesting.engine.ApexValidator')
    def test_backtest_results_include_apex_compliance(
        self, mock_validator_class, engine, strategy, candles, config
    ):
        """Test that BacktestResults includes apex_compliant flag from ApexValidator."""
        # Setup mock ApexValidator
        mock_validator = Mock()
        mock_validator.validate.return_value = {
            'is_compliant': True,
            'violations': []
        }
        mock_validator_class.return_value = mock_validator

        # Run the backtest
        results = engine.run_backtest(
            strategy=strategy,
            candles=candles,
            config=config
        )

        # Verify ApexValidator was called
        mock_validator.validate.assert_called_once()

        # Verify apex_compliant is set correctly
        assert results.apex_compliant is True

    def test_backtest_with_different_timeframes(self, engine, strategy, candles):
        """Test backtest works with different timeframes."""
        timeframes = ["1min", "5min", "15min", "1h"]

        for tf in timeframes:
            config = BacktestConfig(
                strategy_id=f"test_{tf}",
                timeframe=tf,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 2)
            )

            results = engine.run_backtest(
                strategy=strategy,
                candles=candles,
                config=config
            )

            assert results is not None
            assert results.strategy_id == f"test_{tf}"

    def test_backtest_with_custom_commission_and_slippage(self, engine, strategy, candles):
        """Test that custom commission and slippage are applied."""
        config = BacktestConfig(
            strategy_id="test_costs",
            timeframe="1min",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),
            commission=0.001,  # Higher commission
            slippage=0.002,    # Higher slippage
            initial_capital=25000.0
        )

        results = engine.run_backtest(
            strategy=strategy,
            candles=candles,
            config=config
        )

        # With higher costs, returns should generally be lower
        # (we can't assert exact values without knowing the strategy performance)
        assert results is not None
        assert isinstance(results.total_return, float)


class TestBacktestOptimizer:
    """Test suite for BacktestOptimizer (grid search and walk-forward)."""

    @pytest.fixture
    def optimizer(self):
        """Create a BacktestOptimizer instance."""
        return BacktestOptimizer()

    @pytest.fixture
    def candles(self):
        """Create synthetic NQ candle data."""
        return create_synthetic_nq_candles(n_bars=1000)

    def test_grid_search_returns_multiple_results(self, optimizer, candles):
        """Test that grid_search returns N results for N parameter combinations."""
        # Define parameter grid
        param_grid = {
            'sma_period': [10, 20, 50],
            'threshold': [0.01, 0.02]
        }
        # Total combinations = 3 * 2 = 6

        results = optimizer.grid_search(
            strategy_class=MockStrategy,
            param_grid=param_grid,
            candles=candles
        )

        # Verify we get the correct number of results
        assert len(results) == 6

        # Verify each result is a BacktestResults instance
        for result in results:
            assert isinstance(result, BacktestResults)
            assert result.backtest_id is not None
            assert result.params_hash is not None

        # Verify all parameter combinations were tested
        param_hashes = [r.params_hash for r in results]
        assert len(set(param_hashes)) == 6  # All unique

    def test_walk_forward_splits_correctly(self, optimizer, candles):
        """Test that walk-forward validation creates correct n_splits windows."""
        n_splits = 5

        results = optimizer.walk_forward(
            strategy_class=MockStrategy,
            candles=candles,
            n_splits=n_splits
        )

        # Verify we get n_splits results
        assert len(results) == n_splits

        # Verify each result is a BacktestResults instance
        for i, result in enumerate(results):
            assert isinstance(result, BacktestResults)
            assert result.backtest_id is not None
            # Each split should have a unique identifier
            assert f"split_{i}" in result.backtest_id or str(i) in result.backtest_id

    def test_grid_search_with_empty_param_grid(self, optimizer, candles):
        """Test grid_search with empty parameter grid."""
        param_grid = {}

        results = optimizer.grid_search(
            strategy_class=MockStrategy,
            param_grid=param_grid,
            candles=candles
        )

        # Should return single result with default parameters
        assert len(results) == 1
        assert isinstance(results[0], BacktestResults)

    def test_walk_forward_with_insufficient_data(self, optimizer):
        """Test walk-forward with insufficient data for requested splits."""
        # Create very small dataset
        small_candles = create_synthetic_nq_candles(n_bars=10)

        with pytest.raises(ValueError, match="Insufficient data"):
            optimizer.walk_forward(
                strategy_class=MockStrategy,
                candles=small_candles,
                n_splits=10  # More splits than data points
            )


class TestCeleryTasks:
    """Test suite for Celery tasks."""

    @patch('app.research.backtesting.tasks.BacktestEngine')
    @patch('app.research.backtesting.tasks.save_backtest_results')
    @patch('app.research.backtesting.tasks.publish_event')
    def test_celery_task_saves_to_db(
        self, mock_publish, mock_save, mock_engine_class
    ):
        """Test that Celery task saves results to database."""
        # Setup mocks
        mock_engine = Mock()
        mock_results = BacktestResults(
            backtest_id="test_123",
            strategy_id="strategy_001",
            total_return=0.15,
            sharpe_ratio=1.5,
            sortino_ratio=1.8,
            max_drawdown=0.05,
            win_rate=0.6,
            profit_factor=1.8,
            total_trades=42,
            apex_compliant=True,
            params_hash="abc123"
        )
        mock_engine.run_backtest.return_value = mock_results
        mock_engine_class.return_value = mock_engine

        # Create config
        config_dict = {
            "strategy_id": "strategy_001",
            "timeframe": "1min",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-02T00:00:00",
            "commission": 0.0002,
            "slippage": 0.0001,
            "initial_capital": 25000.0
        }

        # Run the task
        result = run_backtest_task(config_dict)

        # Verify engine was called
        mock_engine.run_backtest.assert_called_once()

        # Verify results were saved to DB
        mock_save.assert_called_once_with(mock_results)

        # Verify event was published
        mock_publish.assert_called_once_with(
            "backtest.completed",
            {"backtest_id": "test_123", "strategy_id": "strategy_001"}
        )

        # Verify task returns the results
        assert result == mock_results.dict()

    @patch('app.research.backtesting.tasks.BacktestEngine')
    def test_celery_task_handles_exceptions(self, mock_engine_class):
        """Test that Celery task properly handles exceptions."""
        # Setup mock to raise exception
        mock_engine = Mock()
        mock_engine.run_backtest.side_effect = ValueError("Invalid parameters")
        mock_engine_class.return_value = mock_engine

        config_dict = {
            "strategy_id": "strategy_001",
            "timeframe": "1min",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-02T00:00:00"
        }

        # Task should raise the exception (no retry configured)
        with pytest.raises(ValueError, match="Invalid parameters"):
            run_backtest_task(config_dict)

    @patch('app.research.backtesting.tasks.redis_client')
    def test_celery_task_publishes_progress(self, mock_redis):
        """Test that task publishes progress updates via Redis pub/sub."""
        config_dict = {
            "strategy_id": "strategy_001",
            "timeframe": "1min",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-02T00:00:00"
        }

        # Run task (will fail but we're checking Redis calls)
        try:
            run_backtest_task(config_dict)
        except:
            pass

        # Verify progress was published to Redis
        # At minimum, start and end events
        assert mock_redis.publish.call_count >= 2


# Additional integration tests
class TestBacktestIntegration:
    """Integration tests for the complete backtest flow."""

    @pytest.fixture
    def setup_data(self):
        """Setup test data and dependencies."""
        return {
            'engine': BacktestEngine(),
            'optimizer': BacktestOptimizer(),
            'candles': create_synthetic_nq_candles(n_bars=2000),
            'strategy_class': MockStrategy
        }

    def test_complete_backtest_workflow(self, setup_data):
        """Test complete workflow: single backtest → optimization → selection."""
        engine = setup_data['engine']
        optimizer = setup_data['optimizer']
        candles = setup_data['candles']

        # Step 1: Run single backtest
        config = BacktestConfig(
            strategy_id="initial_test",
            timeframe="5min",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5)
        )

        initial_results = engine.run_backtest(
            strategy=MockStrategy(),
            candles=candles,
            config=config
        )

        assert initial_results is not None

        # Step 2: Run grid search optimization
        param_grid = {
            'sma_period': [10, 20, 30, 50]
        }

        optimization_results = optimizer.grid_search(
            strategy_class=MockStrategy,
            param_grid=param_grid,
            candles=candles
        )

        assert len(optimization_results) == 4

        # Step 3: Select best result (highest Sharpe ratio)
        best_result = max(optimization_results, key=lambda r: r.sharpe_ratio)
        assert best_result.sharpe_ratio >= min(r.sharpe_ratio for r in optimization_results)

    def test_backtest_with_real_world_constraints(self, setup_data):
        """Test backtest with real-world NQ trading constraints."""
        engine = setup_data['engine']
        candles = setup_data['candles']

        # NQ specific configuration
        config = BacktestConfig(
            strategy_id="nq_realistic",
            timeframe="1min",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),
            commission=2.0 / 20.0 / 15000.0,  # $2 RT per contract / point_value / price
            slippage=0.25 / 15000.0,  # 1 tick slippage
            initial_capital=25000.0  # Apex minimum
        )

        strategy = MockStrategy(sma_period=20)
        results = engine.run_backtest(
            strategy=strategy,
            candles=candles,
            config=config
        )

        # Verify NQ-specific validations
        assert results is not None
        # With realistic costs, profit factor should be reasonable
        assert 0.5 <= results.profit_factor <= 3.0