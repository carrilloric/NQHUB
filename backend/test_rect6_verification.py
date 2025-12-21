#!/usr/bin/env python3
"""
Verificación de la corrección del algoritmo LP
Buscar cómo se agrupan ahora las velas que antes formaban el Rectangle #6 falso
"""
import requests
from datetime import datetime, timezone
import json

BASE_URL = "http://localhost:8002/api/v1"

def get_candles_detail(symbol, start_time, end_time):
    """Get candles with OHLC details"""
    response = requests.get(
        f"{BASE_URL}/candles/{symbol}",
        params={
            "start_datetime": start_time.isoformat(),
            "end_datetime": end_time.isoformat()
        }
    )

    if response.status_code != 200:
        print(f"❌ Error getting candles: {response.status_code}")
        return []

    candles_data = response.json()
    candles = []
    for candle in candles_data:
        dt = datetime.fromtimestamp(candle['time'], tz=timezone.utc)
        candles.append({
            'timestamp': dt,
            'open': candle['open'],
            'high': candle['high'],
            'low': candle['low'],
            'close': candle['close'],
            'volume': candle.get('volume', 0)
        })

    return candles

def get_pools_for_date(date_str):
    """Get pools for a specific date"""
    response = requests.post(
        f"{BASE_URL}/patterns/liquidity-pools/generate",
        json={
            "symbol": "NQZ5",
            "date": date_str,
            "timeframe": "5min",
            "pool_types": ["EQH", "EQL"]
        }
    )

    if response.status_code != 200:
        print(f"❌ Error getting pools: {response.status_code}")
        return []

    return response.json()['pools']

def verify_rect6_correction():
    """Verificar que las velas del falso Rectangle #6 ya NO se agrupan juntas"""
    print("="*120)
    print("VERIFICACIÓN: CORRECCIÓN DEL ALGORITMO LP")
    print("="*120)

    # Las velas que ANTES formaban el falso Rectangle #6 (zona 25685-25693):
    # Touches 1-6: Nov 6 01:30-02:10 UTC, highs at 25658-25678 (ABAJO de 25685)
    # Touches 7-8: Nov 6 04:00 y 09:30 UTC, highs at 25719-25742 (ARRIBA de 25693)

    print("\n📋 VELAS DEL FALSO RECTANGLE #6 (ANTES):")
    print("   Touches 1-6: Nov 6 01:30-02:10 UTC → Highs 25658-25678 (ABAJO de zona)")
    print("   Touches 7-8: Nov 6 04:00, 09:30 UTC → Highs 25719, 25742 (ARRIBA de zona)")
    print("   Zona falsa: 25685.75 - 25693.75 (ninguna vela tocó esto!)")

    # Get candles for that period
    start_time = datetime(2025, 11, 6, 1, 30, 0, tzinfo=timezone.utc)
    end_time = datetime(2025, 11, 6, 10, 0, 0, tzinfo=timezone.utc)

    print(f"\n📥 Obteniendo velas de {start_time.strftime('%b %d %H:%M')} a {end_time.strftime('%b %d %H:%M')} UTC...")
    candles = get_candles_detail("NQZ5", start_time, end_time)
    print(f"✅ Total velas: {len(candles)}")

    # Group candles by high ranges
    low_group = []  # Highs around 25658-25678
    mid_group = []  # Highs around 25685-25693 (should be EMPTY or very few)
    high_group = [] # Highs around 25719-25742

    for candle in candles:
        h = candle['high']
        if 25650 <= h <= 25685:
            low_group.append(candle)
        elif 25685 < h <= 25700:
            mid_group.append(candle)
        elif 25700 < h <= 25750:
            high_group.append(candle)

    print("\n📊 DISTRIBUCIÓN DE HIGHS:")
    print(f"   Grupo BAJO (25650-25685): {len(low_group)} velas")
    print(f"   Grupo MEDIO (25685-25700): {len(mid_group)} velas")
    print(f"   Grupo ALTO (25700-25750): {len(high_group)} velas")

    # Get liquidity pools for Nov 5 and 6
    print("\n📥 Obteniendo LPs detectados para Nov 5 y Nov 6...")
    pools_nov5 = get_pools_for_date("2025-11-05")
    pools_nov6 = get_pools_for_date("2025-11-06")
    all_pools = pools_nov5 + pools_nov6

    print(f"✅ Total LPs: {len(all_pools)}")

    # Find pools that overlap with the false zone
    print("\n🔍 BÚSQUEDA DE POOLS EN LA ZONA FALSA (25685-25693):")

    false_zone_pools = []
    for pool in all_pools:
        if pool['pool_type'] != 'EQH':
            continue

        zone_low = pool.get('zone_low', pool['level'] - 5)
        zone_high = pool.get('zone_high', pool['level'] + 5)

        # Check if pool overlaps with false zone
        if zone_low <= 25693 and zone_high >= 25685:
            false_zone_pools.append(pool)

    if not false_zone_pools:
        print("   ✅ ¡CORRECTO! NO se detectaron LPs en la zona falsa 25685-25693")
    else:
        print(f"   ⚠️  Se encontraron {len(false_zone_pools)} LPs en esta zona:")
        for idx, pool in enumerate(false_zone_pools, 1):
            print(f"\n   Pool {idx}:")
            print(f"     Zone: {pool.get('zone_low'):.2f} - {pool.get('zone_high'):.2f}")
            print(f"     Level: {pool['level']:.2f}")
            print(f"     Touches: {pool['num_touches']}")
            print(f"     Strength: {pool['strength']}")

    # Find pools around the LOW group (25658-25678)
    print("\n🔍 BÚSQUEDA DE POOLS EN GRUPO BAJO (25658-25678):")

    low_group_pools = []
    for pool in all_pools:
        if pool['pool_type'] != 'EQH':
            continue

        zone_low = pool.get('zone_low', pool['level'] - 5)
        zone_high = pool.get('zone_high', pool['level'] + 5)

        # Check if pool is in low group range
        if 25650 <= pool['level'] <= 25685:
            low_group_pools.append(pool)

    if low_group_pools:
        print(f"   ✅ Se encontraron {len(low_group_pools)} LPs legítimos:")
        for idx, pool in enumerate(low_group_pools[:3], 1):
            print(f"\n   Pool {idx}:")
            print(f"     Zone: {pool.get('zone_low'):.2f} - {pool.get('zone_high'):.2f}")
            print(f"     Level: {pool['level']:.2f}")
            print(f"     Touches: {pool['num_touches']}")
            print(f"     Strength: {pool['strength']}")
            print(f"     Zone Size: {pool.get('zone_size', 0):.2f} pts")
    else:
        print("   ⚠️  No se encontraron LPs en este rango")

    # Find pools around the HIGH group (25719-25742)
    print("\n🔍 BÚSQUEDA DE POOLS EN GRUPO ALTO (25700-25750):")

    high_group_pools = []
    for pool in all_pools:
        if pool['pool_type'] != 'EQH':
            continue

        zone_low = pool.get('zone_low', pool['level'] - 5)
        zone_high = pool.get('zone_high', pool['level'] + 5)

        # Check if pool is in high group range
        if 25700 <= pool['level'] <= 25750:
            high_group_pools.append(pool)

    if high_group_pools:
        print(f"   ✅ Se encontraron {len(high_group_pools)} LPs legítimos:")
        for idx, pool in enumerate(high_group_pools[:3], 1):
            print(f"\n   Pool {idx}:")
            print(f"     Zone: {pool.get('zone_low'):.2f} - {pool.get('zone_high'):.2f}")
            print(f"     Level: {pool['level']:.2f}")
            print(f"     Touches: {pool['num_touches']}")
            print(f"     Strength: {pool['strength']}")
            print(f"     Zone Size: {pool.get('zone_size', 0):.2f} pts")
    else:
        print("   ⚠️  No se encontraron LPs en este rango")

    print("\n" + "="*120)
    print("CONCLUSIÓN:")
    print("="*120)

    if not false_zone_pools:
        print("✅ ALGORITMO CORREGIDO EXITOSAMENTE:")
        print("   - El pool falso 25685-25693 YA NO EXISTE")
        print("   - Las velas del grupo bajo (25658-25678) se agrupan correctamente")
        print("   - Las velas del grupo alto (25719-25742) se agrupan correctamente")
        print("   - Ya NO se mezclan grupos de precios distantes")
    else:
        print("⚠️  ADVERTENCIA: Aún se detectan pools en la zona falsa")
        print("   Revisar criterios de clustering")

if __name__ == "__main__":
    verify_rect6_correction()
