#!/usr/bin/env python3
"""
Integration Test: All Pattern Detectors
Tests FVG, LP, SL, and OB detection via API
"""
import requests
from datetime import datetime

BASE_URL = "http://localhost:8002/api/v1"

def print_section(title):
    print("\n" + "="*120)
    print(f"  {title}")
    print("="*120)

def test_fvg_detector():
    print_section("🔲 FAIR VALUE GAPS (FVG) DETECTOR")

    response = requests.post(
        f"{BASE_URL}/patterns/fvgs/generate",
        json={
            "symbol": "NQZ5",
            "start_date": "2025-11-06",
            "end_date": "2025-11-06",
            "timeframe": "5min"
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return False

    data = response.json()
    fvgs = data.get('fvgs', [])

    print(f"\n✅ Total FVGs detected: {len(fvgs)}")

    # Breakdown
    breakdown = data.get('breakdown', {})
    print("\n📊 Breakdown by type:")
    for fvg_type, count in breakdown.items():
        print(f"   {fvg_type}: {count}")

    # Show first 3
    if fvgs:
        print("\n🔝 Top 3 FVGs:")
        for i, fvg in enumerate(fvgs[:3], 1):
            gap_size = fvg.get('gap_size', 0)
            status = fvg.get('status', 'N/A')
            print(f"   {i}. {fvg['fvg_type']} | Gap: {gap_size:.2f} pts | Status: {status}")

    return True

def test_lp_detector():
    print_section("💧 LIQUIDITY POOLS (LP) DETECTOR")

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
        return False

    data = response.json()
    pools = data.get('pools', [])

    print(f"\n✅ Total STRONG pools: {len(pools)}")

    # Breakdown
    breakdown = data.get('breakdown', {})
    print("\n📊 Breakdown by type:")
    for pool_type, count in breakdown.items():
        print(f"   {pool_type}: {count}")

    # Show first 3 with sweep status
    if pools:
        print("\n🔝 Top 3 Pools (with V2.0 features):")
        for i, pool in enumerate(pools[:3], 1):
            modal = pool.get('modal_level') or pool['level']
            sweep_status = pool.get('sweep_status', 'N/A')
            sweep_emoji = "🔴" if sweep_status == "SWEPT" else "🟢"
            importance = pool.get('importance_score', 0)
            print(f"   {i}. {pool['pool_type']} @ ${modal:.2f} | Touches: {pool['num_touches']} | "
                  f"Score: {importance:.1f} | {sweep_emoji} {sweep_status}")

    return True

def test_session_levels_detector():
    print_section("📍 SESSION LEVELS (SL) DETECTOR")

    response = requests.post(
        f"{BASE_URL}/patterns/liquidity-pools/generate",
        json={
            "symbol": "NQZ5",
            "date": "2025-11-06",
            "timeframe": "5min",
            "pool_types": ["ASH", "ASL", "LSH", "LSL", "NYH", "NYL"]
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return False

    data = response.json()
    pools = data.get('pools', [])

    print(f"\n✅ Total session levels: {len(pools)}")

    # Group by session
    sessions = {}
    for pool in pools:
        session = pool['pool_type'][:2]  # AS, LS, NY
        if session not in sessions:
            sessions[session] = []
        sessions[session].append(pool)

    print("\n📊 By session:")
    for session, levels in sessions.items():
        session_names = {"AS": "Asian", "LS": "London", "NY": "New York"}
        print(f"   {session_names.get(session, session)}: {len(levels)} levels")

    # Show all levels
    if pools:
        print("\n📍 Session Levels:")
        for pool in pools:
            level = pool.get('modal_level') or pool['level']
            print(f"   {pool['pool_type']}: ${level:.2f}")

    return True

def test_order_blocks_detector():
    print_section("📦 ORDER BLOCKS (OB) DETECTOR")

    response = requests.post(
        f"{BASE_URL}/patterns/order-blocks/generate",
        json={
            "symbol": "NQZ5",
            "start_date": "2025-11-06",
            "end_date": "2025-11-06",
            "timeframe": "5min"
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return False

    data = response.json()
    obs = data.get('order_blocks', [])

    print(f"\n✅ Total Order Blocks: {len(obs)}")

    # Breakdown
    breakdown = data.get('breakdown', {})
    print("\n📊 Breakdown by type:")
    for ob_type, count in breakdown.items():
        print(f"   {ob_type}: {count}")

    # Show first 3
    if obs:
        print("\n🔝 Top 3 Order Blocks:")
        for i, ob in enumerate(obs[:3], 1):
            formation_time = datetime.fromisoformat(ob['formation_time'].replace('Z', '+00:00'))
            time_str = formation_time.strftime('%H:%M')
            print(f"   {i}. {ob['ob_type']} @ {time_str} | Impulse: {ob['impulse_move']:.1f} pts | Quality: {ob['quality']}")

    return True

def main():
    print("="*120)
    print("🧪 PATTERN DETECTORS - INTEGRATION TEST SUITE")
    print("="*120)
    print(f"\nDate: 2025-11-06 (NQZ5, 5min timeframe)")
    print(f"Testing: FVG, LP (with V2.0), SL, OB")

    results = {
        "FVG": test_fvg_detector(),
        "LP": test_lp_detector(),
        "SL": test_session_levels_detector(),
        "OB": test_order_blocks_detector()
    }

    # Summary
    print_section("📊 TEST SUMMARY")

    all_passed = True
    for detector, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {detector}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "="*120)
    if all_passed:
        print("🎉 ALL PATTERN DETECTORS WORKING CORRECTLY!")
    else:
        print("⚠️  Some detectors failed - check errors above")
    print("="*120)

if __name__ == "__main__":
    main()
