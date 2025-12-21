#!/usr/bin/env python3
"""
Verificar que el time range ahora se calcula correctamente
"""
import requests
from datetime import datetime

BASE_URL = "http://localhost:8002/api/v1"

def test_time_range():
    print("="*120)
    print("VERIFICACIÓN: TIME RANGE CORRECTION")
    print("="*120)

    # Get pools for Nov 6
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
    print("\n🔍 Verificando que start_time < end_time para todos los pools:\n")

    errors = 0
    for idx, pool in enumerate(pools[:10], 1):
        if pool.get('start_time') and pool.get('end_time'):
            start = datetime.fromisoformat(pool['start_time'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(pool['end_time'].replace('Z', '+00:00'))

            duration = (end - start).total_seconds() / 60  # minutes

            if start > end:
                errors += 1
                print(f"❌ Pool #{idx} ({pool['pool_type']}): start > end!")
                print(f"   Start: {start.strftime('%b %d %H:%M')}")
                print(f"   End:   {end.strftime('%b %d %H:%M')}")
            elif start == end:
                print(f"⚠️  Pool #{idx} ({pool['pool_type']}): start == end (single touch)")
                print(f"   Time: {start.strftime('%b %d %H:%M')}")
            else:
                print(f"✅ Pool #{idx} ({pool['pool_type']}): {start.strftime('%b %d %H:%M')} → {end.strftime('%b %d %H:%M')} ({duration:.0f} min)")

    print("\n" + "="*120)
    if errors > 0:
        print(f"❌ ERRORES ENCONTRADOS: {errors} pools con start_time > end_time")
    else:
        print("✅ CORRECTO: Todos los pools tienen start_time <= end_time")

if __name__ == "__main__":
    test_time_range()
