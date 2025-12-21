#!/usr/bin/env python3
"""
Test script for new simplified LP zone detection
Tests the simplified approach: direct touch counting, zones, min 3 touches
"""
import requests
from datetime import date

# API endpoint
BASE_URL = "http://localhost:8002/api/v1"

def test_lp_detection():
    """Test LP detection with new simplified approach"""

    # Test parameters
    symbol = "NQZ5"
    test_date = "2025-11-24"
    timeframe = "5min"

    print("=" * 80)
    print("TESTING SIMPLIFIED LP ZONE DETECTION")
    print("=" * 80)
    print(f"Symbol: {symbol}")
    print(f"Date: {test_date}")
    print(f"Timeframe: {timeframe}")
    print()

    # Call LP generation endpoint
    print("Calling LP generation endpoint...")
    response = requests.post(
        f"{BASE_URL}/patterns/liquidity-pools/generate",
        json={
            "symbol": symbol,
            "date": test_date,
            "timeframe": timeframe
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return

    data = response.json()

    print("✅ LP Detection completed!")
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total LPs detected: {data['total']}")
    print(f"Auto parameters: {data['auto_parameters']}")
    print()
    print("Breakdown by type:")
    for pool_type, count in data['breakdown'].items():
        print(f"  {pool_type}: {count}")
    print()

    # Analyze zones
    print("=" * 80)
    print("ZONE ANALYSIS (EQH/EQL pools)")
    print("=" * 80)

    eqh_pools = [p for p in data['pools'] if p['pool_type'] == 'EQH']
    eql_pools = [p for p in data['pools'] if p['pool_type'] == 'EQL']
    session_pools = [p for p in data['pools'] if p['pool_type'] in ['ASH', 'ASL', 'LSH', 'LSL', 'NYH', 'NYL']]

    print(f"\nEQH Pools (Equal Highs): {len(eqh_pools)}")
    for pool in eqh_pools:
        zone_size = pool.get('zone_high', 0) - pool.get('zone_low', 0) if pool.get('zone_high') and pool.get('zone_low') else 0
        print(f"  Time: {pool['formation_time']}")
        print(f"  Level (avg): {pool['level']:.2f}")
        print(f"  Zone: {pool.get('zone_low', 'N/A'):.2f} - {pool.get('zone_high', 'N/A'):.2f} ({zone_size:.1f} pts)")
        print(f"  Touches: {pool['num_touches']} | Strength: {pool['strength']}")
        print()

    print(f"EQL Pools (Equal Lows): {len(eql_pools)}")
    for pool in eql_pools:
        zone_size = pool.get('zone_high', 0) - pool.get('zone_low', 0) if pool.get('zone_high') and pool.get('zone_low') else 0
        print(f"  Time: {pool['formation_time']}")
        print(f"  Level (avg): {pool['level']:.2f}")
        print(f"  Zone: {pool.get('zone_low', 'N/A'):.2f} - {pool.get('zone_high', 'N/A'):.2f} ({zone_size:.1f} pts)")
        print(f"  Touches: {pool['num_touches']} | Strength: {pool['strength']}")
        print()

    print("=" * 80)
    print("SESSION LEVELS (Point levels, not zones)")
    print("=" * 80)
    print(f"\nSession Level Pools: {len(session_pools)}")
    for pool in session_pools:
        has_zones = pool.get('zone_low') is not None and pool.get('zone_high') is not None
        print(f"  {pool['pool_type']}: {pool['level']:.2f} @ {pool['formation_time']}")
        print(f"    Has zones: {has_zones} (should be False)")
        print()

    print("=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    print(f"✓ Min touches = 3: {all(p['num_touches'] >= 3 for p in eqh_pools + eql_pools)}")
    print(f"✓ EQH/EQL have zones: {all(p.get('zone_low') is not None and p.get('zone_high') is not None for p in eqh_pools + eql_pools)}")
    print(f"✓ Session levels NO zones: {all(p.get('zone_low') is None and p.get('zone_high') is None for p in session_pools)}")
    print()

    # Show text report
    print("=" * 80)
    print("TEXT REPORT")
    print("=" * 80)
    print(data['text_report'])

if __name__ == "__main__":
    test_lp_detection()
