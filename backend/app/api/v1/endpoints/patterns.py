"""
Pattern Detection API Endpoints

Endpoints for FVG, Liquidity Pool, and Order Block detection.
"""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_sync
from app.services.pattern_detection import (
    FVGDetector,
    LiquidityPoolDetector,
    OrderBlockDetector,
    PatternInteractionTracker
)
from app.schemas.patterns import (
    # FVG schemas
    FVGDetectionRequest,
    FVGGenerationResponse,
    FVGListResponse,
    FVGResponse,
    # LP schemas
    LiquidityPoolDetectionRequest,
    LiquidityPoolGenerationResponse,
    LiquidityPoolListResponse,
    LiquidityPoolResponse,
    # OB schemas
    OrderBlockDetectionRequest,
    OrderBlockGenerationResponse,
    OrderBlockListResponse,
    OrderBlockResponse,
    # Interaction schemas
    PatternInteractionsResponse,
    PatternInteractionResponse,
)
from app.models.patterns import DetectedFVG, DetectedLiquidityPool, DetectedOrderBlock, PatternInteraction

router = APIRouter()


# ============================================================================
# FVG Endpoints
# ============================================================================

@router.post("/fvgs/generate", response_model=FVGGenerationResponse)
def generate_fvgs(
    request: FVGDetectionRequest,
    db: Session = Depends(get_db_sync)
):
    """
    Generate Fair Value Gaps for a date range

    Detects FVGs using auto-calibrated parameters and returns:
    - List of detected FVGs
    - Auto-calibrated parameters used
    - Text report in markdown format
    """
    detector = FVGDetector(db)

    try:
        result = detector.generate_fvgs(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            timeframe=request.timeframe,
            save_to_db=True
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting FVGs: {str(e)}")


@router.get("/fvgs/list", response_model=FVGListResponse)
def list_fvgs(
    symbol: str = Query(..., example="NQZ5"),
    timeframe: str = Query("5min", example="5min"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    significance: Optional[str] = Query(None, example="LARGE"),
    status: Optional[str] = Query(None, example="UNMITIGATED"),
    db: Session = Depends(get_db_sync)
):
    """
    List detected FVGs with optional filters

    Query parameters:
    - symbol: Trading symbol (required)
    - timeframe: Candle timeframe (default: 5min)
    - start_date: Filter by formation date
    - end_date: Filter by formation date
    - significance: Filter by MICRO, SMALL, MEDIUM, LARGE, EXTREME
    - status: Filter by UNMITIGATED, FILLED, BROKEN
    """
    query = db.query(DetectedFVG).filter(
        DetectedFVG.symbol == symbol,
        DetectedFVG.timeframe == timeframe
    )

    if start_date:
        query = query.filter(DetectedFVG.formation_time >= start_date)
    if end_date:
        query = query.filter(DetectedFVG.formation_time <= end_date)
    if significance:
        query = query.filter(DetectedFVG.significance == significance)
    if status:
        query = query.filter(DetectedFVG.status == status)

    fvgs = query.order_by(DetectedFVG.formation_time.desc()).all()

    return FVGListResponse(
        total=len(fvgs),
        fvgs=[FVGResponse.from_orm(fvg) for fvg in fvgs]
    )


# ============================================================================
# Liquidity Pool Endpoints
# ============================================================================

@router.post("/liquidity-pools/generate", response_model=LiquidityPoolGenerationResponse)
def generate_liquidity_pools(
    request: LiquidityPoolDetectionRequest,
    db: Session = Depends(get_db_sync)
):
    """
    Generate Liquidity Pools for a specific date

    Detects:
    - Equal Highs (EQH) / Equal Lows (EQL)
    - Session levels (ASH, ASL, LSH, LSL, NYH, NYL)

    Returns:
    - List of detected pools
    - Breakdown by pool type
    - Auto-calibrated parameters
    - Text report in markdown
    """
    detector = LiquidityPoolDetector(db)

    try:
        result = detector.generate_liquidity_pools(
            symbol=request.symbol,
            date_val=request.date_val,
            timeframe=request.timeframe,
            pool_types=request.pool_types,
            save_to_db=True
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting LPs: {str(e)}")


@router.get("/liquidity-pools/list", response_model=LiquidityPoolListResponse)
def list_liquidity_pools(
    symbol: str = Query(..., example="NQZ5"),
    timeframe: str = Query("5min", example="5min"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    pool_type: Optional[str] = Query(None, example="EQH"),
    strength: Optional[str] = Query(None, example="STRONG"),
    status: Optional[str] = Query(None, example="UNMITIGATED"),
    db: Session = Depends(get_db_sync)
):
    """
    List detected Liquidity Pools with optional filters

    Query parameters:
    - symbol: Trading symbol (required)
    - timeframe: Candle timeframe
    - pool_type: Filter by EQH, EQL, NYH, NYL, etc.
    - strength: Filter by STRONG, NORMAL, WEAK
    - status: Filter by UNMITIGATED, RESPECTED, SWEPT, MITIGATED
    """
    query = db.query(DetectedLiquidityPool).filter(
        DetectedLiquidityPool.symbol == symbol,
        DetectedLiquidityPool.timeframe == timeframe
    )

    if start_date:
        query = query.filter(DetectedLiquidityPool.formation_time >= start_date)
    if end_date:
        query = query.filter(DetectedLiquidityPool.formation_time <= end_date)
    if pool_type:
        query = query.filter(DetectedLiquidityPool.pool_type == pool_type)
    if strength:
        query = query.filter(DetectedLiquidityPool.strength == strength)
    if status:
        query = query.filter(DetectedLiquidityPool.status == status)

    pools = query.order_by(DetectedLiquidityPool.formation_time.desc()).all()

    return LiquidityPoolListResponse(
        total=len(pools),
        pools=[LiquidityPoolResponse.from_orm(pool) for pool in pools]
    )


# ============================================================================
# Order Block Endpoints
# ============================================================================

@router.post("/order-blocks/generate", response_model=OrderBlockGenerationResponse)
def generate_order_blocks(
    request: OrderBlockDetectionRequest,
    db: Session = Depends(get_db_sync)
):
    """
    Generate Order Blocks for a date range

    Detects:
    - Bullish OBs (bearish candle + bullish impulse)
    - Bearish OBs (bullish candle + bearish impulse)
    - Strong variants (impulse > threshold)

    Returns:
    - List of detected OBs
    - Breakdown by type and quality
    - Auto-calibrated parameters
    - Text report in markdown
    """
    detector = OrderBlockDetector(db)

    try:
        result = detector.generate_order_blocks(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            timeframe=request.timeframe,
            save_to_db=True
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting OBs: {str(e)}")


@router.get("/order-blocks/list", response_model=OrderBlockListResponse)
def list_order_blocks(
    symbol: str = Query(..., example="NQZ5"),
    timeframe: str = Query("5min", example="5min"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    ob_type: Optional[str] = Query(None, example="BULLISH OB"),
    quality: Optional[str] = Query(None, example="HIGH"),
    status: Optional[str] = Query(None, example="ACTIVE"),
    db: Session = Depends(get_db_sync)
):
    """
    List detected Order Blocks with optional filters

    Query parameters:
    - symbol: Trading symbol (required)
    - timeframe: Candle timeframe
    - ob_type: Filter by BULLISH OB, BEARISH OB, etc.
    - quality: Filter by HIGH, MEDIUM, LOW
    - status: Filter by ACTIVE, TESTED, BROKEN
    """
    query = db.query(DetectedOrderBlock).filter(
        DetectedOrderBlock.symbol == symbol,
        DetectedOrderBlock.timeframe == timeframe
    )

    if start_date:
        query = query.filter(DetectedOrderBlock.formation_time >= start_date)
    if end_date:
        query = query.filter(DetectedOrderBlock.formation_time <= end_date)
    if ob_type:
        query = query.filter(DetectedOrderBlock.ob_type == ob_type)
    if quality:
        query = query.filter(DetectedOrderBlock.quality == quality)
    if status:
        query = query.filter(DetectedOrderBlock.status == status)

    obs = query.order_by(DetectedOrderBlock.formation_time.desc()).all()

    return OrderBlockListResponse(
        total=len(obs),
        order_blocks=[OrderBlockResponse.from_orm(ob) for ob in obs]
    )


# ============================================================================
# Pattern Interaction Endpoints
# ============================================================================

@router.get("/patterns/{pattern_type}/{pattern_id}/interactions", response_model=PatternInteractionsResponse)
def get_pattern_interactions(
    pattern_type: str,  # FVG, LP, OB
    pattern_id: int,
    timeframe: str = Query("5min", example="5min"),
    db: Session = Depends(get_db_sync)
):
    """
    Get interaction history for a specific pattern

    Tracks how price interacted with the pattern zone using R0-R4, P1-P5 classification.

    Args:
    - pattern_type: FVG, LP, or OB
    - pattern_id: Pattern ID
    - timeframe: Candle timeframe for analysis

    Returns:
    - Total interactions
    - Breakdown by type (R0-R4, P1-P5)
    - List of interactions with details
    - Text report
    """
    pattern_type = pattern_type.upper()
    if pattern_type not in ["FVG", "LP", "OB"]:
        raise HTTPException(status_code=400, detail="Invalid pattern_type. Must be FVG, LP, or OB")

    tracker = PatternInteractionTracker(db)

    try:
        # Track interactions
        if pattern_type == "FVG":
            interactions = tracker.track_fvg_interactions(pattern_id, timeframe)
        elif pattern_type == "LP":
            interactions = tracker.track_lp_interactions(pattern_id, timeframe)
        else:  # OB
            interactions = tracker.track_ob_interactions(pattern_id, timeframe)

        # Save interactions to database
        if interactions:
            db.add_all(interactions)
            db.commit()
            for interaction in interactions:
                db.refresh(interaction)

        # Update pattern status
        tracker.update_pattern_status(pattern_type, pattern_id, interactions)

        # Calculate breakdown
        breakdown = {}
        for interaction in interactions:
            breakdown[interaction.interaction_type] = breakdown.get(interaction.interaction_type, 0) + 1

        # Generate text report
        text_report = generate_interaction_report(interactions, pattern_type, pattern_id)

        return PatternInteractionsResponse(
            total=len(interactions),
            breakdown=breakdown,
            interactions=[PatternInteractionResponse.from_orm(i) for i in interactions],
            text_report=text_report
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking interactions: {str(e)}")


def generate_interaction_report(
    interactions: List[PatternInteraction],
    pattern_type: str,
    pattern_id: int
) -> str:
    """Generate markdown report for pattern interactions"""
    if not interactions:
        return f"# Interaction History - {pattern_type} #{pattern_id}\n\nNo interactions detected."

    # Count by type
    type_counts = {}
    for i in interactions:
        type_counts[i.interaction_type] = type_counts.get(i.interaction_type, 0) + 1

    report = f"""# Interaction History - {pattern_type} #{pattern_id}

## Summary

**Total Interactions**: {len(interactions)}

### Breakdown by Type
"""
    for itype in sorted(type_counts.keys()):
        count = type_counts[itype]
        report += f"- **{itype}**: {count}\n"

    report += "\n## Interactions\n\n"

    for i, interaction in enumerate(interactions, 1):
        report += f"""### {i}. {interaction.interaction_type} @ {interaction.interaction_time.strftime('%m-%d %H:%M ET')}

- **Penetration**: {interaction.penetration_pts:.2f} pts ({interaction.penetration_pct:.1f}%)
- **Confidence**: {interaction.confidence:.0%}
- **Candle**: H={interaction.candle_high:.2f}, L={interaction.candle_low:.2f}, C={interaction.candle_close:.2f}

---

"""

    return report


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
def health_check():
    """Health check endpoint for pattern detection service"""
    return {
        "status": "healthy",
        "service": "Pattern Detection API",
        "features": ["FVG", "Liquidity Pools", "Order Blocks", "Interactions"]
    }
