#!/usr/bin/env python3
"""
Check when the 159 Order Blocks were formed
"""
import asyncio
from datetime import datetime
from sqlalchemy import select, and_, func
from app.db.session import AsyncSessionLocal
from app.models.patterns import DetectedOrderBlock, MarketStateSnapshot

async def check_ob_formation_dates():
    """Check formation dates of the 159 OBs"""
    async with AsyncSessionLocal() as db:
        # Get the snapshot
        snapshot_time = datetime(2025, 11, 24, 14, 30, 0)

        result = await db.execute(
            select(MarketStateSnapshot).where(
                MarketStateSnapshot.symbol == 'NQZ5',
                MarketStateSnapshot.snapshot_time == snapshot_time
            )
        )
        snapshot = result.scalar_one_or_none()

        if not snapshot:
            print("❌ Snapshot not found")
            return

        # Get the OB IDs from the snapshot
        ob_ids_5min = snapshot.timeframe_breakdown.get('5min', {}).get('active_ob_ids', [])

        print(f"\n{'='*80}")
        print(f"ORDER BLOCKS ANALYSIS - 5min Timeframe")
        print(f"{'='*80}\n")
        print(f"Total OB IDs in snapshot: {len(ob_ids_5min)}")

        if not ob_ids_5min:
            print("⚠️  No OB IDs found in snapshot")
            return

        # Query the actual OBs
        result = await db.execute(
            select(DetectedOrderBlock).where(
                DetectedOrderBlock.ob_id.in_(ob_ids_5min)
            ).order_by(DetectedOrderBlock.formation_time.desc())
        )
        obs = result.scalars().all()

        print(f"Total OBs found in DB: {len(obs)}\n")

        # Group by formation date
        from collections import defaultdict
        by_date = defaultdict(int)
        by_type = defaultdict(int)

        for ob in obs:
            date_key = ob.formation_time.strftime('%Y-%m-%d')
            by_date[date_key] += 1
            by_type[ob.ob_type] += 1

        print(f"{'='*80}")
        print(f"OBs BY FORMATION DATE")
        print(f"{'='*80}\n")

        for date in sorted(by_date.keys(), reverse=True):
            count = by_date[date]
            pct = (count / len(obs)) * 100
            print(f"{date}: {count:3} OBs ({pct:5.1f}%)")

        print(f"\n{'='*80}")
        print(f"OBs BY TYPE")
        print(f"{'='*80}\n")

        for ob_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
            pct = (count / len(obs)) * 100
            print(f"{ob_type:20}: {count:3} OBs ({pct:5.1f}%)")

        # Check oldest and newest
        print(f"\n{'='*80}")
        print(f"AGE RANGE")
        print(f"{'='*80}\n")

        if obs:
            oldest = min(obs, key=lambda x: x.formation_time)
            newest = max(obs, key=lambda x: x.formation_time)

            print(f"Oldest OB:")
            print(f"  Formation: {oldest.formation_time}")
            print(f"  Type: {oldest.ob_type}")
            print(f"  Status: {oldest.status}")
            print(f"  Age: {(snapshot_time - oldest.formation_time).days} days")

            print(f"\nNewest OB:")
            print(f"  Formation: {newest.formation_time}")
            print(f"  Type: {newest.ob_type}")
            print(f"  Status: {newest.status}")
            print(f"  Age: {(snapshot_time - newest.formation_time).days} days")

        # Sample 10 random OBs
        print(f"\n{'='*80}")
        print(f"SAMPLE OF 10 OBs")
        print(f"{'='*80}\n")

        import random
        sample_obs = random.sample(obs, min(10, len(obs)))

        for i, ob in enumerate(sample_obs, 1):
            age_days = (snapshot_time - ob.formation_time).days
            print(f"{i}. OB #{ob.ob_id}")
            print(f"   Type: {ob.ob_type}")
            print(f"   Formed: {ob.formation_time} ({age_days} days ago)")
            print(f"   Status: {ob.status}")
            print(f"   Range: {ob.ob_low:.2f} - {ob.ob_high:.2f}")
            print()

if __name__ == "__main__":
    asyncio.run(check_ob_formation_dates())
