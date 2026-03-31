"""
API routes for kill switch management.

Provides endpoints for:
- Activating kill switch (per-bot or global)
- Checking bot status
- Resuming halted bots
- Viewing kill switch event history
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.auth import get_current_user
from app.trading.kill_switch import KillSwitchActor, BotStatus
from app.trading.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from app.models.user import User
import logging

# Initialize router
router = APIRouter(prefix="/bots", tags=["kill-switch"])

# Logger
logger = logging.getLogger(__name__)


# Request/Response schemas
class KillSwitchRequest(BaseModel):
    """Request to activate kill switch."""
    reason: str = Field(..., description="Reason for activation")
    force: bool = Field(default=False, description="Force kill even if already halted")


class GlobalKillRequest(BaseModel):
    """Request to activate global kill switch."""
    reason: str = Field(..., description="Reason for global kill")
    confirm: bool = Field(..., description="Confirmation flag (must be true)")


class ResumeRequest(BaseModel):
    """Request to resume a halted bot."""
    manual_confirmation: bool = Field(..., description="Manual confirmation required")
    reason: str = Field(default="", description="Reason for resuming")


class BotStatusResponse(BaseModel):
    """Bot status response."""
    bot_id: str
    status: str
    halted_at: Optional[datetime] = None
    halt_reason: Optional[str] = None
    kill_scope: Optional[str] = None
    positions_count: int = 0
    pending_orders_count: int = 0


class KillEventResponse(BaseModel):
    """Kill switch event response."""
    id: int
    bot_id: Optional[str]
    scope: str
    reason: str
    triggered_by: str
    circuit_breaker_type: Optional[str]
    positions_closed: int
    orders_cancelled: int
    created_at: datetime


class CircuitBreakerStatusResponse(BaseModel):
    """Circuit breaker status response."""
    bot_id: str
    enabled: bool
    max_daily_loss: float
    max_consecutive_losses: int
    trailing_threshold_buffer: float
    max_orders_per_minute: int


# Dependency to get kill switch actor
def get_kill_switch_actor(db: Session = Depends(get_db)) -> KillSwitchActor:
    """Get or create kill switch actor instance."""
    # In production, this would be a singleton or injected service
    # For now, create a new instance
    from app.core.messaging import get_message_bus
    from app.services.execution import get_execution_client

    msgbus = get_message_bus()
    execution_client = get_execution_client()

    return KillSwitchActor(
        logger=logger,
        msgbus=msgbus,
        execution_client=execution_client,
        db_session=db
    )


# Dependency to get circuit breaker
def get_circuit_breaker(
    db: Session = Depends(get_db),
    kill_switch: KillSwitchActor = Depends(get_kill_switch_actor)
) -> CircuitBreaker:
    """Get or create circuit breaker instance."""
    return CircuitBreaker(
        logger=logger,
        kill_switch_actor=kill_switch,
        db_session=db
    )


@router.post("/{bot_id}/kill", response_model=dict)
async def activate_bot_kill(
    bot_id: str,
    request: KillSwitchRequest,
    current_user: User = Depends(get_current_user),
    kill_switch: KillSwitchActor = Depends(get_kill_switch_actor)
):
    """
    Activate kill switch for a specific bot.

    Flattens all positions, cancels pending orders, and marks bot as HALTED.

    Args:
        bot_id: Bot identifier
        request: Kill switch request with reason

    Returns:
        Success message with details

    Raises:
        HTTPException: If bot not found or operation fails
    """
    # Check if user has permission (trader or admin)
    if current_user.role not in ["admin", "trader"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only traders and admins can activate kill switch"
        )

    try:
        # Check bot status first
        current_status = kill_switch.get_bot_status(bot_id)
        if not current_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bot {bot_id} not found"
            )

        if current_status == BotStatus.HALTED and not request.force:
            return {
                "message": f"Bot {bot_id} already HALTED",
                "status": "already_halted",
                "bot_id": bot_id
            }

        # Activate kill switch
        await kill_switch.activate_bot_kill(
            bot_id=bot_id,
            reason=f"Manual: {request.reason} (by {current_user.email})"
        )

        logger.info(f"Kill switch activated for bot {bot_id} by {current_user.email}")

        return {
            "message": f"Kill switch activated for bot {bot_id}",
            "status": "success",
            "bot_id": bot_id,
            "reason": request.reason,
            "activated_by": current_user.email,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to activate kill switch for bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate kill switch: {str(e)}"
        )


@router.post("/kill-all", response_model=dict)
async def activate_global_kill(
    request: GlobalKillRequest,
    current_user: User = Depends(get_current_user),
    kill_switch: KillSwitchActor = Depends(get_kill_switch_actor)
):
    """
    Activate global kill switch for ALL active bots.

    WARNING: This will halt ALL running bots immediately.

    Args:
        request: Global kill request with confirmation

    Returns:
        Success message with affected bots count

    Raises:
        HTTPException: If not confirmed or operation fails
    """
    # Only admins can trigger global kill
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can activate global kill switch"
        )

    # Require explicit confirmation
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Global kill requires explicit confirmation (confirm=true)"
        )

    try:
        # Activate global kill
        await kill_switch.activate_global_kill(
            reason=f"Global: {request.reason} (by {current_user.email})"
        )

        logger.warning(f"GLOBAL KILL SWITCH activated by {current_user.email}")

        return {
            "message": "Global kill switch activated for ALL bots",
            "status": "success",
            "reason": request.reason,
            "activated_by": current_user.email,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to activate global kill switch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate global kill switch: {str(e)}"
        )


@router.get("/{bot_id}/status", response_model=BotStatusResponse)
async def get_bot_status(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    kill_switch: KillSwitchActor = Depends(get_kill_switch_actor),
    db: Session = Depends(get_db)
):
    """
    Get current status of a bot.

    Args:
        bot_id: Bot identifier

    Returns:
        Bot status information

    Raises:
        HTTPException: If bot not found
    """
    from app.models.bot_instance import BotInstance

    # Get bot from database
    bot = db.query(BotInstance).filter(BotInstance.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot {bot_id} not found"
        )

    # Get current status
    status = kill_switch.get_bot_status(bot_id)

    return BotStatusResponse(
        bot_id=bot_id,
        status=status or "UNKNOWN",
        halted_at=bot.halted_at if hasattr(bot, 'halted_at') else None,
        halt_reason=bot.halt_reason if hasattr(bot, 'halt_reason') else None,
        kill_scope=bot.kill_scope if hasattr(bot, 'kill_scope') else None,
        positions_count=len(bot.positions) if hasattr(bot, 'positions') else 0,
        pending_orders_count=len(bot.pending_orders) if hasattr(bot, 'pending_orders') else 0
    )


@router.post("/{bot_id}/resume", response_model=dict)
async def resume_bot(
    bot_id: str,
    request: ResumeRequest,
    current_user: User = Depends(get_current_user),
    kill_switch: KillSwitchActor = Depends(get_kill_switch_actor),
    circuit_breaker: CircuitBreaker = Depends(get_circuit_breaker)
):
    """
    Resume a HALTED bot after manual review.

    Requires explicit manual confirmation.

    Args:
        bot_id: Bot identifier
        request: Resume request with confirmation

    Returns:
        Success message

    Raises:
        HTTPException: If bot not found, not halted, or missing confirmation
    """
    # Check permission (trader or admin)
    if current_user.role not in ["admin", "trader"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only traders and admins can resume bots"
        )

    # Require manual confirmation
    if not request.manual_confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manual confirmation required to resume HALTED bot"
        )

    try:
        # Check current status
        current_status = kill_switch.get_bot_status(bot_id)
        if not current_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bot {bot_id} not found"
            )

        if current_status != BotStatus.HALTED:
            return {
                "message": f"Bot {bot_id} is not HALTED (status: {current_status})",
                "status": "not_halted",
                "bot_id": bot_id
            }

        # Resume bot
        await kill_switch.resume_bot(
            bot_id=bot_id,
            manual_confirmation=True,
            confirmed_by=current_user.email
        )

        # Reset circuit breaker triggers
        circuit_breaker.reset_triggered_breakers(bot_id)

        logger.info(f"Bot {bot_id} resumed by {current_user.email}")

        return {
            "message": f"Bot {bot_id} resumed successfully",
            "status": "success",
            "bot_id": bot_id,
            "resumed_by": current_user.email,
            "reason": request.reason,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to resume bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume bot: {str(e)}"
        )


@router.get("/events", response_model=List[KillEventResponse])
async def get_kill_events(
    bot_id: Optional[str] = None,
    scope: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get kill switch event history.

    Args:
        bot_id: Filter by bot ID
        scope: Filter by scope (per_bot or global)
        limit: Maximum number of events to return

    Returns:
        List of kill switch events
    """
    from app.models.kill_switch import KillSwitchEventModel

    query = db.query(KillSwitchEventModel)

    if bot_id:
        query = query.filter(KillSwitchEventModel.bot_id == bot_id)

    if scope:
        query = query.filter(KillSwitchEventModel.scope == scope)

    events = query.order_by(
        KillSwitchEventModel.created_at.desc()
    ).limit(limit).all()

    return [
        KillEventResponse(
            id=event.id,
            bot_id=event.bot_id,
            scope=event.scope,
            reason=event.reason,
            triggered_by=event.triggered_by,
            circuit_breaker_type=event.circuit_breaker_type,
            positions_closed=event.positions_closed,
            orders_cancelled=event.orders_cancelled,
            created_at=event.created_at
        )
        for event in events
    ]


@router.get("/{bot_id}/circuit-breakers", response_model=CircuitBreakerStatusResponse)
async def get_circuit_breaker_config(
    bot_id: str,
    current_user: User = Depends(get_current_user),
    circuit_breaker: CircuitBreaker = Depends(get_circuit_breaker)
):
    """
    Get circuit breaker configuration for a bot.

    Args:
        bot_id: Bot identifier

    Returns:
        Circuit breaker configuration
    """
    config = circuit_breaker.get_config_from_bot(bot_id)

    return CircuitBreakerStatusResponse(
        bot_id=bot_id,
        enabled=config.enabled,
        max_daily_loss=config.max_daily_loss,
        max_consecutive_losses=config.max_consecutive_losses,
        trailing_threshold_buffer=config.trailing_threshold_buffer,
        max_orders_per_minute=config.max_orders_per_minute
    )


@router.put("/{bot_id}/circuit-breakers", response_model=dict)
async def update_circuit_breaker_config(
    bot_id: str,
    config: CircuitBreakerConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update circuit breaker configuration for a bot.

    Args:
        bot_id: Bot identifier
        config: New configuration

    Returns:
        Success message
    """
    # Only admins and traders can update config
    if current_user.role not in ["admin", "trader"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only traders and admins can update circuit breaker config"
        )

    from app.models.bot_instance import BotInstance

    # Get bot
    bot = db.query(BotInstance).filter(BotInstance.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot {bot_id} not found"
        )

    # Update risk_config JSONB field
    if not bot.risk_config:
        bot.risk_config = {}

    bot.risk_config.update({
        "circuit_breakers_enabled": config.enabled,
        "max_daily_loss": config.max_daily_loss,
        "max_consecutive_losses": config.max_consecutive_losses,
        "trailing_threshold_buffer": config.trailing_threshold_buffer,
        "max_orders_per_minute": config.max_orders_per_minute
    })

    db.commit()

    logger.info(f"Circuit breaker config updated for bot {bot_id} by {current_user.email}")

    return {
        "message": f"Circuit breaker configuration updated for bot {bot_id}",
        "status": "success",
        "bot_id": bot_id,
        "updated_by": current_user.email
    }


# Health check endpoint
@router.get("/kill-switch/health", response_model=dict)
async def health_check():
    """
    Health check for kill switch system.

    Returns:
        System status
    """
    return {
        "status": "healthy",
        "service": "kill-switch",
        "timestamp": datetime.utcnow().isoformat()
    }