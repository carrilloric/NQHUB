#!/usr/bin/env python3
"""
Check actual snapshot breakdown for Nov 24, 2025 @ 09:30 EST
"""
import asyncio
from datetime import datetime
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.patterns import MarketStateSnapshot

async def check_snapshot():
    """Query the actual snapshot data"""
    async with AsyncSessionLocal() as db:
        # Nov 24, 2025 09:30 EST = 14:30 UTC
        snapshot_time = datetime(2025, 11, 24, 14, 30, 0)

        result = await db.execute(
            select(MarketStateSnapshot).where(
                MarketStateSnapshot.symbol == 'NQZ5',
                MarketStateSnapshot.snapshot_time == snapshot_time
            )
        )
        snapshot = result.scalar_one_or_none()

        if not snapshot:
            print(f"❌ No snapshot found for NQZ5 at {snapshot_time} UTC")
            return

        print(f"\n{'='*80}")
        print(f"SNAPSHOT DATA - Nov 24, 2025 @ 09:30 EST")
        print(f"{'='*80}\n")

        print(f"Snapshot ID: {snapshot.snapshot_id}")
        print(f"Symbol: {snapshot.symbol}")
        print(f"Snapshot Time (UTC): {snapshot.snapshot_time}")
        print(f"Total Patterns (All Timeframes): {snapshot.total_patterns_all_timeframes}")
        print(f"Created At: {snapshot.created_at}")

        print(f"\n{'='*80}")
        print(f"BREAKDOWN BY TIMEFRAME")
        print(f"{'='*80}\n")

        if snapshot.timeframe_breakdown:
            total_fvgs = 0
            total_lps = 0
            total_obs = 0

            for tf in ['1min', '5min', '15min', '30min', '1hr', '2hr', '4hr', '1day', '1week']:
                if tf in snapshot.timeframe_breakdown:
                    data = snapshot.timeframe_breakdown[tf]
                    fvgs = data.get('active_fvgs_count', 0)
                    lps = data.get('active_lps_count', 0)
                    obs = data.get('active_obs_count', 0)
                    tf_total = fvgs + lps + obs

                    total_fvgs += fvgs
                    total_lps += lps
                    total_obs += obs

                    print(f"{tf:>6}: {tf_total:3} patterns total")
                    print(f"        - FVGs: {fvgs:3}")
                    print(f"        - LPs:  {lps:3}")
                    print(f"        - OBs:  {obs:3}")
                    print()

            print(f"{'='*80}")
            print(f"TOTALS ACROSS ALL TIMEFRAMES")
            print(f"{'='*80}\n")
            print(f"Total FVGs:  {total_fvgs}")
            print(f"Total LPs:   {total_lps}")
            print(f"Total OBs:   {total_obs}")
            print(f"Grand Total: {total_fvgs + total_lps + total_obs}")
            print(f"\nStored Total: {snapshot.total_patterns_all_timeframes}")

            if (total_fvgs + total_lps + total_obs) != snapshot.total_patterns_all_timeframes:
                print(f"\n⚠️  WARNING: Calculated total doesn't match stored total!")
        else:
            print("⚠️  No timeframe breakdown available")

if __name__ == "__main__":
    asyncio.run(check_snapshot())
