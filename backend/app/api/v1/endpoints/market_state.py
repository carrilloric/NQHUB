"""
Market State Endpoints

Provides endpoints for generating and retrieving market state snapshots
showing active patterns across all 9 timeframes.
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.patterns import (
    MarketStateGenerateRequest,
    MarketStateGenerateResponse,
    MarketStateDetailResponse,
    MarketStateSnapshotInfo
)
from app.services.market_state import MarketStateSnapshotGenerator
import pytz

router = APIRouter()


@router.post("/generate", response_model=MarketStateGenerateResponse)
async def generate_market_state_snapshots(
    request: MarketStateGenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate market state snapshots for a time range

    Creates snapshots showing all active patterns (FVG, Session Levels, OB)
    across all 9 timeframes at regular intervals.

    - **symbol**: Trading symbol (e.g., "NQZ5")
    - **start_time**: Start time (UTC, e.g., "2025-11-24T09:00:00")
    - **end_time**: End time (UTC, e.g., "2025-11-24T16:00:00")
    - **interval_minutes**: Minutes between snapshots (1-60, default: 5)

    Returns job_id IMMEDIATELY for progress tracking.
    Generation happens in background task with its own DB session.
    """
    from app.services.market_state.progress_tracker import progress_tracker
    from datetime import timedelta
    import asyncio

    # Calculate total snapshots for progress tracking
    time_diff = request.end_time - request.start_time
    total_minutes = time_diff.total_seconds() / 60
    total_snapshots = int(total_minutes / request.interval_minutes) + 1

    # Create progress tracking job
    job_id = progress_tracker.create_job(request.symbol, total_snapshots)

    # Background task for generation
    async def generate_in_background():
        """Run generation in background with a new DB session"""
        from app.db.session import AsyncSessionLocal

        # Create a new session for this background task
        async with AsyncSessionLocal() as bg_db:
            try:
                generator = MarketStateSnapshotGenerator(bg_db)

                # Generate snapshots with progress tracking
                await generator.generate_snapshots_bulk(
                    symbol=request.symbol,
                    start_time=request.start_time,
                    end_time=request.end_time,
                    interval_minutes=request.interval_minutes,
                    progress_job_id=job_id
                )

                # Mark job as completed
                progress_tracker.complete_job(job_id)
            except Exception as e:
                # Mark job as failed
                progress_tracker.fail_job(job_id, str(e))
                print(f"[Market State] Background generation failed: {e}")

    # Start background task (fire and forget)
    asyncio.create_task(generate_in_background())

    # Return IMMEDIATELY with job_id (generation happening in background)
    return MarketStateGenerateResponse(
        job_id=job_id,
        total_snapshots=total_snapshots,
        symbol=request.symbol,
        start_time=request.start_time,
        end_time=request.end_time,
        snapshots=[]  # Empty for consistency, use /list to get snapshot info
    )


@router.get("/detail", response_model=MarketStateDetailResponse)
async def get_market_state_detail(
    symbol: str = Query(..., example="NQZ5", description="Trading symbol"),
    snapshot_time: datetime = Query(..., example="2025-11-24T09:30:00", description="Snapshot timestamp (UTC)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed market state with full pattern data for all 9 timeframes

    Retrieves a snapshot and returns complete pattern information (FVG, Session Levels, OB)
    for each of the 9 timeframes (30s, 1min, 5min, 15min, 30min, 1hr, 4hr, daily, weekly).

    - **symbol**: Trading symbol (e.g., "NQZ5")
    - **snapshot_time**: Snapshot timestamp in UTC (e.g., "2025-11-24T09:30:00")

    Returns:
    - Summary counts by timeframe
    - Full pattern details (all fields) for active FVGs, Session Levels, and Order Blocks
    - Bullish/Bearish pattern counts per timeframe
    """
    generator = MarketStateSnapshotGenerator(db)

    # Get detailed snapshot
    detail = await generator.get_snapshot_detail(symbol, snapshot_time)

    if not detail:
        raise HTTPException(
            status_code=404,
            detail=f"No market state snapshot found for {symbol} at {snapshot_time}"
        )

    return MarketStateDetailResponse(**detail)


@router.get("/progress/{job_id}")
async def get_generation_progress(job_id: str):
    """
    Get progress status for a snapshot generation job

    Returns real-time progress including:
    - Current/total snapshots
    - Percentage complete
    - Elapsed time
    - Estimated time remaining
    """
    from app.services.market_state.progress_tracker import progress_tracker

    progress = progress_tracker.get_progress(job_id)

    if not progress:
        raise HTTPException(
            status_code=404,
            detail=f"Progress job {job_id} not found"
        )

    return {
        "job_id": progress.job_id,
        "symbol": progress.symbol,
        "total_snapshots": progress.total_snapshots,
        "completed_snapshots": progress.completed_snapshots,
        "percentage": progress.percentage,
        "status": progress.status,
        "elapsed_seconds": progress.elapsed_seconds,
        "estimated_seconds_remaining": progress.estimated_seconds_remaining,
        "error_message": progress.error_message
    }


@router.get("/list")
async def list_market_state_snapshots(
    symbol: str = Query(..., example="NQZ5", description="Trading symbol"),
    start_time: Optional[datetime] = Query(None, description="Filter snapshots from this time (UTC)"),
    end_time: Optional[datetime] = Query(None, description="Filter snapshots until this time (UTC)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of snapshots to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    List available market state snapshots for a symbol

    Returns basic information about existing snapshots without full pattern details.
    Use /detail endpoint to get complete pattern data for a specific snapshot.

    - **symbol**: Trading symbol
    - **start_time**: Optional start time filter (UTC)
    - **end_time**: Optional end time filter (UTC)
    - **limit**: Max snapshots to return (1-1000, default: 100)
    """
    from sqlalchemy import select, and_
    from app.models.patterns import MarketStateSnapshot

    # Build query
    query = select(MarketStateSnapshot).where(
        MarketStateSnapshot.symbol == symbol
    )

    if start_time:
        query = query.where(MarketStateSnapshot.snapshot_time >= start_time)

    if end_time:
        query = query.where(MarketStateSnapshot.snapshot_time <= end_time)

    # Order by time descending and limit
    query = query.order_by(MarketStateSnapshot.snapshot_time.desc()).limit(limit)

    result = await db.execute(query)
    snapshots = result.scalars().all()

    # Format response
    eastern = pytz.timezone('America/New_York')

    snapshot_list = []
    for snapshot in snapshots:
        # Convert to EST
        if snapshot.snapshot_time.tzinfo is None:
            utc_aware = pytz.UTC.localize(snapshot.snapshot_time)
            et_time = utc_aware.astimezone(eastern)
        else:
            et_time = snapshot.snapshot_time.astimezone(eastern)

        snapshot_time_est = et_time.strftime('%Y-%m-%d %H:%M:%S EST')

        # Calculate by_timeframe counts
        by_timeframe = {}
        for tf, breakdown in snapshot.timeframe_breakdown.items():
            by_timeframe[tf] = (
                breakdown.get('active_fvgs_count', 0) +
                breakdown.get('active_lps_count', 0) +
                breakdown.get('active_obs_count', 0)
            )

        snapshot_list.append({
            'snapshot_id': snapshot.snapshot_id,
            'snapshot_time': snapshot.snapshot_time,
            'snapshot_time_est': snapshot_time_est,
            'total_patterns': snapshot.total_patterns_all_timeframes,
            'by_timeframe': by_timeframe,
            'created_at': snapshot.created_at
        })

    return {
        'total': len(snapshot_list),
        'symbol': symbol,
        'snapshots': snapshot_list
    }
