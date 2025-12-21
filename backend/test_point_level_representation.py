#!/usr/bin/env python3
"""
Test: Point Level Representation (Opción B)
Verifica que EQH/EQL se muestran como PUNTOS, no zonas amplias
"""
import requests

BASE_URL = "http://localhost:8002/api/v1"

def test_point_level():
    print("="*120)
    print("🎯 TEST: POINT LEVEL REPRESENTATION (Opción B)")
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

    print(f"\n✅ Total STRONG pools: {len(pools)}\n")

    print("="*120)
    print("📍 POOLS AS POINT LEVELS (NOT ZONES):")
    print("="*120)
    print(f"{'#':<3} {'Type':<6} {'Modal Level $':<15} {'Touches':<12} {'Concentration':<15} {'Spread':<12} {'Interpretation':<30}")
    print("="*120)

    for i, pool in enumerate(pools, 1):
        modal = pool.get('modal_level') or pool['level']
        modal_touches = pool.get('modal_touches', 0) or 0
        total_touches = pool['num_touches']
        spread = pool.get('spread', 0) or 0

        concentration = (modal_touches / total_touches * 100) if total_touches > 0 else 0

        # Determine if this is a good point level or too dispersed
        if concentration >= 20:
            quality = "✅ Good point"
        elif concentration >= 10:
            quality = "⚠️  Moderate dispersion"
        else:
            quality = "❌ High dispersion"

        print(f"{i:<3} {pool['pool_type']:<6} ${modal:<14.2f} {modal_touches}/{total_touches:<9} {concentration:<14.1f}% {spread:<11.2f}pt {quality:<30}")

    # Detailed analysis
    print("\n" + "="*120)
    print("🔍 DETAILED INTERPRETATION:")
    print("="*120)

    for i, pool in enumerate(pools, 1):
        modal = pool.get('modal_level') or pool['level']
        modal_touches = pool.get('modal_touches', 0) or 0
        total_touches = pool['num_touches']
        spread = pool.get('spread', 0) or 0
        concentration = (modal_touches / total_touches * 100) if total_touches > 0 else 0

        print(f"\n{i}. {pool['pool_type']} at ${modal:.2f}")
        print(f"   📊 Total touches: {total_touches}")
        print(f"   🎯 Modal touches: {modal_touches} ({concentration:.1f}% at modal level)")
        print(f"   📏 Spread: {spread:.2f} pts (cluster dispersion)")
        print(f"   ")
        print(f"   💡 INTERPRETATION:")
        print(f"      ✓ Operational level: ${modal:.2f} (this is the precise level to watch)")
        print(f"      ✓ The {total_touches} touches are distributed across {spread:.2f} pts")
        print(f"      ✓ Only {modal_touches} touches are concentrated at ${modal:.2f}")

        if concentration < 10:
            print(f"      ⚠️  WARNING: Low concentration ({concentration:.1f}%)")
            print(f"         → This pool is highly dispersed (multiple sub-levels)")
            print(f"         → Consider it as an AREA rather than a precise level")
        else:
            print(f"      ✅ Good concentration ({concentration:.1f}%)")
            print(f"         → Clear modal level at ${modal:.2f}")

    # Key points
    print("\n" + "="*120)
    print("📝 KEY POINTS (Opción B - Point Levels):")
    print("="*120)
    print("\n✅ CORRECT INTERPRETATION:")
    print("  • EQH/EQL are shown as POINT LEVELS (e.g., 'EQH at $25313.44')")
    print("  • The 'modal level' is the OPERATIONAL LEVEL to watch")
    print("  • 'Spread' shows how dispersed the cluster is (NOT an operational zone)")
    print("  • High spread = touches are distributed, not all at modal level")
    print("")
    print("❌ INCORRECT INTERPRETATION:")
    print("  • DON'T treat spread as an operational zone")
    print("  • DON'T expect all touches to be at the modal level")
    print("  • DON'T use zone_high/zone_low for entries (they're metadata only)")
    print("")
    print("🎯 FOR TRADING:")
    print("  • Use the modal_level as your precise level (e.g., $25313.44)")
    print("  • If concentration is low (<10%), be aware it's a dispersed cluster")
    print("  • High spread (>100 pts) = multiple sub-levels merged together")

    # Check text report
    text_report = data.get('text_report', '')

    print("\n" + "="*120)
    print("📄 TEXT REPORT VERIFICATION:")
    print("="*120)

    checks = {
        "Shows 'Point Level'": "Point Level - NOT a zone" in text_report,
        "Shows 'Operational Level'": "Operational Level" in text_report,
        "Shows concentration": "Concentration" in text_report,
        "Clarifies spread meaning": "cluster dispersion" in text_report,
    }

    all_pass = True
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
        if not passed:
            all_pass = False

    print("\n" + "="*120)
    if all_pass:
        print("🎉 OPCIÓN B IMPLEMENTED - Pools shown as POINT LEVELS, not zones")
    else:
        print("❌ Some verifications failed")
    print("="*120)

if __name__ == "__main__":
    test_point_level()
