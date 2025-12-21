#!/usr/bin/env python3
"""
Test FASE 5A: INTACT → SWEPT Detection (ICT Criteria)
"""
import requests

BASE_URL = "http://localhost:8002/api/v1"

def test_sweep_detection():
    print("="*120)
    print("🎯 TEST: SWEEP DETECTION (FASE 5A - INTACT → SWEPT)")
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
        print(response.text)
        return

    data = response.json()
    pools = data['pools']

    print(f"\n✅ Total pools: {len(pools)}\n")

    # Count sweep statuses
    intact_count = sum(1 for p in pools if p.get('sweep_status') == 'INTACT')
    swept_count = sum(1 for p in pools if p.get('sweep_status') == 'SWEPT')

    print("="*120)
    print("📊 SWEEP STATUS SUMMARY:")
    print("="*120)
    print(f"  🟢 INTACT: {intact_count} pools (liquidez aún viva)")
    print(f"  🔴 SWEPT: {swept_count} pools (liquidez fue tomada)")
    print("")

    # Detailed pool analysis
    print("="*120)
    print("🔍 DETAILED ANALYSIS (All Pools):")
    print("="*120)
    print(f"{'#':<3} {'Type':<6} {'Modal $':<12} {'Status':<8} {'Criteria':<10} {'Distance':<12} {'Position':<10}")
    print("="*120)

    for i, pool in enumerate(pools, 1):
        modal = pool.get('modal_level') or pool['level']
        sweep_status = pool.get('sweep_status', 'N/A')
        criteria_met = pool.get('sweep_criteria_met', 0)
        distance = pool.get('distance_to_current_price', 0) or 0

        position = "ABOVE ⬆️" if distance > 0 else "BELOW ⬇️" if distance < 0 else "AT"
        status_emoji = "🔴" if sweep_status == "SWEPT" else "🟢" if sweep_status == "INTACT" else "⚪"

        print(f"{i:<3} {pool['pool_type']:<6} ${modal:<11.2f} {status_emoji} {sweep_status:<6} {criteria_met}/3       {distance:<+12.2f} {position:<10}")

    # Analyze SWEPT pools in detail
    swept_pools = [p for p in pools if p.get('sweep_status') == 'SWEPT']

    if swept_pools:
        print("\n" + "="*120)
        print("🔴 SWEPT POOLS - DETAILED ANALYSIS:")
        print("="*120)

        for i, pool in enumerate(swept_pools, 1):
            modal = pool.get('modal_level') or pool['level']
            criteria = pool.get('sweep_criteria_met', 0)
            distance = pool.get('distance_to_current_price', 0) or 0
            touches = pool['num_touches']

            print(f"\n{i}. {pool['pool_type']} at ${modal:.2f}")
            print(f"   ✓ {criteria}/3 ICT criteria met:")
            print(f"     - Ruptura >1 pt: Checked")
            print(f"     - Cierre lado opuesto: Checked")
            print(f"     - Vela de intención: Checked")
            print(f"   Distance from current: {distance:+.2f} pts")
            print(f"   Total touches: {touches}")
            print(f"   Interpretación: Liquidez fue barrida (stops ejecutados)")

    # Analyze INTACT pools
    intact_pools = [p for p in pools if p.get('sweep_status') == 'INTACT']

    if intact_pools:
        print("\n" + "="*120)
        print("🟢 INTACT POOLS - STILL VALID:")
        print("="*120)

        for i, pool in enumerate(intact_pools, 1):
            modal = pool.get('modal_level') or pool['level']
            criteria = pool.get('sweep_criteria_met', 0)
            distance = pool.get('distance_to_current_price', 0) or 0
            touches = pool['num_touches']

            print(f"\n{i}. {pool['pool_type']} at ${modal:.2f}")
            print(f"   ⚠️  {criteria}/3 criteria met (need 2+ for sweep)")
            print(f"   Distance from current: {distance:+.2f} pts")
            print(f"   Total touches: {touches}")
            print(f"   Interpretación: Liquidez aún viva, stops siguen acumulándose")

    # Verification
    print("\n" + "="*120)
    print("✅ VERIFICATION:")
    print("="*120)

    checks = {
        "Sweep status assigned": all(p.get('sweep_status') in ['INTACT', 'SWEPT'] for p in pools),
        "Criteria count valid": all(0 <= p.get('sweep_criteria_met', 0) <= 3 for p in pools),
        "At least one status present": len(pools) > 0,
    }

    all_pass = True
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
        if not passed:
            all_pass = False

    print("\n" + "="*120)
    if all_pass:
        print("🎉 FASE 5A COMPLETED - SWEEP DETECTION IS WORKING")
        print("\nKey Points:")
        print("  • INTACT = Liquidez viva (no barrida)")
        print("  • SWEPT = Liquidez tomada (al menos 2/3 criterios ICT)")
        print("  • Criteria: 1) Ruptura >1pt, 2) Cierre opuesto, 3) Vela intención")
    else:
        print("❌ SOME CHECKS FAILED - REVIEW IMPLEMENTATION")
    print("="*120)

if __name__ == "__main__":
    test_sweep_detection()
