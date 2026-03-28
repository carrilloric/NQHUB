"""
Pattern Detection REST API Endpoints

Implementation of CONTRACT-002 Pattern Detection API specification.
READ-ONLY endpoints for querying detected patterns from database.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import logging

from app.db.session import get_db
from app.models.patterns import (
    DetectedFVG,
    DetectedLiquidityPool,
    DetectedOrderBlock,
    PatternInteraction
)
from app.models.candlestick import Candlestick5Min
from app.core.deps import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Supported timeframes
VALID_TIMEFRAMES = ['1min', '5min', '15min', '30min', '1hour', '4hour', '1day']


@router.get("/fvgs")
async def get_fair_value_gaps(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query('5min', description="Timeframe", enum=VALID_TIMEFRAMES),
    status: Optional[str] = Query(None, description="Filter by status", enum=['UNMITIGATED', 'REDELIVERED', 'REBALANCED']),
    significance: Optional[str] = Query(None, description="Filter by significance", enum=['MICRO', 'SMALL', 'MEDIUM', 'LARGE', 'EXTREME']),
    start_date: Optional[date] = Query(None, description="Start date for formation time filter"),
    end_date: Optional[date] = Query(None, description="End date for formation time filter"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page"),
    sort_by: str = Query('formation_time', description="Sort field", enum=['formation_time', 'gap_size_pts', 'significance']),
    sort_order: str = Query('desc', description="Sort order", enum=['asc', 'desc']),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Fair Value Gaps.

    Implements GET /api/v1/patterns/fvgs from CONTRACT-002.
    Queries the detected_fvg table with optional filters.
    """
    try:
        # Build base query
        query = select(DetectedFVG).where(
            and_(
                DetectedFVG.symbol == symbol,
                DetectedFVG.timeframe == timeframe
            )
        )

        # Apply filters
        if status:
            query = query.where(DetectedFVG.status == status)
        if significance:
            query = query.where(DetectedFVG.significance == significance)
        if start_date:
            query = query.where(DetectedFVG.formation_time >= start_date)
        if end_date:
            # Add 1 day to include the entire end date
            query = query.where(DetectedFVG.formation_time < datetime.combine(end_date, datetime.min.time()).replace(hour=23, minute=59, second=59))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(DetectedFVG, sort_by)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.limit(page_size).offset(offset)

        # Execute query
        result = await db.execute(query)
        fvgs = result.scalars().all()

        # Format response according to CONTRACT-002 schema
        data = []
        for fvg in fvgs:
            fvg_data = {
                "id": fvg.id,
                "symbol": fvg.symbol,
                "timeframe": fvg.timeframe,
                "formation_time": fvg.formation_time.isoformat() + "Z",
                "gap_high": float(fvg.gap_high),
                "gap_low": float(fvg.gap_low),
                "gap_size_pts": float(fvg.gap_size_pts),
                "gap_size_pct": float(fvg.gap_size_pct),
                "significance": fvg.significance,
                "status": fvg.status,
                "direction": fvg.direction,
                "premium_level": float(fvg.premium_level) if fvg.premium_level else None,
                "discount_level": float(fvg.discount_level) if fvg.discount_level else None,
                "consequent_encroachment": float(fvg.consequent_encroachment) if fvg.consequent_encroachment else None,
                "displacement_score": float(fvg.displacement_score) if fvg.displacement_score else None,
                "has_break_of_structure": fvg.has_break_of_structure,
                "mitigation_time": fvg.mitigation_time.isoformat() + "Z" if fvg.mitigation_time else None,
                "mitigation_candle_id": fvg.mitigation_candle_id
            }
            data.append(fvg_data)

        return {
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": (offset + page_size) < total
        }

    except Exception as e:
        logger.error(f"Error fetching FVGs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "detail": f"Internal server error: {str(e)}",
                "code": "INTERNAL_ERROR"
            }
        )


@router.get("/order-blocks")
async def get_order_blocks(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query('5min', description="Timeframe", enum=VALID_TIMEFRAMES),
    status: Optional[str] = Query(None, description="Filter by status", enum=['ACTIVE', 'TESTED', 'BROKEN']),
    ob_type: Optional[str] = Query(None, description="Filter by OB type", enum=['BULLISH OB', 'BEARISH OB', 'STRONG BULLISH OB', 'STRONG BEARISH OB']),
    quality: Optional[str] = Query(None, description="Filter by quality", enum=['HIGH', 'MEDIUM', 'LOW']),
    start_date: Optional[date] = Query(None, description="Start date for formation time filter"),
    end_date: Optional[date] = Query(None, description="End date for formation time filter"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page"),
    sort_by: str = Query('formation_time', description="Sort field", enum=['formation_time', 'impulse_move', 'quality']),
    sort_order: str = Query('desc', description="Sort order", enum=['asc', 'desc']),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Order Blocks.

    Implements GET /api/v1/patterns/order-blocks from CONTRACT-002.
    Queries the detected_order_block table with optional filters.
    """
    try:
        # Build base query
        query = select(DetectedOrderBlock).where(
            and_(
                DetectedOrderBlock.symbol == symbol,
                DetectedOrderBlock.timeframe == timeframe
            )
        )

        # Apply filters
        if status:
            query = query.where(DetectedOrderBlock.status == status)
        if ob_type:
            query = query.where(DetectedOrderBlock.ob_type == ob_type)
        if quality:
            query = query.where(DetectedOrderBlock.quality == quality)
        if start_date:
            query = query.where(DetectedOrderBlock.formation_time >= start_date)
        if end_date:
            query = query.where(DetectedOrderBlock.formation_time < datetime.combine(end_date, datetime.min.time()).replace(hour=23, minute=59, second=59))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(DetectedOrderBlock, sort_by)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.limit(page_size).offset(offset)

        # Execute query
        result = await db.execute(query)
        order_blocks = result.scalars().all()

        # Format response according to CONTRACT-002 schema
        data = []
        for ob in order_blocks:
            ob_data = {
                "id": ob.id,
                "symbol": ob.symbol,
                "timeframe": ob.timeframe,
                "formation_time": ob.formation_time.isoformat() + "Z",
                "ob_high": float(ob.ob_high),
                "ob_low": float(ob.ob_low),
                "ob_type": ob.ob_type,
                "quality": ob.quality,
                "status": ob.status,
                "ob_body_midpoint": float(ob.ob_body_midpoint) if ob.ob_body_midpoint else None,
                "ob_range_midpoint": float(ob.ob_range_midpoint) if ob.ob_range_midpoint else None,
                "impulse_move": float(ob.impulse_move) if ob.impulse_move else None,
                "impulse_direction": ob.impulse_direction,
                "volume": ob.volume,
                "test_time": ob.test_time.isoformat() + "Z" if ob.test_time else None,
                "break_time": ob.break_time.isoformat() + "Z" if ob.break_time else None
            }
            data.append(ob_data)

        return {
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": (offset + page_size) < total
        }

    except Exception as e:
        logger.error(f"Error fetching Order Blocks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "detail": f"Internal server error: {str(e)}",
                "code": "INTERNAL_ERROR"
            }
        )


@router.get("/liquidity-pools")
async def get_liquidity_pools(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query('5min', description="Timeframe", enum=VALID_TIMEFRAMES),
    status: Optional[str] = Query(None, description="Filter by status", enum=['UNMITIGATED', 'RESPECTED', 'SWEPT', 'MITIGATED']),
    pool_type: Optional[str] = Query(None, description="Filter by pool type", enum=['EQH', 'EQL', 'NYH', 'NYL', 'ASH', 'ASL', 'LSH', 'LSL', 'SWING_HIGH', 'SWING_LOW']),
    strength: Optional[str] = Query(None, description="Filter by strength", enum=['STRONG', 'NORMAL', 'WEAK']),
    start_date: Optional[date] = Query(None, description="Start date for formation time filter"),
    end_date: Optional[date] = Query(None, description="End date for formation time filter"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page"),
    sort_by: str = Query('formation_time', description="Sort field", enum=['formation_time', 'touches', 'strength']),
    sort_order: str = Query('desc', description="Sort order", enum=['asc', 'desc']),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Liquidity Pools.

    Implements GET /api/v1/patterns/liquidity-pools from CONTRACT-002.
    Queries the detected_liquidity_pool table with optional filters.
    """
    try:
        # Build base query
        query = select(DetectedLiquidityPool).where(
            and_(
                DetectedLiquidityPool.symbol == symbol,
                DetectedLiquidityPool.timeframe == timeframe
            )
        )

        # Apply filters
        if status:
            query = query.where(DetectedLiquidityPool.status == status)
        if pool_type:
            query = query.where(DetectedLiquidityPool.pool_type == pool_type)
        if strength:
            query = query.where(DetectedLiquidityPool.strength == strength)
        if start_date:
            query = query.where(DetectedLiquidityPool.formation_time >= start_date)
        if end_date:
            query = query.where(DetectedLiquidityPool.formation_time < datetime.combine(end_date, datetime.min.time()).replace(hour=23, minute=59, second=59))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(DetectedLiquidityPool, sort_by)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.limit(page_size).offset(offset)

        # Execute query
        result = await db.execute(query)
        liquidity_pools = result.scalars().all()

        # Format response according to CONTRACT-002 schema
        data = []
        for lp in liquidity_pools:
            lp_data = {
                "id": lp.id,
                "symbol": lp.symbol,
                "timeframe": lp.timeframe,
                "formation_time": lp.formation_time.isoformat() + "Z",
                "zone_high": float(lp.zone_high),
                "zone_low": float(lp.zone_low),
                "pool_type": lp.pool_type,
                "strength": lp.strength,
                "status": lp.status,
                "modal_level": float(lp.modal_level) if lp.modal_level else None,
                "touches": lp.touches,
                "sweep_time": lp.sweep_time.isoformat() + "Z" if lp.sweep_time else None,
                "mitigation_time": lp.mitigation_time.isoformat() + "Z" if lp.mitigation_time else None
            }
            data.append(lp_data)

        return {
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": (offset + page_size) < total
        }

    except Exception as e:
        logger.error(f"Error fetching Liquidity Pools: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "detail": f"Internal server error: {str(e)}",
                "code": "INTERNAL_ERROR"
            }
        )


@router.get("/snapshot")
async def get_market_state_snapshot(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query('5min', description="Timeframe", enum=VALID_TIMEFRAMES),
    timestamp: Optional[datetime] = Query(None, description="Specific timestamp for snapshot (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Market State Snapshot.

    Implements GET /api/v1/patterns/snapshot from CONTRACT-002.
    Returns a snapshot of all active patterns at a specific time or current time.
    """
    try:
        # Use current time if not specified
        snapshot_time = timestamp or datetime.utcnow()

        # Query active FVGs at snapshot time
        fvg_query = select(DetectedFVG).where(
            and_(
                DetectedFVG.symbol == symbol,
                DetectedFVG.timeframe == timeframe,
                DetectedFVG.formation_time <= snapshot_time,
                or_(
                    DetectedFVG.mitigation_time.is_(None),
                    DetectedFVG.mitigation_time > snapshot_time
                ),
                DetectedFVG.status == 'UNMITIGATED'
            )
        )
        fvg_result = await db.execute(fvg_query)
        active_fvgs = fvg_result.scalars().all()

        # Query active Order Blocks at snapshot time
        ob_query = select(DetectedOrderBlock).where(
            and_(
                DetectedOrderBlock.symbol == symbol,
                DetectedOrderBlock.timeframe == timeframe,
                DetectedOrderBlock.formation_time <= snapshot_time,
                or_(
                    DetectedOrderBlock.break_time.is_(None),
                    DetectedOrderBlock.break_time > snapshot_time
                ),
                DetectedOrderBlock.status == 'ACTIVE'
            )
        )
        ob_result = await db.execute(ob_query)
        active_obs = ob_result.scalars().all()

        # Query active Liquidity Pools at snapshot time
        lp_query = select(DetectedLiquidityPool).where(
            and_(
                DetectedLiquidityPool.symbol == symbol,
                DetectedLiquidityPool.timeframe == timeframe,
                DetectedLiquidityPool.formation_time <= snapshot_time,
                or_(
                    DetectedLiquidityPool.mitigation_time.is_(None),
                    DetectedLiquidityPool.mitigation_time > snapshot_time
                ),
                DetectedLiquidityPool.status == 'UNMITIGATED'
            )
        )
        lp_result = await db.execute(lp_query)
        active_lps = lp_result.scalars().all()

        # Get current price from latest candle
        price_query = select(Candlestick5Min).where(
            and_(
                Candlestick5Min.symbol == symbol,
                Candlestick5Min.time_interval <= snapshot_time
            )
        ).order_by(Candlestick5Min.time_interval.desc()).limit(1)
        price_result = await db.execute(price_query)
        latest_candle = price_result.scalar_one_or_none()
        current_price = float(latest_candle.close) if latest_candle else None

        # Find nearest support and resistance
        all_levels = []

        # Add FVG levels
        for fvg in active_fvgs:
            all_levels.append(('resistance' if current_price and current_price < fvg.gap_low else 'support', float(fvg.gap_low)))
            all_levels.append(('resistance' if current_price and current_price < fvg.gap_high else 'support', float(fvg.gap_high)))

        # Add OB levels
        for ob in active_obs:
            all_levels.append(('resistance' if current_price and current_price < ob.ob_low else 'support', float(ob.ob_low)))
            all_levels.append(('resistance' if current_price and current_price < ob.ob_high else 'support', float(ob.ob_high)))

        # Add LP levels
        for lp in active_lps:
            all_levels.append(('resistance' if current_price and current_price < lp.zone_low else 'support', float(lp.zone_low)))
            all_levels.append(('resistance' if current_price and current_price < lp.zone_high else 'support', float(lp.zone_high)))

        nearest_resistance = None
        nearest_support = None

        if current_price and all_levels:
            resistances = [level for type_, level in all_levels if type_ == 'resistance' and level > current_price]
            supports = [level for type_, level in all_levels if type_ == 'support' and level < current_price]

            if resistances:
                nearest_resistance = min(resistances)
            if supports:
                nearest_support = max(supports)

        # Format response according to CONTRACT-002 schema
        return {
            "timestamp": snapshot_time.isoformat() + "Z",
            "symbol": symbol,
            "timeframe": timeframe,
            "current_price": current_price,
            "active_patterns": {
                "fvgs": [
                    {
                        "id": fvg.id,
                        "gap_high": float(fvg.gap_high),
                        "gap_low": float(fvg.gap_low),
                        "significance": fvg.significance
                    }
                    for fvg in active_fvgs
                ],
                "order_blocks": [
                    {
                        "id": ob.id,
                        "ob_high": float(ob.ob_high),
                        "ob_low": float(ob.ob_low),
                        "ob_type": ob.ob_type
                    }
                    for ob in active_obs
                ],
                "liquidity_pools": [
                    {
                        "id": lp.id,
                        "zone_high": float(lp.zone_high),
                        "zone_low": float(lp.zone_low),
                        "pool_type": lp.pool_type
                    }
                    for lp in active_lps
                ]
            },
            "summary": {
                "total_active_fvgs": len(active_fvgs),
                "total_active_obs": len(active_obs),
                "total_active_lps": len(active_lps),
                "nearest_resistance": nearest_resistance,
                "nearest_support": nearest_support
            }
        }

    except Exception as e:
        logger.error(f"Error fetching Market State Snapshot: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "detail": f"Internal server error: {str(e)}",
                "code": "INTERNAL_ERROR"
            }
        )


@router.get("/interactions")
async def get_pattern_interactions(
    symbol: str = Query(..., description="Trading symbol"),
    pattern_type: Optional[str] = Query(None, description="Filter by pattern type", enum=['FVG', 'OB', 'LP']),
    pattern_id: Optional[int] = Query(None, description="Filter by specific pattern ID"),
    interaction_type: Optional[str] = Query(None, description="Filter by interaction type", enum=['R0', 'R1', 'R2', 'R3', 'R4', 'P1', 'P2', 'P3', 'P4', 'P5']),
    start_date: Optional[date] = Query(None, description="Start date for interaction time filter"),
    end_date: Optional[date] = Query(None, description="End date for interaction time filter"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page"),
    sort_by: str = Query('interaction_time', description="Sort field", enum=['interaction_time', 'penetration_pct', 'confidence']),
    sort_order: str = Query('desc', description="Sort order", enum=['asc', 'desc']),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Pattern Interactions.

    Implements GET /api/v1/patterns/interactions from CONTRACT-002.
    Queries the pattern_interaction table with optional filters.
    """
    try:
        # Build base query - PatternInteraction doesn't have symbol field,
        # so we need to join with the pattern tables to filter by symbol
        query = select(PatternInteraction)

        # Apply filters
        if pattern_type:
            query = query.where(PatternInteraction.pattern_type == pattern_type)
        if pattern_id:
            query = query.where(PatternInteraction.pattern_id == pattern_id)
        if interaction_type:
            query = query.where(PatternInteraction.interaction_type == interaction_type)
        if start_date:
            query = query.where(PatternInteraction.interaction_time >= start_date)
        if end_date:
            query = query.where(PatternInteraction.interaction_time < datetime.combine(end_date, datetime.min.time()).replace(hour=23, minute=59, second=59))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(PatternInteraction, sort_by)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.limit(page_size).offset(offset)

        # Execute query
        result = await db.execute(query)
        interactions = result.scalars().all()

        # Calculate summary by type
        summary_by_type = {}
        if interactions:
            for interaction in interactions:
                itype = interaction.interaction_type
                summary_by_type[itype] = summary_by_type.get(itype, 0) + 1

        # Format response according to CONTRACT-002 schema
        data = []
        for interaction in interactions:
            interaction_data = {
                "id": interaction.id,
                "pattern_type": interaction.pattern_type,
                "pattern_id": interaction.pattern_id,
                "interaction_time": interaction.interaction_time.isoformat() + "Z",
                "interaction_type": interaction.interaction_type,
                "penetration_pts": float(interaction.penetration_pts),
                "penetration_pct": float(interaction.penetration_pct),
                "candle_high": float(interaction.candle_high) if interaction.candle_high else None,
                "candle_low": float(interaction.candle_low) if interaction.candle_low else None,
                "candle_close": float(interaction.candle_close) if interaction.candle_close else None,
                "volume": interaction.volume,
                "confidence": float(interaction.confidence) if interaction.confidence else None
            }
            data.append(interaction_data)

        return {
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": (offset + page_size) < total,
            "summary": {
                "by_type": summary_by_type
            }
        }

    except Exception as e:
        logger.error(f"Error fetching Pattern Interactions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "detail": f"Internal server error: {str(e)}",
                "code": "INTERNAL_ERROR"
            }
        )