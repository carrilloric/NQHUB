"""
Risk Manager REST API Endpoints (AUT-349)

Provides REST API for risk configuration and status monitoring.

Endpoints:
- GET  /risk/config   — Get risk_config for active bot
- PUT  /risk/config   — Update risk thresholds (requires bot STOPPED)
- GET  /risk/status   — Current risk status (balance, P&L, position)
- GET  /risk/events   — Historical risk events and rejections

Critical Rules:
- risk_config can ONLY be modified when bot state = STOPPED
- Attempting to update config while bot is RUNNING returns 403 Forbidden

References:
- Linear Issue: AUT-349
- Related: AUT-350 (OMS), AUT-348 (Kill Switch)
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional, List

from app.trading.risk_manager import RiskConfig


# ============= Router Setup =============

router = APIRouter(prefix="/risk", tags=["Risk Manager"])


# ============= Request/Response Models =============

class RiskConfigResponse(BaseModel):
    """Risk configuration response"""
    bot_id: str
    apex_account_size: int
    apex_max_contracts: int
    apex_trailing_threshold: int
    trailing_safety_buffer: int
    max_daily_loss: int
    max_consecutive_losses: int
    max_orders_per_minute: int
    news_blackout_minutes: int
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "bot_id": "bot_001",
                "apex_account_size": 25000,
                "apex_max_contracts": 4,
                "apex_trailing_threshold": 1500,
                "trailing_safety_buffer": 500,
                "max_daily_loss": 1000,
                "max_consecutive_losses": 5,
                "max_orders_per_minute": 10,
                "news_blackout_minutes": 5,
                "updated_at": "2024-03-15T10:30:00Z"
            }
        }


class RiskConfigUpdateRequest(BaseModel):
    """Request to update risk configuration"""
    apex_max_contracts: Optional[int] = Field(None, ge=1, le=10)
    apex_trailing_threshold: Optional[int] = Field(None, ge=500, le=5000)
    trailing_safety_buffer: Optional[int] = Field(None, ge=100, le=1000)
    max_daily_loss: Optional[int] = Field(None, ge=100, le=5000)
    max_consecutive_losses: Optional[int] = Field(None, ge=1, le=20)
    max_orders_per_minute: Optional[int] = Field(None, ge=1, le=100)
    news_blackout_minutes: Optional[int] = Field(None, ge=0, le=60)

    class Config:
        json_schema_extra = {
            "example": {
                "apex_max_contracts": 3,
                "trailing_safety_buffer": 600,
                "max_daily_loss": 800
            }
        }


class RiskStatusResponse(BaseModel):
    """Current risk status for active bot"""
    bot_id: str
    bot_state: str  # RUNNING, STOPPED, PAUSED
    account_balance: Decimal
    daily_pnl: Decimal
    current_position: int  # contracts
    apex_max_contracts: int
    trailing_threshold: Decimal
    trailing_safety_buffer: Decimal
    distance_to_threshold: Decimal  # How far from threshold
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    last_check_time: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "bot_id": "bot_001",
                "bot_state": "RUNNING",
                "account_balance": "24500.00",
                "daily_pnl": "-200.00",
                "current_position": 2,
                "apex_max_contracts": 4,
                "trailing_threshold": "1500.00",
                "trailing_safety_buffer": "500.00",
                "distance_to_threshold": "23000.00",
                "risk_level": "LOW",
                "last_check_time": "2024-03-15T14:30:00Z"
            }
        }


class RiskEventResponse(BaseModel):
    """Historical risk event record"""
    id: int
    bot_id: str
    check_name: str
    order_id: Optional[str]
    result: str  # PASSED, REJECTED
    reason: Optional[str]
    kill_switch_triggered: bool
    account_balance: Optional[Decimal]
    current_pnl: Optional[Decimal]
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "bot_id": "bot_001",
                "check_name": "daily_loss_check",
                "order_id": "ORDER-456",
                "result": "REJECTED",
                "reason": "Daily loss limit exceeded",
                "kill_switch_triggered": False,
                "account_balance": "24200.00",
                "current_pnl": "-1200.00",
                "created_at": "2024-03-15T14:25:00Z"
            }
        }


# ============= Endpoints =============

@router.get("/config", response_model=RiskConfigResponse)
async def get_risk_config(bot_id: str = Query(..., description="Bot instance ID")):
    """
    Get risk configuration for a bot.

    Returns the current risk_config JSONB from bot_instances table.

    Args:
        bot_id: Bot instance ID

    Returns:
        RiskConfigResponse with current configuration

    Raises:
        404: Bot not found
    """
    # In production, query bot_instances table
    # SELECT bot_id, risk_config, updated_at FROM bot_instances WHERE bot_id = ?

    # Mock response for now
    raise HTTPException(
        status_code=501,
        detail="Risk config retrieval not yet implemented. Requires database integration."
    )


@router.put("/config")
async def update_risk_config(
    bot_id: str = Query(..., description="Bot instance ID"),
    config: RiskConfigUpdateRequest = None,
):
    """
    Update risk configuration for a bot.

    CRITICAL: Can ONLY update config when bot state = STOPPED.
    Attempting to update while bot is RUNNING will return 403 Forbidden.

    Args:
        bot_id: Bot instance ID
        config: Updated configuration values

    Returns:
        Updated RiskConfigResponse

    Raises:
        403: Bot is RUNNING (config cannot be modified)
        404: Bot not found
    """
    # In production:
    # 1. Check bot state: SELECT state FROM bot_instances WHERE bot_id = ?
    # 2. If state != 'STOPPED', return 403 Forbidden
    # 3. Update risk_config JSONB: UPDATE bot_instances SET risk_config = jsonb_set(...)
    # 4. Return updated config

    # Mock response for now
    raise HTTPException(
        status_code=501,
        detail="Risk config update not yet implemented. Requires database integration."
    )


@router.get("/status", response_model=RiskStatusResponse)
async def get_risk_status(bot_id: str = Query(..., description="Bot instance ID")):
    """
    Get current risk status for a bot.

    Returns real-time status including:
    - Account balance
    - Daily P&L
    - Current position (contracts)
    - Distance to trailing threshold
    - Risk level assessment

    Args:
        bot_id: Bot instance ID

    Returns:
        RiskStatusResponse with current status

    Raises:
        404: Bot not found
    """
    # In production:
    # 1. Query bot_instances for bot state and config
    # 2. Query account balance from account_manager
    # 3. Calculate daily P&L from trades table
    # 4. Get current position from positions table
    # 5. Calculate risk level based on thresholds

    # Mock response for now
    raise HTTPException(
        status_code=501,
        detail="Risk status retrieval not yet implemented. Requires database integration."
    )


@router.get("/events", response_model=List[RiskEventResponse])
async def get_risk_events(
    bot_id: str = Query(..., description="Bot instance ID"),
    limit: int = Query(100, ge=1, le=1000, description="Max events to return"),
    result_filter: Optional[str] = Query(None, description="Filter by result (PASSED, REJECTED)"),
):
    """
    Get historical risk events for a bot.

    Returns events from risk_events table, including:
    - Order rejections
    - Check results
    - Kill switch activations

    Args:
        bot_id: Bot instance ID
        limit: Maximum events to return (default 100)
        result_filter: Optional filter by result (PASSED or REJECTED)

    Returns:
        List of RiskEventResponse records

    Raises:
        404: Bot not found
    """
    # In production:
    # SELECT * FROM risk_events
    # WHERE bot_id = ?
    # AND (result = ? OR ? IS NULL)
    # ORDER BY created_at DESC
    # LIMIT ?

    # Mock response for now
    raise HTTPException(
        status_code=501,
        detail="Risk events retrieval not yet implemented. Requires database integration."
    )


# ============= Helper Functions =============

def calculate_risk_level(
    balance: Decimal,
    trailing_threshold: Decimal,
    safety_buffer: Decimal,
) -> str:
    """
    Calculate risk level based on distance to trailing threshold.

    Levels:
    - LOW: balance > threshold + 3x buffer
    - MEDIUM: balance > threshold + buffer
    - HIGH: balance > threshold + 0.5x buffer
    - CRITICAL: balance <= threshold + 0.5x buffer

    Args:
        balance: Current account balance
        trailing_threshold: Trailing threshold amount
        safety_buffer: Safety buffer amount

    Returns:
        Risk level string
    """
    distance = balance - trailing_threshold

    if distance > (3 * safety_buffer):
        return "LOW"
    elif distance > safety_buffer:
        return "MEDIUM"
    elif distance > (safety_buffer / 2):
        return "HIGH"
    else:
        return "CRITICAL"
