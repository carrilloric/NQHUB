"""
Trade Journal API endpoints - Post-trade analysis and EOD reports (AUT-351)

Manages trade lifecycle:
1. Calculate trades from bracket orders (match entry/exit by bracket_id)
2. Persist trades with P&L calculations
3. Allow annotations (notes and tags)
4. Generate EOD reports with performance metrics
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal
import pandas as pd

from app.core.database import get_async_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.production import Order, Trade, BotInstance
from app.research.metrics.performance import PerformanceMetrics

router = APIRouter()

# ==================== Request/Response Models ====================

class TradeAnnotation(BaseModel):
    """Partial update for notes and tags only"""
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class TradeResponse(BaseModel):
    """Trade details response"""
    id: UUID
    bot_id: UUID
    strategy_id: UUID
    entry_order_id: Optional[UUID]
    exit_order_id: Optional[UUID]
    direction: Optional[str]
    entry_price: Optional[Decimal]
    exit_price: Optional[Decimal]
    quantity: Optional[int]
    pnl_ticks: Optional[int]
    pnl_usd: Optional[Decimal]
    commission: Optional[Decimal]
    notes: Optional[str]
    tags: List[str]
    opened_at: Optional[datetime]
    closed_at: Optional[datetime]

    class Config:
        from_attributes = True


class CalculateTradesRequest(BaseModel):
    """Request to calculate trades from bracket orders"""
    bracket_ids: Optional[List[UUID]] = Field(None, description="Specific bracket IDs to process. If None, process all unprocessed brackets.")
    start_date: Optional[date] = Field(None, description="Start date filter for orders")
    end_date: Optional[date] = Field(None, description="End date filter for orders")


class CalculateTradesResponse(BaseModel):
    """Response from trade calculation"""
    trades_created: int
    trades_updated: int
    brackets_processed: int
    errors: List[str] = []


class EODReportRequest(BaseModel):
    """Request for end of day report"""
    report_date: date
    bot_id: Optional[UUID] = None
    strategy_id: Optional[UUID] = None


class EODReportResponse(BaseModel):
    """End of day report with performance metrics"""
    report_date: date
    total_trades: int
    total_pnl_usd: Decimal
    total_pnl_ticks: int
    win_rate: float
    profit_factor: float
    avg_win_usd: float
    avg_loss_usd: float
    expectancy_usd: float
    sharpe_ratio: Optional[float]
    sortino_ratio: Optional[float]
    max_drawdown_pct: Optional[float]
    max_drawdown_usd: Optional[float]
    trades: List[TradeResponse]


# ==================== Helper Functions ====================

async def calculate_pnl(entry_order: Order, exit_order: Order) -> tuple[int, Decimal, str]:
    """
    Calculate P&L for NQ futures trade

    Returns:
        (pnl_ticks, pnl_usd, direction)
    """
    # NQ constants
    TICK_SIZE = 0.25
    TICK_VALUE = 5.0

    if not entry_order.fill_price or not exit_order.fill_price:
        raise ValueError("Both orders must have fill prices")

    # Determine direction
    if entry_order.side.upper() == "BUY":
        direction = "LONG"
        price_diff = float(exit_order.fill_price) - float(entry_order.fill_price)
    else:
        direction = "SHORT"
        price_diff = float(entry_order.fill_price) - float(exit_order.fill_price)

    # Calculate ticks
    pnl_ticks = int(round(price_diff / TICK_SIZE))

    # Calculate USD
    pnl_usd = Decimal(str(pnl_ticks * TICK_VALUE))

    return pnl_ticks, pnl_usd, direction


async def find_bracket_orders(
    db: AsyncSession,
    bracket_id: UUID
) -> Dict[str, Optional[Order]]:
    """
    Find all orders in a bracket (entry, stop loss, take profit)

    Returns:
        Dict with 'entry', 'stop_loss', 'take_profit' keys
    """
    result = await db.execute(
        select(Order).where(Order.bracket_id == bracket_id)
    )
    orders = result.scalars().all()

    bracket_orders = {
        'entry': None,
        'stop_loss': None,
        'take_profit': None,
        'exit': None  # Whichever fired (SL or TP)
    }

    for order in orders:
        if order.type.upper() == "MARKET" and order.status == "FILLED":
            bracket_orders['entry'] = order
        elif order.type.upper() == "STOP" and order.status == "FILLED":
            bracket_orders['stop_loss'] = order
            bracket_orders['exit'] = order
        elif order.type.upper() == "LIMIT" and order.status == "FILLED":
            bracket_orders['take_profit'] = order
            bracket_orders['exit'] = order

    return bracket_orders


async def create_trade_from_bracket(
    db: AsyncSession,
    bracket_id: UUID
) -> Optional[Trade]:
    """
    Create or update trade from bracket orders

    Returns:
        Trade object or None if incomplete bracket
    """
    orders = await find_bracket_orders(db, bracket_id)

    entry = orders['entry']
    exit_order = orders['exit']

    if not entry or not exit_order:
        # Incomplete bracket - skip
        return None

    # Check if trade already exists
    result = await db.execute(
        select(Trade).where(
            or_(
                Trade.entry_order_id == entry.id,
                Trade.exit_order_id == exit_order.id
            )
        )
    )
    existing_trade = result.scalar_one_or_none()

    # Calculate P&L
    pnl_ticks, pnl_usd, direction = await calculate_pnl(entry, exit_order)

    # Estimate commission (standard NQ commission)
    commission = Decimal("4.50")  # $2.25 per side x 2 sides

    if existing_trade:
        # Update existing trade
        existing_trade.entry_order_id = entry.id
        existing_trade.exit_order_id = exit_order.id
        existing_trade.entry_price = entry.fill_price
        existing_trade.exit_price = exit_order.fill_price
        existing_trade.quantity = entry.quantity
        existing_trade.pnl_ticks = pnl_ticks
        existing_trade.pnl_usd = pnl_usd
        existing_trade.commission = commission
        existing_trade.direction = direction
        existing_trade.opened_at = entry.filled_at
        existing_trade.closed_at = exit_order.filled_at

        await db.commit()
        await db.refresh(existing_trade)
        return existing_trade
    else:
        # Create new trade
        trade = Trade(
            bot_id=entry.bot_id,
            strategy_id=entry.bot.strategy_id,
            entry_order_id=entry.id,
            exit_order_id=exit_order.id,
            entry_price=entry.fill_price,
            exit_price=exit_order.fill_price,
            quantity=entry.quantity,
            pnl_ticks=pnl_ticks,
            pnl_usd=pnl_usd,
            commission=commission,
            direction=direction,
            opened_at=entry.filled_at,
            closed_at=exit_order.filled_at
        )

        db.add(trade)
        await db.commit()
        await db.refresh(trade)
        return trade


# ==================== Endpoints ====================

@router.get("/trades", response_model=List[TradeResponse])
async def list_trades(
    bot_id: Optional[UUID] = None,
    strategy_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    List trades with optional filters
    """
    query = select(Trade)

    # Apply filters
    filters = []
    if bot_id:
        filters.append(Trade.bot_id == bot_id)
    if strategy_id:
        filters.append(Trade.strategy_id == strategy_id)
    if start_date:
        filters.append(Trade.closed_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        filters.append(Trade.closed_at <= datetime.combine(end_date, datetime.max.time()))

    if filters:
        query = query.where(and_(*filters))

    query = query.order_by(Trade.closed_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    trades = result.scalars().all()

    return trades


@router.post("/calculate", response_model=CalculateTradesResponse)
async def calculate_trades(
    request: CalculateTradesRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate and persist trades from bracket orders

    Matches entry/exit orders by bracket_id and calculates P&L
    """
    # Find bracket IDs to process
    query = select(Order.bracket_id).distinct()

    filters = [Order.bracket_id.isnot(None)]

    if request.bracket_ids:
        filters.append(Order.bracket_id.in_(request.bracket_ids))

    if request.start_date:
        filters.append(Order.submitted_at >= datetime.combine(request.start_date, datetime.min.time()))

    if request.end_date:
        filters.append(Order.submitted_at <= datetime.combine(request.end_date, datetime.max.time()))

    query = query.where(and_(*filters))

    result = await db.execute(query)
    bracket_ids = [row[0] for row in result.all()]

    trades_created = 0
    trades_updated = 0
    errors = []

    for bracket_id in bracket_ids:
        try:
            trade = await create_trade_from_bracket(db, bracket_id)
            if trade:
                if trade.id:  # Check if it's an existing trade
                    # Simple heuristic: if all fields match, it was likely just created
                    trades_created += 1
                else:
                    trades_updated += 1
        except Exception as e:
            errors.append(f"Bracket {bracket_id}: {str(e)}")

    return CalculateTradesResponse(
        trades_created=trades_created,
        trades_updated=trades_updated,
        brackets_processed=len(bracket_ids),
        errors=errors
    )


@router.get("/trades/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get single trade by ID
    """
    result = await db.execute(
        select(Trade).where(Trade.id == trade_id)
    )
    trade = result.scalar_one_or_none()

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    return trade


@router.patch("/trades/{trade_id}/annotations", response_model=TradeResponse)
async def update_trade_annotations(
    trade_id: UUID,
    annotation: TradeAnnotation,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update trade notes and tags (partial update only)

    Does NOT replace entire trade, only updates notes and tags fields
    """
    result = await db.execute(
        select(Trade).where(Trade.id == trade_id)
    )
    trade = result.scalar_one_or_none()

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    # Update only provided fields
    if annotation.notes is not None:
        trade.notes = annotation.notes

    if annotation.tags is not None:
        trade.tags = annotation.tags

    await db.commit()
    await db.refresh(trade)

    return trade


@router.post("/eod-report", response_model=EODReportResponse)
async def generate_eod_report(
    request: EODReportRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate End of Day report with performance metrics

    Uses PerformanceMetrics class for calculations
    """
    # Fetch trades for the date
    start_datetime = datetime.combine(request.report_date, datetime.min.time())
    end_datetime = datetime.combine(request.report_date, datetime.max.time())

    query = select(Trade).where(
        and_(
            Trade.closed_at >= start_datetime,
            Trade.closed_at <= end_datetime
        )
    )

    if request.bot_id:
        query = query.where(Trade.bot_id == request.bot_id)

    if request.strategy_id:
        query = query.where(Trade.strategy_id == request.strategy_id)

    query = query.order_by(Trade.closed_at)

    result = await db.execute(query)
    trades = result.scalars().all()

    if not trades:
        return EODReportResponse(
            report_date=request.report_date,
            total_trades=0,
            total_pnl_usd=Decimal("0"),
            total_pnl_ticks=0,
            win_rate=0.0,
            profit_factor=0.0,
            avg_win_usd=0.0,
            avg_loss_usd=0.0,
            expectancy_usd=0.0,
            trades=[]
        )

    # Prepare data for PerformanceMetrics
    trade_data = []
    for trade in trades:
        trade_data.append({
            'pnl_usd': float(trade.pnl_usd) if trade.pnl_usd else 0.0,
            'pnl_ticks': trade.pnl_ticks or 0,
            'closed_at': trade.closed_at
        })

    df = pd.DataFrame(trade_data)

    # Calculate equity curve
    df['equity'] = df['pnl_usd'].cumsum()
    equity_curve = pd.Series(df['equity'].values, index=df['closed_at'])

    # Calculate metrics using PerformanceMetrics
    metrics_calculator = PerformanceMetrics()
    report = metrics_calculator.calculate_all(
        equity_curve=equity_curve,
        trades=df,
        n_trials=1,
        risk_free_rate=0.0,
        periods_per_year=252
    )

    return EODReportResponse(
        report_date=request.report_date,
        total_trades=report.total_trades,
        total_pnl_usd=Decimal(str(report.total_pnl_usd)),
        total_pnl_ticks=report.total_pnl_ticks,
        win_rate=report.win_rate,
        profit_factor=report.profit_factor,
        avg_win_usd=report.avg_win_usd,
        avg_loss_usd=report.avg_loss_usd,
        expectancy_usd=report.expectancy_usd,
        sharpe_ratio=report.sharpe_ratio if report.sharpe_ratio != 0 else None,
        sortino_ratio=report.sortino_ratio if report.sortino_ratio != 0 else None,
        max_drawdown_pct=report.max_drawdown_pct,
        max_drawdown_usd=report.max_drawdown_usd,
        trades=[TradeResponse.from_orm(t) for t in trades]
    )
