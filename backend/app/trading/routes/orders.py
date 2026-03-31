"""
Order Management REST API Endpoints (AUT-350)

GET /orders                  — List with filters: bot_id, status, date
GET /orders/{id}             — Detail + bracket children
GET /orders/pending          — PENDING_SUBMIT or SUBMITTED
GET /orders/active-brackets  — Entry filled, TP/SL pending
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Path, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.production import Order
from app.trading.order_manager import OrderStatus

router = APIRouter()


# Pydantic models for request/response
class OrderResponse(BaseModel):
    """Order response schema"""
    id: str
    bot_id: str
    client_order_id: str
    broker_order_id: Optional[str] = None
    bracket_role: Optional[str] = None
    parent_order_id: Optional[str] = None
    symbol: str
    side: str
    order_type: str
    contracts: int
    price: Optional[float] = None
    fill_price: Optional[float] = None
    fill_time: Optional[datetime] = None
    status: str
    gross_pnl: Optional[float] = None
    net_pnl: Optional[float] = None
    commission: Optional[float] = None
    rejection_reason: Optional[str] = None
    submitted_at: datetime
    cancelled_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderDetailResponse(OrderResponse):
    """Order detail with bracket children"""
    children: List[OrderResponse] = Field(default_factory=list)


class BracketOrderResponse(BaseModel):
    """Active bracket order group"""
    entry_order: OrderResponse
    tp_order: OrderResponse
    sl_order: OrderResponse


@router.get("/orders", response_model=List[OrderResponse])
async def list_orders(
    bot_id: Optional[str] = Query(None, description="Filter by bot ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    from_date: Optional[datetime] = Query(None, description="Filter from date (submitted_at)"),
    to_date: Optional[datetime] = Query(None, description="Filter to date (submitted_at)"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """
    List orders with optional filters.

    Supports filtering by:
    - bot_id: UUID of bot instance
    - status: Order status (PENDING_SUBMIT, SUBMITTED, FILLED, etc.)
    - from_date/to_date: Date range filter on submitted_at
    """
    query = select(Order)

    # Apply filters
    filters = []
    if bot_id:
        filters.append(Order.bot_id == UUID(bot_id))
    if status:
        filters.append(Order.status == status)
    if from_date:
        filters.append(Order.submitted_at >= from_date)
    if to_date:
        filters.append(Order.submitted_at <= to_date)

    if filters:
        query = query.where(and_(*filters))

    # Order by submitted_at DESC (most recent first)
    query = query.order_by(Order.submitted_at.desc())

    # Pagination
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    orders = result.scalars().all()

    return [
        OrderResponse(
            id=str(order.id),
            bot_id=str(order.bot_id),
            client_order_id=order.client_order_id,
            broker_order_id=order.broker_order_id,
            bracket_role=order.bracket_role,
            parent_order_id=str(order.parent_order_id) if order.parent_order_id else None,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            contracts=order.contracts,
            price=float(order.price) if order.price else None,
            fill_price=float(order.fill_price) if order.fill_price else None,
            fill_time=order.fill_time,
            status=order.status,
            gross_pnl=float(order.gross_pnl) if order.gross_pnl else None,
            net_pnl=float(order.net_pnl) if order.net_pnl else None,
            commission=float(order.commission) if order.commission else None,
            rejection_reason=order.rejection_reason,
            submitted_at=order.submitted_at,
            cancelled_at=order.cancelled_at,
            updated_at=order.updated_at
        )
        for order in orders
    ]


@router.get("/orders/{order_id}", response_model=OrderDetailResponse)
async def get_order_detail(
    order_id: str = Path(..., description="Order UUID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get order detail including bracket children.

    If order is an ENTRY order, includes TP and SL children.
    If order is TP/SL, shows parent_order_id.
    """
    # Fetch order
    query = select(Order).where(Order.id == UUID(order_id))
    result = await db.execute(query)
    order = result.scalars().first()

    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

    # Build base response
    order_response = OrderResponse(
        id=str(order.id),
        bot_id=str(order.bot_id),
        client_order_id=order.client_order_id,
        broker_order_id=order.broker_order_id,
        bracket_role=order.bracket_role,
        parent_order_id=str(order.parent_order_id) if order.parent_order_id else None,
        symbol=order.symbol,
        side=order.side,
        order_type=order.order_type,
        contracts=order.contracts,
        price=float(order.price) if order.price else None,
        fill_price=float(order.fill_price) if order.fill_price else None,
        fill_time=order.fill_time,
        status=order.status,
        gross_pnl=float(order.gross_pnl) if order.gross_pnl else None,
        net_pnl=float(order.net_pnl) if order.net_pnl else None,
        commission=float(order.commission) if order.commission else None,
        rejection_reason=order.rejection_reason,
        submitted_at=order.submitted_at,
        cancelled_at=order.cancelled_at,
        updated_at=order.updated_at
    )

    # If ENTRY order, fetch children
    children = []
    if order.bracket_role == 'ENTRY':
        child_query = select(Order).where(Order.parent_order_id == order.id)
        child_result = await db.execute(child_query)
        child_orders = child_result.scalars().all()

        children = [
            OrderResponse(
                id=str(child.id),
                bot_id=str(child.bot_id),
                client_order_id=child.client_order_id,
                broker_order_id=child.broker_order_id,
                bracket_role=child.bracket_role,
                parent_order_id=str(child.parent_order_id) if child.parent_order_id else None,
                symbol=child.symbol,
                side=child.side,
                order_type=child.order_type,
                contracts=child.contracts,
                price=float(child.price) if child.price else None,
                fill_price=float(child.fill_price) if child.fill_price else None,
                fill_time=child.fill_time,
                status=child.status,
                gross_pnl=float(child.gross_pnl) if child.gross_pnl else None,
                net_pnl=float(child.net_pnl) if child.net_pnl else None,
                commission=float(child.commission) if child.commission else None,
                rejection_reason=child.rejection_reason,
                submitted_at=child.submitted_at,
                cancelled_at=child.cancelled_at,
                updated_at=child.updated_at
            )
            for child in child_orders
        ]

    return OrderDetailResponse(**order_response.dict(), children=children)


@router.get("/orders/pending", response_model=List[OrderResponse])
async def list_pending_orders(
    bot_id: Optional[str] = Query(None, description="Filter by bot ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    List pending orders (PENDING_SUBMIT or SUBMITTED).

    Used by kill switch to find orders that need to be cancelled.
    """
    query = select(Order).where(
        or_(
            Order.status == OrderStatus.PENDING_SUBMIT,
            Order.status == OrderStatus.SUBMITTED
        )
    )

    if bot_id:
        query = query.where(Order.bot_id == UUID(bot_id))

    query = query.order_by(Order.submitted_at.desc())

    result = await db.execute(query)
    orders = result.scalars().all()

    return [
        OrderResponse(
            id=str(order.id),
            bot_id=str(order.bot_id),
            client_order_id=order.client_order_id,
            broker_order_id=order.broker_order_id,
            bracket_role=order.bracket_role,
            parent_order_id=str(order.parent_order_id) if order.parent_order_id else None,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            contracts=order.contracts,
            price=float(order.price) if order.price else None,
            fill_price=float(order.fill_price) if order.fill_price else None,
            fill_time=order.fill_time,
            status=order.status,
            gross_pnl=float(order.gross_pnl) if order.gross_pnl else None,
            net_pnl=float(order.net_pnl) if order.net_pnl else None,
            commission=float(order.commission) if order.commission else None,
            rejection_reason=order.rejection_reason,
            submitted_at=order.submitted_at,
            cancelled_at=order.cancelled_at,
            updated_at=order.updated_at
        )
        for order in orders
    ]


@router.get("/orders/active-brackets", response_model=List[BracketOrderResponse])
async def list_active_brackets(
    bot_id: Optional[str] = Query(None, description="Filter by bot ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    List active bracket orders.

    Returns bracket groups where:
    - Entry order is FILLED
    - TP/SL orders are PENDING_SUBMIT or SUBMITTED (not yet filled)

    Used for monitoring open positions.
    """
    # Find filled entry orders
    entry_query = select(Order).where(
        and_(
            Order.bracket_role == 'ENTRY',
            Order.status == OrderStatus.FILLED
        )
    )

    if bot_id:
        entry_query = entry_query.where(Order.bot_id == UUID(bot_id))

    entry_result = await db.execute(entry_query)
    entry_orders = entry_result.scalars().all()

    brackets = []
    for entry in entry_orders:
        # Fetch TP and SL children
        child_query = select(Order).where(Order.parent_order_id == entry.id)
        child_result = await db.execute(child_query)
        children = child_result.scalars().all()

        # Find TP and SL
        tp_order = next((c for c in children if c.bracket_role == 'TP'), None)
        sl_order = next((c for c in children if c.bracket_role == 'SL'), None)

        # Only include if both TP and SL are pending/submitted (not filled/cancelled)
        if tp_order and sl_order:
            tp_active = tp_order.status in [OrderStatus.PENDING_SUBMIT, OrderStatus.SUBMITTED, OrderStatus.ACCEPTED]
            sl_active = sl_order.status in [OrderStatus.PENDING_SUBMIT, OrderStatus.SUBMITTED, OrderStatus.ACCEPTED]

            if tp_active or sl_active:
                brackets.append(
                    BracketOrderResponse(
                        entry_order=OrderResponse(
                            id=str(entry.id),
                            bot_id=str(entry.bot_id),
                            client_order_id=entry.client_order_id,
                            broker_order_id=entry.broker_order_id,
                            bracket_role=entry.bracket_role,
                            parent_order_id=None,
                            symbol=entry.symbol,
                            side=entry.side,
                            order_type=entry.order_type,
                            contracts=entry.contracts,
                            price=float(entry.price) if entry.price else None,
                            fill_price=float(entry.fill_price) if entry.fill_price else None,
                            fill_time=entry.fill_time,
                            status=entry.status,
                            gross_pnl=None,
                            net_pnl=None,
                            commission=None,
                            rejection_reason=entry.rejection_reason,
                            submitted_at=entry.submitted_at,
                            cancelled_at=entry.cancelled_at,
                            updated_at=entry.updated_at
                        ),
                        tp_order=OrderResponse(
                            id=str(tp_order.id),
                            bot_id=str(tp_order.bot_id),
                            client_order_id=tp_order.client_order_id,
                            broker_order_id=tp_order.broker_order_id,
                            bracket_role=tp_order.bracket_role,
                            parent_order_id=str(tp_order.parent_order_id),
                            symbol=tp_order.symbol,
                            side=tp_order.side,
                            order_type=tp_order.order_type,
                            contracts=tp_order.contracts,
                            price=float(tp_order.price) if tp_order.price else None,
                            fill_price=float(tp_order.fill_price) if tp_order.fill_price else None,
                            fill_time=tp_order.fill_time,
                            status=tp_order.status,
                            gross_pnl=float(tp_order.gross_pnl) if tp_order.gross_pnl else None,
                            net_pnl=float(tp_order.net_pnl) if tp_order.net_pnl else None,
                            commission=float(tp_order.commission) if tp_order.commission else None,
                            rejection_reason=tp_order.rejection_reason,
                            submitted_at=tp_order.submitted_at,
                            cancelled_at=tp_order.cancelled_at,
                            updated_at=tp_order.updated_at
                        ),
                        sl_order=OrderResponse(
                            id=str(sl_order.id),
                            bot_id=str(sl_order.bot_id),
                            client_order_id=sl_order.client_order_id,
                            broker_order_id=sl_order.broker_order_id,
                            bracket_role=sl_order.bracket_role,
                            parent_order_id=str(sl_order.parent_order_id),
                            symbol=sl_order.symbol,
                            side=sl_order.side,
                            order_type=sl_order.order_type,
                            contracts=sl_order.contracts,
                            price=float(sl_order.price) if sl_order.price else None,
                            fill_price=float(sl_order.fill_price) if sl_order.fill_price else None,
                            fill_time=sl_order.fill_time,
                            status=sl_order.status,
                            gross_pnl=float(sl_order.gross_pnl) if sl_order.gross_pnl else None,
                            net_pnl=float(sl_order.net_pnl) if sl_order.net_pnl else None,
                            commission=float(sl_order.commission) if sl_order.commission else None,
                            rejection_reason=sl_order.rejection_reason,
                            submitted_at=sl_order.submitted_at,
                            cancelled_at=sl_order.cancelled_at,
                            updated_at=sl_order.updated_at
                        )
                    )
                )

    return brackets
