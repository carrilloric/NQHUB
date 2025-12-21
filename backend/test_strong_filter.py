#!/usr/bin/env python3
"""
Test STRONG-only filter (FASE 4)
"""
import requests

BASE_URL = "http://localhost:8002/api/v1"

def test_strong_filter():
    print("="*120)
    print("TEST: STRONG-Only Filter (FASE 4)")
    print("="*120)

    response = requests.post(
        f"{BASE_URL}/patterns/liquidity-pools/generate",
        json={
            "symbol": "NQZ5",
            "date": "2025-11-06",
            "timeframe": "5min",
            "pool_types": ["EQH", "EQL"]
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return

    data = response.json()
    pools = data['pools']

    print(f"\n✅ Total pools returned: {len(pools)}")
    print(f"   (Expected: Only STRONG pools after filtering)\n")

    # Check breakdown
    breakdown = data.get('breakdown', {})
    print("📊 Breakdown by type:")
    for pool_type, count in breakdown.items():
        print(f"   {pool_type}: {count}")

    # Verify all are STRONG
    print("\n" + "="*120)
    print("🔍 VERIFYING ALL POOLS ARE STRONG:")
    print("="*120)

    non_strong = [p for p in pools if p['strength'] != 'STRONG']

    if non_strong:
        print(f"\n❌ ERROR: Found {len(non_strong)} NON-STRONG pools:")
        for pool in non_strong:
            print(f"   - {pool['pool_type']}: Strength = {pool['strength']}, Touches = {pool['num_touches']}")
    else:
        print(f"\n✅ PERFECT: All {len(pools)} pools are STRONG\n")

    # Show all pools
    print("="*120)
    print("🏆 ALL STRONG POOLS (sorted by importance_score):")
    print("="*120)
    print(f"{'Rank':<5} {'Type':<6} {'Score':<10} {'Touches':<8} {'Modal Level':<12} {'Spread':<8} {'Fresh (h)':<10}")
    print("="*120)

    for i, pool in enumerate(pools, 1):
        score = pool.get('importance_score', 0) or 0
        touches = pool['num_touches']
        modal = pool.get('modal_level', 0) or pool['level']
        spread = pool.get('spread', 0) or 0
        freshness = pool.get('time_freshness', 0) or 0

        print(f"{i:<5} {pool['pool_type']:<6} {score:<10.2f} {touches:<8} {modal:<12.2f} {spread:<8.2f} {freshness:<10.1f}")

    print("\n" + "="*120)
    print(f"📊 SUMMARY:")
    print(f"   Total STRONG pools: {len(pools)}")
    print(f"   EQH (Buy-Side Liquidity): {breakdown.get('EQH', 0)}")
    print(f"   EQL (Sell-Side Liquidity): {breakdown.get('EQL', 0)}")
    print("="*120)

if __name__ == "__main__":
    test_strong_filter()
