"""
Schemas for backtesting module.

BacktestConfig: Configuration for running a backtest.
BacktestResults: Results from a completed backtest.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import hashlib
import json


class BacktestConfig(BaseModel):
    """Configuration for running a backtest."""

    strategy_id: str = Field(..., description="Unique identifier for the strategy")
    timeframe: str = Field(..., description="Timeframe: 1min, 5min, 15min, 1h, etc.")
    start_date: datetime = Field(..., description="Start date for the backtest")
    end_date: datetime = Field(..., description="End date for the backtest")
    commission: float = Field(
        default=0.0002,
        description="Commission rate (e.g., 0.0002 = 0.02%)"
    )
    slippage: float = Field(
        default=0.0001,
        description="Slippage rate (e.g., 0.0001 = 0.01%)"
    )
    initial_capital: float = Field(
        default=25000.0,
        description="Initial capital in USD (Apex $25K account minimum)"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BacktestResults(BaseModel):
    """Results from a completed backtest."""

    backtest_id: str = Field(..., description="Unique identifier for this backtest run")
    strategy_id: str = Field(..., description="Strategy that was backtested")

    # Performance metrics
    total_return: float = Field(..., description="Total return as decimal (0.15 = 15%)")
    sharpe_ratio: float = Field(..., description="Risk-adjusted return metric")
    sortino_ratio: float = Field(..., description="Downside risk-adjusted return")
    max_drawdown: float = Field(..., description="Maximum drawdown as decimal (0.05 = 5%)")
    win_rate: float = Field(..., description="Percentage of winning trades (0.6 = 60%)")
    profit_factor: float = Field(..., description="Gross profit / gross loss ratio")
    total_trades: int = Field(..., description="Total number of trades executed")

    # Additional metrics
    avg_win: Optional[float] = Field(None, description="Average winning trade in USD")
    avg_loss: Optional[float] = Field(None, description="Average losing trade in USD")
    avg_trade: Optional[float] = Field(None, description="Average trade P&L in USD")
    max_consecutive_wins: Optional[int] = Field(None, description="Maximum consecutive winning trades")
    max_consecutive_losses: Optional[int] = Field(None, description="Maximum consecutive losing trades")
    recovery_factor: Optional[float] = Field(None, description="Net profit / max drawdown")
    calmar_ratio: Optional[float] = Field(None, description="Annual return / max drawdown")

    # Apex compliance (from AUT-337)
    apex_compliant: bool = Field(
        ...,
        description="Whether the strategy passes Apex evaluation rules"
    )
    apex_violations: Optional[list[str]] = Field(
        default_factory=list,
        description="List of Apex rule violations if any"
    )

    # Parameter tracking
    params_hash: str = Field(
        ...,
        description="Hash of strategy parameters for drift detection"
    )
    strategy_params: Optional[dict] = Field(
        None,
        description="Strategy parameters used in this backtest"
    )

    # Metadata
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="When this backtest was run"
    )
    execution_time_seconds: Optional[float] = Field(
        None,
        description="How long the backtest took to run"
    )
    data_points: Optional[int] = Field(
        None,
        description="Number of candles/bars processed"
    )

    @staticmethod
    def generate_params_hash(params: dict) -> str:
        """Generate a hash from strategy parameters for tracking."""
        # Sort keys for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        return hashlib.md5(sorted_params.encode()).hexdigest()

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OptimizationConfig(BaseModel):
    """Configuration for optimization (grid search or walk-forward)."""

    strategy_class: str = Field(..., description="Strategy class name to optimize")
    optimization_type: str = Field(
        ...,
        description="Type: 'grid_search' or 'walk_forward'"
    )
    timeframe: str = Field(..., description="Timeframe for the optimization")
    start_date: datetime = Field(..., description="Start date for the optimization")
    end_date: datetime = Field(..., description="End date for the optimization")

    # Grid search specific
    param_grid: Optional[dict] = Field(
        None,
        description="Parameter grid for grid search"
    )

    # Walk-forward specific
    n_splits: Optional[int] = Field(
        5,
        description="Number of splits for walk-forward validation"
    )
    train_ratio: Optional[float] = Field(
        0.7,
        description="Ratio of data to use for training in each split"
    )

    # Common optimization settings
    metric: str = Field(
        default="sharpe_ratio",
        description="Metric to optimize: sharpe_ratio, total_return, profit_factor, etc."
    )
    n_jobs: int = Field(
        default=4,
        description="Number of parallel jobs (Celery workers)"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OptimizationResults(BaseModel):
    """Results from an optimization run."""

    optimization_id: str = Field(..., description="Unique identifier for this optimization")
    optimization_type: str = Field(..., description="Type: grid_search or walk_forward")
    strategy_class: str = Field(..., description="Strategy class that was optimized")

    # Best result
    best_params: dict = Field(..., description="Best parameters found")
    best_metric_value: float = Field(..., description="Best metric value achieved")
    best_backtest_id: str = Field(..., description="Backtest ID of best result")

    # All results
    all_results: list[BacktestResults] = Field(
        ...,
        description="All backtest results from optimization"
    )
    n_iterations: int = Field(..., description="Total number of backtests run")

    # Metadata
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="When this optimization was run"
    )
    execution_time_seconds: Optional[float] = Field(
        None,
        description="Total time for optimization"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }