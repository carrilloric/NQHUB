"""
Pattern Detection Models

SQLAlchemy ORM models for Fair Value Gaps, Liquidity Pools, Order Blocks,
and Pattern Interactions.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ARRAY, Boolean,
    Index, func, UniqueConstraint
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY, JSONB
from app.db.session import Base


class DetectedFVG(Base):
    """Fair Value Gap detected pattern"""
    __tablename__ = "detected_fvgs"

    fvg_id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    formation_time = Column(DateTime(timezone=True), nullable=False)
    fvg_type = Column(String(10), nullable=False)  # BULLISH, BEARISH
    fvg_start = Column(Float, nullable=False)
    fvg_end = Column(Float, nullable=False)
    gap_size = Column(Float, nullable=False)
    midpoint = Column(Float, nullable=False)
    vela1_high = Column(Float, nullable=False)
    vela1_low = Column(Float, nullable=False)
    vela3_high = Column(Float, nullable=False)
    vela3_low = Column(Float, nullable=False)
    significance = Column(String(10), nullable=False)  # MICRO, SMALL, MEDIUM, LARGE, EXTREME

    # ICT-specific fields
    premium_level = Column(Float, nullable=True)  # High boundary (fvg_end for BULLISH, fvg_start for BEARISH)
    discount_level = Column(Float, nullable=True)  # Low boundary (fvg_start for BULLISH, fvg_end for BEARISH)
    consequent_encroachment = Column(Float, nullable=True)  # 50% level (midpoint)
    displacement_score = Column(Float, nullable=True)  # Energetic movement score
    has_break_of_structure = Column(Boolean, nullable=True, server_default="false")  # BOS detection

    status = Column(String(20), nullable=False, server_default="UNMITIGATED")  # UNMITIGATED, REDELIVERED, REBALANCED
    last_checked_time = Column(DateTime(timezone=True), nullable=True)  # Last time FVG state was checked
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_fvgs_symbol_time', 'symbol', 'formation_time'),
        Index('idx_fvgs_status', 'status'),
    )

    def __repr__(self):
        return f"<FVG {self.fvg_type} @ {self.formation_time} gap={self.gap_size}pts>"


class DetectedLiquidityPool(Base):
    """Liquidity Pool detected pattern"""
    __tablename__ = "detected_liquidity_pools"

    lp_id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    formation_time = Column(DateTime(timezone=True), nullable=False)
    pool_type = Column(String(15), nullable=False)  # EQH, EQL, TH, TL, SWING_HIGH, SWING_LOW, ASH, ASL, LSH, LSL, NYH, NYL
    level = Column(Float, nullable=False)
    zone_low = Column(Float, nullable=True)  # For EQH/EQL pools (zones), NULL for session levels
    zone_high = Column(Float, nullable=True)  # For EQH/EQL pools (zones), NULL for session levels
    tolerance = Column(Float, nullable=False, server_default="10.0")
    touch_times = Column(PG_ARRAY(DateTime(timezone=True)))
    num_touches = Column(Integer, nullable=False, server_default="1")
    total_volume = Column(Float)
    strength = Column(String(10), nullable=False)  # STRONG, NORMAL, WEAK
    status = Column(String(20), nullable=False, server_default="UNMITIGATED")  # UNMITIGATED, RESPECTED, SWEPT, MITIGATED
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_lps_symbol_time', 'symbol', 'formation_time'),
        Index('idx_lps_type', 'pool_type'),
        Index('idx_lps_status', 'status'),
    )

    def __repr__(self):
        return f"<LP {self.pool_type} @ {self.level} touches={self.num_touches}>"


class DetectedOrderBlock(Base):
    """Order Block detected pattern"""
    __tablename__ = "detected_order_blocks"

    ob_id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    formation_time = Column(DateTime(timezone=True), nullable=False)
    ob_type = Column(String(20), nullable=False)  # BULLISH OB, BEARISH OB, STRONG BULLISH OB, STRONG BEARISH OB
    ob_high = Column(Float, nullable=False)
    ob_low = Column(Float, nullable=False)
    ob_open = Column(Float, nullable=False)
    ob_close = Column(Float, nullable=False)
    ob_volume = Column(Float, nullable=False)
    ob_body_midpoint = Column(Float, nullable=False)  # 50% of body (open+close)/2
    ob_range_midpoint = Column(Float, nullable=False)  # 50% of range (high+low)/2
    impulse_move = Column(Float, nullable=False)
    impulse_direction = Column(String(10), nullable=False)  # UP, DOWN
    candle_direction = Column(String(10), nullable=False)  # BULLISH, BEARISH
    quality = Column(String(10), nullable=False)  # HIGH, MEDIUM, LOW
    status = Column(String(20), nullable=False, server_default="ACTIVE")  # ACTIVE, TESTED, BROKEN
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Lifecycle tracking fields
    last_checked_time = Column(DateTime(timezone=True), nullable=True)
    last_checked_candle_time = Column(DateTime(timezone=True), nullable=True)

    # Test interaction tracking
    test_count = Column(Integer, nullable=False, server_default="0")
    test_times = Column(postgresql.ARRAY(DateTime(timezone=True)), nullable=True)

    # Option 1: Edge touch (price touches OB boundary)
    first_touch_edge_time = Column(DateTime(timezone=True), nullable=True)
    first_touch_edge_price = Column(Float, nullable=True)

    # Option 2: Midpoint touch (price reaches 50% level)
    first_touch_midpoint_time = Column(DateTime(timezone=True), nullable=True)
    first_touch_midpoint_price = Column(Float, nullable=True)

    # Option 3: Entry without close (candle enters zone but doesn't close inside)
    first_entry_no_close_time = Column(DateTime(timezone=True), nullable=True)
    first_entry_candle_close = Column(Float, nullable=True)

    # BROKEN state tracking
    broken_time = Column(DateTime(timezone=True), nullable=True)
    broken_candle_close = Column(Float, nullable=True)

    # Penetration metrics
    max_penetration_pts = Column(Float, nullable=False, server_default="0.0")
    max_penetration_pct = Column(Float, nullable=False, server_default="0.0")

    __table_args__ = (
        Index('idx_obs_symbol_time', 'symbol', 'formation_time'),
        Index('idx_obs_type', 'ob_type'),
        Index('idx_obs_quality', 'quality'),
        Index('idx_obs_status', 'status'),
    )

    def __repr__(self):
        return f"<OB {self.ob_type} @ {self.formation_time} impulse={self.impulse_move}pts>"


class PatternInteraction(Base):
    """
    Pattern Interaction - unified table for tracking interactions with all pattern types

    Uses R0-R4, P1-P5 classification from REBOTE_Y_PENETRACION_CRITERIOS.md
    """
    __tablename__ = "pattern_interactions"

    interaction_id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_type = Column(String(10), nullable=False)  # FVG, LP, OB
    pattern_id = Column(Integer, nullable=False)
    interaction_time = Column(DateTime(timezone=True), nullable=False)
    interaction_type = Column(String(25), nullable=False)  # R0_CLEAN_BOUNCE, R1_SHALLOW_TOUCH, P4_FALSE_BREAKOUT, etc.
    penetration_pts = Column(Float, nullable=False)
    penetration_pct = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    candle_high = Column(Float, nullable=False)
    candle_low = Column(Float, nullable=False)
    candle_close = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_interactions_pattern', 'pattern_type', 'pattern_id'),
        Index('idx_interactions_time', 'interaction_time'),
        Index('idx_interactions_type', 'interaction_type'),
    )

    def __repr__(self):
        return f"<Interaction {self.pattern_type}#{self.pattern_id} {self.interaction_type} @ {self.interaction_time}>"


class MarketStateSnapshot(Base):
    """
    Market State Snapshot - aggregated view of active patterns across all timeframes at a specific timestamp

    Stores snapshot of market state showing all active patterns (FVG, LP, OB) for all 9 timeframes.
    Uses JSONB column 'timeframe_breakdown' to store IDs and counts per timeframe.
    """
    __tablename__ = "market_state_snapshots"

    snapshot_id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    snapshot_time = Column(DateTime(timezone=False), nullable=False)  # UTC naive (standard)
    total_patterns_all_timeframes = Column(Integer, nullable=False, server_default="0")

    # JSONB structure:
    # {
    #   "30s": {"active_fvgs_count": 1, "active_lps_count": 0, "active_obs_count": 2, "active_fvg_ids": [95], ...},
    #   "1min": {"active_fvgs_count": 2, ...},
    #   ...
    # }
    timeframe_breakdown = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=False), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('symbol', 'snapshot_time', name='uq_snapshot'),
        Index('idx_snapshots_symbol_time', 'symbol', 'snapshot_time'),
        Index('idx_snapshots_time', 'snapshot_time'),
    )

    def __repr__(self):
        return f"<MarketStateSnapshot {self.symbol} @ {self.snapshot_time} total={self.total_patterns_all_timeframes}>"
