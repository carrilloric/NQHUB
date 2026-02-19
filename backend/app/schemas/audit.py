"""
Audit Schemas

Pydantic schemas for audit report generation and validation.
"""
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class AuditOrderBlocksRequest(BaseModel):
    """Request to generate Order Blocks audit report"""
    symbol: str = Field(..., example="NQZ5")
    timeframe: str = Field(..., example="5min")
    snapshot_time: datetime = Field(..., example="2025-11-24T14:30:00", description="Snapshot timestamp (UTC)")


class OrderBlockAuditItem(BaseModel):
    """Single Order Block for audit validation"""
    ob_id: int
    ob_type: str  # BULLISH OB, BEARISH OB, STRONG BULLISH OB, STRONG BEARISH OB
    formation_time_est: str  # Formatted: "Nov 6, 2025 05:20:00 EST"
    formation_time_utc: str  # For reference
    zone_low: float
    zone_high: float
    body_midpoint: float
    range_midpoint: float
    status: str  # ACTIVE, TESTED, BROKEN
    quality: str  # HIGH, MEDIUM, LOW
    impulse_move: float
    impulse_direction: str  # UP, DOWN
    candle_direction: str  # BULLISH, BEARISH
    ob_open: float
    ob_close: float
    ob_volume: float


class AuditOrderBlocksResponse(BaseModel):
    """Response with Order Blocks audit report"""
    report_markdown: str  # Markdown formatted report
    total_obs: int  # Total ACTIVE OBs at snapshot
    snapshot_time_est: str  # Formatted: "Nov 24, 2025 09:30:00 EST"
    snapshot_time_utc: str
    symbol: str
    timeframe: str
    order_blocks: List[OrderBlockAuditItem]  # Full data for programmatic access
