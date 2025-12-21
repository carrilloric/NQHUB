#!/usr/bin/env python3
"""
Análisis detallado del Rectangle #5
Inicio: Nov 5 19:55 EST
Zone: 25703.75 (H) / 25695.50 (L)
"""
import requests
from datetime import datetime, timezone
import json

BASE_URL = "http://localhost:8002/api/v1"

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
        print(f"❌ Error getting pools for {date_str}: {response.status_code}")
        return []

    return response.json()['pools']

def analyze_rectangle_5():
    """Analizar Rectangle #5 específicamente"""
    print("="*120)
    print("ANÁLISIS DETALLADO: RECTANGLE #5")
    print("Búsqueda: Inicio Nov 5 19:55 EST, Zone 25703.75/25695.50, 10 touches")
    print("="*120)

    # Get pools from Nov 5
    print("\n📥 Obteniendo pools de Nov 5...")
    pools_nov5 = get_pools_for_date("2025-11-05")

    print(f"✅ Total pools Nov 5: {len(pools_nov5)}")

    # Filter to find the specific rectangle
    # Looking for:
    # - start_time around Nov 5 19:55 EST (Nov 6 00:55 UTC)
    # - zone_high = 25703.75
    # - zone_low = 25695.50
    # - 10 touches

    target_high = 25703.75
    target_low = 25695.50
    target_touches = 10

    print(f"\n🔍 Buscando Rectangle con:")
    print(f"   - Zone High: {target_high}")
    print(f"   - Zone Low: {target_low}")
    print(f"   - Touches: {target_touches}")

    matching_pools = []
    for pool in pools_nov5:
        if (pool.get('zone_high') == target_high and
            pool.get('zone_low') == target_low and
            pool['num_touches'] == target_touches):
            matching_pools.append(pool)

    if not matching_pools:
        print("\n❌ No se encontró el rectangle exacto. Buscando similares...")
        # Try with tolerance
        for pool in pools_nov5:
            if (pool.get('zone_high') and pool.get('zone_low') and
                abs(pool.get('zone_high') - target_high) < 1.0 and
                abs(pool.get('zone_low') - target_low) < 1.0 and
                pool['num_touches'] == target_touches):
                matching_pools.append(pool)
                print(f"   Encontrado similar: High={pool.get('zone_high')}, Low={pool.get('zone_low')}")

    if not matching_pools:
        print("\n❌ No se encontró. Mostrando pools con 10 touches:")
        ten_touch_pools = [p for p in pools_nov5 if p['num_touches'] == 10]
        print(f"\n   Total pools con 10 touches: {len(ten_touch_pools)}")

        for idx, pool in enumerate(ten_touch_pools, 1):
            start_dt = datetime.fromisoformat(pool.get('start_time', pool['formation_time']).replace('Z', '+00:00'))
            print(f"\n   Pool {idx}:")
            print(f"     Start: {start_dt.strftime('%b %d %H:%M EST')}")
            print(f"     Type: {pool['pool_type']}")
            print(f"     Zone: {pool.get('zone_high'):.2f} / {pool.get('zone_low'):.2f}")
            print(f"     Size: {pool.get('zone_size', 0):.2f} pts")
            print(f"     Touches: {pool['num_touches']}")

        if ten_touch_pools:
            rect5 = ten_touch_pools[4] if len(ten_touch_pools) > 4 else ten_touch_pools[0]
            print(f"\n   Usando pool #{5 if len(ten_touch_pools) > 4 else 1} para análisis...")
        else:
            print("\n❌ No hay pools con 10 touches")
            return
    else:
        rect5 = matching_pools[0]
        print(f"\n✅ Rectangle encontrado! Pool ID: {rect5['lp_id']}")

    # Detailed analysis
    print("\n" + "="*120)
    print("ANÁLISIS COMPLETO")
    print("="*120)

    print(f"\n📍 IDENTIFICACIÓN:")
    print(f"   Pool ID: {rect5['lp_id']}")
    print(f"   Pool Type: {rect5['pool_type']}")
    print(f"   Liquidity Type: {rect5.get('liquidity_type', 'N/A')}")

    print(f"\n⏰ RANGO DE TIEMPO:")
    if rect5.get('start_time') and rect5.get('end_time'):
        start_dt = datetime.fromisoformat(rect5['start_time'].replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(rect5['end_time'].replace('Z', '+00:00'))
        duration_minutes = (end_dt - start_dt).total_seconds() / 60

        # Check if it starts around 19:55 EST
        start_hour_est = start_dt.hour - 5 if start_dt.hour >= 5 else start_dt.hour + 19

        print(f"   Start: {start_dt.strftime('%b %d, %Y %H:%M:%S')} UTC")
        print(f"          (Aprox {start_dt.strftime('%b %d')} {(start_dt.hour - 5) % 24:02d}:{start_dt.minute:02d} EST)")
        print(f"   End:   {end_dt.strftime('%b %d, %Y %H:%M:%S')} UTC")
        print(f"          (Aprox {end_dt.strftime('%b %d')} {(end_dt.hour - 5) % 24:02d}:{end_dt.minute:02d} EST)")
        print(f"   Duration: {duration_minutes:.0f} minutes ({duration_minutes/60:.1f} hours)")

    print(f"\n📐 RECTANGLE ZONE:")
    print(f"   Zone High: {rect5['zone_high']:.2f}")
    print(f"   Zone Low:  {rect5['zone_low']:.2f}")
    print(f"   Zone Size: {rect5.get('zone_size', rect5['zone_high'] - rect5['zone_low']):.2f} pts")
    print(f"   Level (Mid): {rect5['level']:.2f}")
    print(f"   Tolerance: ±{rect5['tolerance']:.2f} pts")

    print(f"\n📊 TOUCHES DETALLADOS:")
    print(f"   Total Touches: {rect5['num_touches']}")
    print(f"\n   Touch Times (UTC → EST aprox):")

    touch_times = []
    for i, touch_time in enumerate(rect5.get('touch_times', []), 1):
        touch_dt = datetime.fromisoformat(touch_time.replace('Z', '+00:00'))
        touch_times.append(touch_dt)
        est_hour = (touch_dt.hour - 5) % 24
        print(f"      {i:2d}. {touch_dt.strftime('%b %d %H:%M:%S')} UTC  →  {touch_dt.strftime('%b %d')} {est_hour:02d}:{touch_dt.minute:02d} EST")

    print(f"\n💪 STRENGTH & STATUS:")
    print(f"   Strength: {rect5['strength']}")
    print(f"   Status: {rect5['status']}")
    print(f"   Total Volume: {rect5.get('total_volume', 'N/A')}")

    print(f"\n✅ CRITERIOS CUMPLIDOS:")

    # Criterio 1: Es EQH o EQL
    is_eqh_eql = rect5['pool_type'] in ['EQH', 'EQL']
    print(f"   ✓ Tipo EQH/EQL: {'✅ SÍ' if is_eqh_eql else '❌ NO'} ({rect5['pool_type']})")

    # Criterio 2: Mínimo 3 touches
    min_touches = rect5['num_touches'] >= 3
    print(f"   ✓ Min 3 touches: {'✅ SÍ' if min_touches else '❌ NO'} ({rect5['num_touches']} touches)")

    # Criterio 3: Todos los toques dentro de tolerancia
    tolerance = rect5['tolerance']
    level = rect5['level']
    print(f"   ✓ Tolerancia: ±{tolerance:.0f} pts desde nivel {level:.2f}")
    print(f"     Rango válido: {level - tolerance:.2f} - {level + tolerance:.2f}")

    # Criterio 4: Zona definida
    has_zone = rect5.get('zone_low') is not None and rect5.get('zone_high') is not None
    zone_size = rect5.get('zone_size', 0)
    print(f"   ✓ Zona definida: {'✅ SÍ' if has_zone else '❌ NO'} ({zone_size:.2f} pts)")

    print(f"\n💡 EXPLICACIÓN:")
    if rect5['pool_type'] == 'EQH':
        print(f"   Este es un Equal High (EQH) - BUY-SIDE LIQUIDITY:")
        print(f"   - {rect5['num_touches']} velas alcanzaron niveles similares ALTOS")
        print(f"   - Todos los highs están dentro de ±{tolerance:.0f} pts de {level:.2f}")
        print(f"   - El rectángulo va desde {rect5['zone_low']:.2f} (low más bajo de esas velas)")
        print(f"   - Hasta {rect5['zone_high']:.2f} (high más alto de esas velas)")
        print(f"   - Esto indica STOPS de compra acumulados arriba")
        print(f"   - Alta probabilidad de que el precio 'barra' estos stops antes de caer")
    else:  # EQL
        print(f"   Este es un Equal Low (EQL) - SELL-SIDE LIQUIDITY:")
        print(f"   - {rect5['num_touches']} velas alcanzaron niveles similares BAJOS")
        print(f"   - Todos los lows están dentro de ±{tolerance:.0f} pts de {level:.2f}")
        print(f"   - El rectángulo va desde {rect5['zone_low']:.2f} (low más bajo de esas velas)")
        print(f"   - Hasta {rect5['zone_high']:.2f} (high más alto de esas velas)")
        print(f"   - Esto indica STOPS de venta acumulados abajo")
        print(f"   - Alta probabilidad de que el precio 'barra' estos stops antes de subir")

    # Analyze touch pattern
    if touch_times:
        print(f"\n📈 PATRÓN DE TOUCHES:")

        # Group touches by session (EST times)
        asian_touches = []
        london_touches = []
        ny_touches = []

        for t in touch_times:
            est_hour = (t.hour - 5) % 24
            if 19 <= est_hour or est_hour < 3:
                asian_touches.append(t)
            elif 3 <= est_hour < 9:
                london_touches.append(t)
            elif 9 <= est_hour < 16:
                ny_touches.append(t)

        print(f"   - Asian Session (19:00-03:00 EST): {len(asian_touches)} touches")
        if asian_touches:
            for t in asian_touches:
                est_hour = (t.hour - 5) % 24
                print(f"      • {t.strftime('%b %d')} {est_hour:02d}:{t.minute:02d} EST")

        print(f"   - London Session (03:00-09:00 EST): {len(london_touches)} touches")
        if london_touches:
            for t in london_touches:
                est_hour = (t.hour - 5) % 24
                print(f"      • {t.strftime('%b %d')} {est_hour:02d}:{t.minute:02d} EST")

        print(f"   - NY Session (09:00-16:00 EST): {len(ny_touches)} touches")
        if ny_touches:
            for t in ny_touches:
                est_hour = (t.hour - 5) % 24
                print(f"      • {t.strftime('%b %d')} {est_hour:02d}:{t.minute:02d} EST")

        # Time gaps
        gaps = []
        for i in range(1, len(touch_times)):
            gap = (touch_times[i] - touch_times[i-1]).total_seconds() / 60
            gaps.append(gap)

        if gaps:
            avg_gap = sum(gaps) / len(gaps)
            max_gap = max(gaps)
            min_gap = min(gaps)
            print(f"\n   📏 Intervalos entre touches:")
            print(f"      - Gap promedio: {avg_gap:.0f} minutos ({avg_gap/60:.1f} horas)")
            print(f"      - Gap máximo: {max_gap:.0f} minutos ({max_gap/60:.1f} horas)")
            print(f"      - Gap mínimo: {min_gap:.0f} minutos")

    print("\n" + "="*120)

    # Show full JSON for inspection
    print("\n📄 DATOS COMPLETOS (JSON):")
    print(json.dumps(rect5, indent=2, default=str))

if __name__ == "__main__":
    analyze_rectangle_5()
