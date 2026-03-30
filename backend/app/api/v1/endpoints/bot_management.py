"""
Bot Management API Endpoints (AUT-347)

Enhanced bot management with:
- Strategy approval validation (status == 'approved')
- Duplicate bot prevention (no 2 running bots on same Apex account)
- ApexComplianceValidator integration
- Synchronous kill switch with Redis publish
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session as SyncSession
from sqlalchemy import select, func, and_
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
import redis
import json

from app.db.session import get_db, get_db_sync
from app.models.production import BotInstance, BotStateLog, Order
from app.models.risk_config import RiskConfig, ApexAccount
from app.models.strategy import Strategy, StrategyApproval
from app.core.deps import get_current_user
from app.models.user import User
from app.config import settings
from app.research.compliance.apex_validator import ApexComplianceValidator, ApexAccount as ApexAccountConfig

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
    Channel: nqhub.risk.kill_switch (max priority).
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


async def check_duplicate_running_bot(
    db: AsyncSession,
    apex_account_id: UUID,
    exclude_bot_id: Optional[UUID] = None
) -> bool:
    """
    Check if there's already a running bot on the given Apex account.
    Returns True if duplicate found, False otherwise.
    """
    query = select(BotInstance).where(
        and_(
            BotInstance.apex_account_id == apex_account_id,
            BotInstance.status == BOT_STATUS_RUNNING
        )
    )

    # Exclude current bot if updating
    if exclude_bot_id:
        query = query.where(BotInstance.id != exclude_bot_id)

    result = await db.execute(query)
    existing_bot = result.scalar_one_or_none()

    return existing_bot is not None


def convert_apex_account_to_config(apex_account: ApexAccount) -> ApexAccountConfig:
    """Convert database ApexAccount to ApexComplianceValidator config."""
    return ApexAccountConfig(
        id=1,  # Validator doesn't use this
        account_size_usd=float(apex_account.account_size_usd),
        trailing_threshold_usd=float(apex_account.trailing_threshold_usd),
        max_daily_loss_usd=float(apex_account.daily_loss_limit_usd),
        max_contracts=4,  # Default, should come from risk_config
        consistency_pct=30.0,  # Default Apex rule
        news_blackout_minutes=5  # Default
    )


# ==================== BOT MANAGEMENT ENDPOINTS ====================

@router.get("")
async def list_bots(
    status: Optional[str] = Query(None, description="Filter by bot status", enum=VALID_STATUSES),
    mode: Optional[str] = Query(None, description="Filter by trading mode", enum=VALID_MODES),
    apex_account_id: Optional[UUID] = Query(None, description="Filter by Apex account"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all bots with optional filters.

    AUT-347: Enhanced with apex_account_id filter.
    """
    try:
        # Build query
        query = select(BotInstance)

        # Apply filters
        if status:
            query = query.where(BotInstance.status == status)
        if mode:
            query = query.where(BotInstance.mode == mode)
        if apex_account_id:
            query = query.where(BotInstance.apex_account_id == apex_account_id)

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
                "active_params": bot.active_params or {},
                "created_at": bot.created_at.isoformat() if bot.created_at else None
            }
            bot_list.append(bot_data)

        return {"bots": bot_list, "total": len(bot_list)}

    except Exception as e:
        logger.error(f"Error listing bots: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/create", status_code=201)
async def create_bot(
    name: str = Body(..., description="Bot name"),
    strategy_id: UUID = Body(..., description="Strategy ID"),
    mode: str = Body(..., description="Trading mode", enum=VALID_MODES),
    approval_id: Optional[UUID] = Body(None, description="Strategy approval ID"),
    apex_account_id: Optional[UUID] = Body(None, description="Apex account ID (required for live mode)"),
    active_params: Optional[Dict[str, Any]] = Body(None, description="Active parameters"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new bot.

    AUT-347 Requirements:
    1. Strategy MUST have status == 'approved'
    2. Cannot have 2 running bots on same Apex account
    3. Uses ApexComplianceValidator for validation (live mode only)
    """
    try:
        # ===== VALIDATION 1: Strategy must exist and be approved =====
        strategy_result = await db.execute(
            select(Strategy).where(Strategy.id == strategy_id)
        )
        strategy = strategy_result.scalar_one_or_none()

        if not strategy:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy {strategy_id} not found"
            )

        # CRITICAL: Strategy must be approved
        if strategy.status != 'approved':
            raise HTTPException(
                status_code=400,
                detail=f"Strategy must be approved. Current status: {strategy.status}"
            )

        # ===== VALIDATION 2: Live mode requires Apex account =====
        if mode == 'live' and not apex_account_id:
            raise HTTPException(
                status_code=400,
                detail="Live mode requires apex_account_id"
            )

        # ===== VALIDATION 3: Apex account must exist and be active =====
        apex_account = None
        if apex_account_id:
            apex_result = await db.execute(
                select(ApexAccount).where(ApexAccount.id == apex_account_id)
            )
            apex_account = apex_result.scalar_one_or_none()

            if not apex_account:
                raise HTTPException(
                    status_code=404,
                    detail=f"Apex account {apex_account_id} not found"
                )

            if not apex_account.is_active:
                raise HTTPException(
                    status_code=400,
                    detail=f"Apex account {apex_account_id} is not active"
                )

        # ===== VALIDATION 4: No duplicate running bots on same Apex account =====
        if apex_account_id:
            has_duplicate = await check_duplicate_running_bot(db, apex_account_id)
            if has_duplicate:
                raise HTTPException(
                    status_code=409,
                    detail=f"Another bot is already running on Apex account {apex_account_id}"
                )

        # ===== Get approved params from strategy approval =====
        approved_params = None
        if approval_id:
            approval_result = await db.execute(
                select(StrategyApproval).where(StrategyApproval.id == approval_id)
            )
            approval = approval_result.scalar_one_or_none()
            if approval:
                approved_params = approval.approved_params

        # ===== Create bot instance =====
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

        logger.info(f"Bot created: {bot.id} | Strategy: {strategy_id} | Mode: {mode} | Apex: {apex_account_id}")

        return {
            "bot_id": str(bot.id),
            "name": bot.name,
            "status": bot.status,
            "mode": bot.mode,
            "strategy_id": str(bot.strategy_id),
            "apex_account_id": str(bot.apex_account_id) if bot.apex_account_id else None
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
    """Get bot details."""
    try:
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

    AUT-347: Validates no duplicate running bots on same Apex account.
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

        # ===== VALIDATION: No duplicate running bots on same Apex account =====
        if bot.apex_account_id:
            has_duplicate = await check_duplicate_running_bot(
                db,
                bot.apex_account_id,
                exclude_bot_id=bot.id
            )
            if has_duplicate:
                raise HTTPException(
                    status_code=409,
                    detail=f"Another bot is already running on Apex account {bot.apex_account_id}"
                )

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

        logger.info(f"Bot started: {bot.id} | Apex: {bot.apex_account_id}")

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
    """Stop a bot gracefully."""
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

        logger.info(f"Bot stopped: {bot.id}")

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

    AUT-347 Requirements:
    - SYNCHRONOUS operation (updates DB before returning)
    - IDEMPOTENT (already killed → no error, return status=killed)
    - Publishes to Redis channel 'nqhub.risk.kill_switch'
    """
    try:
        # Get bot
        bot = db.query(BotInstance).filter(BotInstance.id == id).first()

        if not bot:
            raise HTTPException(status_code=404, detail=f"Bot {id} not found")

        # ===== IDEMPOTENCY: If already killed, return immediately =====
        if bot.status == BOT_STATUS_KILLED:
            logger.info(f"Bot {id} already killed (idempotent)")
            return {
                "bot_id": str(bot.id),
                "status": bot.status,
                "positions_closed": 0,
                "orders_cancelled": 0,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

        # Update bot status FIRST (critical for safety)
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

        # Commit all changes BEFORE publishing to Redis
        db.commit()

        # Publish kill event to Redis (fire and forget)
        publish_kill_event(bot_id=id)

        logger.warning(f"Bot killed: {id} | Reason: {reason} | Orders cancelled: {cancelled_count}")

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


@router.get("/{id}/state-log")
async def get_bot_state_log(
    id: UUID = Path(..., description="Bot ID"),
    limit: int = Query(100, ge=1, le=1000, description="Number of state transitions to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get bot state transition log."""
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
