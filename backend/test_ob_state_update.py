#!/usr/bin/env python3
"""
Test Order Block State Update Functionality

Tests the update_ob_states() method and API endpoint with real data.
"""
import asyncio
from datetime import datetime
import pytz
from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.models.patterns import DetectedOrderBlock

async def test_ob_state_update():
    """Test OB state update with real data"""
    async with AsyncSessionLocal() as db:
        print(f"\n{'='*80}")
        print("ORDER BLOCK STATE UPDATE TEST")
        print(f"{'='*80}\n")

        # Count OBs by status BEFORE update
        result = await db.execute(
            select(
                DetectedOrderBlock.status,
                func.count(DetectedOrderBlock.ob_id).label('count')
            ).where(
                DetectedOrderBlock.symbol == 'NQZ5',
                DetectedOrderBlock.timeframe == '5min'
            ).group_by(DetectedOrderBlock.status)
        )

        status_counts_before = {row.status: row.count for row in result}

        print("BEFORE UPDATE:")
        print(f"{'='*80}")
        for status, count in sorted(status_counts_before.items()):
            print(f"  {status:10}: {count:3} OBs")
        print(f"\n  Total: {sum(status_counts_before.values())} OBs\n")

        # Get sample of old ACTIVE OBs
        result = await db.execute(
            select(DetectedOrderBlock).where(
                DetectedOrderBlock.symbol == 'NQZ5',
                DetectedOrderBlock.timeframe == '5min',
                DetectedOrderBlock.status == 'ACTIVE'
            ).order_by(DetectedOrderBlock.formation_time).limit(5)
        )
        old_obs = result.scalars().all()

        if old_obs:
            print("SAMPLE OF OLDEST ACTIVE OBs:")
            print(f"{'='*80}")
            for ob in old_obs:
                age_days = (datetime.now(pytz.UTC) - ob.formation_time.replace(tzinfo=pytz.UTC)).days
                print(f"  OB #{ob.ob_id}")
                print(f"    Type: {ob.ob_type}")
                print(f"    Formed: {ob.formation_time} ({age_days} days ago)")
                print(f"    Range: {ob.ob_low:.2f} - {ob.ob_high:.2f}")
                print()

if __name__ == "__main__":
    asyncio.run(test_ob_state_update())
