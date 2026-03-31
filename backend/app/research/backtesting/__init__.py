"""
Backtesting module for NQHub.

Provides VectorBT Pro wrapper for running backtests, optimization, and async execution via Celery.
"""

from app.research.backtesting.engine import BacktestEngine, ApexValidator
from app.research.backtesting.schemas import (
    BacktestConfig,
    BacktestResults,
    OptimizationConfig,
    OptimizationResults
)
from app.research.backtesting.optimizer import BacktestOptimizer
from app.research.backtesting.tasks import (
    run_backtest_task,
    optimize_backtest_task
)

__all__ = [
    # Engine
    "BacktestEngine",
    "ApexValidator",

    # Schemas
    "BacktestConfig",
    "BacktestResults",
    "OptimizationConfig",
    "OptimizationResults",

    # Optimizer
    "BacktestOptimizer",

    # Celery tasks
    "run_backtest_task",
    "optimize_backtest_task",
]

__version__ = "1.0.0"