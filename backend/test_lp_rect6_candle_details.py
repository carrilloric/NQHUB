#!/usr/bin/env python3
"""
Análisis detallado de las velas que tocaron el Rectangle #6
Muestra los valores OHLC de cada touch
"""
import requests
from datetime import datetime, timezone, timedelta
import json

BASE_URL = "http://localhost:8002/api/v1"

def get_candles_for_timerange(symbol, start_time, end_time):
    """Get candles for a specific time range"""
    # Format datetimes for API (ISO format)
    start_str = start_time.isoformat()
    end_str = end_time.isoformat()

    response = requests.get(
        f"{BASE_URL}/candles/{symbol}",
        params={
            "start_datetime": start_str,
            "end_datetime": end_str
        }
    )

    if response.status_code != 200:
        print(f"❌ Error getting candles: {response.status_code}")
        print(f"   URL: {response.url}")
        print(f"   Response: {response.text[:200]}")
        return []

    candles_data = response.json()

    # Convert from TradingView format (time as unix timestamp) to dict with datetime
    candles = []
    for candle in candles_data:
        # Convert unix timestamp back to datetime
        dt = datetime.fromtimestamp(candle['time'], tz=timezone.utc)
        candles.append({
            'timestamp': dt.isoformat(),
            'open': candle['open'],
            'high': candle['high'],
            'low': candle['low'],
            'close': candle['close'],
            'volume': candle.get('volume', 0)
        })

    return candles

def analyze_rect6_touches():
    """Analizar los valores exactos de cada touch del Rectangle #6"""
    print("="*120)
    print("RECTANGLE #6 - VALORES EXACTOS DE CADA TOUCH")
    print("Zone: 25685.75 (Low) - 25693.75 (High)")
    print("="*120)

    # Rectangle #6 data from previous analysis
    rect6_touches_utc = [
        "2025-11-06T01:30:00Z",
        "2025-11-06T01:40:00Z",
        "2025-11-06T01:55:00Z",
        "2025-11-06T02:00:00Z",
        "2025-11-06T02:05:00Z",
        "2025-11-06T02:10:00Z",
        "2025-11-06T04:00:00Z",
        "2025-11-06T09:30:00Z"
    ]

    zone_high = 25693.75
    zone_low = 25685.75
    level = 25690.91

    # Get candles for the entire period
    start_time = datetime.fromisoformat(rect6_touches_utc[0].replace('Z', '+00:00'))
    end_time = datetime.fromisoformat(rect6_touches_utc[-1].replace('Z', '+00:00')) + timedelta(days=1)

    print(f"\n📥 Obteniendo velas desde {start_time.strftime('%b %d %H:%M')} hasta {end_time.strftime('%b %d %H:%M')} UTC...")

    candles = get_candles_for_timerange("NQZ5", start_time, end_time)

    if not candles:
        print("❌ No se pudieron obtener las velas")
        return

    print(f"✅ Total velas obtenidas: {len(candles)}")

    # Create a dict of candles by timestamp for quick lookup
    candles_dict = {}
    for candle in candles:
        # Parse timestamp
        ts_str = candle['timestamp']
        if ts_str.endswith('Z'):
            ts_str = ts_str.replace('Z', '+00:00')
        ts = datetime.fromisoformat(ts_str)
        # Round to 5-minute intervals for matching
        ts = ts.replace(second=0, microsecond=0)
        candles_dict[ts] = candle

    print("\n" + "="*120)
    print("VALORES OHLC DE CADA TOUCH")
    print("="*120)
    print(f"Touch #\tTime (EST)\t\tOpen\t\tHigh\t\tLow\t\tClose\t\tVolume\t\tToque en")
    print("="*120)

    for idx, touch_time_str in enumerate(rect6_touches_utc, 1):
        touch_dt = datetime.fromisoformat(touch_time_str.replace('Z', '+00:00'))
        # Normalize to match candles_dict keys
        touch_dt_normalized = touch_dt.replace(second=0, microsecond=0)
        est_hour = (touch_dt.hour - 5) % 24
        time_est = f"{touch_dt.strftime('%b %d')} {est_hour:02d}:{touch_dt.minute:02d}"

        # Find the candle
        candle = candles_dict.get(touch_dt_normalized)

        if candle:
            open_price = candle['open']
            high_price = candle['high']
            low_price = candle['low']
            close_price = candle['close']
            volume = candle.get('volume', 0)

            # Determine where it touched (high or low)
            # For EQH, we check if the HIGH is within the zone
            touched_at = "HIGH"
            touch_value = high_price

            # Check if high is within tolerance of level
            if abs(high_price - level) <= 10:
                touched_at = "HIGH"
                touch_value = high_price
            elif abs(low_price - level) <= 10:
                touched_at = "LOW"
                touch_value = low_price

            # Distance from zone boundaries
            dist_from_high = high_price - zone_high
            dist_from_low = zone_low - low_price

            print(f"{idx}\t{time_est}\t{open_price:.2f}\t\t{high_price:.2f}\t\t{low_price:.2f}\t\t{close_price:.2f}\t\t{volume}\t\t{touched_at} ({touch_value:.2f})")
        else:
            print(f"{idx}\t{time_est}\t[VELA NO ENCONTRADA]")

    # Now show more detailed analysis
    print("\n" + "="*120)
    print("ANÁLISIS DETALLADO DE CADA TOUCH")
    print("="*120)

    for idx, touch_time_str in enumerate(rect6_touches_utc, 1):
        touch_dt = datetime.fromisoformat(touch_time_str.replace('Z', '+00:00'))
        touch_dt_normalized = touch_dt.replace(second=0, microsecond=0)
        est_hour = (touch_dt.hour - 5) % 24

        candle = candles_dict.get(touch_dt_normalized)

        if not candle:
            continue

        print(f"\n{'='*60}")
        print(f"Touch #{idx} - {touch_dt.strftime('%b %d')} {est_hour:02d}:{touch_dt.minute:02d} EST")
        print(f"{'='*60}")

        open_price = candle['open']
        high_price = candle['high']
        low_price = candle['low']
        close_price = candle['close']
        volume = candle.get('volume', 0)

        # Candle direction
        if close_price > open_price:
            direction = "BULLISH (verde)"
            body_size = close_price - open_price
        elif close_price < open_price:
            direction = "BEARISH (roja)"
            body_size = open_price - close_price
        else:
            direction = "DOJI"
            body_size = 0

        # Wick sizes
        upper_wick = high_price - max(open_price, close_price)
        lower_wick = min(open_price, close_price) - low_price
        total_range = high_price - low_price

        print(f"📊 Precios:")
        print(f"   Open:  {open_price:.2f}")
        print(f"   High:  {high_price:.2f} {'← TOCÓ ZONA' if abs(high_price - level) <= 10 else ''}")
        print(f"   Low:   {low_price:.2f}")
        print(f"   Close: {close_price:.2f}")
        print(f"   Volume: {volume:,}")

        print(f"\n📏 Estructura:")
        print(f"   Dirección: {direction}")
        print(f"   Cuerpo: {body_size:.2f} pts")
        print(f"   Mecha superior: {upper_wick:.2f} pts")
        print(f"   Mecha inferior: {lower_wick:.2f} pts")
        print(f"   Rango total: {total_range:.2f} pts")

        print(f"\n🎯 Relación con la Zona (25685.75 - 25693.75):")
        print(f"   High vs Zone High: {high_price - zone_high:+.2f} pts")
        if high_price > zone_high:
            print(f"      → Penetró {high_price - zone_high:.2f} pts ARRIBA de la zona")
        elif high_price >= zone_low:
            print(f"      → Dentro de la zona")

        print(f"   Low vs Zone Low: {low_price - zone_low:+.2f} pts")
        if low_price < zone_low:
            print(f"      → Penetró {zone_low - low_price:.2f} pts ABAJO de la zona")
        elif low_price <= zone_high:
            print(f"      → Dentro de la zona")

        print(f"   Nivel medio (25690.91):")
        print(f"      High: {high_price - level:+.2f} pts del nivel")
        print(f"      Low:  {low_price - level:+.2f} pts del nivel")

        # Rejection analysis
        if direction == "BEARISH (roja)" and upper_wick > body_size:
            print(f"\n⚠️  RECHAZO: Vela roja con mecha superior grande ({upper_wick:.2f} pts)")
            print(f"    → Intentó romper pero fue rechazada")
        elif direction == "BULLISH (verde)" and high_price > zone_high and close_price < zone_high:
            print(f"\n⚠️  RECHAZO: Vela verde que cerró abajo de la zona")
            print(f"    → Penetró pero no pudo sostener")

    print("\n" + "="*120)
    print("RESUMEN DEL PATRÓN")
    print("="*120)

    # Count rejections
    rejections = 0
    penetrations = 0

    for touch_time_str in rect6_touches_utc:
        touch_dt = datetime.fromisoformat(touch_time_str.replace('Z', '+00:00'))
        touch_dt_normalized = touch_dt.replace(second=0, microsecond=0)
        candle = candles_dict.get(touch_dt_normalized)
        if candle:
            if candle['high'] > zone_high:
                penetrations += 1
            if candle['close'] < zone_high and candle['high'] >= zone_low:
                rejections += 1

    print(f"\n📈 Estadísticas:")
    print(f"   Total touches: 8")
    print(f"   Velas que penetraron arriba de {zone_high:.2f}: {penetrations}")
    print(f"   Velas que fueron rechazadas: {rejections}")

    print(f"\n💡 Interpretación:")
    print(f"   - El precio intentó {penetrations} veces romper la zona")
    print(f"   - Fue rechazado {rejections} veces")
    print(f"   - Esto acumuló STOPS de compra arriba de {zone_high:.2f}")
    print(f"   - Smart Money sabe que hay liquidez acumulada")
    print(f"   - Próximo sweep probable: {zone_high + 5:.2f} - {zone_high + 10:.2f}")

if __name__ == "__main__":
    analyze_rect6_touches()
