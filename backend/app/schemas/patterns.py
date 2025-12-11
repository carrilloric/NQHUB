"""
Pattern Detection Schemas

Pydantic schemas for API requests and responses for FVGs, Liquidity Pools, and Order Blocks.
"""
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# FVG Schemas
# ============================================================================

class FVGDetectionRequest(BaseModel):
    """Request to detect Fair Value Gaps"""
    symbol: str = Field(..., example="NQZ5")
    start_date: date = Field(..., example="2025-11-24")
    end_date: date = Field(..., example="2025-11-25")
    timeframe: str = Field(default="5min", example="5min")


class FVGResponse(BaseModel):
    """Single FVG response"""
    fvg_id: int
    symbol: str
    timeframe: str
    formation_time: datetime
    fvg_type: str  # BULLISH, BEARISH
    fvg_start: float
    fvg_end: float
    gap_size: float
    midpoint: float
    vela1_high: float
    vela1_low: float
    vela3_high: float
    vela3_low: float
    significance: str  # MICRO, SMALL, MEDIUM, LARGE, EXTREME

    # ICT-specific fields
    premium_level: Optional[float] = None  # High boundary
    discount_level: Optional[float] = None  # Low boundary
    consequent_encroachment: Optional[float] = None  # 50% level
    displacement_score: Optional[float] = None  # Energetic movement score
    has_break_of_structure: Optional[bool] = None  # BOS detection

    status: str  # UNMITIGATED, REDELIVERED, REBALANCED
    last_checked_time: Optional[datetime] = None  # Last time FVG state was checked
    created_at: datetime

    class Config:
        from_attributes = True


class FVGGenerationResponse(BaseModel):
    """Response from FVG generation endpoint"""
    total: int
    auto_parameters: dict  # {min_gap_size: float, ...}
    state_update_stats: Optional[dict] = None  # {total_checked: int, redelivered: int, rebalanced: int}
    fvgs: List[FVGResponse]
    text_report: str  # Markdown formatted report


# ============================================================================
# Liquidity Pool Schemas
# ============================================================================

class LiquidityPoolDetectionRequest(BaseModel):
    """Request to detect Liquidity Pools"""
    symbol: str = Field(..., example="NQZ5")
    date_val: date = Field(..., example="2025-11-20", alias="date")
    timeframe: str = Field(default="5min", example="5min")
    pool_types: Optional[List[str]] = Field(
        default=None,
        example=["EQH", "EQL", "SESSION"],
        description="Optional filter: EQH, EQL, TH, TL, SWING_HIGH, SWING_LOW, ASH, ASL, LSH, LSL, NYH, NYL"
    )


class LiquidityPoolResponse(BaseModel):
    """Single Liquidity Pool response"""
    lp_id: int
    symbol: str
    timeframe: str
    formation_time: datetime
    pool_type: str  # EQH, EQL, TH, TL, SWING_HIGH, SWING_LOW, ASH, ASL, LSH, LSL, NYH, NYL
    level: float
    tolerance: float
    touch_times: Optional[List[datetime]]
    num_touches: int
    total_volume: Optional[float]
    strength: str  # STRONG, NORMAL, WEAK
    status: str  # UNMITIGATED, RESPECTED, SWEPT, MITIGATED
    created_at: datetime

    class Config:
        from_attributes = True


class LiquidityPoolGenerationResponse(BaseModel):
    """Response from Liquidity Pool generation endpoint"""
    total: int
    breakdown: dict  # {EQH: 3, EQL: 2, NYH: 1, ...}
    auto_parameters: dict  # {tolerance: 10, ...}
    pools: List[LiquidityPoolResponse]
    text_report: str  # Markdown formatted report


# ============================================================================
# Order Block Schemas
# ============================================================================

class OrderBlockDetectionRequest(BaseModel):
    """Request to detect Order Blocks"""
    symbol: str = Field(..., example="NQZ5")
    start_date: date = Field(..., example="2025-11-24")
    end_date: date = Field(..., example="2025-11-24")
    timeframe: str = Field(default="5min", example="5min")


class OrderBlockResponse(BaseModel):
    """Single Order Block response"""
    ob_id: int
    symbol: str
    timeframe: str
    formation_time: datetime
    ob_type: str  # BULLISH OB, BEARISH OB, STRONG BULLISH OB, STRONG BEARISH OB
    ob_high: float
    ob_low: float
    ob_open: float
    ob_close: float
    ob_volume: float
    impulse_move: float
    impulse_direction: str  # UP, DOWN
    candle_direction: str  # BULLISH, BEARISH
    quality: str  # HIGH, MEDIUM, LOW
    status: str  # ACTIVE, TESTED, BROKEN
    created_at: datetime

    class Config:
        from_attributes = True


class OrderBlockGenerationResponse(BaseModel):
    """Response from Order Block generation endpoint"""
    total: int
    breakdown: dict  # {BULLISH_OB: 6, BEARISH_OB: 7, ...}
    auto_parameters: dict  # {min_impulse: 18.5, strong_threshold: 28, ...}
    order_blocks: List[OrderBlockResponse]
    text_report: str  # Markdown formatted report


# ============================================================================
# Pattern Interaction Schemas
# ============================================================================

class PatternInteractionResponse(BaseModel):
    """Single Pattern Interaction response"""
    interaction_id: int
    pattern_type: str  # FVG, LP, OB
    pattern_id: int
    interaction_time: datetime
    interaction_type: str  # R0_CLEAN_BOUNCE, R1_SHALLOW_TOUCH, P4_FALSE_BREAKOUT, etc.
    penetration_pts: float
    penetration_pct: float
    confidence: float
    candle_high: float
    candle_low: float
    candle_close: float
    created_at: datetime

    class Config:
        from_attributes = True


class PatternInteractionsResponse(BaseModel):
    """Response for pattern interactions endpoint"""
    total: int
    breakdown: dict  # {R0: 0, R1: 6, R2: 8, P1: 0, ...}
    interactions: List[PatternInteractionResponse]
    text_report: str  # Markdown formatted interaction history


# ============================================================================
# List/Query Schemas
# ============================================================================

class PatternListRequest(BaseModel):
    """Request for listing patterns"""
    symbol: str
    timeframe: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    # Type-specific filters
    quality: Optional[str] = None  # For OBs: HIGH, MEDIUM, LOW
    strength: Optional[str] = None  # For LPs: STRONG, NORMAL, WEAK
    significance: Optional[str] = None  # For FVGs: MICRO, SMALL, MEDIUM, LARGE, EXTREME
    status: Optional[str] = None  # For all: varies by type


class FVGListResponse(BaseModel):
    """Response for FVG list endpoint"""
    total: int
    fvgs: List[FVGResponse]


class LiquidityPoolListResponse(BaseModel):
    """Response for LP list endpoint"""
    total: int
    pools: List[LiquidityPoolResponse]


class OrderBlockListResponse(BaseModel):
    """Response for OB list endpoint"""
    total: int
    order_blocks: List[OrderBlockResponse]
