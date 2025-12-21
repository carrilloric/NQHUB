#!/usr/bin/env python3
"""
Test importance score ranking (FASE 3)
"""
import requests

BASE_URL = "http://localhost:8002/api/v1"

def test_importance_score():
    print("="*120)
    print("TEST: Importance Score Ranking (FASE 3)")
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

    pools = response.json()['pools']

    print(f"\n✅ Total pools: {len(pools)}")
    print("\n🏆 TOP 10 POOLS BY IMPORTANCE SCORE:\n")
    print(f"{'Rank':<5} {'Type':<6} {'Score':<8} {'Touches':<8} {'Strength':<8} {'Spread':<8} {'Fresh (h)':<10} {'Modal Level':<12}")
    print("="*120)

    for i, pool in enumerate(pools[:10], 1):
        score = pool.get('importance_score', 0) or 0
        touches = pool['num_touches']
        strength = pool['strength']
        spread = pool.get('spread', 0) or 0
        freshness = pool.get('time_freshness', 0) or 0
        modal = pool.get('modal_level', 0) or 0

        print(f"{i:<5} {pool['pool_type']:<6} {score:<8.2f} {touches:<8} {strength:<8} {spread:<8.2f} {freshness:<10.1f} {modal:<12.2f}")

    # Show comparison with bottom 10
    print("\n" + "="*120)
    print("📉 BOTTOM 10 POOLS BY IMPORTANCE SCORE:\n")
    print(f"{'Rank':<5} {'Type':<6} {'Score':<8} {'Touches':<8} {'Strength':<8} {'Spread':<8} {'Fresh (h)':<10} {'Modal Level':<12}")
    print("="*120)

    for i, pool in enumerate(pools[-10:], len(pools)-9):
        score = pool.get('importance_score', 0) or 0
        touches = pool['num_touches']
        strength = pool['strength']
        spread = pool.get('spread', 0) or 0
        freshness = pool.get('time_freshness', 0) or 0
        modal = pool.get('modal_level', 0) or 0

        print(f"{i:<5} {pool['pool_type']:<6} {score:<8.2f} {touches:<8} {strength:<8} {spread:<8.2f} {freshness:<10.1f} {modal:<12.2f}")

    # Show STRONG pools
    strong_pools = [p for p in pools if p['strength'] == 'STRONG']
    print("\n" + "="*120)
    print(f"💪 STRONG POOLS: {len(strong_pools)}/{len(pools)}")
    print("="*120)

    for i, pool in enumerate(strong_pools[:5], 1):
        score = pool.get('importance_score', 0) or 0
        print(f"\n{i}. {pool['pool_type']} - Score: {score:.2f}")
        print(f"   Modal Level: {pool.get('modal_level', 0):.2f}")
        print(f"   Touches: {pool['num_touches']} (modal: {pool.get('modal_touches', 0)})")
        print(f"   Spread: {pool.get('spread', 0):.2f} pts")
        print(f"   Freshness: {pool.get('time_freshness', 0):.1f} hours ago")

if __name__ == "__main__":
    test_importance_score()
