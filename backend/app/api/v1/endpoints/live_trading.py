"""
Live Trading API Endpoints

Implementation of CONTRACT-004 Live Trading API specification.
Safety-critical endpoints for bot management, orders, and risk control.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session as SyncSession
from sqlalchemy import select, func, update, and_, or_
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4, UUID
import logging
import redis
import json

from app.db.session import get_db, get_db_sync
from app.models.production import BotInstance, BotStateLog, Order, Trade
from app.models.risk_config import RiskConfig, ApexAccount
from app.models.strategy import Strategy, StrategyApproval
from app.core.deps import get_current_user
from app.models.user import User
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Redis client for publishing kill switch events
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)

# Bot statuses
BOT_STATUS_STOPPED = 'stopped'
BOT_STATUS_RUNNING = 'running'
BOT_STATUS_KILLED = 'killed'
BOT_STATUS_ERROR = 'error'

VALID_STATUSES = [BOT_STATUS_STOPPED, BOT_STATUS_RUNNING, BOT_STATUS_KILLED, BOT_STATUS_ERROR]
VALID_MODES = ['live', 'paper', 'simulation']


# ==================== HELPER FUNCTIONS ====================

def log_state_transition(db: SyncSession, bot_id: UUID, from_status: str, to_status: str, reason: str):
    """
    Log bot state transition to bot_state_log table.
    Must be called within a database transaction.
    """
    state_log = BotStateLog(
        bot_id=bot_id,
        from_status=from_status,
        to_status=to_status,
        reason=reason
    )
    db.add(state_log)
    return state_log


def publish_kill_event(bot_id: Optional[UUID] = None, kill_all: bool = False):
    """
    Publish kill switch event to Redis for NautilusTrader to consume.
    This is fire-and-forget - endpoint doesn't depend on engine running.
    """
    try:
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'kill_all': kill_all
        }
        if bot_id:
            event['bot_id'] = str(bot_id)

        redis_client.publish('nqhub.risk.kill_switch', json.dumps(event))
        logger.info(f"Published kill switch event: {event}")
    except Exception as e:
        # Log but don't fail the endpoint if Redis is down
        logger.error(f"Failed to publish kill switch event: {str(e)}")


def exclude_sensitive_fields(apex_account: ApexAccount) -> dict:
    """
    Convert ApexAccount to dict excluding rithmic_credentials.
    """
    # NEVER include rithmic_credentials in the response
    return {
        "id": str(apex_account.id),
        "account_name": apex_account.account_name,
        "account_size_usd": float(apex_account.account_size_usd),
        "trailing_threshold_usd": float(apex_account.trailing_threshold_usd),
        "daily_loss_limit_usd": float(apex_account.daily_loss_limit_usd),
        "is_active": apex_account.is_active,
        "created_at": apex_account.created_at.isoformat() if apex_account.created_at else None
    }


# ==================== BOT MANAGEMENT ENDPOINTS ====================

@router.get("")
async def list_bots(
    status: Optional[str] = Query(None, description="Filter by bot status", enum=VALID_STATUSES),
    mode: Optional[str] = Query(None, description="Filter by trading mode", enum=VALID_MODES),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all bots.

    Implements GET /api/v1/bots from CONTRACT-004.
    """
    try:
        # Build query
        query = select(BotInstance)

        # Apply filters
        if status:
            query = query.where(BotInstance.status == status)
        if mode:
            query = query.where(BotInstance.mode == mode)

        # Order by last heartbeat
        query = query.order_by(BotInstance.last_heartbeat.desc().nullslast())

        # Execute query
        result = await db.execute(query)
        bots = result.scalars().all()

        # Format response
        bot_list = []
        for bot in bots:
            bot_data = {
                "id": str(bot.id),
                "name": bot.name,
                "strategy_id": str(bot.strategy_id) if bot.strategy_id else None,
                "status": bot.status,
                "mode": bot.mode,
                "last_heartbeat": bot.last_heartbeat.isoformat() if bot.last_heartbeat else None,
                "apex_account_id": str(bot.apex_account_id) if bot.apex_account_id else None,
                "active_params": bot.active_params or {}
            }
            bot_list.append(bot_data)

        return {"bots": bot_list}

    except Exception as e:
        logger.error(f"Error listing bots: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/create", status_code=201)
async def create_bot(
    name: str = Body(..., description="Bot name"),
    strategy_id: UUID = Body(..., description="Strategy ID"),
    mode: str = Body(..., description="Trading mode", enum=VALID_MODES),
    approval_id: Optional[UUID] = Body(None, description="Strategy approval ID"),
    apex_account_id: Optional[UUID] = Body(None, description="Apex account ID"),
    active_params: Optional[Dict[str, Any]] = Body(None, description="Active parameters"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new bot.

    Implements POST /api/v1/bots/create from CONTRACT-004.
    Copies approved_params from strategy_approvals if approval_id provided.
    """
    try:
        # Verify strategy exists
        strategy_result = await db.execute(
            select(Strategy).where(Strategy.id == strategy_id)
        )
        strategy = strategy_result.scalar_one_or_none()
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

        # If approval_id provided, copy approved params
        approved_params = None
        if approval_id:
            approval_result = await db.execute(
                select(StrategyApproval).where(StrategyApproval.id == approval_id)
            )
            approval = approval_result.scalar_one_or_none()
            if approval:
                approved_params = approval.approved_params

        # Create bot instance
        bot = BotInstance(
            name=name,
            strategy_id=strategy_id,
            approval_id=approval_id,
            apex_account_id=apex_account_id,
            mode=mode,
            status=BOT_STATUS_STOPPED,
            approved_params=approved_params,
            active_params=active_params or approved_params,
            last_heartbeat=None
        )
        db.add(bot)

        # Log initial state
        state_log = BotStateLog(
            bot_id=bot.id,
            from_status=None,
            to_status=BOT_STATUS_STOPPED,
            reason="Bot created"
        )
        db.add(state_log)

        await db.commit()
        await db.refresh(bot)

        return {
            "bot_id": str(bot.id),
            "status": bot.status
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating bot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}")
async def get_bot(
    id: UUID = Path(..., description="Bot ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get bot details.

    Implements GET /api/v1/bots/{id} from CONTRACT-004.
    """
    try:
        # Get bot with relationships
        result = await db.execute(
            select(BotInstance).where(BotInstance.id == id)
        )
        bot = result.scalar_one_or_none()

        if not bot:
            raise HTTPException(status_code=404, detail=f"Bot {id} not found")

        return {
            "id": str(bot.id),
            "name": bot.name,
            "strategy_id": str(bot.strategy_id) if bot.strategy_id else None,
            "approval_id": str(bot.approval_id) if bot.approval_id else None,
            "apex_account_id": str(bot.apex_account_id) if bot.apex_account_id else None,
            "mode": bot.mode,
            "status": bot.status,
            "approved_params": bot.approved_params,
            "active_params": bot.active_params,
            "params_modified": bot.params_modified,
            "last_heartbeat": bot.last_heartbeat.isoformat() if bot.last_heartbeat else None,
            "created_at": bot.created_at.isoformat() if bot.created_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bot {id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{id}/start")
async def start_bot(
    id: UUID = Path(..., description="Bot ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a bot.

    Implements POST /api/v1/bots/{id}/start from CONTRACT-004.
    """
    try:
        # Get bot
        result = await db.execute(
            select(BotInstance).where(BotInstance.id == id)
        )
        bot = result.scalar_one_or_none()

        if not bot:
            raise HTTPException(status_code=404, detail=f"Bot {id} not found")

        if bot.status == BOT_STATUS_RUNNING:
            raise HTTPException(status_code=409, detail="Bot is already running")

        if bot.status == BOT_STATUS_KILLED:
            raise HTTPException(status_code=409, detail="Cannot start a killed bot")

        # Update bot status
        old_status = bot.status
        bot.status = BOT_STATUS_RUNNING
        bot.last_heartbeat = datetime.utcnow()

        # Log state transition
        state_log = BotStateLog(
            bot_id=bot.id,
            from_status=old_status,
            to_status=BOT_STATUS_RUNNING,
            reason="Bot started by user"
        )
        db.add(state_log)

        await db.commit()
        await db.refresh(bot)

        return {
            "bot_id": str(bot.id),
            "status": bot.status,
            "last_heartbeat": bot.last_heartbeat.isoformat() if bot.last_heartbeat else None
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error starting bot {id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{id}/stop")
async def stop_bot(
    id: UUID = Path(..., description="Bot ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stop a bot gracefully.

    Implements POST /api/v1/bots/{id}/stop from CONTRACT-004.
    """
    try:
        # Get bot
        result = await db.execute(
            select(BotInstance).where(BotInstance.id == id)
        )
        bot = result.scalar_one_or_none()

        if not bot:
            raise HTTPException(status_code=404, detail=f"Bot {id} not found")

        if bot.status == BOT_STATUS_STOPPED:
            # Already stopped, idempotent
            return {
                "bot_id": str(bot.id),
                "status": bot.status,
                "last_heartbeat": bot.last_heartbeat.isoformat() if bot.last_heartbeat else None
            }

        # Update bot status
        old_status = bot.status
        bot.status = BOT_STATUS_STOPPED
        bot.last_heartbeat = datetime.utcnow()

        # Log state transition
        state_log = BotStateLog(
            bot_id=bot.id,
            from_status=old_status,
            to_status=BOT_STATUS_STOPPED,
            reason="Bot stopped by user"
        )
        db.add(state_log)

        await db.commit()
        await db.refresh(bot)

        return {
            "bot_id": str(bot.id),
            "status": bot.status,
            "last_heartbeat": bot.last_heartbeat.isoformat() if bot.last_heartbeat else None
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error stopping bot {id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ==================== KILL SWITCH ENDPOINTS (HIGHEST PRIORITY - SYNCHRONOUS) ====================

@router.post("/{id}/kill")
def kill_bot(
    id: UUID = Path(..., description="Bot ID"),
    reason: Optional[str] = Body(None, description="Reason for killing the bot"),
    close_positions: bool = Body(True, description="Whether to close all open positions"),
    db: SyncSession = Depends(get_db_sync),  # SYNCHRONOUS SESSION
    current_user: User = Depends(get_current_user)
):
    """
    Kill a bot immediately (HIGHEST PRIORITY).

    Implements POST /api/v1/bots/{id}/kill from CONTRACT-004.
    This is SYNCHRONOUS for safety - must complete database operations before returning.
    """
    try:
        # Get bot
        bot = db.query(BotInstance).filter(BotInstance.id == id).first()

        if not bot:
            raise HTTPException(status_code=404, detail=f"Bot {id} not found")

        # If already killed, return idempotently
        if bot.status == BOT_STATUS_KILLED:
            return {
                "bot_id": str(bot.id),
                "status": bot.status,
                "positions_closed": 0,
                "orders_cancelled": 0,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

        # Update bot status FIRST (critical)
        old_status = bot.status
        bot.status = BOT_STATUS_KILLED
        bot.last_heartbeat = datetime.utcnow()

        # Log state transition
        log_state_transition(
            db,
            bot.id,
            old_status,
            BOT_STATUS_KILLED,
            reason or "Emergency kill switch activated"
        )

        # Cancel all pending orders
        cancelled_count = db.query(Order).filter(
            and_(
                Order.bot_id == id,
                Order.status == 'PENDING'
            )
        ).update({'status': 'CANCELLED', 'cancelled_at': datetime.utcnow()})

        # Count open positions (would be closed by trading engine)
        positions_count = 0  # TODO: implement position tracking

        # Commit all changes
        db.commit()

        # Publish kill event to Redis (fire and forget)
        publish_kill_event(bot_id=id)

        return {
            "bot_id": str(bot.id),
            "status": bot.status,
            "positions_closed": positions_count,
            "orders_cancelled": cancelled_count,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error killing bot {id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/kill-all")
def kill_all_bots(
    reason: Optional[str] = Body(None, description="Reason for global kill"),
    close_positions: bool = Body(True, description="Whether to close all open positions"),
    confirm: Optional[str] = Body(None, description="Safety confirmation (must be 'KILL_ALL_BOTS')"),
    db: SyncSession = Depends(get_db_sync),  # SYNCHRONOUS SESSION
    current_user: User = Depends(get_current_user)
):
    """
    Kill all bots immediately (GLOBAL KILL SWITCH - HIGHEST PRIORITY).

    Implements POST /api/v1/bots/kill-all from CONTRACT-004.
    This is SYNCHRONOUS for safety - must complete all database operations before returning.
    """
    try:
        # Safety confirmation check (optional but recommended)
        if confirm and confirm != "KILL_ALL_BOTS":
            raise HTTPException(status_code=400, detail="Invalid confirmation string")

        # Get all non-killed bots
        bots_to_kill = db.query(BotInstance).filter(
            BotInstance.status != BOT_STATUS_KILLED
        ).all()

        killed_count = 0
        positions_closed_total = 0
        orders_cancelled_total = 0
        affected_bots = []

        # Kill each bot
        for bot in bots_to_kill:
            old_status = bot.status
            bot.status = BOT_STATUS_KILLED
            bot.last_heartbeat = datetime.utcnow()

            # Log state transition
            log_state_transition(
                db,
                bot.id,
                old_status,
                BOT_STATUS_KILLED,
                reason or "Global kill switch activated"
            )

            # Cancel pending orders for this bot
            cancelled = db.query(Order).filter(
                and_(
                    Order.bot_id == bot.id,
                    Order.status == 'PENDING'
                )
            ).update({'status': 'CANCELLED', 'cancelled_at': datetime.utcnow()})

            # Count positions (would be closed by trading engine)
            positions = 0  # TODO: implement position tracking

            affected_bots.append({
                "bot_id": str(bot.id),
                "positions_closed": positions,
                "orders_cancelled": cancelled
            })

            killed_count += 1
            positions_closed_total += positions
            orders_cancelled_total += cancelled

        # Commit all changes
        db.commit()

        # Publish global kill event to Redis (fire and forget)
        publish_kill_event(kill_all=True)

        return {
            "killed_count": killed_count,
            "positions_closed_total": positions_closed_total,
            "orders_cancelled_total": orders_cancelled_total,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "affected_bots": affected_bots
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in global kill switch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}/state-log")
async def get_bot_state_log(
    id: UUID = Path(..., description="Bot ID"),
    limit: int = Query(100, ge=1, le=1000, description="Number of state transitions to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get bot state transition log.

    Implements GET /api/v1/bots/{id}/state-log from CONTRACT-004.
    """
    try:
        # Verify bot exists
        bot_result = await db.execute(
            select(BotInstance).where(BotInstance.id == id)
        )
        bot = bot_result.scalar_one_or_none()

        if not bot:
            raise HTTPException(status_code=404, detail=f"Bot {id} not found")

        # Get state logs
        result = await db.execute(
            select(BotStateLog)
            .where(BotStateLog.bot_id == id)
            .order_by(BotStateLog.created_at.desc())
            .limit(limit)
        )
        state_logs = result.scalars().all()

        # Format response
        states = []
        for log in state_logs:
            states.append({
                "from": log.from_status,
                "to": log.to_status,
                "reason": log.reason,
                "timestamp": log.created_at.isoformat() if log.created_at else None
            })

        return {"states": states}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting state log for bot {id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ==================== ORDER MANAGEMENT ENDPOINTS ====================

@router.get("/orders")
async def list_orders(
    bot_id: Optional[UUID] = Query(None, description="Filter by bot ID"),
    status: Optional[str] = Query(None, description="Filter by order status"),
    start: Optional[datetime] = Query(None, description="Start date"),
    end: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(100, ge=1, le=10000, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List orders.

    Implements GET /api/v1/orders from CONTRACT-004.
    """
    try:
        # Build query
        query = select(Order)

        # Apply filters
        if bot_id:
            query = query.where(Order.bot_id == bot_id)
        if status:
            query = query.where(Order.status == status)
        if start:
            query = query.where(Order.submitted_at >= start)
        if end:
            query = query.where(Order.submitted_at <= end)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply ordering and pagination
        query = query.order_by(Order.submitted_at.desc())
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        orders = result.scalars().all()

        # Format response
        order_list = []
        for order in orders:
            order_data = {
                "id": str(order.id),
                "bot_id": str(order.bot_id) if order.bot_id else None,
                "rithmic_order_id": order.rithmic_order_id,
                "symbol": order.symbol,
                "side": order.side,
                "type": order.type,
                "quantity": order.quantity,
                "price": float(order.price) if order.price else None,
                "fill_price": float(order.fill_price) if order.fill_price else None,
                "status": order.status,
                "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
                "filled_at": order.filled_at.isoformat() if order.filled_at else None,
                "cancelled_at": order.cancelled_at.isoformat() if order.cancelled_at else None
            }
            order_list.append(order_data)

        return {
            "orders": order_list,
            "total": total
        }

    except Exception as e:
        logger.error(f"Error listing orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/orders/{id}")
async def get_order(
    id: UUID = Path(..., description="Order ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get order details.

    Implements GET /api/v1/orders/{id} from CONTRACT-004.
    """
    try:
        # Get order
        result = await db.execute(
            select(Order).where(Order.id == id)
        )
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail=f"Order {id} not found")

        return {
            "id": str(order.id),
            "bot_id": str(order.bot_id) if order.bot_id else None,
            "rithmic_order_id": order.rithmic_order_id,
            "symbol": order.symbol,
            "side": order.side,
            "type": order.type,
            "quantity": order.quantity,
            "price": float(order.price) if order.price else None,
            "fill_price": float(order.fill_price) if order.fill_price else None,
            "status": order.status,
            "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
            "filled_at": order.filled_at.isoformat() if order.filled_at else None,
            "cancelled_at": order.cancelled_at.isoformat() if order.cancelled_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order {id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/orders/pending")
async def list_pending_orders(
    bot_id: Optional[UUID] = Query(None, description="Filter by bot ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List pending orders.

    Implements GET /api/v1/orders/pending from CONTRACT-004.
    """
    try:
        # Build query for pending orders
        query = select(Order).where(Order.status == 'PENDING')

        # Apply bot filter if provided
        if bot_id:
            query = query.where(Order.bot_id == bot_id)

        # Order by submission time
        query = query.order_by(Order.submitted_at.desc())

        # Execute query
        result = await db.execute(query)
        orders = result.scalars().all()

        # Format response
        order_list = []
        for order in orders:
            order_data = {
                "id": str(order.id),
                "bot_id": str(order.bot_id) if order.bot_id else None,
                "rithmic_order_id": order.rithmic_order_id,
                "symbol": order.symbol,
                "side": order.side,
                "type": order.type,
                "quantity": order.quantity,
                "price": float(order.price) if order.price else None,
                "status": order.status,
                "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None
            }
            order_list.append(order_data)

        return {
            "orders": order_list,
            "total": len(order_list)
        }

    except Exception as e:
        logger.error(f"Error listing pending orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ==================== RISK MANAGEMENT ENDPOINTS ====================

@router.get("/risk/status")
async def get_risk_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time risk status.

    Implements GET /api/v1/risk/status from CONTRACT-004.
    """
    try:
        # Get today's trades for P&L calculation
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Calculate daily loss from trades
        trades_result = await db.execute(
            select(func.sum(Trade.pnl_usd))
            .where(Trade.closed_at >= today_start)
        )
        daily_pnl = trades_result.scalar() or 0
        daily_loss_usd = abs(daily_pnl) if daily_pnl < 0 else 0

        # Get active bot's risk config for thresholds
        active_bot_result = await db.execute(
            select(RiskConfig)
            .join(BotInstance)
            .where(BotInstance.status == BOT_STATUS_RUNNING)
            .limit(1)
        )
        risk_config = active_bot_result.scalar_one_or_none()

        # Calculate trailing drawdown proximity
        trailing_drawdown_proximity_pct = 0.0
        circuit_breaker_active = False

        if risk_config:
            # Check if we're approaching drawdown limit
            if risk_config.max_trailing_drawdown_usd > 0:
                trailing_drawdown_proximity_pct = (daily_loss_usd / float(risk_config.max_trailing_drawdown_usd)) * 100

            # Check if circuit breaker should be active
            if daily_loss_usd >= float(risk_config.max_daily_loss_usd):
                circuit_breaker_active = True

        return {
            "daily_loss_usd": float(daily_loss_usd),
            "trailing_drawdown_proximity_pct": float(trailing_drawdown_proximity_pct),
            "circuit_breaker_active": circuit_breaker_active
        }

    except Exception as e:
        logger.error(f"Error getting risk status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/risk/config")
async def get_risk_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get risk configuration.

    Implements GET /api/v1/risk/config from CONTRACT-004.
    """
    try:
        # Get risk config for active bot
        result = await db.execute(
            select(RiskConfig)
            .join(BotInstance)
            .where(BotInstance.status == BOT_STATUS_RUNNING)
            .limit(1)
        )
        risk_config = result.scalar_one_or_none()

        if not risk_config:
            # Return default config if no active bot
            return {
                "max_daily_loss_usd": 0.0,
                "max_trailing_drawdown_usd": 0.0,
                "max_contracts": 1,
                "max_orders_per_minute": 10,
                "news_blackout_minutes": 5,
                "apex_consistency_pct": 30.0
            }

        return {
            "id": str(risk_config.id),
            "bot_id": str(risk_config.bot_id) if risk_config.bot_id else None,
            "max_daily_loss_usd": float(risk_config.max_daily_loss_usd),
            "max_trailing_drawdown_usd": float(risk_config.max_trailing_drawdown_usd),
            "max_contracts": risk_config.max_contracts,
            "max_orders_per_minute": risk_config.max_orders_per_minute,
            "news_blackout_minutes": risk_config.news_blackout_minutes,
            "apex_consistency_pct": float(risk_config.apex_consistency_pct),
            "updated_at": risk_config.updated_at.isoformat() if risk_config.updated_at else None
        }

    except Exception as e:
        logger.error(f"Error getting risk config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/risk/config")
async def update_risk_config(
    max_daily_loss_usd: Optional[float] = Body(None),
    max_trailing_drawdown_usd: Optional[float] = Body(None),
    max_contracts: Optional[int] = Body(None),
    max_orders_per_minute: Optional[int] = Body(None),
    news_blackout_minutes: Optional[int] = Body(None),
    apex_consistency_pct: Optional[float] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update risk configuration.

    Implements PUT /api/v1/risk/config from CONTRACT-004.
    """
    try:
        # Get risk config for active bot
        result = await db.execute(
            select(RiskConfig)
            .join(BotInstance)
            .where(BotInstance.status == BOT_STATUS_RUNNING)
            .limit(1)
        )
        risk_config = result.scalar_one_or_none()

        if not risk_config:
            raise HTTPException(status_code=404, detail="No active bot with risk configuration found")

        # Update fields if provided
        if max_daily_loss_usd is not None:
            risk_config.max_daily_loss_usd = max_daily_loss_usd
        if max_trailing_drawdown_usd is not None:
            risk_config.max_trailing_drawdown_usd = max_trailing_drawdown_usd
        if max_contracts is not None:
            risk_config.max_contracts = max_contracts
        if max_orders_per_minute is not None:
            risk_config.max_orders_per_minute = max_orders_per_minute
        if news_blackout_minutes is not None:
            risk_config.news_blackout_minutes = news_blackout_minutes
        if apex_consistency_pct is not None:
            risk_config.apex_consistency_pct = apex_consistency_pct

        risk_config.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(risk_config)

        return {
            "id": str(risk_config.id),
            "bot_id": str(risk_config.bot_id) if risk_config.bot_id else None,
            "max_daily_loss_usd": float(risk_config.max_daily_loss_usd),
            "max_trailing_drawdown_usd": float(risk_config.max_trailing_drawdown_usd),
            "max_contracts": risk_config.max_contracts,
            "max_orders_per_minute": risk_config.max_orders_per_minute,
            "news_blackout_minutes": risk_config.news_blackout_minutes,
            "apex_consistency_pct": float(risk_config.apex_consistency_pct),
            "updated_at": risk_config.updated_at.isoformat() if risk_config.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating risk config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/risk/apex-accounts")
async def list_apex_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List Apex accounts.

    Implements GET /api/v1/risk/apex-accounts from CONTRACT-004.
    NEVER returns rithmic_credentials.
    """
    try:
        # Get all active Apex accounts
        result = await db.execute(
            select(ApexAccount)
            .where(ApexAccount.is_active == True)
            .order_by(ApexAccount.account_name)
        )
        accounts = result.scalars().all()

        # Format response, EXCLUDING rithmic_credentials
        account_list = []
        for account in accounts:
            account_list.append(exclude_sensitive_fields(account))

        return {"accounts": account_list}

    except Exception as e:
        logger.error(f"Error listing Apex accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/risk/apex-accounts")
async def add_apex_account(
    account_name: str = Body(..., description="Account name"),
    account_size_usd: float = Body(..., description="Account size in USD"),
    trailing_threshold_usd: float = Body(..., description="Trailing threshold in USD"),
    daily_loss_limit_usd: float = Body(..., description="Daily loss limit in USD"),
    rithmic_credentials: Optional[Dict[str, Any]] = Body(None, description="Encrypted Rithmic credentials"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add Apex account.

    Implements POST /api/v1/risk/apex-accounts from CONTRACT-004.
    Returns account WITHOUT rithmic_credentials.
    """
    try:
        # Create new Apex account
        account = ApexAccount(
            account_name=account_name,
            account_size_usd=account_size_usd,
            trailing_threshold_usd=trailing_threshold_usd,
            daily_loss_limit_usd=daily_loss_limit_usd,
            rithmic_credentials=rithmic_credentials,  # Store but never return
            is_active=True
        )
        db.add(account)

        await db.commit()
        await db.refresh(account)

        # Return WITHOUT rithmic_credentials
        return exclude_sensitive_fields(account)

    except Exception as e:
        await db.rollback()
        logger.error(f"Error adding Apex account: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")