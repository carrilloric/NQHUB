"""
Live Trading API Pydantic Schemas (AUT-364)
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class KillRequest(BaseModel):
    """Kill switch request - reason is MANDATORY (no default)"""
    reason: str = Field(..., description="MANDATORY reason for kill switch", min_length=10)


class BotStatusResponse(BaseModel):
    """Bot status with halt_reason"""
    bot_id: str
    strategy_id: str  
    status: str
    mode: str
    apex_account_id: str
    halt_reason: Optional[str] = None
    started_at: Optional[datetime] = None
    created_at: datetime


class OrderResponse(BaseModel):
    """Order response with bracket_role"""
    id: str
    bot_id: str
    order_type: str
    bracket_role: Optional[str] = None  # 'ENTRY' | 'TP' | 'SL'
    side: str
    contracts: int
    status: str
    submitted_at: datetime


class RiskStatusResponse(BaseModel):
    """Risk status with trailing_threshold_remaining calculation"""
    bot_id: str
    account_balance: float
    trailing_threshold: float
    trailing_threshold_remaining: float = Field(
        ..., 
        description="Distance to threshold = balance - threshold (CRITICAL)"
    )
    daily_pnl: float
    apex_compliant: bool
