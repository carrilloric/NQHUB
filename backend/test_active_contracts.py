"""
Test Active Contract Detection

Checks database for:
1. ETL job status
2. Candlestick data availability
3. Active contracts detected
"""
import asyncio
from datetime import date
from sqlalchemy import text
from app.db.session import AsyncSessionLocal


async def test_active_contracts():
    """Test active contract detection"""
    async with AsyncSessionLocal() as session:
        print("=" * 80)
        print("ACTIVE CONTRACT DETECTION TEST")
        print("=" * 80)

        # Check ETL jobs
        print("\n1. Checking ETL Jobs...")
        result = await session.execute(text("""
            SELECT id, status, zip_filename,
                   ticks_inserted, candles_created,
                   started_at, completed_at
            FROM etl_jobs
            ORDER BY created_at DESC
            LIMIT 3
        """))
        jobs = result.fetchall()

        if jobs:
            for job in jobs:
                print(f"   Job: {job[0]}")
                print(f"   Status: {job[1]}")
                print(f"   File: {job[2]}")
                print(f"   Ticks: {job[3]:,} | Candles: {job[4]:,}")
                print(f"   Started: {job[5]} | Completed: {job[6]}")
                print()
        else:
            print("   ⚠️  No ETL jobs found")

        # Check candlestick data
        print("\n2. Checking Candlestick Data...")
        result = await session.execute(text("""
            SELECT
                DATE(time_interval) as date,
                symbol,
                COUNT(*) as candle_count,
                SUM(volume) as total_volume
            FROM candlestick_daily
            GROUP BY DATE(time_interval), symbol
            ORDER BY date DESC, total_volume DESC
            LIMIT 10
        """))
        candles = result.fetchall()

        if candles:
            print(f"   Found {len(candles)} symbol/date combinations (showing top 10):")
            for row in candles:
                print(f"   {row[0]}: {row[1]} - {row[2]} candles, {row[3]:,} volume")
        else:
            print("   ⚠️  No candlestick data found")
            return

        # Check active contracts
        print("\n3. Checking Active Contracts Table...")
        result = await session.execute(text("""
            SELECT id, symbol, start_date, end_date,
                   volume_score, tick_count, is_current
            FROM active_contracts
            ORDER BY start_date DESC
            LIMIT 10
        """))
        active = result.fetchall()

        if active:
            print(f"   Found {len(active)} active contract periods:")
            for row in active:
                status = "✅ CURRENT" if row[6] else ""
                print(f"   {row[1]}: {row[2]} to {row[3] or 'ongoing'} - "
                      f"{row[4]:,} volume, {row[5]:,} ticks {status}")
        else:
            print("   ⚠️  No active contracts found")
            print("\n4. Running Active Contract Detection...")

            # Get date range from candles
            result = await session.execute(text("""
                SELECT MIN(DATE(time_interval)), MAX(DATE(time_interval))
                FROM candlestick_daily
            """))
            date_range = result.first()

            if date_range and date_range[0]:
                start_date, end_date = date_range[0], date_range[1]
                print(f"   Date range: {start_date} to {end_date}")

                # Import and run detector
                from app.etl.services.active_contract_detector import (
                    detect_active_contracts,
                    save_active_periods
                )

                print("   Detecting active contracts...")
                periods = await detect_active_contracts(session, start_date, end_date)

                print(f"   ✅ Detected {len(periods)} active contract periods")
                for p in periods:
                    print(f"      {p['symbol']}: {p['start_date']} to {p['end_date']} - "
                          f"{p['volume_score']:,} volume")

                # Save to database
                print("\n   Saving to database...")
                saved_count = await save_active_periods(session, periods)
                print(f"   ✅ Saved {saved_count} periods")

        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_active_contracts())
