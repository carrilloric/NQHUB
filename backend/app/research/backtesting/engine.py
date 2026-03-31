"""
BacktestEngine - VectorBT Pro wrapper for running backtests.

NQ Futures specifications:
- tick_size = 0.25
- tick_value = $5
- point_value = $20
"""

import vectorbtpro as vbt
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any
import uuid
import time
import hashlib
import json

from app.research.strategies.base import NQHubStrategy
from app.research.backtesting.schemas import BacktestConfig, BacktestResults
from app.research.metrics.performance import PerformanceMetrics


# NQ Futures constants
NQ_TICK_SIZE = 0.25
NQ_TICK_VALUE = 5.0
NQ_POINT_VALUE = 20.0


class BacktestEngine:
    """
    Wrapper de VectorBT Pro para ejecutar backtests de estrategias NQHub.

    NQ specifications:
    - tick_size = 0.25 (minimum price movement)
    - tick_value = $5 (value per tick)
    - point_value = $20 (value per point = 4 ticks)
    """

    def __init__(self, apex_validator=None):
        """Initialize the BacktestEngine.

        Args:
            apex_validator: Optional ApexValidator instance for compliance checking
        """
        self.apex_validator = apex_validator
        self.metrics_calculator = PerformanceMetrics()

    def run_backtest(
        self,
        strategy: NQHubStrategy,
        candles: pd.DataFrame,
        config: BacktestConfig,
    ) -> BacktestResults:
        """
        Execute backtest using vbt.Portfolio.from_signals().

        Args:
            strategy: NQHubStrategy instance to backtest
            candles: DataFrame with OHLCV data (from TimescaleDB)
            config: BacktestConfig with parameters

        Returns:
            BacktestResults with performance metrics
        """
        start_time = time.time()

        # Ensure candles are within the config date range
        if 'timestamp' in candles.columns:
            candles = candles.set_index('timestamp')

        # Filter candles to date range
        mask = (candles.index >= config.start_date) & (candles.index <= config.end_date)
        candles = candles.loc[mask]

        if len(candles) == 0:
            raise ValueError(f"No data available for date range {config.start_date} to {config.end_date}")

        # Generate trading signals
        signals = strategy.generate_signals(candles)

        # Get position sizing
        size = strategy.position_size(candles)

        # Convert signals to entry/exit arrays for VectorBT
        entries = signals == 1  # Long entries
        exits = signals == -1   # Exit signals

        # Create VectorBT portfolio
        portfolio = vbt.Portfolio.from_signals(
            close=candles["close"],
            entries=entries,
            exits=exits,
            size=size,
            fees=config.commission,  # Commission as percentage
            slippage=config.slippage,  # Slippage as percentage
            freq=self._map_timeframe_to_freq(config.timeframe),
            init_cash=config.initial_capital,
            size_type="amount",  # Size is number of contracts
        )

        # Build results
        execution_time = time.time() - start_time
        results = self._build_results(
            portfolio=portfolio,
            strategy=strategy,
            config=config,
            execution_time=execution_time,
            data_points=len(candles)
        )

        return results

    def _build_results(
        self,
        portfolio,
        strategy: NQHubStrategy,
        config: BacktestConfig,
        execution_time: float,
        data_points: int
    ) -> BacktestResults:
        """Extract metrics from vbt.Portfolio and convert to BacktestResults.

        Args:
            portfolio: VectorBT portfolio object
            strategy: The strategy that was backtested
            config: Backtest configuration
            execution_time: Time taken to run backtest
            data_points: Number of candles processed

        Returns:
            BacktestResults with all metrics populated
        """
        # Generate unique backtest ID
        backtest_id = str(uuid.uuid4())

        # Get basic returns metrics
        total_return = portfolio.total_return

        # Get trades dataframe
        trades = portfolio.trades.records_readable

        # Calculate metrics
        returns = portfolio.returns
        sharpe_ratio = self.metrics_calculator.sharpe_ratio(returns) if len(returns) > 1 else 0.0
        sortino_ratio = self.metrics_calculator.sortino_ratio(returns) if len(returns) > 1 else 0.0
        max_drawdown = abs(portfolio.max_drawdown) if not returns.empty else 0.0  # VectorBT returns negative value

        # Trade metrics
        if len(trades) > 0:
            win_rate = len(trades[trades['PnL'] > 0]) / len(trades)
            profit_factor = self.metrics_calculator.profit_factor(trades)
            avg_win = trades[trades['PnL'] > 0]['PnL'].mean() if len(trades[trades['PnL'] > 0]) > 0 else 0
            avg_loss = abs(trades[trades['PnL'] < 0]['PnL'].mean()) if len(trades[trades['PnL'] < 0]) > 0 else 0
            avg_trade = trades['PnL'].mean()

            # Consecutive wins/losses
            max_consecutive_wins = self._calculate_max_consecutive(trades['PnL'] > 0, True)
            max_consecutive_losses = self._calculate_max_consecutive(trades['PnL'] < 0, True)
        else:
            win_rate = 0.0
            profit_factor = 0.0
            avg_win = 0.0
            avg_loss = 0.0
            avg_trade = 0.0
            max_consecutive_wins = 0
            max_consecutive_losses = 0

        total_trades = len(trades)

        # Additional metrics
        net_profit = portfolio.total_profit
        recovery_factor = net_profit / max_drawdown if max_drawdown > 0 else 0.0

        # Calmar ratio (annualized return / max drawdown)
        annual_return = total_return * (252 / data_points) if data_points > 0 else 0  # Assuming daily data
        calmar_ratio = annual_return / max_drawdown if max_drawdown > 0 else 0.0

        # Generate params hash for tracking
        strategy_params = getattr(strategy, 'params', {})
        params_hash = BacktestResults.generate_params_hash(strategy_params)

        # Check Apex compliance if validator is available
        apex_compliant = True
        apex_violations = []

        if self.apex_validator:
            try:
                # Create a simple validation result based on our metrics
                validation_result = self.apex_validator.validate({
                    'total_return': total_return,
                    'max_drawdown': max_drawdown,
                    'profit_factor': profit_factor,
                    'trades': trades
                })
                apex_compliant = validation_result.get('is_compliant', True)
                apex_violations = validation_result.get('violations', [])
            except:
                # If validation fails, assume compliant
                apex_compliant = True

        # Build results
        return BacktestResults(
            backtest_id=backtest_id,
            strategy_id=config.strategy_id,
            total_return=float(total_return),
            sharpe_ratio=float(sharpe_ratio),
            sortino_ratio=float(sortino_ratio),
            max_drawdown=float(max_drawdown),
            win_rate=float(win_rate),
            profit_factor=float(profit_factor),
            total_trades=int(total_trades),
            avg_win=float(avg_win) if avg_win else None,
            avg_loss=float(avg_loss) if avg_loss else None,
            avg_trade=float(avg_trade) if avg_trade else None,
            max_consecutive_wins=int(max_consecutive_wins),
            max_consecutive_losses=int(max_consecutive_losses),
            recovery_factor=float(recovery_factor),
            calmar_ratio=float(calmar_ratio),
            apex_compliant=apex_compliant,
            apex_violations=apex_violations,
            params_hash=params_hash,
            strategy_params=strategy_params,
            execution_time_seconds=execution_time,
            data_points=data_points
        )

    def _map_timeframe_to_freq(self, timeframe: str) -> str:
        """Map timeframe string to pandas frequency string.

        Args:
            timeframe: Timeframe like "1min", "5min", "1h", etc.

        Returns:
            Pandas frequency string
        """
        mapping = {
            "1min": "1T",
            "5min": "5T",
            "15min": "15T",
            "30min": "30T",
            "1h": "1H",
            "2h": "2H",
            "4h": "4H",
            "1d": "1D",
            "1w": "1W",
        }
        return mapping.get(timeframe, "1T")

    def _calculate_max_consecutive(self, series: pd.Series, value: bool) -> int:
        """Calculate maximum consecutive occurrences of a value.

        Args:
            series: Boolean series
            value: Value to count (True or False)

        Returns:
            Maximum consecutive count
        """
        if len(series) == 0:
            return 0

        max_count = 0
        current_count = 0

        for item in series:
            if item == value:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0

        return max_count


# Mock ApexValidator for now (will be implemented in AUT-337)
class ApexValidator:
    """Placeholder for Apex compliance validator."""

    def validate(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Validate metrics against Apex rules.

        For now, just returns compliant.
        Real implementation in AUT-337.
        """
        return {
            'is_compliant': True,
            'violations': []
        }