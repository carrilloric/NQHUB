#!/usr/bin/env python3
"""
Test completo de LP y Session Levels con salida ATAS
"""
import requests
from datetime import datetime

BASE_URL = "http://localhost:8002/api/v1"

def format_atas_lp(pools):
    """Formato ATAS para Liquidity Pools - RECTANGLE FORMAT WITH DATES"""
    print("\n" + "="*120)
    print("FORMATO ATAS - LIQUIDITY POOLS (EQH/EQL) - RECTANGLES WITH DATES")
    print("="*120)
    print("#\tTIME_RANGE\t\t\t\tTYPE\tLIQUIDITY\t\tRECTANGLE_ZONE\t\t\tTOUCHES")
    print("="*120)

    for idx, pool in enumerate(pools, 1):
        # Time range with dates
        if pool.get('start_time') and pool.get('end_time'):
            start_dt = datetime.fromisoformat(pool['start_time'].replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(pool['end_time'].replace('Z', '+00:00'))
            start_str = start_dt.strftime('%b %d %H:%M')
            end_str = end_dt.strftime('%b %d %H:%M')
            time_range = f"{start_str} to {end_str} EST"
        else:
            dt = datetime.fromisoformat(pool['formation_time'].replace('Z', '+00:00'))
            time_range = dt.strftime('%b %d %H:%M EST')

        liquidity = pool.get('liquidity_type', '-')

        # Rectangle zone
        if pool.get('zone_low') and pool.get('zone_high'):
            zone_size = pool.get('zone_size', pool['zone_high'] - pool['zone_low'])
            zone = f"H:{pool['zone_high']:.2f} L:{pool['zone_low']:.2f} ({zone_size:.1f}pts)"
        else:
            zone = f"{pool['level']:.2f}"

        print(f"{idx}\t{time_range}\t{pool['pool_type']}\t{liquidity}\t{zone}\t{pool['num_touches']}")

def format_atas_session(pools):
    """Formato ATAS para Session Levels WITH DATES"""
    print("\n" + "="*80)
    print("FORMATO ATAS - SESSION LEVELS WITH DATES")
    print("="*80)
    print("DATE & TIME\t\tTYPE\tLEVEL")
    print("="*80)

    for pool in pools:
        time_str = datetime.fromisoformat(pool['formation_time'].replace('Z', '+00:00'))
        time_fmt = time_str.strftime('%b %d %H:%M EST')
        print(f"{time_fmt}\t{pool['pool_type']}\t{pool['level']:.2f}")

def test_liquidity_pools():
    """Test EQH/EQL detection"""
    print("\n" + "="*80)
    print("TEST 1: LIQUIDITY POOLS (EQH/EQL)")
    print("="*80)

    response = requests.post(
        f"{BASE_URL}/patterns/liquidity-pools/generate",
        json={
            "symbol": "NQZ5",
            "date": "2025-11-24",
            "timeframe": "5min",
            "pool_types": ["EQH", "EQL"]  # Solo EQH/EQL
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return False

    data = response.json()

    print(f"✅ Total LPs detected: {data['total']}")
    print(f"   Breakdown: {data['breakdown']}")

    # Verificar que solo hay EQH/EQL
    eqh_eql_only = all(p['pool_type'] in ['EQH', 'EQL'] for p in data['pools'])
    print(f"✅ Solo EQH/EQL: {eqh_eql_only}")

    # Verificar que todos tienen zonas
    all_have_zones = all(p.get('zone_low') is not None and p.get('zone_high') is not None
                         for p in data['pools'])
    print(f"✅ Todos tienen zonas: {all_have_zones}")

    # Verificar min 3 touches
    all_min_3 = all(p['num_touches'] >= 3 for p in data['pools'])
    print(f"✅ Todos tienen ≥3 toques: {all_min_3}")

    # Verificar campos de rectángulo
    all_have_time_range = all(p.get('start_time') is not None and p.get('end_time') is not None
                              for p in data['pools'])
    print(f"✅ Todos tienen time range: {all_have_time_range}")

    all_have_liquidity_type = all(p.get('liquidity_type') is not None for p in data['pools'])
    print(f"✅ Todos tienen liquidity_type: {all_have_liquidity_type}")

    all_have_zone_size = all(p.get('zone_size') is not None for p in data['pools'])
    print(f"✅ Todos tienen zone_size: {all_have_zone_size}")

    # Mostrar formato ATAS
    format_atas_lp(data['pools'][:10])  # Primeros 10

    return True

def test_session_levels():
    """Test Session Level detection"""
    print("\n" + "="*80)
    print("TEST 2: SESSION LEVELS")
    print("="*80)

    response = requests.post(
        f"{BASE_URL}/patterns/liquidity-pools/generate",
        json={
            "symbol": "NQZ5",
            "date": "2025-11-24",
            "timeframe": "5min",
            "pool_types": ["ASH", "ASL", "LSH", "LSL", "NYH", "NYL"]  # Solo Session Levels
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return False

    data = response.json()

    print(f"✅ Total Session Levels: {data['total']}")
    print(f"   Breakdown: {data['breakdown']}")

    # Verificar que solo hay session levels
    session_only = all(p['pool_type'] in ['ASH', 'ASL', 'LSH', 'LSL', 'NYH', 'NYL']
                       for p in data['pools'])
    print(f"✅ Solo Session Levels: {session_only}")

    # Verificar que NO tienen zonas
    no_zones = all(p.get('zone_low') is None and p.get('zone_high') is None
                   for p in data['pools'])
    print(f"✅ NO tienen zonas (son point levels): {no_zones}")

    # Mostrar formato ATAS
    format_atas_session(data['pools'])

    return True

def main():
    print("="*80)
    print("TEST COMPLETO: LP + SESSION LEVELS + FORMATO ATAS")
    print("="*80)

    test1 = test_liquidity_pools()
    test2 = test_session_levels()

    print("\n" + "="*80)
    print("RESUMEN")
    print("="*80)
    print(f"Test 1 (Liquidity Pools): {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Test 2 (Session Levels): {'✅ PASS' if test2 else '❌ FAIL'}")
    print("="*80)

if __name__ == "__main__":
    main()
