"""
Research & Backtesting API Schemas (AUT-363)

Pydantic models for OpenAPI documentation generation.
Used by FastAPI to auto-generate the OpenAPI spec.

References:
- Linear Issue: AUT-363 (CONTRACT-002)
- Depends on: AUT-336 (Backtesting engine), AUT-335 (AbstractStrategy)
- Unblocks: AUT-340 (Backtesting page React)
"""
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, Dict, Any, List


# ============= Backtest Run Schemas =============

class BacktestRunRequest(BaseModel):
    """
    Request to launch a backtest run.

    Submitted via POST /backtest/run, executed async via Celery.
    """
    strategy_id: str = Field(
        ...,
        description="ID of the registered strategy to backtest",
        examples=["sma_crossover_v1", "rsi_mean_reversion"]
    )
    timeframe: str = Field(
        ...,
        description="Candlestick timeframe",
        examples=["1min", "5min", "15min", "1h"]
    )
    start_date: date = Field(
        ...,
        description="Backtest start date (inclusive)",
        examples=["2024-01-01"]
    )
    end_date: date = Field(
        ...,
        description="Backtest end date (inclusive)",
        examples=["2024-12-31"]
    )
    commission: float = Field(
        default=0.0002,
        description="Commission per trade (as decimal, e.g., 0.0002 = 0.02%)",
        ge=0.0,
        le=0.01
    )
    slippage: float = Field(
        default=0.0001,
        description="Slippage per trade (as decimal, e.g., 0.0001 = 0.01%)",
        ge=0.0,
        le=0.01
    )
    initial_capital: float = Field(
        default=25000.0,
        description="Initial capital for backtest (Apex $25K default)",
        ge=1000.0,
        le=1000000.0
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy-specific parameters override (e.g., {'sma_period': 20})",
        examples=[{"sma_fast": 10, "sma_slow": 50, "rsi_threshold": 30}]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "sma_crossover_v1",
                "timeframe": "5min",
                "start_date": "2024-01-01",
                "end_date": "2024-06-30",
                "commission": 0.0002,
                "slippage": 0.0001,
                "initial_capital": 25000.0,
                "parameters": {
                    "sma_fast": 10,
                    "sma_slow": 50
                }
            }
        }


class BacktestRunResponse(BaseModel):
    """
    Response after submitting a backtest run.

    Contains Celery task ID for progress tracking.
    """
    task_id: str = Field(
        ...,
        description="Celery task ID for async execution tracking"
    )
    status: str = Field(
        ...,
        description="Initial task status",
        examples=["queued", "running", "completed", "failed"]
    )
    backtest_id: Optional[str] = Field(
        default=None,
        description="Backtest run ID (assigned when task starts)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "a8b3c4d5-e6f7-8g9h-0i1j-2k3l4m5n6o7p",
                "status": "queued",
                "backtest_id": None
            }
        }


class BacktestResultsSchema(BaseModel):
    """
    Backtest results with performance metrics.

    Retrieved via GET /backtest/screener or after task completion.
    """
    backtest_id: str = Field(
        ...,
        description="Unique backtest run identifier"
    )
    strategy_id: str = Field(
        ...,
        description="Strategy used for this backtest"
    )
    status: str = Field(
        ...,
        description="Backtest status",
        examples=["completed", "failed", "running"]
    )
    total_return: float = Field(
        ...,
        description="Total return as decimal (e.g., 0.15 = 15%)"
    )
    sharpe_ratio: float = Field(
        ...,
        description="Sharpe ratio (risk-adjusted returns)"
    )
    sortino_ratio: float = Field(
        ...,
        description="Sortino ratio (downside risk-adjusted returns)"
    )
    max_drawdown: float = Field(
        ...,
        description="Maximum drawdown as decimal (e.g., -0.10 = -10%)"
    )
    win_rate: float = Field(
        ...,
        description="Percentage of winning trades (0.0 to 1.0)"
    )
    profit_factor: float = Field(
        ...,
        description="Ratio of gross profit to gross loss"
    )
    total_trades: int = Field(
        ...,
        description="Total number of trades executed"
    )
    apex_compliant: bool = Field(
        ...,
        description="Whether backtest passed Apex compliance checks (AUT-337)"
    )
    created_at: datetime = Field(
        ...,
        description="Backtest creation timestamp (UTC)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "backtest_id": "bt_20240315_001",
                "strategy_id": "sma_crossover_v1",
                "status": "completed",
                "total_return": 0.1234,
                "sharpe_ratio": 1.85,
                "sortino_ratio": 2.15,
                "max_drawdown": -0.0856,
                "win_rate": 0.62,
                "profit_factor": 1.42,
                "total_trades": 156,
                "apex_compliant": True,
                "created_at": "2024-03-15T14:30:00Z"
            }
        }


class BacktestImportRequest(BaseModel):
    """
    Request to import backtest results from Jupyter notebook.

    Allows researchers to run backtests in notebooks and import results.
    """
    strategy_id: str = Field(
        ...,
        description="Strategy ID used in notebook"
    )
    notebook_path: str = Field(
        ...,
        description="Path to Jupyter notebook file"
    )
    results_json: Dict[str, Any] = Field(
        ...,
        description="Backtest results as JSON (from notebook output)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "custom_ml_v2",
                "notebook_path": "/research/notebooks/ml_backtest_20240315.ipynb",
                "results_json": {
                    "total_return": 0.15,
                    "sharpe_ratio": 2.1,
                    "trades": 200
                }
            }
        }


# ============= Optimization Schemas =============

class OptimizeRequest(BaseModel):
    """
    Request to optimize strategy parameters.

    Supports grid search or walk-forward optimization.
    """
    strategy_id: str = Field(
        ...,
        description="Strategy to optimize"
    )
    method: str = Field(
        ...,
        description="Optimization method",
        examples=["grid_search", "walk_forward"]
    )
    param_grid: Dict[str, List[Any]] = Field(
        ...,
        description="Parameter grid for optimization (e.g., {'sma_period': [10, 20, 50]})"
    )
    n_splits: int = Field(
        default=5,
        description="Number of splits for walk-forward optimization",
        ge=2,
        le=20
    )
    timeframe: str = Field(
        default="1min",
        description="Candlestick timeframe"
    )
    start_date: date = Field(
        ...,
        description="Optimization start date"
    )
    end_date: date = Field(
        ...,
        description="Optimization end date"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "sma_crossover_v1",
                "method": "grid_search",
                "param_grid": {
                    "sma_fast": [5, 10, 20],
                    "sma_slow": [30, 50, 100],
                    "rsi_threshold": [30, 40, 50]
                },
                "n_splits": 5,
                "timeframe": "5min",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        }


class OptimizeResponse(BaseModel):
    """
    Response after submitting optimization job.

    Returns task ID for tracking the long-running optimization process.
    """
    task_id: str = Field(
        ...,
        description="Celery task ID for optimization job"
    )
    status: str = Field(
        ...,
        description="Initial task status",
        examples=["queued", "running"]
    )
    total_combinations: int = Field(
        ...,
        description="Total parameter combinations to test"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "opt_a1b2c3d4-e5f6-7g8h-9i0j",
                "status": "queued",
                "total_combinations": 27
            }
        }


# ============= Strategy Management Schemas =============

class StrategySchema(BaseModel):
    """
    Strategy metadata and configuration.

    Retrieved via GET /strategies or after registration.
    """
    id: str = Field(
        ...,
        description="Unique strategy identifier"
    )
    name: str = Field(
        ...,
        description="Human-readable strategy name"
    )
    version: str = Field(
        ...,
        description="Strategy version (e.g., 'v1.2.3')"
    )
    type: str = Field(
        ...,
        description="Strategy type",
        examples=["rule_based", "ml", "dl", "rl"]
    )
    description: str = Field(
        ...,
        description="Strategy description and logic summary"
    )
    parameters_schema: Dict[str, Any] = Field(
        ...,
        description="JSON schema for strategy parameters"
    )
    last_used: Optional[datetime] = Field(
        default=None,
        description="Last time this strategy was used in a backtest"
    )
    is_active: bool = Field(
        ...,
        description="Whether strategy is active and available for use"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "sma_crossover_v1",
                "name": "SMA Crossover",
                "version": "1.0.0",
                "type": "rule_based",
                "description": "Simple moving average crossover strategy with RSI filter",
                "parameters_schema": {
                    "sma_fast": {"type": "integer", "default": 10, "min": 5, "max": 50},
                    "sma_slow": {"type": "integer", "default": 50, "min": 20, "max": 200},
                    "rsi_period": {"type": "integer", "default": 14},
                    "rsi_threshold": {"type": "integer", "default": 30}
                },
                "last_used": "2024-03-15T10:30:00Z",
                "is_active": True
            }
        }


class StrategyRegisterRequest(BaseModel):
    """
    Request to register a new strategy.

    Strategy class must inherit from AbstractStrategy (AUT-335).
    """
    name: str = Field(
        ...,
        description="Strategy name",
        min_length=3,
        max_length=100
    )
    version: str = Field(
        ...,
        description="Version string (e.g., '1.0.0')",
        pattern=r"^\d+\.\d+\.\d+$"
    )
    file_path: str = Field(
        ...,
        description="Path to strategy Python file"
    )
    type: str = Field(
        ...,
        description="Strategy type",
        examples=["rule_based", "ml", "dl", "rl"]
    )
    description: str = Field(
        default="",
        description="Optional strategy description"
    )
    parameters_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional JSON schema for parameters"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "SMA Crossover",
                "version": "1.0.0",
                "file_path": "/strategies/sma_crossover.py",
                "type": "rule_based",
                "description": "Simple moving average crossover with RSI filter",
                "parameters_schema": {
                    "sma_fast": {"type": "integer", "default": 10},
                    "sma_slow": {"type": "integer", "default": 50}
                }
            }
        }


class StrategyRegisterResponse(BaseModel):
    """
    Response after registering a strategy.

    Returns the assigned strategy ID.
    """
    strategy_id: str = Field(
        ...,
        description="Unique ID assigned to the registered strategy"
    )
    status: str = Field(
        ...,
        description="Registration status",
        examples=["registered", "failed"]
    )
    message: str = Field(
        default="",
        description="Additional information or error message"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "sma_crossover_v1",
                "status": "registered",
                "message": "Strategy successfully registered and validated"
            }
        }


class StrategyValidateRequest(BaseModel):
    """
    Request to validate strategy before registration.

    Checks syntax, inheritance from AbstractStrategy, and parameter schema.
    """
    file_path: str = Field(
        ...,
        description="Path to strategy Python file to validate"
    )
    type: str = Field(
        ...,
        description="Expected strategy type",
        examples=["rule_based", "ml", "dl", "rl"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "/strategies/new_strategy.py",
                "type": "rule_based"
            }
        }


class StrategyValidateResponse(BaseModel):
    """
    Response from strategy validation.

    Returns validation errors if any.
    """
    is_valid: bool = Field(
        ...,
        description="Whether strategy passed validation"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Validation error messages (empty if valid)"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-blocking warnings"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "errors": [],
                "warnings": ["Parameter 'risk_per_trade' not defined in schema"]
            }
        }


# ============= Screener Schemas =============

class BacktestScreenerParams(BaseModel):
    """
    Query parameters for backtest screener.

    Used for filtering and sorting backtest results.
    """
    strategy_id: Optional[str] = Field(
        default=None,
        description="Filter by strategy ID"
    )
    min_sharpe: Optional[float] = Field(
        default=None,
        description="Minimum Sharpe ratio filter"
    )
    min_return: Optional[float] = Field(
        default=None,
        description="Minimum total return filter (as decimal)"
    )
    apex_compliant_only: bool = Field(
        default=False,
        description="Only show Apex-compliant backtests"
    )
    limit: int = Field(
        default=50,
        description="Maximum results to return",
        ge=1,
        le=500
    )
    offset: int = Field(
        default=0,
        description="Result offset for pagination",
        ge=0
    )


class BacktestScreenerResponse(BaseModel):
    """
    Response from backtest screener endpoint.

    Returns list of matching backtests with pagination info.
    """
    total: int = Field(
        ...,
        description="Total number of matching backtests"
    )
    results: List[BacktestResultsSchema] = Field(
        ...,
        description="List of backtest results"
    )
    limit: int = Field(
        ...,
        description="Results per page"
    )
    offset: int = Field(
        ...,
        description="Current offset"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total": 156,
                "results": [
                    {
                        "backtest_id": "bt_20240315_001",
                        "strategy_id": "sma_crossover_v1",
                        "status": "completed",
                        "total_return": 0.1234,
                        "sharpe_ratio": 1.85,
                        "sortino_ratio": 2.15,
                        "max_drawdown": -0.0856,
                        "win_rate": 0.62,
                        "profit_factor": 1.42,
                        "total_trades": 156,
                        "apex_compliant": True,
                        "created_at": "2024-03-15T14:30:00Z"
                    }
                ],
                "limit": 50,
                "offset": 0
            }
        }
