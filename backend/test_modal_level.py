#!/usr/bin/env python3
"""
Test modal level detection
"""
import requests

BASE_URL = "http://localhost:8002/api/v1"

def test_modal_level():
    print("="*120)
    print("TEST: Modal Level Detection (FASE 1)")
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
    print("\n🔍 Primeros 5 pools con nivel modal:\n")

    for i, pool in enumerate(pools[:5], 1):
        if pool.get('modal_level'):
            print(f"{i}. {pool['pool_type']} - Level (old): {pool['level']:.2f}")
            print(f"   → Modal Level: {pool['modal_level']:.2f}")
            print(f"   → Modal Touches: {pool['modal_touches']}/{pool['num_touches']}")
            print(f"   → Spread: {pool['spread']:.2f} pts")
            print(f"   → Zone Size (old): {pool.get('zone_size', 0):.2f} pts")
            print(f"   → Strength: {pool['strength']}\n")
        else:
            print(f"{i}. {pool['pool_type']} - NO modal level (session level?)\n")

    # Find a STRONG pool
    strong_pools = [p for p in pools if p['strength'] == 'STRONG' and p.get('modal_level')]

    if strong_pools:
        print("="*120)
        print("🎯 EJEMPLO DE POOL STRONG CON NIVEL MODAL:")
        print("="*120)
        p = strong_pools[0]
        print(f"\nPool Type: {p['pool_type']}")
        print(f"Total Touches: {p['num_touches']}")
        print(f"Modal Level: {p['modal_level']:.2f} (con {p['modal_touches']} touches en este nivel)")
        print(f"Spread Total: {p['spread']:.2f} pts")
        print(f"Strength: {p['strength']}")
        print(f"\n💡 Interpretación:")
        print(f"   De {p['num_touches']} touches totales, {p['modal_touches']} tocaron el nivel {p['modal_level']:.2f}")
        print(f"   La dispersión total del cluster es {p['spread']:.2f} pts")
        print(f"   Esto indica una concentración de liquidez en {p['modal_level']:.2f}")

if __name__ == "__main__":
    test_modal_level()
