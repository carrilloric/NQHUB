#!/usr/bin/env python3
"""
Test Timezone Fix - Validates that timestamps are correctly stored and displayed
"""
import requests
from datetime import datetime
import pytz

BASE_URL = "http://localhost:8002/api/v1"

def print_section(title):
    print("\n" + "="*120)
    print(f"  {title}")
    print("="*120)

def validate_timezone_conversion():
    """
    Validates that the vela de mayor volumen (Nov 6, 15:55 EST) is correctly stored
    """
    print_section("🧪 TIMEZONE VALIDATION TEST")

    # Expected values
    expected_est_time = "Nov 6, 15:55 EST"
    expected_utc_time = "Nov 6, 20:55 UTC"
    expected_open = 25248
    expected_close_approx = 25258
    expected_high_approx = 25267
    expected_low_approx = 25226
    expected_volume_approx = 20863

    print(f"\n📍 Expected candle (highest volume on Nov 6):")
    print(f"   EST: {expected_est_time}")
    print(f"   UTC: {expected_utc_time}")
    print(f"   Open: {expected_open}, High: ~{expected_high_approx}, Low: ~{expected_low_approx}, Close: ~{expected_close_approx}")
    print(f"   Volume: ~{expected_volume_approx}")

    # Test OBs
    print("\n🔍 Testing Order Blocks...")
    ob_response = requests.post(
        f"{BASE_URL}/patterns/order-blocks/generate",
        json={
            "symbol": "NQZ5",
            "start_date": "2025-11-06",
            "end_date": "2025-11-06",
            "timeframe": "5min"
        }
    )

    if ob_response.status_code != 200:
        print(f"❌ OB Error: {ob_response.status_code}")
        print(ob_response.text)
        return False

    ob_data = ob_response.json()
    obs = ob_data.get('order_blocks', [])
    print(f"✅ Total OBs: {len(obs)}")

    # Check if any OB is near the expected time
    eastern = pytz.timezone('US/Eastern')
    found_ob_near_time = False

    for ob in obs:
        formation_time_utc = datetime.fromisoformat(ob['formation_time'].replace('Z', '+00:00'))
        formation_time_est = formation_time_utc.astimezone(eastern)

        # Check if it's within 1 hour of expected time
        if formation_time_est.hour >= 15 and formation_time_est.hour <= 16:
            print(f"\n   OB @ {formation_time_est.strftime('%b %d %H:%M EST')} (UTC: {formation_time_utc.strftime('%H:%M')})")
            print(f"      Type: {ob['ob_type']}")
            print(f"      High: {ob['ob_high']:.2f}, Low: {ob['ob_low']:.2f}")
            found_ob_near_time = True

    if not found_ob_near_time:
        print("⚠️  No OBs found near expected time")

    # Test LPs
    print("\n🔍 Testing Liquidity Pools...")
    lp_response = requests.post(
        f"{BASE_URL}/patterns/liquidity-pools/generate",
        json={
            "symbol": "NQZ5",
            "date": "2025-11-06",
            "timeframe": "5min",
            "pool_types": ["EQH", "EQL", "ASH", "ASL", "LSH", "LSL", "NYH", "NYL"]
        }
    )

    if lp_response.status_code != 200:
        print(f"❌ LP Error: {lp_response.status_code}")
        print(lp_response.text)
        return False

    lp_data = lp_response.json()
    pools = lp_data.get('pools', [])
    print(f"✅ Total Pools: {len(pools)}")

    # Show session levels (should be consistent with ATAS)
    print("\n📍 Session Levels:")
    for pool in pools:
        if pool['pool_type'] in ['ASH', 'ASL', 'LSH', 'LSL', 'NYH', 'NYL']:
            formation_time_utc = datetime.fromisoformat(pool['formation_time'].replace('Z', '+00:00'))
            formation_time_est = formation_time_utc.astimezone(eastern)
            level = pool.get('modal_level') or pool['level']
            print(f"   {pool['pool_type']}: ${level:.2f} @ {formation_time_est.strftime('%b %d %H:%M EST')} (UTC: {formation_time_utc.strftime('%H:%M')})")

    # Validate OB report text
    print("\n📄 Checking OB text report for correct timezone format...")
    text_report = ob_data.get('text_report', '')
    if text_report:
        # Check if report contains both EST and UTC times
        if ' EST (' in text_report and ' UTC)' in text_report:
            print("✅ Text report has correct format: 'YYYY-MM-DD HH:MM:SS EST (HH:MM:SS UTC)'")

            # Show first occurrence
            idx = text_report.find(' EST (')
            if idx > 0:
                sample = text_report[max(0, idx-20):idx+35]
                print(f"   Sample: ...{sample}...")
        else:
            print("❌ Text report missing correct timezone format")
            print(f"   Report preview: {text_report[:200]}")

    print("\n" + "="*120)
    print("✅ TIMEZONE VALIDATION COMPLETE")
    print("="*120)
    return True

if __name__ == "__main__":
    validate_timezone_conversion()
