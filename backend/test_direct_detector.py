#!/usr/bin/env python3
"""
Test LP detector directly (without HTTP API) to see debug output
"""
from datetime import date
from app.db.session import SessionLocal
from app.services.pattern_detection.lp_detector import LiquidityPoolDetector

def test_direct():
    print("="*120)
    print("TESTING LP DETECTOR DIRECTLY")
    print("="*120)

    db = SessionLocal()

    try:
        detector = LiquidityPoolDetector(db)

        print("\n📥 Generating pools for Nov 6, 2025...")
        result = detector.generate_liquidity_pools(
            symbol="NQZ5",
            date_val=date(2025, 11, 6),
            timeframe="5min",
            pool_types=["EQH"],
            save_to_db=False  # Don't save to avoid duplicates
        )

        print(f"\n✅ Total pools detected: {result.total}")

        # Find pools in zone 25680-25695
        target_pools = [p for p in result.pools if p.pool_type == 'EQH' and 25680 <= p.level <= 25695]

        print(f"\n📊 Pools in zone 25680-25695: {len(target_pools)}")

        for pool in target_pools:
            print(f"\n   Pool:")
            print(f"     Level: {pool.level:.2f}")
            print(f"     Zone: {pool.zone_low:.2f} - {pool.zone_high:.2f}")
            print(f"     Zone Size: {pool.zone_size:.2f}")
            print(f"     Touches: {pool.num_touches}")
            print(f"     Strength: {pool.strength}")

    finally:
        db.close()

if __name__ == "__main__":
    test_direct()
