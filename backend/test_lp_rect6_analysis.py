#!/usr/bin/env python3
"""
Análisis detallado del Rectangle #6
Inicio: Nov 5 20:30 EST
Zone: 25693.75 (H) / 25685.75 (L)
Touches: 8
Strength: STRONG
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

def analyze_rectangle_6():
    """Buscar Rectangle #6 específicamente"""
    print("="*120)
    print("BÚSQUEDA: RECTANGLE #6")
    print("Características: Nov 5 20:30 EST, Zone 25693.75/25685.75, 8 touches, STRONG")
    print("="*120)

    # Get pools from Nov 5 and Nov 6
    print("\n📥 Obteniendo pools de Nov 5 y Nov 6...")
    pools_nov5 = get_pools_for_date("2025-11-05")
    pools_nov6 = get_pools_for_date("2025-11-06")

    print(f"✅ Total pools Nov 5: {len(pools_nov5)}")
    print(f"✅ Total pools Nov 6: {len(pools_nov6)}")

    # Nov 5 20:30 EST = Nov 6 01:30 UTC
    # So we need to look in Nov 6 pools that start around 01:30 UTC

    target_high = 25693.75
    target_low = 25685.75
    target_touches = 8

    print(f"\n🔍 Buscando Rectangle con:")
    print(f"   - Start time: Nov 5 20:30 EST (Nov 6 01:30 UTC)")
    print(f"   - Zone High: {target_high}")
    print(f"   - Zone Low: {target_low}")
    print(f"   - Touches: {target_touches}")
    print(f"   - Strength: STRONG")

    # Search in both dates
    all_pools = pools_nov5 + pools_nov6

    # First try exact match
    matching_pools = []
    for pool in all_pools:
        if (pool.get('zone_high') == target_high and
            pool.get('zone_low') == target_low and
            pool['num_touches'] == target_touches):
            matching_pools.append(pool)

    if not matching_pools:
        print("\n⚠️  No se encontró exacto. Buscando con tolerancia de ±0.5 pts...")
        for pool in all_pools:
            if (pool.get('zone_high') and pool.get('zone_low') and
                abs(pool.get('zone_high') - target_high) < 0.5 and
                abs(pool.get('zone_low') - target_low) < 0.5 and
                pool['num_touches'] == target_touches):
                matching_pools.append(pool)
                print(f"   Encontrado: High={pool.get('zone_high')}, Low={pool.get('zone_low')}")

    if not matching_pools:
        print("\n⚠️  No encontrado con zona exacta. Buscando por 8 touches + STRONG...")
        for pool in all_pools:
            if pool['num_touches'] == target_touches and pool.get('strength') == 'STRONG':
                matching_pools.append(pool)

    if not matching_pools:
        print("\n❌ No se encontró. Mostrando pools con 8 touches:")
        eight_touch_pools = [p for p in all_pools if p['num_touches'] == 8]
        print(f"\n   Total pools con 8 touches: {len(eight_touch_pools)}")

        for idx, pool in enumerate(eight_touch_pools[:10], 1):
            start_dt = datetime.fromisoformat(pool.get('start_time', pool['formation_time']).replace('Z', '+00:00'))
            est_hour = (start_dt.hour - 5) % 24
            print(f"\n   Pool {idx}:")
            print(f"     Start: {start_dt.strftime('%b %d')} {est_hour:02d}:{start_dt.minute:02d} EST")
            print(f"     Type: {pool['pool_type']}")
            print(f"     Zone: {pool.get('zone_high'):.2f} / {pool.get('zone_low'):.2f}")
            print(f"     Size: {pool.get('zone_size', 0):.2f} pts")
            print(f"     Strength: {pool.get('strength')}")
            print(f"     Touches: {pool['num_touches']}")

        if not eight_touch_pools:
            print("\n❌ No hay pools con 8 touches")
            return

        # Try to find the one closest to 20:30 EST start time
        target_start_utc = datetime(2025, 11, 6, 1, 30, 0, tzinfo=timezone.utc)
        closest_pool = min(eight_touch_pools,
                          key=lambda p: abs((datetime.fromisoformat(p.get('start_time', p['formation_time']).replace('Z', '+00:00')) - target_start_utc).total_seconds()))

        start_dt = datetime.fromisoformat(closest_pool.get('start_time', closest_pool['formation_time']).replace('Z', '+00:00'))
        est_hour = (start_dt.hour - 5) % 24
        print(f"\n   🎯 Pool más cercano a Nov 5 20:30 EST:")
        print(f"      Start: {start_dt.strftime('%b %d')} {est_hour:02d}:{start_dt.minute:02d} EST")
        print(f"      Zone: {closest_pool.get('zone_high'):.2f} / {closest_pool.get('zone_low'):.2f}")

        rect6 = closest_pool
    else:
        rect6 = matching_pools[0]
        print(f"\n✅ Rectangle encontrado! Pool ID: {rect6['lp_id']}")

    # Detailed analysis
    print("\n" + "="*120)
    print("ANÁLISIS COMPLETO: RECTANGLE #6")
    print("="*120)

    print(f"\n📍 IDENTIFICACIÓN:")
    print(f"   Pool ID: {rect6['lp_id']}")
    print(f"   Pool Type: {rect6['pool_type']}")
    print(f"   Liquidity Type: {rect6.get('liquidity_type', 'N/A')}")

    print(f"\n⏰ RANGO DE TIEMPO:")
    if rect6.get('start_time') and rect6.get('end_time'):
        start_dt = datetime.fromisoformat(rect6['start_time'].replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(rect6['end_time'].replace('Z', '+00:00'))
        duration_minutes = (end_dt - start_dt).total_seconds() / 60

        start_est_hour = (start_dt.hour - 5) % 24
        end_est_hour = (end_dt.hour - 5) % 24

        print(f"   Start: {start_dt.strftime('%b %d, %Y %H:%M:%S')} UTC")
        print(f"          {start_dt.strftime('%b %d')} {start_est_hour:02d}:{start_dt.minute:02d} EST")
        print(f"   End:   {end_dt.strftime('%b %d, %Y %H:%M:%S')} UTC")
        print(f"          {end_dt.strftime('%b %d')} {end_est_hour:02d}:{end_dt.minute:02d} EST")
        print(f"   Duration: {duration_minutes:.0f} minutes ({duration_minutes/60:.1f} hours)")

    print(f"\n📐 RECTANGLE ZONE:")
    print(f"   Zone High: {rect6['zone_high']:.2f}")
    print(f"   Zone Low:  {rect6['zone_low']:.2f}")
    print(f"   Zone Size: {rect6.get('zone_size', rect6['zone_high'] - rect6['zone_low']):.2f} pts")
    print(f"   Level (Mid): {rect6['level']:.2f}")
    print(f"   Tolerance: ±{rect6['tolerance']:.2f} pts")

    print(f"\n📊 TOUCHES DETALLADOS:")
    print(f"   Total Touches: {rect6['num_touches']}")
    print(f"\n   Touch Times:")

    touch_times = []
    for i, touch_time in enumerate(rect6.get('touch_times', []), 1):
        touch_dt = datetime.fromisoformat(touch_time.replace('Z', '+00:00'))
        touch_times.append(touch_dt)
        est_hour = (touch_dt.hour - 5) % 24
        print(f"      {i:2d}. {touch_dt.strftime('%b %d %H:%M:%S')} UTC  →  {touch_dt.strftime('%b %d')} {est_hour:02d}:{touch_dt.minute:02d} EST")

    print(f"\n💪 STRENGTH & STATUS:")
    print(f"   Strength: {rect6['strength']}")
    print(f"   Status: {rect6['status']}")
    print(f"   Total Volume: {rect6.get('total_volume', 'N/A')}")

    print(f"\n✅ CRITERIOS CUMPLIDOS:")

    # Criterio 1: Es EQH o EQL
    is_eqh_eql = rect6['pool_type'] in ['EQH', 'EQL']
    print(f"   ✓ Tipo EQH/EQL: {'✅ SÍ' if is_eqh_eql else '❌ NO'} ({rect6['pool_type']})")

    # Criterio 2: Mínimo 3 touches
    min_touches = rect6['num_touches'] >= 3
    print(f"   ✓ Min 3 touches: {'✅ SÍ' if min_touches else '❌ NO'} ({rect6['num_touches']} touches)")

    # Criterio 3: Strength STRONG
    is_strong = rect6.get('strength') == 'STRONG'
    strength_result = '✅ SÍ' if is_strong else f"⚠️  {rect6.get('strength')}"
    print(f"   ✓ Strength STRONG: {strength_result}")

    # Criterio 4: Tolerancia
    tolerance = rect6['tolerance']
    level = rect6['level']
    print(f"   ✓ Tolerancia: ±{tolerance:.0f} pts desde nivel {level:.2f}")
    print(f"     Rango válido: {level - tolerance:.2f} - {level + tolerance:.2f}")

    # Criterio 5: Zona definida
    has_zone = rect6.get('zone_low') is not None and rect6.get('zone_high') is not None
    zone_size = rect6.get('zone_size', 0)
    print(f"   ✓ Zona definida: {'✅ SÍ' if has_zone else '❌ NO'} ({zone_size:.2f} pts)")

    print(f"\n💡 EXPLICACIÓN:")
    if rect6['pool_type'] == 'EQH':
        print(f"   Este es un Equal High (EQH) - BUY-SIDE LIQUIDITY:")
        print(f"   - {rect6['num_touches']} velas alcanzaron niveles similares ALTOS")
        print(f"   - Todos los highs están dentro de ±{tolerance:.0f} pts de {level:.2f}")
        print(f"   - El rectángulo va desde {rect6['zone_low']:.2f} (low más bajo)")
        print(f"   - Hasta {rect6['zone_high']:.2f} (high más alto)")
        print(f"   - Strength STRONG indica alta confiabilidad")
        print(f"   - STOPS de compra acumulados arriba de {rect6['zone_high']:.2f}")
        print(f"   - Setup probable: Sweep de liquidez → Reversión bajista")
    else:  # EQL
        print(f"   Este es un Equal Low (EQL) - SELL-SIDE LIQUIDITY:")
        print(f"   - {rect6['num_touches']} velas alcanzaron niveles similares BAJOS")
        print(f"   - Todos los lows están dentro de ±{tolerance:.0f} pts de {level:.2f}")
        print(f"   - El rectángulo va desde {rect6['zone_low']:.2f} (low más bajo)")
        print(f"   - Hasta {rect6['zone_high']:.2f} (high más alto)")
        print(f"   - Strength STRONG indica alta confiabilidad")
        print(f"   - STOPS de venta acumulados abajo de {rect6['zone_low']:.2f}")
        print(f"   - Setup probable: Sweep de liquidez → Reversión alcista")

    # Analyze touch pattern
    if touch_times:
        print(f"\n📈 PATRÓN DE TOUCHES:")

        # Group by session
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

    # Trading implications
    print(f"\n🎯 IMPLICACIONES DE TRADING:")
    zone_high = rect6['zone_high']
    zone_low = rect6['zone_low']

    if rect6['pool_type'] == 'EQH':
        print(f"   📍 Zona de Alerta: {zone_low:.2f} - {zone_high:.2f}")
        print(f"   🎣 Setup esperado:")
        print(f"      1. Precio vuelve a {zone_high:.2f}")
        print(f"      2. Sweep (penetración) arriba de {zone_high + 5:.2f}")
        print(f"      3. Rechazo / wick largo")
        print(f"      4. Entrada SHORT en rechazo")
        print(f"      5. Stop arriba de {zone_high + 15:.2f}")
        print(f"      6. Target: Próximo nivel de liquidez abajo")
    else:
        print(f"   📍 Zona de Alerta: {zone_low:.2f} - {zone_high:.2f}")
        print(f"   🎣 Setup esperado:")
        print(f"      1. Precio vuelve a {zone_low:.2f}")
        print(f"      2. Sweep (penetración) abajo de {zone_low - 5:.2f}")
        print(f"      3. Rechazo / wick largo")
        print(f"      4. Entrada LONG en rechazo")
        print(f"      5. Stop abajo de {zone_low - 15:.2f}")
        print(f"      6. Target: Próximo nivel de liquidez arriba")

    print("\n" + "="*120)

    # Show full JSON
    print("\n📄 DATOS COMPLETOS (JSON):")
    print(json.dumps(rect6, indent=2, default=str))

if __name__ == "__main__":
    analyze_rectangle_6()
