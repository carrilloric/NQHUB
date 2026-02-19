"""
Market State Snapshot Generator

Generates market state snapshots showing all active patterns across all 9 timeframes.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytz
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.patterns import (
    DetectedFVG,
    DetectedLiquidityPool,
    DetectedOrderBlock,
    MarketStateSnapshot
)
from app.schemas.patterns import (
    FVGResponse,
    LiquidityPoolResponse,
    OrderBlockResponse
)

# 9 timeframes supported
TIMEFRAMES = ['30s', '1min', '5min', '15min', '30min', '1hr', '4hr', 'daily', 'weekly']

# Session level pool types
SESSION_LEVEL_TYPES = ['NYH', 'NYL', 'ASH', 'ASL', 'LSH', 'LSL']


class MarketStateSnapshotGenerator:
    """Generate market state snapshots for a given symbol at specific timestamps"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_snapshot(
        self,
        symbol: str,
        snapshot_time: datetime  # UTC naive
    ) -> MarketStateSnapshot:
        """
        Generate single snapshot of market state at specific timestamp

        Args:
            symbol: Trading symbol (e.g., "NQZ5")
            snapshot_time: UTC naive datetime for the snapshot

        Returns:
            MarketStateSnapshot with timeframe_breakdown populated
        """
        # IMPORTANT: Update OB states BEFORE generating snapshot
        # This ensures BROKEN OBs are not counted as ACTIVE
        await self._update_all_ob_states(symbol, snapshot_time)

        timeframe_breakdown = {}
        total_patterns = 0

        # Iterate over all 9 timeframes
        for tf in TIMEFRAMES:
            # Query active FVGs
            active_fvgs = await self._get_active_fvgs(symbol, tf, snapshot_time)

            # Query active session levels (LPs)
            active_lps = await self._get_active_session_levels(symbol, tf, snapshot_time)

            # Query active OBs
            active_obs = await self._get_active_obs(symbol, tf, snapshot_time)

            # Calculate counts
            tf_total = len(active_fvgs) + len(active_lps) + len(active_obs)
            total_patterns += tf_total

            # Store in breakdown
            timeframe_breakdown[tf] = {
                'active_fvgs_count': len(active_fvgs),
                'active_lps_count': len(active_lps),
                'active_obs_count': len(active_obs),
                'active_fvg_ids': [fvg.fvg_id for fvg in active_fvgs],
                'active_lp_ids': [lp.lp_id for lp in active_lps],
                'active_ob_ids': [ob.ob_id for ob in active_obs]
            }

        # Check if snapshot already exists
        existing = await self.db.execute(
            select(MarketStateSnapshot).where(
                and_(
                    MarketStateSnapshot.symbol == symbol,
                    MarketStateSnapshot.snapshot_time == snapshot_time
                )
            )
        )
        existing_snapshot = existing.scalar_one_or_none()

        if existing_snapshot:
            # Update existing snapshot
            existing_snapshot.total_patterns_all_timeframes = total_patterns
            existing_snapshot.timeframe_breakdown = timeframe_breakdown
            await self.db.commit()
            await self.db.refresh(existing_snapshot)
            return existing_snapshot
        else:
            # Create new snapshot
            snapshot = MarketStateSnapshot(
                symbol=symbol,
                snapshot_time=snapshot_time,
                total_patterns_all_timeframes=total_patterns,
                timeframe_breakdown=timeframe_breakdown
            )
            self.db.add(snapshot)
            await self.db.commit()
            await self.db.refresh(snapshot)
            return snapshot

    async def generate_snapshots_bulk(
        self,
        symbol: str,
        start_time: datetime,  # UTC naive
        end_time: datetime,    # UTC naive
        interval_minutes: int = 5,
        progress_job_id: str = None
    ) -> List[MarketStateSnapshot]:
        """
        Generate multiple snapshots across a time range

        Args:
            symbol: Trading symbol
            start_time: Start time (UTC naive)
            end_time: End time (UTC naive)
            interval_minutes: Minutes between snapshots
            progress_job_id: Optional job ID for progress tracking

        Returns:
            List of generated snapshots
        """
        from app.services.market_state.progress_tracker import progress_tracker

        snapshots = []
        current_time = start_time
        completed = 0

        while current_time <= end_time:
            snapshot = await self.generate_snapshot(symbol, current_time)
            snapshots.append(snapshot)
            current_time += timedelta(minutes=interval_minutes)

            # Update progress
            completed += 1
            if progress_job_id:
                progress_tracker.update_progress(progress_job_id, completed)

        return snapshots

    async def _get_active_fvgs(
        self,
        symbol: str,
        timeframe: str,
        snapshot_time: datetime
    ) -> List[DetectedFVG]:
        """Get active FVGs (UNMITIGATED) formed before snapshot_time"""
        result = await self.db.execute(
            select(DetectedFVG).where(
                and_(
                    DetectedFVG.symbol == symbol,
                    DetectedFVG.timeframe == timeframe,
                    DetectedFVG.formation_time <= snapshot_time,
                    DetectedFVG.status == "UNMITIGATED"
                )
            )
        )
        return result.scalars().all()

    async def _get_active_session_levels(
        self,
        symbol: str,
        timeframe: str,
        snapshot_time: datetime
    ) -> List[DetectedLiquidityPool]:
        """Get active session levels (UNMITIGATED or RESPECTED) formed before snapshot_time"""
        result = await self.db.execute(
            select(DetectedLiquidityPool).where(
                and_(
                    DetectedLiquidityPool.symbol == symbol,
                    DetectedLiquidityPool.timeframe == timeframe,
                    DetectedLiquidityPool.formation_time <= snapshot_time,
                    DetectedLiquidityPool.pool_type.in_(SESSION_LEVEL_TYPES),
                    DetectedLiquidityPool.status.in_(["UNMITIGATED", "RESPECTED"])
                )
            )
        )
        return result.scalars().all()

    async def _get_active_obs(
        self,
        symbol: str,
        timeframe: str,
        snapshot_time: datetime
    ) -> List[DetectedOrderBlock]:
        """Get active OBs (ACTIVE) formed before snapshot_time"""
        result = await self.db.execute(
            select(DetectedOrderBlock).where(
                and_(
                    DetectedOrderBlock.symbol == symbol,
                    DetectedOrderBlock.timeframe == timeframe,
                    DetectedOrderBlock.formation_time <= snapshot_time,
                    DetectedOrderBlock.status == "ACTIVE"
                )
            )
        )
        return result.scalars().all()

    async def get_snapshot_detail(
        self,
        symbol: str,
        snapshot_time: datetime
    ) -> Dict[str, Any]:
        """
        Get snapshot with full pattern details (for /detail endpoint)

        Returns dict with complete data for all timeframes including full pattern objects
        """
        # Get snapshot
        result = await self.db.execute(
            select(MarketStateSnapshot).where(
                and_(
                    MarketStateSnapshot.symbol == symbol,
                    MarketStateSnapshot.snapshot_time == snapshot_time
                )
            )
        )
        snapshot = result.scalar_one_or_none()

        if not snapshot:
            return None

        # Build response with full pattern data
        timeframes_data = {}

        for tf, breakdown in snapshot.timeframe_breakdown.items():
            # Fetch full FVG objects
            fvg_ids = breakdown.get('active_fvg_ids', [])
            active_fvgs = []
            if fvg_ids:
                result = await self.db.execute(
                    select(DetectedFVG).where(DetectedFVG.fvg_id.in_(fvg_ids))
                )
                active_fvgs = result.scalars().all()

            # Fetch full LP objects (session levels only)
            lp_ids = breakdown.get('active_lp_ids', [])
            active_lps = []
            if lp_ids:
                result = await self.db.execute(
                    select(DetectedLiquidityPool).where(
                        DetectedLiquidityPool.lp_id.in_(lp_ids)
                    )
                )
                active_lps = result.scalars().all()

            # Fetch full OB objects
            ob_ids = breakdown.get('active_ob_ids', [])
            active_obs = []
            if ob_ids:
                result = await self.db.execute(
                    select(DetectedOrderBlock).where(
                        DetectedOrderBlock.ob_id.in_(ob_ids)
                    )
                )
                active_obs = result.scalars().all()

            # Calculate bullish/bearish counts
            bullish_count = (
                sum(1 for fvg in active_fvgs if fvg.fvg_type == "BULLISH") +
                sum(1 for ob in active_obs if "BULLISH" in ob.ob_type.upper())
            )
            bearish_count = (
                sum(1 for fvg in active_fvgs if fvg.fvg_type == "BEARISH") +
                sum(1 for ob in active_obs if "BEARISH" in ob.ob_type.upper())
            )

            timeframes_data[tf] = {
                'summary': {
                    'active_fvgs_count': len(active_fvgs),
                    'active_lps_count': len(active_lps),
                    'active_obs_count': len(active_obs),
                    'bullish_count': bullish_count,
                    'bearish_count': bearish_count
                },
                'active_fvgs': [FVGResponse.from_orm(fvg).dict() for fvg in active_fvgs],
                'active_session_levels': [LiquidityPoolResponse.from_orm(lp).dict() for lp in active_lps],
                'active_obs': [OrderBlockResponse.from_orm(ob).dict() for ob in active_obs]
            }

        # Build by_timeframe summary
        by_timeframe = {}
        for tf, data in timeframes_data.items():
            by_timeframe[tf] = (
                data['summary']['active_fvgs_count'] +
                data['summary']['active_lps_count'] +
                data['summary']['active_obs_count']
            )

        # Format snapshot_time_est
        eastern = pytz.timezone('America/New_York')
        if snapshot.snapshot_time.tzinfo is None:
            # UTC naive -> make aware as UTC -> convert to ET
            utc_aware = pytz.UTC.localize(snapshot.snapshot_time)
            et_time = utc_aware.astimezone(eastern)
        else:
            et_time = snapshot.snapshot_time.astimezone(eastern)

        snapshot_time_est = et_time.strftime('%Y-%m-%d %H:%M:%S EST')

        return {
            'snapshot_time': snapshot.snapshot_time,
            'snapshot_time_est': snapshot_time_est,
            'symbol': snapshot.symbol,
            'summary': {
                'total_patterns_all_timeframes': snapshot.total_patterns_all_timeframes,
                'by_timeframe': by_timeframe
            },
            'timeframes': timeframes_data
        }

    async def _update_all_ob_states(
        self,
        symbol: str,
        up_to_time: datetime  # UTC naive
    ) -> None:
        """
        Update Order Block states for all timeframes before generating snapshot

        This method calls update_ob_states() for each timeframe to ensure
        BROKEN OBs are not counted as ACTIVE in the snapshot.

        Args:
            symbol: Trading symbol
            up_to_time: Check price action up to this time (UTC naive)
        """
        from app.db.session import SessionLocal
        from app.services.pattern_detection import OrderBlockDetector

        # Convert to UTC aware for OB detector
        up_to_time_utc = up_to_time.replace(tzinfo=pytz.UTC) if up_to_time.tzinfo is None else up_to_time.astimezone(pytz.UTC)

        # Use synchronous DB session for OB detector
        # OB detector uses sync Session, AsyncSession cannot be used
        sync_db = SessionLocal()
        try:
            detector = OrderBlockDetector(sync_db)

            # Update OB states for each timeframe
            for tf in TIMEFRAMES:
                detector.update_ob_states(
                    symbol=symbol,
                    timeframe=tf,
                    up_to_time=up_to_time_utc
                )
        finally:
            sync_db.close()
