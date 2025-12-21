#!/usr/bin/env python3
"""
Mostrar valores OHLC de pools específicos para verificar si son reales
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

def verify_pool_touches(pool):
    """Verificar que los touches de un pool son reales"""
    print("="*120)
    print(f"VERIFICACIÓN DE POOL")
    print("="*120)

    print(f"\n📊 POOL INFO:")
    print(f"   ID: {pool['lp_id']}")
    print(f"   Type: {pool['pool_type']}")
    print(f"   Zone: {pool['zone_low']:.2f} - {pool['zone_high']:.2f}")
    print(f"   Zone Size: {pool.get('zone_size', 0):.2f} pts")
    print(f"   Level: {pool['level']:.2f}")
    print(f"   Touches: {pool['num_touches']}")
    print(f"   Strength: {pool['strength']}")

    touch_times = pool.get('touch_times', [])
    if not touch_times:
        print("\n❌ No touch times available")
        return

    # Get candles around the touch times
    touch_datetimes = [datetime.fromisoformat(t.replace('Z', '+00:00')) for t in touch_times]
    first_touch = min(touch_datetimes)
    last_touch = max(touch_datetimes)

    print(f"\n📥 Obteniendo velas para los touches...")
    candles = get_candles_detail("NQZ5", first_touch, last_touch)

    # Create dict for quick lookup
    candles_dict = {}
    for candle in candles:
        ts = candle['timestamp'].replace(second=0, microsecond=0)
        candles_dict[ts] = candle

    print(f"\n📋 VALORES EXACTOS DE CADA TOUCH:")
    print(f"{'Touch':<6} {'Time (UTC)':<20} {'High':<10} {'Low':<10} {'Zone?':<10} {'Distance':<15}")
    print("="*120)

    zone_low = pool['zone_low']
    zone_high = pool['zone_high']
    level = pool['level']

    touches_in_zone = 0
    touches_outside_zone = 0

    for idx, touch_time_str in enumerate(touch_times, 1):
        # Parse touch time (comes from API as UTC)
        touch_dt_utc = datetime.fromisoformat(touch_time_str.replace('Z', '+00:00'))
        touch_dt_normalized = touch_dt_utc.replace(second=0, microsecond=0)

        # Convert to EST for display
        from zoneinfo import ZoneInfo
        touch_dt_est = touch_dt_utc.astimezone(ZoneInfo("America/New_York"))

        candle = candles_dict.get(touch_dt_normalized)

        if candle:
            high = candle['high']
            low = candle['low']

            # For EQH, we check the HIGH
            if pool['pool_type'] == 'EQH':
                touched_value = high
                in_zone = zone_low <= high <= zone_high
                distance = high - level
            else:  # EQL
                touched_value = low
                in_zone = zone_low <= low <= zone_high
                distance = low - level

            if in_zone:
                touches_in_zone += 1
                zone_status = "✅ IN"
            else:
                touches_outside_zone += 1
                zone_status = "❌ OUT"

            # Show both UTC and EST times
            print(f"{idx:<6} {touch_dt_utc.strftime('%Y-%m-%d %H:%M')} UTC ({touch_dt_est.strftime('%H:%M')} EST)  H:{high:<10.2f} L:{low:<10.2f} {zone_status:<10} {distance:+.2f} pts")
        else:
            print(f"{idx:<6} {touch_dt_utc.strftime('%Y-%m-%d %H:%M')} UTC ({touch_dt_est.strftime('%H:%M')} EST)  [CANDLE NOT FOUND]")

    print("="*120)
    print(f"\n📊 RESUMEN:")
    print(f"   Touches DENTRO de la zona: {touches_in_zone}")
    print(f"   Touches FUERA de la zona: {touches_outside_zone}")

    if touches_outside_zone > 0:
        pct_outside = (touches_outside_zone / pool['num_touches']) * 100
        print(f"   % Fuera: {pct_outside:.1f}%")
        if pct_outside > 10:
            print(f"\n   ⚠️  MÁS DEL 10% DE TOUCHES ESTÁN FUERA DE LA ZONA!")
            print(f"   → Este pool podría ser FALSO")
    else:
        print(f"\n   ✅ POOL VÁLIDO: Todos los touches están dentro de la zona")

def main():
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

    # Find pools in the "false zone" area (25680-25695)
    print("="*120)
    print("BÚSQUEDA DE POOLS EN ZONA 25680-25695")
    print("="*120)

    target_pools = []
    for pool in pools:
        if pool['pool_type'] != 'EQH':
            continue

        if 25680 <= pool['level'] <= 25695:
            target_pools.append(pool)

    print(f"\n✅ Encontrados {len(target_pools)} pools EQH en rango 25680-25695")

    # Verify each pool
    for pool in target_pools[:3]:  # Check first 3
        verify_pool_touches(pool)
        print("\n")

if __name__ == "__main__":
    main()
