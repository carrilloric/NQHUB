#!/usr/bin/env python3
"""
Test post-clustering by proximity (FASE 2)
Verify that pools within 20 pts are being merged
"""
import requests

BASE_URL = "http://localhost:8002/api/v1"

def test_post_clustering():
    print("="*120)
    print("TEST: Post-Clustering by Proximity (FASE 2)")
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

    print(f"\n✅ Total pools AFTER post-clustering: {len(pools)}")
    print(f"   (Expected: Significantly less than 61 after merging pools within 20 pts)\n")

    # Check breakdown
    breakdown = data.get('breakdown', {})
    print("📊 Breakdown by type:")
    for pool_type, count in breakdown.items():
        print(f"   {pool_type}: {count}")

    # Check for proximity violations (pools too close to each other)
    print("\n" + "="*120)
    print("🔍 CHECKING FOR PROXIMITY VIOLATIONS (pools < 20 pts apart):")
    print("="*120)

    # Separate EQH and EQL
    eqh_pools = sorted([p for p in pools if p['pool_type'] == 'EQH'], key=lambda p: p.get('modal_level') or p['level'])
    eql_pools = sorted([p for p in pools if p['pool_type'] == 'EQL'], key=lambda p: p.get('modal_level') or p['level'])

    violations = 0

    print("\n📈 EQH Pools (Buy-Side Liquidity):")
    for i in range(len(eqh_pools) - 1):
        level1 = eqh_pools[i].get('modal_level') or eqh_pools[i]['level']
        level2 = eqh_pools[i+1].get('modal_level') or eqh_pools[i+1]['level']
        distance = abs(level2 - level1)

        if distance < 20:
            violations += 1
            print(f"   ❌ VIOLATION: Pool at {level1:.2f} and {level2:.2f} are only {distance:.2f} pts apart!")
        else:
            print(f"   ✅ Pool at {level1:.2f} → next at {level2:.2f} ({distance:.2f} pts)")

    print("\n📉 EQL Pools (Sell-Side Liquidity):")
    for i in range(len(eql_pools) - 1):
        level1 = eql_pools[i].get('modal_level') or eql_pools[i]['level']
        level2 = eql_pools[i+1].get('modal_level') or eql_pools[i+1]['level']
        distance = abs(level2 - level1)

        if distance < 20:
            violations += 1
            print(f"   ❌ VIOLATION: Pool at {level1:.2f} and {level2:.2f} are only {distance:.2f} pts apart!")
        else:
            print(f"   ✅ Pool at {level1:.2f} → next at {level2:.2f} ({distance:.2f} pts)")

    print("\n" + "="*120)
    if violations > 0:
        print(f"❌ FOUND {violations} PROXIMITY VIOLATIONS (post-clustering may not be working)")
    else:
        print("✅ NO VIOLATIONS: All pools are at least 20 pts apart (post-clustering working correctly)")

    # Show top 10 pools
    print("\n" + "="*120)
    print("🏆 TOP 10 POOLS AFTER POST-CLUSTERING:")
    print("="*120)
    print(f"{'Rank':<5} {'Type':<6} {'Score':<8} {'Touches':<8} {'Strength':<8} {'Modal Level':<12}")
    print("="*120)

    for i, pool in enumerate(pools[:10], 1):
        score = pool.get('importance_score', 0) or 0
        touches = pool['num_touches']
        strength = pool['strength']
        modal = pool.get('modal_level', 0) or pool['level']

        print(f"{i:<5} {pool['pool_type']:<6} {score:<8.2f} {touches:<8} {strength:<8} {modal:<12.2f}")

if __name__ == "__main__":
    test_post_clustering()
