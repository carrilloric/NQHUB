#!/usr/bin/env python3
"""
Análisis detallado de Order Block específico
"""
import requests
from datetime import datetime

response = requests.post(
    'http://localhost:8002/api/v1/patterns/order-blocks/generate',
    json={
        'symbol': 'NQZ5',
        'start_date': '2025-11-06',
        'end_date': '2025-11-06',
        'timeframe': '5min'
    }
)

data = response.json()
obs = data.get('order_blocks', [])

if not obs:
    print("No se encontraron Order Blocks")
    exit()

# Analizar el primer OB
ob = obs[0]
formation_time = datetime.fromisoformat(ob['formation_time'].replace('Z', '+00:00'))

print('='*120)
print('📦 ORDER BLOCK ANALYSIS - PRIMER OB DETECTADO')
print('='*120)
print()
print('⏰ TIMING:')
print(f"   Formation Time (UTC): {formation_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Formation Time (Local): {formation_time.strftime('%b %d, %H:%M')}")
print()
print('📊 CLASIFICACIÓN:')
print(f"   Type: {ob['ob_type']}")
print(f"   Status: {ob['status']}")
print(f"   Quality: {ob['quality']}")
print()
print('📈 LA VELA QUE FORMÓ EL OB:')
print(f"   Open:   ${ob['ob_open']:.2f}")
print(f"   High:   ${ob['ob_high']:.2f}  ← Techo del Order Block")
print(f"   Low:    ${ob['ob_low']:.2f}   ← Piso del Order Block")
print(f"   Close:  ${ob['ob_close']:.2f}")
print()
print(f"   Range: {ob['ob_high'] - ob['ob_low']:.2f} pts")
print(f"   Volume: {ob['ob_volume']:,.0f} contratos")
print(f"   Candle Direction: {ob['candle_direction']} (vela {ob['candle_direction'].lower()})")
print()
print('💨 EL IMPULSO QUE LO VALIDÓ:')
print(f"   Direction: {ob['impulse_direction']}")
print(f"   Movement: {ob['impulse_move']:.2f} pts (en las siguientes {data['auto_parameters']['lookforward_candles']} velas)")
strength = '⚡ STRONG' if 'STRONG' in ob['ob_type'] else '→ Normal'
print(f"   Strength: {strength} (threshold: {data['auto_parameters']['strong_threshold']:.1f} pts)")
print()

# Análisis específico según tipo
if 'BEARISH' in ob['ob_type']:
    print('🎯 ANÁLISIS ICT - BEARISH ORDER BLOCK (SUPPLY ZONE):')
    print()
    print('   📉 ¿QUÉ PASÓ?')
    print(f"   1. Vela BULLISH (alcista verde) cerró en ${ob['ob_close']:.2f}")
    print('   2. Las instituciones colocaron órdenes de VENTA en esta zona')
    print(f"   3. Después vino un impulso BAJISTA de {abs(ob['impulse_move']):.2f} pts")
    print('   4. Esto confirma que hubo SUPPLY (presión vendedora institucional)')
    print()
    print('   🧠 INTERPRETACIÓN:')
    print(f"   → Esta zona ${ob['ob_low']:.2f} - ${ob['ob_high']:.2f} es donde las instituciones vendieron")
    print('   → Si el precio vuelve aquí, probablemente habrá MÁS órdenes de venta esperando')
    print('   → Es una zona de "resistencia institucional"')
    print()
    print('   💡 CÓMO TRADEAR:')
    print(f"   1. Esperar que el precio RETESTE la zona ${ob['ob_low']:.2f} - ${ob['ob_high']:.2f}")
    print('   2. Buscar RECHAZO (precio no puede romper arriba, forma velas bajistas)')
    print(f"   3. Entrada SHORT cerca de ${ob['ob_high']:.2f}")
    print(f"   4. Stop Loss: ${ob['ob_high'] + 5:.2f} (5 pts arriba del OB)")
    print('   5. Target: Liquidez más cercana abajo (EQL, session low, etc.)')
    print()
    print('   ⚠️  INVALIDACIÓN:')
    print(f"   → Si el precio rompe ARRIBA de ${ob['ob_high']:.2f} con fuerza")
    print('   → Si cierra una vela por encima del OB')
    print('   → El Order Block se considera "mitigado" (ya no válido)')
else:  # BULLISH OB
    print('🎯 ANÁLISIS ICT - BULLISH ORDER BLOCK (DEMAND ZONE):')
    print()
    print('   📈 ¿QUÉ PASÓ?')
    print(f"   1. Vela BEARISH (bajista roja) cerró en ${ob['ob_close']:.2f}")
    print('   2. Las instituciones colocaron órdenes de COMPRA en esta zona')
    print(f"   3. Después vino un impulso ALCISTA de {abs(ob['impulse_move']):.2f} pts")
    print('   4. Esto confirma que hubo DEMAND (presión compradora institucional)')
    print()
    print('   🧠 INTERPRETACIÓN:')
    print(f"   → Esta zona ${ob['ob_low']:.2f} - ${ob['ob_high']:.2f} es donde las instituciones compraron")
    print('   → Si el precio vuelve aquí, probablemente habrá MÁS órdenes de compra esperando')
    print('   → Es una zona de "soporte institucional"')
    print()
    print('   💡 CÓMO TRADEAR:')
    print(f"   1. Esperar que el precio RETESTE la zona ${ob['ob_low']:.2f} - ${ob['ob_high']:.2f}")
    print('   2. Buscar RESPETO (precio rebota, forma velas alcistas)')
    print(f"   3. Entrada LONG cerca de ${ob['ob_low']:.2f}")
    print(f"   4. Stop Loss: ${ob['ob_low'] - 5:.2f} (5 pts abajo del OB)")
    print('   5. Target: Liquidez más cercana arriba (EQH, session high, etc.)')
    print()
    print('   ⚠️  INVALIDACIÓN:')
    print(f"   → Si el precio rompe ABAJO de ${ob['ob_low']:.2f} con fuerza")
    print('   → Si cierra una vela por debajo del OB')
    print('   → El Order Block se considera "mitigado" (ya no válido)')

print()
print('='*120)
print('📝 NOTAS ADICIONALES:')
print('='*120)
quality_note = 'Alta confiabilidad' if ob['quality'] == 'HIGH' else 'Baja confiabilidad, necesita más confirmación'
print(f"   • Quality: {ob['quality']} - {quality_note}")
print('   • Auto-parameters used:')
print(f"     - Min impulse: {data['auto_parameters']['min_impulse']:.1f} pts")
print(f"     - Strong threshold: {data['auto_parameters']['strong_threshold']:.1f} pts")
print(f"     - Lookforward: {data['auto_parameters']['lookforward_candles']} candles")
print('='*120)
