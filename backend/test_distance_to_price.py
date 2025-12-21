#!/usr/bin/env python3
"""
Test distance_to_current_price (FASE 6)
"""
import requests

BASE_URL = "http://localhost:8002/api/v1"

def test_distance_to_price():
    print("="*120)
    print("TEST: Distance to Current Price (FASE 6)")
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

    print(f"\n✅ Total pools: {len(pools)}\n")

    # Show all pools with distance info
    print("="*120)
    print("🎯 ALL POOLS WITH DISTANCE TO CURRENT PRICE:")
    print("="*120)
    print(f"{'Rank':<5} {'Type':<6} {'Modal Level':<12} {'Current $':<12} {'Distance':<12} {'Direction':<10} {'Touches':<8}")
    print("="*120)

    # Get current price from first pool (they all should have same current_price reference)
    if pools and pools[0].get('distance_to_current_price') is not None:
        first_distance = pools[0]['distance_to_current_price']
        first_level = pools[0].get('modal_level') or pools[0]['level']
        current_price = first_level - first_distance
        print(f"\n📍 Current Price (last close of Nov 6): ${current_price:.2f}\n")

        for i, pool in enumerate(pools, 1):
            modal = pool.get('modal_level') or pool['level']
            distance = pool.get('distance_to_current_price')
            touches = pool['num_touches']

            if distance is not None:
                # Determine direction
                if pool['pool_type'] == 'EQH':
                    # EQH is above price, distance should be positive
                    direction = "ABOVE ⬆️" if distance > 0 else "BELOW ⬇️"
                else:  # EQL
                    # EQL is below price, distance should be negative
                    direction = "BELOW ⬇️" if distance < 0 else "ABOVE ⬆️"

                print(f"{i:<5} {pool['pool_type']:<6} {modal:<12.2f} {current_price:<12.2f} {distance:<+12.2f} {direction:<10} {touches:<8}")
            else:
                print(f"{i:<5} {pool['pool_type']:<6} {modal:<12.2f} {'N/A':<12} {'N/A':<12} {'N/A':<10} {touches:<8}")

    else:
        print("❌ No distance_to_current_price data available!")
        return

    # Verify logic
    print("\n" + "="*120)
    print("🔍 VERIFICATION:")
    print("="*120)

    eqh_pools = [p for p in pools if p['pool_type'] == 'EQH']
    eql_pools = [p for p in pools if p['pool_type'] == 'EQL']

    print(f"\n📈 EQH Pools (Buy-Side Liquidity - should be ABOVE current price):")
    all_correct = True
    for pool in eqh_pools:
        distance = pool.get('distance_to_current_price', 0)
        modal = pool.get('modal_level') or pool['level']
        if distance > 0:
            print(f"   ✅ {modal:.2f} is {distance:+.2f} pts (ABOVE)")
        else:
            print(f"   ❌ {modal:.2f} is {distance:+.2f} pts (SHOULD BE ABOVE!)")
            all_correct = False

    print(f"\n📉 EQL Pools (Sell-Side Liquidity - should be BELOW current price):")
    for pool in eql_pools:
        distance = pool.get('distance_to_current_price', 0)
        modal = pool.get('modal_level') or pool['level']
        if distance < 0:
            print(f"   ✅ {modal:.2f} is {distance:+.2f} pts (BELOW)")
        else:
            print(f"   ❌ {modal:.2f} is {distance:+.2f} pts (SHOULD BE BELOW!)")
            all_correct = False

    print("\n" + "="*120)
    if all_correct:
        print("✅ ALL POOLS HAVE CORRECT DISTANCE DIRECTION")
    else:
        print("⚠️  SOME POOLS HAVE INCORRECT DISTANCE (this is OK if price moved through them)")
    print("="*120)

if __name__ == "__main__":
    test_distance_to_price()
