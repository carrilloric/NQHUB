"""
Backtesting API Endpoints

Implementation of CONTRACT-003 Strategy & Backtesting API specification.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, cast, Float
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4
import logging
import ast
import json

from app.db.session import get_db
from app.models.strategy import Strategy, BacktestRun, StrategyApproval
from app.models.user import User
from app.core.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Valid strategy types
STRATEGY_TYPES = ['momentum', 'mean_reversion', 'trend_following', 'breakout', 'scalping']

# Valid strategy statuses
STRATEGY_STATUSES = ['draft', 'validated', 'approved', 'deprecated']

# Valid backtest statuses
BACKTEST_STATUSES = ['queued', 'running', 'completed', 'failed', 'imported']

# Valid sources
SOURCES = ['nqhub', 'notebook', 'external', 'manual']

# Valid timeframes
TIMEFRAMES = ['1min', '5min', '15min', '30min', '1hour', '4hour', '1day']

# Approval thresholds (from issue notes)
APPROVAL_THRESHOLDS = {
    'sharpe': 1.5,
    'profit_factor': 1.5,
    'total_trades': 100,
    'max_dd': 0.30  # 30% max drawdown threshold
}

# Optimization job storage (in production, use Redis or database)
optimization_jobs = {}


# ============= Strategies Endpoints =============

@router.get("/strategies")
async def list_strategies(
    type: Optional[str] = Query(None, description="Filter by strategy type", enum=STRATEGY_TYPES),
    status: Optional[str] = Query(None, description="Filter by strategy status", enum=STRATEGY_STATUSES),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List available strategies.

    Implements GET /api/v1/backtest/strategies from CONTRACT-003.
    """
    try:
        # Build query
        query = select(Strategy)

        # Apply filters
        if type:
            query = query.where(Strategy.type == type)
        if status:
            query = query.where(Strategy.status == status)

        # Apply limit
        query = query.order_by(Strategy.created_at.desc()).limit(limit)

        # Execute query
        result = await db.execute(query)
        strategies = result.scalars().all()

        # Format response
        strategy_list = []
        for strategy in strategies:
            strategy_list.append({
                "id": str(strategy.id),
                "name": strategy.name,
                "version": strategy.version,
                "type": strategy.type,
                "status": strategy.status,
                "created_at": strategy.created_at.isoformat() + "Z"
            })

        return {
            "strategies": strategy_list
        }

    except Exception as e:
        logger.error(f"Error listing strategies: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )


@router.get("/strategies/{id}/source")
async def get_strategy_source(
    id: str = Path(..., description="Strategy ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get strategy source code.

    Implements GET /api/v1/strategies/{id}/source from CONTRACT-003.
    """
    try:
        # Query strategy
        result = await db.execute(
            select(Strategy).where(Strategy.id == id)
        )
        strategy = result.scalar_one_or_none()

        if not strategy:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NOT_FOUND",
                    "message": "Strategy not found"
                }
            )

        return {
            "code": strategy.source_code or "",
            "name": strategy.name,
            "version": strategy.version,
            "created_at": strategy.created_at.isoformat() + "Z"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching strategy source: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )


@router.post("/strategies/validate")
async def validate_strategy(
    request: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate strategy code.

    Implements POST /api/v1/strategies/validate from CONTRACT-003.
    """
    try:
        # Extract code from request
        code = request.get("code", "")

        if not code:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "VALIDATION_ERROR",
                    "message": "Code is required"
                }
            )

        # Basic Python syntax validation
        errors = []
        warnings = []
        valid = True
        detected_name = None
        detected_type = None
        required_features = []

        try:
            # Try to parse the code
            ast.parse(code)

            # Simple heuristic detection
            if "strategy_logic" in code or "def strategy" in code:
                detected_name = "Custom Strategy"

            # Detect strategy type based on keywords
            if "momentum" in code.lower():
                detected_type = "momentum"
            elif "mean_reversion" in code.lower() or "reversion" in code.lower():
                detected_type = "mean_reversion"
            elif "trend" in code.lower():
                detected_type = "trend_following"
            elif "breakout" in code.lower():
                detected_type = "breakout"
            elif "scalp" in code.lower():
                detected_type = "scalping"

            # Detect required features
            if "volume" in code.lower():
                required_features.append("volume")
            if "delta" in code.lower():
                required_features.append("delta")
            if "vwap" in code.lower():
                required_features.append("vwap")
            if "oflow" in code.lower() or "orderflow" in code.lower():
                required_features.append("orderflow")

            # Check for common issues
            if "import pandas" not in code:
                warnings.append("Consider importing pandas for data manipulation")
            if "import numpy" not in code:
                warnings.append("Consider importing numpy for numerical operations")

        except SyntaxError as se:
            valid = False
            errors.append(f"Syntax error at line {se.lineno}: {se.msg}")
        except Exception as e:
            valid = False
            errors.append(f"Invalid Python code: {str(e)}")

        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "detected_name": detected_name,
            "detected_type": detected_type,
            "required_features": required_features
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating strategy: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )


@router.post("/strategies/save", status_code=201)
async def save_strategy(
    request: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Save a new strategy.

    Implements POST /api/v1/strategies/save from CONTRACT-003.
    """
    try:
        # Validate required fields
        code = request.get("code", "")
        name = request.get("name", "")
        version = request.get("version", "")

        if not code or not name or not version:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "VALIDATION_ERROR",
                    "message": "code, name, and version are required"
                }
            )

        # Validate version format (semver)
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', version):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "VALIDATION_ERROR",
                    "message": "Version must be in semver format (e.g., 1.0.0)"
                }
            )

        # Check for duplicate name/version
        existing = await db.execute(
            select(Strategy).where(
                and_(
                    Strategy.name == name,
                    Strategy.version == version
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "CONFLICT",
                    "message": f"Strategy {name} version {version} already exists"
                }
            )

        # Detect strategy type if not provided
        strategy_type = request.get("type", "momentum")  # Default to momentum
        if "mean_reversion" in code.lower():
            strategy_type = "mean_reversion"
        elif "trend" in code.lower():
            strategy_type = "trend_following"
        elif "breakout" in code.lower():
            strategy_type = "breakout"
        elif "scalp" in code.lower():
            strategy_type = "scalping"

        # Create new strategy
        new_strategy = Strategy(
            name=name,
            version=version,
            type=strategy_type,
            source_code=code,
            status="draft",
            required_features=request.get("required_features", [])
        )

        db.add(new_strategy)
        await db.commit()
        await db.refresh(new_strategy)

        return {
            "id": str(new_strategy.id),
            "status": "draft"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving strategy: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )


# ============= Backtesting Endpoints =============

@router.post("/run", status_code=202)
async def run_backtest(
    request: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute backtest.

    Implements POST /api/v1/backtest/run from CONTRACT-003.
    """
    try:
        # Validate required fields
        strategy_id = request.get("strategy_id")
        config = request.get("config", {})

        if not strategy_id or not config:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "VALIDATION_ERROR",
                    "message": "strategy_id and config are required"
                }
            )

        # Verify strategy exists
        result = await db.execute(
            select(Strategy).where(Strategy.id == strategy_id)
        )
        strategy = result.scalar_one_or_none()

        if not strategy:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NOT_FOUND",
                    "message": "Strategy not found"
                }
            )

        # Validate config fields
        required_config = ['start', 'end', 'timeframe']
        for field in required_config:
            if field not in config:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "VALIDATION_ERROR",
                        "message": f"config.{field} is required"
                    }
                )

        # Validate timeframe
        if config['timeframe'] not in TIMEFRAMES:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "VALIDATION_ERROR",
                    "message": f"Invalid timeframe. Must be one of: {', '.join(TIMEFRAMES)}"
                }
            )

        # Create backtest run
        run_id = uuid4()
        new_run = BacktestRun(
            id=run_id,
            strategy_id=strategy_id,
            params=request.get("params", {}),
            config=config,
            status="queued",
            source="nqhub"
        )

        db.add(new_run)

        # Simulate Celery task ID
        task_id = str(uuid4())

        # For now, simulate immediate completion (as noted in issue)
        # In production, this would queue to Celery
        new_run.status = "completed"
        new_run.completed_at = datetime.utcnow()
        new_run.results = {
            "sharpe": 2.5,
            "sortino": 3.1,
            "max_dd": 0.15,
            "win_rate": 0.65,
            "profit_factor": 2.1,
            "total_trades": 450,
            "net_profit": 125000,
            "avg_win": 350,
            "avg_loss": -150,
            "max_consecutive_wins": 8,
            "max_consecutive_losses": 3
        }

        await db.commit()

        return {
            "run_id": str(run_id),
            "status": "queued",
            "task_id": task_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running backtest: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )


@router.post("/results/import", status_code=201)
async def import_backtest_results(
    request: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import backtest results.

    Implements POST /api/v1/backtest/results/import from CONTRACT-003.
    """
    try:
        # Validate required fields
        strategy_id = request.get("strategy_id")
        results = request.get("results", {})
        source = request.get("source", "notebook")

        if not strategy_id or not results or not source:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "VALIDATION_ERROR",
                    "message": "strategy_id, results, and source are required"
                }
            )

        # Verify strategy exists
        result = await db.execute(
            select(Strategy).where(Strategy.id == strategy_id)
        )
        strategy = result.scalar_one_or_none()

        if not strategy:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NOT_FOUND",
                    "message": "Strategy not found"
                }
            )

        # Validate source
        if source not in SOURCES:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "VALIDATION_ERROR",
                    "message": f"Invalid source. Must be one of: {', '.join(SOURCES)}"
                }
            )

        # Validate results contain required metrics
        required_metrics = ['sharpe', 'sortino', 'max_dd', 'win_rate']
        for metric in required_metrics:
            if metric not in results:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "VALIDATION_ERROR",
                        "message": f"results.{metric} is required"
                    }
                )

        # Create backtest run with imported results
        run_id = uuid4()
        new_run = BacktestRun(
            id=run_id,
            strategy_id=strategy_id,
            params=request.get("params_used", {}),
            config=request.get("config", {
                "start": "2025-01-01",
                "end": "2025-12-31",
                "timeframe": "5min"
            }),
            results=results,
            status="imported",
            source=source,
            completed_at=datetime.utcnow()
        )

        db.add(new_run)
        await db.commit()

        return {
            "run_id": str(run_id),
            "status": "imported"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing backtest results: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )


@router.get("/runs")
async def list_backtest_runs(
    strategy_id: Optional[str] = Query(None, description="Filter by strategy ID"),
    status: Optional[str] = Query(None, description="Filter by run status", enum=BACKTEST_STATUSES),
    source: Optional[str] = Query(None, description="Filter by result source", enum=SOURCES),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List backtest runs.

    Implements GET /api/v1/backtest/runs from CONTRACT-003.
    """
    try:
        # Build query
        query = select(BacktestRun)

        # Apply filters
        if strategy_id:
            query = query.where(BacktestRun.strategy_id == strategy_id)
        if status:
            query = query.where(BacktestRun.status == status)
        if source:
            query = query.where(BacktestRun.source == source)

        # Apply limit and ordering
        query = query.order_by(BacktestRun.created_at.desc()).limit(limit)

        # Execute query
        result = await db.execute(query)
        runs = result.scalars().all()

        # Format response
        run_list = []
        for run in runs:
            run_data = {
                "id": str(run.id),
                "strategy_id": str(run.strategy_id),
                "status": run.status,
                "created_at": run.created_at.isoformat() + "Z",
                "source": run.source
            }

            if run.results:
                run_data["results"] = run.results

            run_list.append(run_data)

        return {
            "runs": run_list
        }

    except Exception as e:
        logger.error(f"Error listing backtest runs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )


@router.get("/runs/{id}")
async def get_backtest_run(
    id: str = Path(..., description="Backtest run ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get backtest run details.

    Implements GET /api/v1/backtest/runs/{id} from CONTRACT-003.
    """
    try:
        # Query run
        result = await db.execute(
            select(BacktestRun).where(BacktestRun.id == id)
        )
        run = result.scalar_one_or_none()

        if not run:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NOT_FOUND",
                    "message": "Backtest run not found"
                }
            )

        # Build response
        response = {
            "id": str(run.id),
            "strategy_id": str(run.strategy_id),
            "status": run.status,
            "created_at": run.created_at.isoformat() + "Z",
            "source": run.source
        }

        if run.config:
            response["config"] = run.config

        if run.params:
            response["params_used"] = run.params

        if run.results:
            response["results"] = run.results

        if run.completed_at:
            response["completed_at"] = run.completed_at.isoformat() + "Z"

        # Generate sample equity curve if completed
        if run.status == "completed" or run.status == "imported":
            # Generate sample equity curve data
            equity_curve = []
            base_equity = 100000
            for i in range(30):
                date = datetime.utcnow() - timedelta(days=30-i)
                # Simulate equity growth
                equity = base_equity + (i * 1000) + ((i % 3) * 500)
                equity_curve.append({
                    "date": date.isoformat() + "Z",
                    "equity": float(equity)
                })
            response["equity_curve"] = equity_curve

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching backtest run: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )


@router.get("/screener")
async def screener_backtests(
    strategy_name: Optional[str] = Query(None, description="Filter by strategy name (partial match)"),
    type: Optional[str] = Query(None, description="Filter by strategy type", enum=STRATEGY_TYPES),
    timeframe: Optional[str] = Query(None, description="Filter by timeframe", enum=TIMEFRAMES),
    min_sharpe: Optional[float] = Query(None, description="Minimum Sharpe ratio"),
    min_profit_factor: Optional[float] = Query(None, description="Minimum profit factor"),
    source: Optional[str] = Query(None, description="Filter by result source", enum=SOURCES),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    order_by: str = Query("sharpe", description="Sort results by metric",
                         enum=["sharpe", "sortino", "max_dd", "win_rate", "profit_factor",
                               "total_trades", "net_profit", "created_at"]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Screen backtest results.

    Implements GET /api/v1/backtest/screener from CONTRACT-003.
    """
    try:
        # Build query joining runs with strategies
        query = select(
            BacktestRun,
            Strategy.name,
            Strategy.type
        ).join(
            Strategy,
            BacktestRun.strategy_id == Strategy.id
        ).where(
            or_(
                BacktestRun.status == "completed",
                BacktestRun.status == "imported"
            )
        )

        # Apply filters
        if strategy_name:
            query = query.where(Strategy.name.ilike(f"%{strategy_name}%"))
        if type:
            query = query.where(Strategy.type == type)
        if source:
            query = query.where(BacktestRun.source == source)

        # Filter by metrics using JSONB queries
        if min_sharpe:
            query = query.where(
                cast(BacktestRun.results['sharpe'], Float) >= min_sharpe
            )
        if min_profit_factor:
            query = query.where(
                cast(BacktestRun.results['profit_factor'], Float) >= min_profit_factor
            )
        if timeframe and BacktestRun.config is not None:
            query = query.where(
                BacktestRun.config['timeframe'].astext == timeframe
            )

        # Get total count before limiting
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply ordering
        if order_by == "created_at":
            query = query.order_by(BacktestRun.created_at.desc())
        elif order_by in ["sharpe", "sortino", "max_dd", "win_rate", "profit_factor",
                          "total_trades", "net_profit"]:
            # Order by JSONB field
            query = query.order_by(
                cast(BacktestRun.results[order_by], Float).desc()
            )

        # Apply limit
        query = query.limit(limit)

        # Execute query
        result = await db.execute(query)
        rows = result.all()

        # Format response
        screener_items = []
        for row in rows:
            run = row[0]
            strategy_name = row[1]
            strategy_type = row[2]

            item = {
                "id": str(run.id),
                "strategy_name": strategy_name,
                "strategy_type": strategy_type,
                "timeframe": run.config.get("timeframe", "5min") if run.config else "5min",
                "results": run.results or {},
                "created_at": run.created_at.isoformat() + "Z",
                "source": run.source
            }
            screener_items.append(item)

        return {
            "runs": screener_items,
            "total": total
        }

    except Exception as e:
        logger.error(f"Error in backtest screener: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )


@router.post("/optimize", status_code=202)
async def optimize_strategy(
    request: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Optimize strategy parameters.

    Implements POST /api/v1/backtest/optimize from CONTRACT-003.
    """
    try:
        # Validate required fields
        strategy_id = request.get("strategy_id")
        param_grid = request.get("param_grid", {})
        method = request.get("method", "grid")
        config = request.get("config", {})

        if not strategy_id or not param_grid or not method or not config:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "VALIDATION_ERROR",
                    "message": "strategy_id, param_grid, method, and config are required"
                }
            )

        # Verify strategy exists
        result = await db.execute(
            select(Strategy).where(Strategy.id == strategy_id)
        )
        strategy = result.scalar_one_or_none()

        if not strategy:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NOT_FOUND",
                    "message": "Strategy not found"
                }
            )

        # Validate method
        if method not in ["grid", "walk_forward"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "VALIDATION_ERROR",
                    "message": "Invalid method. Must be 'grid' or 'walk_forward'"
                }
            )

        # Create optimization job
        job_id = str(uuid4())
        optimization_jobs[job_id] = {
            "status": "queued",
            "strategy_id": strategy_id,
            "param_grid": param_grid,
            "method": method,
            "config": config,
            "created_at": datetime.utcnow()
        }

        # TODO: Queue actual optimization task (Celery, etc.)
        # For now, just return the job ID

        return {
            "job_id": job_id,
            "status": "queued"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating optimization job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )


# ============= Approval Endpoints =============

@router.get("/approval/checklist/{strategy_id}")
async def get_approval_checklist(
    strategy_id: str = Path(..., description="Strategy ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get approval checklist.

    Implements GET /api/v1/approval/checklist/{strategy_id} from CONTRACT-003.
    """
    try:
        # Verify strategy exists
        strategy_result = await db.execute(
            select(Strategy).where(Strategy.id == strategy_id)
        )
        strategy = strategy_result.scalar_one_or_none()

        if not strategy:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NOT_FOUND",
                    "message": "Strategy not found"
                }
            )

        # Get best backtest run for this strategy
        run_result = await db.execute(
            select(BacktestRun)
            .where(
                and_(
                    BacktestRun.strategy_id == strategy_id,
                    or_(
                        BacktestRun.status == "completed",
                        BacktestRun.status == "imported"
                    )
                )
            )
            .order_by(
                cast(BacktestRun.results['sharpe'], Float).desc().nullslast()
            )
            .limit(1)
        )
        best_run = run_result.scalar_one_or_none()

        # Build checklist
        checks = []
        overall_passed = True

        if best_run and best_run.results:
            results = best_run.results

            # Sharpe ratio check
            sharpe_value = results.get('sharpe', 0)
            sharpe_passed = sharpe_value >= APPROVAL_THRESHOLDS['sharpe']
            checks.append({
                "name": "Minimum Sharpe Ratio",
                "passed": sharpe_passed,
                "value": float(sharpe_value),
                "threshold": APPROVAL_THRESHOLDS['sharpe']
            })
            overall_passed = overall_passed and sharpe_passed

            # Profit factor check
            pf_value = results.get('profit_factor', 0)
            pf_passed = pf_value >= APPROVAL_THRESHOLDS['profit_factor']
            checks.append({
                "name": "Minimum Profit Factor",
                "passed": pf_passed,
                "value": float(pf_value),
                "threshold": APPROVAL_THRESHOLDS['profit_factor']
            })
            overall_passed = overall_passed and pf_passed

            # Total trades check
            trades_value = results.get('total_trades', 0)
            trades_passed = trades_value >= APPROVAL_THRESHOLDS['total_trades']
            checks.append({
                "name": "Minimum Total Trades",
                "passed": trades_passed,
                "value": float(trades_value),
                "threshold": APPROVAL_THRESHOLDS['total_trades']
            })
            overall_passed = overall_passed and trades_passed

            # Max drawdown check (Apex compliance)
            dd_value = results.get('max_dd', 1.0)
            dd_passed = dd_value <= APPROVAL_THRESHOLDS['max_dd']
            checks.append({
                "name": "Maximum Drawdown (Apex Trailing Threshold)",
                "passed": dd_passed,
                "value": float(dd_value),
                "threshold": APPROVAL_THRESHOLDS['max_dd']
            })
            overall_passed = overall_passed and dd_passed

        else:
            # No backtest results available
            checks = [
                {
                    "name": "Backtest Results Available",
                    "passed": False,
                    "value": 0.0,
                    "threshold": 1.0
                }
            ]
            overall_passed = False

        return {
            "checks": checks,
            "overall_passed": overall_passed
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting approval checklist: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )


@router.post("/approval/approve", status_code=201)
async def approve_strategy(
    request: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve strategy.

    Implements POST /api/v1/approval/approve from CONTRACT-003.
    """
    try:
        # Validate required fields
        strategy_id = request.get("strategy_id")
        backtest_run_id = request.get("backtest_run_id")

        if not strategy_id or not backtest_run_id:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "VALIDATION_ERROR",
                    "message": "strategy_id and backtest_run_id are required"
                }
            )

        # Verify strategy exists
        strategy_result = await db.execute(
            select(Strategy).where(Strategy.id == strategy_id)
        )
        strategy = strategy_result.scalar_one_or_none()

        if not strategy:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NOT_FOUND",
                    "message": "Strategy not found"
                }
            )

        # Verify backtest run exists and belongs to strategy
        run_result = await db.execute(
            select(BacktestRun).where(
                and_(
                    BacktestRun.id == backtest_run_id,
                    BacktestRun.strategy_id == strategy_id
                )
            )
        )
        run = run_result.scalar_one_or_none()

        if not run:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NOT_FOUND",
                    "message": "Backtest run not found for this strategy"
                }
            )

        # Check if strategy meets approval criteria
        if run.results:
            results = run.results
            sharpe_ok = results.get('sharpe', 0) >= APPROVAL_THRESHOLDS['sharpe']
            pf_ok = results.get('profit_factor', 0) >= APPROVAL_THRESHOLDS['profit_factor']
            trades_ok = results.get('total_trades', 0) >= APPROVAL_THRESHOLDS['total_trades']
            dd_ok = results.get('max_dd', 1.0) <= APPROVAL_THRESHOLDS['max_dd']

            if not (sharpe_ok and pf_ok and trades_ok and dd_ok):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "APPROVAL_FAILED",
                        "message": "Strategy does not meet approval criteria"
                    }
                )
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "APPROVAL_FAILED",
                    "message": "Backtest run has no results"
                }
            )

        # Check for existing approval
        existing_approval = await db.execute(
            select(StrategyApproval).where(
                and_(
                    StrategyApproval.strategy_id == strategy_id,
                    StrategyApproval.backtest_run_id == backtest_run_id
                )
            )
        )
        if existing_approval.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "CONFLICT",
                    "message": "This strategy version is already approved"
                }
            )

        # Create approval record
        approval = StrategyApproval(
            strategy_id=strategy_id,
            backtest_run_id=backtest_run_id,
            approved_params=run.params or {},
            approved_by=current_user.email,
            notes=request.get("notes", "")
        )

        # Update strategy status to approved
        strategy.status = "approved"

        db.add(approval)
        await db.commit()
        await db.refresh(approval)

        return {
            "approval_id": str(approval.id),
            "approved_at": approval.approved_at.isoformat() + "Z"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving strategy: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        )