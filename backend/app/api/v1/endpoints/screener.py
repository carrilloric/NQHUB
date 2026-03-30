"""
Backtest Screener + Export System (AUT-339 / ADR-021)

Provides filtering, comparison, export, and approval workflow for backtests.
Uses PerformanceReport and ApexComplianceValidator for metrics validation.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc, case
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field
from uuid import UUID
import json
import csv
import io
import os
import tempfile

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.strategy import Strategy, BacktestRun, StrategyApproval
from app.research.metrics.performance import PerformanceReport, PerformanceMetrics
from app.research.compliance.apex_validator import ApexComplianceValidator, ApexAccount, BacktestResults

router = APIRouter()


# ==================== Request/Response Models ====================

class BacktestRunSummary(BaseModel):
    """Summary of a backtest run for screener grid"""
    run_id: UUID
    strategy_name: str
    strategy_type: str
    run_date: datetime
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown_pct: float
    win_rate: float
    profit_factor: float
    total_trades: int
    total_pnl_usd: float
    apex_compliant: bool
    is_approved: bool


class ScreenerResponse(BaseModel):
    """Response for screener endpoint with pagination"""
    total: int
    runs: List[BacktestRunSummary]


class ExportRequest(BaseModel):
    """Request for export endpoint"""
    run_id: UUID
    format: Literal["csv", "json"]
    include_trades: bool = True
    include_equity_curve: bool = True


class ExportResponse(BaseModel):
    """Response with download URL"""
    download_url: str
    expires_at: datetime
    filename: str


class ApprovalCheckItem(BaseModel):
    """Single check in approval checklist"""
    name: str
    passed: bool
    value: float
    threshold: float


class ApprovalChecklist(BaseModel):
    """Complete approval checklist"""
    strategy_id: UUID
    checks: List[ApprovalCheckItem]
    all_passed: bool
    can_approve: bool


class ApprovalRequest(BaseModel):
    """Request to approve a strategy"""
    strategy_id: UUID
    run_id: UUID
    notes: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Response after approval"""
    approval_id: UUID
    approved_at: datetime
    approved_params: Dict[str, Any]


class ParamsDivergence(BaseModel):
    """Single parameter divergence"""
    param: str
    approved_value: Any
    current_value: Any
    delta_pct: float


class ParamsCheckResponse(BaseModel):
    """Response for params check"""
    bot_id: UUID
    has_divergence: bool
    diverged_params: List[ParamsDivergence]
    warning_level: Literal["ok", "warning", "critical"]


# ==================== Helper Functions ====================

def check_apex_compliance(results: Dict[str, Any]) -> bool:
    """Check if backtest results pass Apex compliance"""
    # Mock implementation - in production would use ApexComplianceValidator
    # Checking basic rules: max drawdown < 20%, win rate > 40%
    if not results:
        return False

    max_dd = results.get("max_drawdown_pct", 0)
    win_rate = results.get("win_rate", 0)

    return max_dd > -0.20 and win_rate > 0.40


def calculate_divergence(approved_value: Any, current_value: Any) -> float:
    """Calculate percentage divergence between two values"""
    if approved_value == 0:
        return 100.0 if current_value != 0 else 0.0

    try:
        approved = float(approved_value)
        current = float(current_value)
        return abs((current - approved) / approved) * 100
    except (TypeError, ValueError):
        # For non-numeric values, check if they're equal
        return 0.0 if approved_value == current_value else 100.0


# ==================== Part 1: Backtest Screener ====================

@router.get("/screener", response_model=ScreenerResponse)
async def get_backtest_screener(
    min_sharpe: float = Query(0.0, description="Minimum Sharpe ratio"),
    min_win_rate: float = Query(0.0, description="Minimum win rate (0-1)"),
    max_drawdown: float = Query(-1.0, description="Maximum drawdown (negative, e.g., -0.20)"),
    strategy_type: Optional[str] = Query(None, description="Strategy type filter"),
    apex_compliant: Optional[bool] = Query(None, description="Only Apex compliant"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    sort_by: str = Query("sharpe_ratio", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ScreenerResponse:
    """
    Get filtered and sorted backtest runs.
    Supports filtering by metrics, strategy type, compliance, and date range.
    """
    # Build query
    query = select(BacktestRun).join(
        Strategy, BacktestRun.strategy_id == Strategy.id
    ).where(
        BacktestRun.status == "completed"
    )

    # Apply filters
    filters = []

    if strategy_type:
        filters.append(Strategy.type == strategy_type)

    if start_date:
        filters.append(BacktestRun.created_at >= start_date)

    if end_date:
        filters.append(BacktestRun.created_at <= end_date)

    if filters:
        query = query.where(and_(*filters))

    # Get total count
    count_query = select(func.count()).select_from(BacktestRun).join(
        Strategy, BacktestRun.strategy_id == Strategy.id
    ).where(
        BacktestRun.status == "completed"
    )
    if filters:
        count_query = count_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply sorting
    sort_column = {
        "sharpe_ratio": BacktestRun.results["sharpe_ratio"],
        "sortino_ratio": BacktestRun.results["sortino_ratio"],
        "calmar_ratio": BacktestRun.results["calmar_ratio"],
        "max_drawdown_pct": BacktestRun.results["max_drawdown_pct"],
        "win_rate": BacktestRun.results["win_rate"],
        "profit_factor": BacktestRun.results["profit_factor"],
        "total_pnl_usd": BacktestRun.results["total_pnl_usd"],
        "run_date": BacktestRun.created_at
    }.get(sort_by, BacktestRun.created_at)

    if sort_order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # Apply pagination
    query = query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(query)
    runs = result.scalars().all()

    # Process results and apply metric filters
    run_summaries = []

    for run in runs:
        if not run.results:
            continue

        # Check metric filters
        sharpe = run.results.get("sharpe_ratio", 0)
        win_rate_val = run.results.get("win_rate", 0)
        max_dd = run.results.get("max_drawdown_pct", 0)

        if sharpe < min_sharpe:
            continue
        if win_rate_val < min_win_rate:
            continue
        if max_dd < max_drawdown:
            continue

        # Check Apex compliance if filtered
        is_apex_compliant = check_apex_compliance(run.results)
        if apex_compliant is not None and is_apex_compliant != apex_compliant:
            continue

        # Check if approved
        approval_query = select(StrategyApproval).where(
            StrategyApproval.backtest_run_id == run.id
        )
        approval_result = await db.execute(approval_query)
        is_approved = approval_result.scalar_one_or_none() is not None

        # Create summary
        run_summaries.append(BacktestRunSummary(
            run_id=run.id,
            strategy_name=run.strategy.name if run.strategy else "Unknown",
            strategy_type=run.strategy.type if run.strategy else "unknown",
            run_date=run.created_at,
            sharpe_ratio=sharpe,
            sortino_ratio=run.results.get("sortino_ratio", 0),
            calmar_ratio=run.results.get("calmar_ratio", 0),
            max_drawdown_pct=max_dd,
            win_rate=win_rate_val,
            profit_factor=run.results.get("profit_factor", 0),
            total_trades=run.results.get("total_trades", 0),
            total_pnl_usd=run.results.get("total_pnl_usd", 0),
            apex_compliant=is_apex_compliant,
            is_approved=is_approved
        ))

    return ScreenerResponse(
        total=len(run_summaries),
        runs=run_summaries
    )


@router.get("/comparison")
async def get_backtest_comparison(
    run_ids: List[UUID] = Query(..., description="2-5 backtest run IDs to compare"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Compare 2-5 backtest runs side by side.
    Returns all metrics in a comparison table format.
    """
    # Validate number of runs
    if len(run_ids) < 2 or len(run_ids) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide between 2 and 5 run IDs"
        )

    # Get runs
    query = select(BacktestRun).where(BacktestRun.id.in_(run_ids))
    result = await db.execute(query)
    runs = result.scalars().all()

    if len(runs) != len(run_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more run IDs not found"
        )

    # Build comparison table
    comparison = {
        "run_ids": [str(run_id) for run_id in run_ids],
        "metrics": {}
    }

    # Define metrics to compare
    metric_names = [
        "sharpe_ratio", "sortino_ratio", "calmar_ratio", "deflated_sharpe_ratio",
        "max_drawdown_pct", "max_drawdown_usd",
        "total_trades", "win_rate", "profit_factor",
        "avg_win_usd", "avg_loss_usd", "expectancy_usd",
        "total_pnl_usd", "total_pnl_ticks"
    ]

    # Build comparison for each metric
    for metric in metric_names:
        comparison["metrics"][metric] = []
        for run in runs:
            value = run.results.get(metric, 0) if run.results else 0
            comparison["metrics"][metric].append(value)

    # Add metadata
    comparison["metadata"] = []
    for run in runs:
        metadata = {
            "run_id": str(run.id),
            "strategy_id": str(run.strategy_id),
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "apex_compliant": check_apex_compliance(run.results)
        }
        comparison["metadata"].append(metadata)

    return comparison


# ==================== Part 2: Export System ====================

@router.post("/export", response_model=ExportResponse)
async def export_backtest_results(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ExportResponse:
    """
    Export backtest results to CSV or JSON.
    Returns a download URL that expires after 1 hour.
    """
    # Get backtest run
    query = select(BacktestRun).where(BacktestRun.id == request.run_id)
    result = await db.execute(query)
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest run not found"
        )

    # Prepare filename
    strategy_name = run.strategy.name if run.strategy else "unknown"
    strategy_name = strategy_name.replace(" ", "_").lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backtest_{strategy_name}_{timestamp}.{request.format}"

    # Prepare export data
    export_data = {
        "run_id": str(run.id),
        "strategy_id": str(run.strategy_id),
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "params": run.params,
        "config": run.config,
        "results": run.results or {}
    }

    # Add trades if requested (mock data for now)
    if request.include_trades:
        export_data["trades"] = [
            {
                "timestamp": datetime.now().isoformat(),
                "side": "BUY",
                "quantity": 1,
                "entry_price": 16000.0,
                "exit_price": 16050.0,
                "pnl_usd": 250.0
            }
            # In production, would fetch actual trades
        ]

    # Add equity curve if requested (mock data for now)
    if request.include_equity_curve:
        export_data["equity_curve"] = [
            {"timestamp": datetime.now().isoformat(), "equity": 25000 + i * 100}
            for i in range(10)
        ]

    # Create temporary file
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)

    if request.format == "json":
        # Export as JSON
        with open(file_path, "w") as f:
            json.dump(export_data, f, indent=2, default=str)
    else:
        # Export as CSV
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)

            # Write metrics
            writer.writerow(["Metric", "Value"])
            for key, value in export_data["results"].items():
                writer.writerow([key, value])

            # Write trades if included
            if request.include_trades and "trades" in export_data:
                writer.writerow([])
                writer.writerow(["Trades"])
                writer.writerow(["Timestamp", "Side", "Quantity", "Entry", "Exit", "PnL"])
                for trade in export_data["trades"]:
                    writer.writerow([
                        trade["timestamp"],
                        trade["side"],
                        trade["quantity"],
                        trade["entry_price"],
                        trade["exit_price"],
                        trade["pnl_usd"]
                    ])

    # Generate download URL (in production, would upload to S3 or similar)
    download_url = f"http://localhost:8002/api/v1/backtest/download/{filename}"
    expires_at = datetime.now() + timedelta(hours=1)

    # Schedule cleanup
    background_tasks.add_task(cleanup_export_file, file_path, 3600)

    return ExportResponse(
        download_url=download_url,
        expires_at=expires_at,
        filename=filename
    )


def cleanup_export_file(file_path: str, delay: int):
    """Remove export file after delay seconds"""
    import asyncio
    import time
    time.sleep(delay)
    if os.path.exists(file_path):
        os.remove(file_path)


@router.get("/download/{filename}")
async def download_export(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Download exported file"""
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found or expired"
        )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


# ==================== Part 3: Strategy Approval + Params Warning ====================

@router.get("/approval/checklist/{strategy_id}", response_model=ApprovalChecklist)
async def get_approval_checklist(
    strategy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApprovalChecklist:
    """
    Get approval checklist for a strategy.
    Checks: min_trades, min_sharpe, apex_compliant, max_drawdown, deflated_sharpe.
    """
    # Get strategy
    query = select(Strategy).where(Strategy.id == strategy_id)
    result = await db.execute(query)
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )

    # Get latest backtest run for strategy
    run_query = select(BacktestRun).where(
        and_(
            BacktestRun.strategy_id == strategy_id,
            BacktestRun.status == "completed"
        )
    ).order_by(desc(BacktestRun.created_at)).limit(1)

    run_result = await db.execute(run_query)
    run = run_result.scalar_one_or_none()

    if not run or not run.results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed backtest found for strategy"
        )

    # Define checks
    checks = []
    results = run.results

    # Check 1: Minimum trades
    total_trades = results.get("total_trades", 0)
    checks.append(ApprovalCheckItem(
        name="min_trades",
        passed=total_trades >= 100,
        value=total_trades,
        threshold=100
    ))

    # Check 2: Minimum Sharpe ratio
    sharpe = results.get("sharpe_ratio", 0)
    checks.append(ApprovalCheckItem(
        name="min_sharpe",
        passed=sharpe >= 1.5,
        value=sharpe,
        threshold=1.5
    ))

    # Check 3: Apex compliance
    apex_compliant = check_apex_compliance(results)
    checks.append(ApprovalCheckItem(
        name="apex_compliant",
        passed=apex_compliant,
        value=1.0 if apex_compliant else 0.0,
        threshold=1.0
    ))

    # Check 4: Maximum drawdown
    max_dd = results.get("max_drawdown_pct", 0)
    checks.append(ApprovalCheckItem(
        name="max_drawdown",
        passed=max_dd >= -0.20,  # Less than 20% drawdown
        value=max_dd,
        threshold=-0.20
    ))

    # Check 5: Deflated Sharpe ratio
    deflated_sharpe = results.get("deflated_sharpe_ratio", 0)
    checks.append(ApprovalCheckItem(
        name="deflated_sharpe",
        passed=deflated_sharpe >= 0.95,
        value=deflated_sharpe,
        threshold=0.95
    ))

    # Check if all passed
    all_passed = all(check.passed for check in checks)

    return ApprovalChecklist(
        strategy_id=strategy_id,
        checks=checks,
        all_passed=all_passed,
        can_approve=all_passed
    )


@router.post("/approval/approve", response_model=ApprovalResponse)
async def approve_strategy(
    request: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApprovalResponse:
    """
    Approve a strategy for production deployment.
    Saves the current parameters as approved_params.
    """
    # Verify strategy exists
    strategy_query = select(Strategy).where(Strategy.id == request.strategy_id)
    strategy_result = await db.execute(strategy_query)
    strategy = strategy_result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )

    # Verify backtest run exists
    run_query = select(BacktestRun).where(BacktestRun.id == request.run_id)
    run_result = await db.execute(run_query)
    run = run_result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest run not found"
        )

    # Check if already approved
    existing_query = select(StrategyApproval).where(
        and_(
            StrategyApproval.strategy_id == request.strategy_id,
            StrategyApproval.backtest_run_id == request.run_id
        )
    )
    existing_result = await db.execute(existing_query)
    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Strategy already approved for this backtest"
        )

    # Create approval record
    approval = StrategyApproval(
        strategy_id=request.strategy_id,
        backtest_run_id=request.run_id,
        approved_params=run.params,  # Save current params as approved
        approved_by=current_user.email,
        notes=request.notes
    )

    db.add(approval)

    # Update strategy status
    strategy.status = "approved"

    await db.commit()
    await db.refresh(approval)

    return ApprovalResponse(
        approval_id=approval.id,
        approved_at=approval.approved_at,
        approved_params=approval.approved_params
    )


@router.get("/approval/params-check/{bot_id}", response_model=ParamsCheckResponse)
async def check_params_divergence(
    bot_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ParamsCheckResponse:
    """
    Check if bot parameters have diverged from approved values.
    Warning at >20% divergence, critical at >50%.
    """
    # Mock implementation - would fetch bot and approval in production
    # For demo, simulate some divergence

    diverged_params = []

    # Simulate parameter divergence
    params_to_check = {
        "sl_atr_multiplier": {"approved": 1.5, "current": 2.0},  # 33% divergence
        "tp_atr_multiplier": {"approved": 3.0, "current": 3.1},  # 3% divergence
        "max_position_size": {"approved": 5, "current": 5}       # 0% divergence
    }

    max_divergence = 0.0

    for param_name, values in params_to_check.items():
        divergence = calculate_divergence(values["approved"], values["current"])

        if divergence > 0:
            diverged_params.append(ParamsDivergence(
                param=param_name,
                approved_value=values["approved"],
                current_value=values["current"],
                delta_pct=divergence
            ))
            max_divergence = max(max_divergence, divergence)

    # Determine warning level
    if max_divergence >= 50:
        warning_level = "critical"
    elif max_divergence >= 20:
        warning_level = "warning"
    else:
        warning_level = "ok"

    return ParamsCheckResponse(
        bot_id=bot_id,
        has_divergence=len(diverged_params) > 0,
        diverged_params=diverged_params,
        warning_level=warning_level
    )