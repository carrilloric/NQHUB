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
    """Single Liquidity Pool response - represents LP as a rectangle"""
    lp_id: int
    symbol: str
    timeframe: str
    formation_time: datetime
    pool_type: str  # EQH, EQL, TH, TL, SWING_HIGH, SWING_LOW, ASH, ASL, LSH, LSL, NYH, NYL
    level: float
    zone_low: Optional[float] = None  # Rectangle bottom (for EQH/EQL)
    zone_high: Optional[float] = None  # Rectangle top (for EQH/EQL)
    tolerance: float
    touch_times: Optional[List[datetime]]
    num_touches: int
    total_volume: Optional[float]
    strength: str  # STRONG, NORMAL, WEAK
    status: str  # UNMITIGATED, RESPECTED, SWEPT, MITIGATED
    created_at: datetime

    # Rectangle representation fields (computed from touch_times)
    start_time: Optional[datetime] = None  # Rectangle start (first touch)
    end_time: Optional[datetime] = None    # Rectangle end (last touch)
    liquidity_type: Optional[str] = None   # "Buy-Side Liquidity" or "Sell-Side Liquidity"
    zone_size: Optional[float] = None      # Rectangle height in points

    # Modal level fields (ICT-aligned representation)
    modal_level: Optional[float] = None    # The price level with most touches
    modal_touches: Optional[int] = None    # Number of touches at modal level
    spread: Optional[float] = None         # Dispersion around modal (in pts)

    # Ranking and freshness fields
    importance_score: Optional[float] = None  # Composite ranking metric
    time_freshness: Optional[float] = None    # Hours since last touch
    distance_to_current_price: Optional[float] = None  # Distance in points from current price

    # Sweep detection (ICT lifecycle)
    sweep_status: Optional[str] = None  # INTACT or SWEPT
    sweep_criteria_met: Optional[int] = None  # Number of criteria met (0-3)

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
    ob_body_midpoint: float  # 50% of body (open+close)/2
    ob_range_midpoint: float  # 50% of range (high+low)/2
    impulse_move: float
    impulse_direction: str  # UP, DOWN
    candle_direction: str  # BULLISH, BEARISH
    quality: str  # HIGH, MEDIUM, LOW
    status: str  # ACTIVE, TESTED, BROKEN
    created_at: datetime

    # Lifecycle tracking fields
    last_checked_time: Optional[datetime] = None
    last_checked_candle_time: Optional[datetime] = None

    # Test interaction tracking
    test_count: int = 0
    test_times: Optional[List[datetime]] = None

    # Option 1: Edge touch (price touches OB boundary)
    first_touch_edge_time: Optional[datetime] = None
    first_touch_edge_price: Optional[float] = None

    # Option 2: Midpoint touch (price reaches 50% level)
    first_touch_midpoint_time: Optional[datetime] = None
    first_touch_midpoint_price: Optional[float] = None

    # Option 3: Entry without close (candle enters zone but doesn't close inside)
    first_entry_no_close_time: Optional[datetime] = None
    first_entry_candle_close: Optional[float] = None

    # BROKEN state tracking
    broken_time: Optional[datetime] = None
    broken_candle_close: Optional[float] = None

    # Penetration metrics
    max_penetration_pts: float = 0.0
    max_penetration_pct: float = 0.0

    class Config:
        from_attributes = True


class OrderBlockGenerationResponse(BaseModel):
    """Response from Order Block generation endpoint"""
    total: int
    breakdown: dict  # {BULLISH_OB: 6, BEARISH_OB: 7, ...}
    auto_parameters: dict  # {min_impulse: 18.5, strong_threshold: 28, ...}
    order_blocks: List[OrderBlockResponse]
    text_report: str  # Markdown formatted report


class OrderBlockStateUpdateRequest(BaseModel):
    """Request to update Order Block states"""
    symbol: str = Field(..., example="NQZ5")
    timeframe: str = Field(default="5min", example="5min")
    up_to_time: datetime = Field(..., example="2025-11-24T16:00:00")


class OrderBlockStateUpdateResponse(BaseModel):
    """Response from Order Block state update endpoint"""
    total_checked: int
    tested: int
    broken: int
    message: str


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


# ============================================================================
# Market State Schemas
# ============================================================================

class MarketStateGenerateRequest(BaseModel):
    """Request to generate market state snapshots"""
    symbol: str = Field(..., example="NQZ5")
    start_time: datetime = Field(..., example="2025-11-24T09:00:00")
    end_time: datetime = Field(..., example="2025-11-24T16:00:00")
    interval_minutes: int = Field(default=5, ge=1, le=60, example=5)


class TimeframeSummary(BaseModel):
    """Summary for a single timeframe"""
    active_fvgs_count: int
    active_lps_count: int
    active_obs_count: int
    bullish_count: int
    bearish_count: int


class TimeframeData(BaseModel):
    """Complete data for a single timeframe"""
    summary: TimeframeSummary
    active_fvgs: List[FVGResponse]
    active_session_levels: List[LiquidityPoolResponse]
    active_obs: List[OrderBlockResponse]


class MarketStateSummary(BaseModel):
    """Overall market state summary across all timeframes"""
    total_patterns_all_timeframes: int
    by_timeframe: dict  # {"30s": 3, "1min": 8, "5min": 12, ...}


class MarketStateDetailResponse(BaseModel):
    """Detailed market state response with full pattern data for all timeframes"""
    snapshot_time: datetime
    snapshot_time_est: str  # Formatted display: "2025-11-24 04:30:00 EST"
    symbol: str
    summary: MarketStateSummary
    timeframes: dict  # {"30s": TimeframeData, "1min": TimeframeData, ...}

    class Config:
        json_schema_extra = {
            "example": {
                "snapshot_time": "2025-11-24T09:30:00",
                "snapshot_time_est": "2025-11-24 04:30:00 EST",
                "symbol": "NQZ5",
                "summary": {
                    "total_patterns_all_timeframes": 95,
                    "by_timeframe": {
                        "30s": 3,
                        "1min": 8,
                        "5min": 12,
                        "15min": 10,
                        "30min": 15,
                        "1hr": 18,
                        "4hr": 12,
                        "daily": 8,
                        "weekly": 4
                    }
                },
                "timeframes": {
                    "5min": {
                        "summary": {
                            "active_fvgs_count": 5,
                            "active_lps_count": 3,
                            "active_obs_count": 4,
                            "bullish_count": 6,
                            "bearish_count": 6
                        },
                        "active_fvgs": [],
                        "active_session_levels": [],
                        "active_obs": []
                    }
                }
            }
        }


class MarketStateSnapshotInfo(BaseModel):
    """Basic snapshot information without full pattern details"""
    snapshot_time: datetime
    snapshot_time_est: str
    total_patterns: int
    by_timeframe: dict


class MarketStateGenerateResponse(BaseModel):
    """Response after generating snapshots"""
    job_id: str
    total_snapshots: int
    symbol: str
    start_time: datetime
    end_time: datetime
    snapshots: List[MarketStateSnapshotInfo]
