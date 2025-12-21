#!/usr/bin/env python3
"""
Análisis detallado de Liquidity Pools desde Nov 5 19:00 EST
Enfocado en el Rectangle #3
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

def analyze_from_nov5_7pm():
    """Analizar desde Nov 5 19:00 EST"""
    print("="*120)
    print("ANÁLISIS DE LIQUIDITY POOLS DESDE NOV 5 19:00 EST")
    print("="*120)

    # Get pools from Nov 5 and Nov 6
    print("\n📥 Obteniendo pools de Nov 5 y Nov 6...")
    pools_nov5 = get_pools_for_date("2025-11-05")
    pools_nov6 = get_pools_for_date("2025-11-06")

    # Combine all pools
    all_pools = pools_nov5 + pools_nov6

    # Filter pools that start at or after Nov 5 19:00 EST
    # EST is UTC-5, so 19:00 EST Nov 5 = 00:00 UTC Nov 6
    cutoff_utc = datetime(2025, 11, 6, 0, 0, 0, tzinfo=timezone.utc)

    filtered_pools = []
    for pool in all_pools:
        start_time_str = pool.get('start_time') or pool['formation_time']
        # Parse ISO format with Z timezone
        if start_time_str.endswith('Z'):
            start_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        else:
            start_dt = datetime.fromisoformat(start_time_str)

        # Make sure it's timezone aware
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)

        if start_dt >= cutoff_utc:
            filtered_pools.append(pool)

    # Sort by start_time
    filtered_pools = sorted(filtered_pools, key=lambda p: p.get('start_time') or p['formation_time'])

    print(f"✅ Total pools desde Nov 5 19:00 EST: {len(filtered_pools)}")
    print(f"   (Nov 5 pools: {len(pools_nov5)}, Nov 6 pools: {len(pools_nov6)})")

    # Count by type
    eqh_count = sum(1 for p in filtered_pools if p['pool_type'] == 'EQH')
    eql_count = sum(1 for p in filtered_pools if p['pool_type'] == 'EQL')
    print(f"   Breakdown: EQH: {eqh_count}, EQL: {eql_count}")

    print("\n" + "="*120)
    print("TODOS LOS RECTANGLES DESDE NOV 5 19:00 EST")
    print("="*120)
    print("#\tTIME_RANGE\t\t\t\tTYPE\tLIQUIDITY\t\tRECTANGLE_ZONE\t\t\tTOUCHES")
    print("="*120)

    for idx, pool in enumerate(filtered_pools[:20], 1):  # Show first 20
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

    if len(filtered_pools) > 20:
        print(f"... y {len(filtered_pools) - 20} más")

    # Detailed analysis of Rectangle #3
    if len(filtered_pools) >= 3:
        rect3 = filtered_pools[2]  # Index 2 = Rectangle #3

        print("\n" + "="*120)
        print("ANÁLISIS DETALLADO: RECTANGLE #3 (DESDE NOV 5 19:00 EST)")
        print("="*120)

        print(f"\n📍 IDENTIFICACIÓN:")
        print(f"   Pool ID: {rect3['lp_id']}")
        print(f"   Pool Type: {rect3['pool_type']}")
        print(f"   Liquidity Type: {rect3.get('liquidity_type', 'N/A')}")

        print(f"\n⏰ RANGO DE TIEMPO:")
        if rect3.get('start_time') and rect3.get('end_time'):
            start_dt = datetime.fromisoformat(rect3['start_time'].replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(rect3['end_time'].replace('Z', '+00:00'))
            duration_minutes = (end_dt - start_dt).total_seconds() / 60
            print(f"   Start: {start_dt.strftime('%b %d, %Y %H:%M:%S EST')}")
            print(f"   End:   {end_dt.strftime('%b %d, %Y %H:%M:%S EST')}")
            print(f"   Duration: {duration_minutes:.0f} minutes ({duration_minutes/60:.1f} hours)")

        print(f"\n📐 RECTANGLE ZONE:")
        print(f"   Zone High: {rect3['zone_high']:.2f}")
        print(f"   Zone Low:  {rect3['zone_low']:.2f}")
        print(f"   Zone Size: {rect3.get('zone_size', rect3['zone_high'] - rect3['zone_low']):.2f} pts")
        print(f"   Level (Mid): {rect3['level']:.2f}")
        print(f"   Tolerance: ±{rect3['tolerance']:.2f} pts")

        print(f"\n📊 TOUCHES:")
        print(f"   Total Touches: {rect3['num_touches']}")
        print(f"   Touch Times:")
        for i, touch_time in enumerate(rect3.get('touch_times', []), 1):
            touch_dt = datetime.fromisoformat(touch_time.replace('Z', '+00:00'))
            print(f"      {i}. {touch_dt.strftime('%b %d %H:%M:%S EST')}")

        print(f"\n💪 STRENGTH & STATUS:")
        print(f"   Strength: {rect3['strength']}")
        print(f"   Status: {rect3['status']}")
        print(f"   Total Volume: {rect3.get('total_volume', 'N/A')}")

        print(f"\n✅ CRITERIOS CUMPLIDOS:")

        # Criterio 1: Es EQH o EQL
        is_eqh_eql = rect3['pool_type'] in ['EQH', 'EQL']
        print(f"   ✓ Tipo EQH/EQL: {'✅ SÍ' if is_eqh_eql else '❌ NO'} ({rect3['pool_type']})")

        # Criterio 2: Mínimo 3 touches
        min_touches = rect3['num_touches'] >= 3
        print(f"   ✓ Min 3 touches: {'✅ SÍ' if min_touches else '❌ NO'} ({rect3['num_touches']} touches)")

        # Criterio 3: Todos los toques dentro de tolerancia (±10 pts default)
        tolerance = rect3['tolerance']
        level = rect3['level']
        print(f"   ✓ Tolerancia: ±{tolerance:.0f} pts desde nivel {level:.2f}")
        print(f"     Rango válido: {level - tolerance:.2f} - {level + tolerance:.2f}")

        # Criterio 4: Zona definida
        has_zone = rect3.get('zone_low') is not None and rect3.get('zone_high') is not None
        zone_size = rect3.get('zone_size', 0)
        print(f"   ✓ Zona definida: {'✅ SÍ' if has_zone else '❌ NO'} ({zone_size:.2f} pts)")

        print(f"\n💡 EXPLICACIÓN:")
        if rect3['pool_type'] == 'EQH':
            print(f"   Este es un Equal High (EQH) - BUY-SIDE LIQUIDITY:")
            print(f"   - {rect3['num_touches']} velas alcanzaron niveles similares ALTOS")
            print(f"   - Todos los highs están dentro de ±{tolerance:.0f} pts de {level:.2f}")
            print(f"   - El rectángulo va desde {rect3['zone_low']:.2f} (low más bajo de esas velas)")
            print(f"   - Hasta {rect3['zone_high']:.2f} (high más alto de esas velas)")
            print(f"   - Esto indica STOPS de compra acumulados arriba")
            print(f"   - Alta probabilidad de que el precio 'barra' estos stops antes de caer")
        else:  # EQL
            print(f"   Este es un Equal Low (EQL) - SELL-SIDE LIQUIDITY:")
            print(f"   - {rect3['num_touches']} velas alcanzaron niveles similares BAJOS")
            print(f"   - Todos los lows están dentro de ±{tolerance:.0f} pts de {level:.2f}")
            print(f"   - El rectángulo va desde {rect3['zone_low']:.2f} (low más bajo de esas velas)")
            print(f"   - Hasta {rect3['zone_high']:.2f} (high más alto de esas velas)")
            print(f"   - Esto indica STOPS de venta acumulados abajo")
            print(f"   - Alta probabilidad de que el precio 'barra' estos stops antes de subir")

        # Analyze touch pattern
        if rect3.get('touch_times'):
            print(f"\n📈 PATRÓN DE TOUCHES:")
            touch_times = [datetime.fromisoformat(t.replace('Z', '+00:00')) for t in rect3['touch_times']]

            # Group touches by session
            asian_touches = [t for t in touch_times if 19 <= t.hour or t.hour < 3]
            london_touches = [t for t in touch_times if 3 <= t.hour < 9]
            ny_touches = [t for t in touch_times if 9 <= t.hour < 16]

            print(f"   - Asian Session (19:00-03:00): {len(asian_touches)} touches")
            print(f"   - London Session (03:00-09:00): {len(london_touches)} touches")
            print(f"   - NY Session (09:00-16:00): {len(ny_touches)} touches")

            # Time gaps
            gaps = []
            for i in range(1, len(touch_times)):
                gap = (touch_times[i] - touch_times[i-1]).total_seconds() / 60
                gaps.append(gap)

            if gaps:
                avg_gap = sum(gaps) / len(gaps)
                max_gap = max(gaps)
                print(f"   - Gap promedio entre touches: {avg_gap:.0f} minutos")
                print(f"   - Gap máximo: {max_gap:.0f} minutos ({max_gap/60:.1f} horas)")

        print("\n" + "="*120)

        # Show full JSON for inspection
        print("\n📄 DATOS COMPLETOS (JSON):")
        print(json.dumps(rect3, indent=2, default=str))
    else:
        print(f"\n❌ No hay suficientes LPs desde Nov 5 19:00. Solo se detectaron {len(filtered_pools)} pools.")

if __name__ == "__main__":
    analyze_from_nov5_7pm()
