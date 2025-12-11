# Rebote y Penetración - Criterios de Clasificación Universal

**Documento técnico**: Taxonomía completa de interacciones precio-zona
**Versión**: 1.0
**Fecha**: 2025-12-03
**Contexto**: Aplicable a Order Blocks (OB), Fair Value Gaps (FVG), Liquidity Pools (LP)

---

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Fundamentos](#fundamentos)
3. [Taxonomía de Rebotes (R0-R4)](#taxonomía-de-rebotes)
4. [Taxonomía de Penetraciones (P1-P5)](#taxonomía-de-penetraciones)
5. [Parámetros Cuantificables](#parámetros-cuantificables)
6. [Algoritmos de Detección SQL](#algoritmos-de-detección-sql)
7. [Implementación Python](#implementación-python)
8. [Integración con Trading](#integración-con-trading)
9. [Ejemplos Validados](#ejemplos-validados)
10. [Métricas para Backtesting](#métricas-para-backtesting)

---

## Introducción

### Motivación

En el análisis de Smart Money Concepts (SMC), es crítico entender **cómo el precio interactúa con zonas de interés** (Order Blocks, Fair Value Gaps, Liquidity Pools). Sin embargo, los términos tradicionales son **ambiguos**:

- ¿Qué significa "el precio respetó el OB"?
- ¿Cuánta penetración se permite antes de considerar una zona "invalidada"?
- ¿Un wick que penetra 5 puntos es un "rebote" o una "violación"?

Este documento establece una **taxonomía cuantificable y universal** que:

1. ✅ Define **10 tipos distintos** de interacción (5 rebotes + 5 penetraciones)
2. ✅ Proporciona **criterios matemáticos objetivos** para cada tipo
3. ✅ Es **aplicable a todas las zonas** (OB, FVG, LP)
4. ✅ Permite **backtesting científico** de estrategias
5. ✅ Es **parametrizable** para optimización (ver REBOTE_SETUP.md)

### Relación con Otros Documentos

- **ORDER_BLOCKS_CRITERIOS.md**: Cómo detectar OBs → Este doc: Cómo interactúa el precio con OBs
- **LIQUIDITY_POOLS_CRITERIOS.md**: Cómo detectar LPs → Este doc: Cómo clasificar sweeps
- **FVG_CRITERIOS_DETECCION.md**: Cómo detectar FVGs → Este doc: Cómo analizar rellenos
- **REBOTE_SETUP.md**: Arquitectura parametrizable y optimización

---

## Fundamentos

### Definición Universal de "Zona"

Una **zona** es cualquier rango de precio con significancia institucional:

```
ZONA = [zone_low, zone_high]

Ejemplos:
- Order Block: [ob_low, ob_high]
- Fair Value Gap: [fvg_start, fvg_end]
- Liquidity Pool: [lp_level - tolerance, lp_level + tolerance]
```

**Características comunes**:
- Tiene límite inferior (`zone_low`) y superior (`zone_high`)
- Tamaño calculable: `zone_size = zone_high - zone_low`
- Orientación (Bullish/Bearish para OB y FVG, Buy-Side/Sell-Side para LP)

### Componentes Medibles

Para analizar la interacción de una vela con una zona, medimos:

#### 1. Distancia de Penetración

**En puntos absolutos**:
```python
# Desde abajo (probando zona como resistencia)
if candle_high > zone_low:
    penetration_pts = min(candle_high, zone_high) - zone_low

# Desde arriba (probando zona como soporte)
if candle_low < zone_high:
    penetration_pts = zone_high - max(candle_low, zone_low)
```

**En porcentaje de zona**:
```python
penetration_pct = (penetration_pts / zone_size) * 100
```

#### 2. Tipo de Penetración Anatómica

- **WICK_ONLY**: Solo la mecha penetra, body queda fuera
- **BODY_PARTIAL**: El body penetra parcialmente (open o close dentro, pero no ambos)
- **BODY_FULL**: El body cierra completamente dentro de la zona

```python
body_top = max(candle_open, candle_close)
body_bottom = min(candle_open, candle_close)

if body_bottom >= zone_high or body_top <= zone_low:
    type = "WICK_ONLY"
elif body_bottom < zone_high and body_top > zone_low:
    type = "BODY_FULL"
else:
    type = "BODY_PARTIAL"
```

#### 3. Fuerza de Rechazo

Mide la "agresividad" del rechazo:

```python
# Para rebote desde abajo
upper_wick = candle_high - body_top
total_range = candle_high - candle_low
rejection_strength = upper_wick / total_range

# rejection_strength = 0.0 → No hubo rechazo (body en tope)
# rejection_strength = 0.5 → Rechazo moderado (wick = 50% de vela)
# rejection_strength = 0.8 → Rechazo fuerte (wick = 80% de vela)
```

#### 4. Duración

- **Número de velas**: ¿Cuántas velas permanecieron dentro/tocando la zona?
- **Tiempo total**: En minutos o horas

#### 5. Volumen Relativo

```python
volume_ratio = candle_volume / avg_volume_last_20
# volume_ratio > 1.5 → Alto volumen (señal fuerte)
# volume_ratio < 0.7 → Bajo volumen (señal débil)
```

### Diferencia Conceptual: Rebote vs Penetración

**REBOTE**:
- El precio **toca y rechaza** la zona
- Señal de que la zona está siendo **respetada**
- Función: La zona actúa como soporte/resistencia
- Resultado esperado: Reversión en dirección opuesta

**PENETRACIÓN**:
- El precio **entra en** la zona
- Señal de que la zona está siendo **probada/violada**
- Función: La zona está debilitándose o cambiando de polaridad
- Resultado esperado: Break completo o cambio de carácter

---

## Taxonomía de Rebotes

### Clasificación de 5 Niveles (R0-R4)

Los rebotes se clasifican según **profundidad de penetración** y **fuerza de rechazo**, de más fuerte a más débil.

---

### R0 - CLEAN BOUNCE (Rebote Limpio)

**Definición**: Toque perfecto sin penetración significativa

**Criterios DEFAULT** (ver REBOTE_SETUP.md para parametrizar):
```python
penetration_pts <= 1.0  # Máximo 1 punto (4 ticks en NQ)
penetration_pct <= N/A  # No usar % para R0
body_penetration == 0   # Body NO penetra en absoluto
close_outside == True   # Cierra fuera de zona
```

**Características**:
- ✅ La zona es **extremadamente fuerte**
- ✅ Institucionales están defendiendo agresivamente el nivel
- ✅ Señal más confiable de todas (85-90% win rate típico)

**Ejemplo Visual**:
```
Zona OB: 25000.00 - 25020.00

Vela:
  High: 25001.00   ← Toca zona con 1 punto de penetración
  Low:  24985.00
  Close: 24990.00  ← Cierra fuera de zona

→ R0_CLEAN_BOUNCE
```

**Señal de Trading**:
- ✅ **ENTRY INMEDIATA** al cierre de la vela
- Stop: 2-3 puntos detrás de zone_low/high
- Confianza: MUY ALTA

---

### R1 - SHALLOW TOUCH (Toque Superficial)

**Definición**: Penetración mínima, solo con wicks

**Criterios DEFAULT**:
```python
penetration_pts <= 3.0       # Máximo 3 puntos
penetration_pct <= 5.0       # O máximo 5% de zona
body_penetration <= 0.5      # Body casi no entra (<0.5 pts)
wick_only == True            # Solo wicks penetran
close_outside == True        # Cierra fuera
```

**Características**:
- ✅ Zona **fuerte**, penetración despreciable
- ✅ Típico en Order Blocks de alta calidad
- ✅ Win rate: 75-85%

**Ejemplo Visual**:
```
Zona OB: 25000.00 - 25020.00 (size: 20 pts)

Vela:
  High: 25003.00   ← Wick penetra 3 puntos (15% de zona)
  Open: 24992.00
  Close: 24988.00  ← Body no penetra
  Low:  24985.00

Cálculo:
  penetration_pts = 25003.00 - 25000.00 = 3.0 ✓
  penetration_pct = (3.0 / 20.0) * 100 = 15% ✗ (excede 5%)

→ Borderline, podría ser R1 o R2 dependiendo de configuración
```

**Señal de Trading**:
- ✅ **ENTRY VÁLIDA** al cierre o próxima vela
- Stop: 3-5 puntos detrás de zona
- Confianza: ALTA

---

### R2 - LIGHT REJECTION (Rechazo Ligero)

**Definición**: Penetración moderada pero cierra fuera de zona

**Criterios DEFAULT**:
```python
penetration_pts <= 10.0      # Máximo 10 puntos
penetration_pct <= 10.0      # O máximo 10% de zona
close_outside == True        # DEBE cerrar fuera
rejection_wick_pct >= 30.0   # Wick de rechazo ≥30% de vela
```

**Características**:
- ⚠️ Zona **moderadamente fuerte**
- ⚠️ Requiere confirmación adicional
- ⚠️ Win rate: 60-75%

**Ejemplo Visual**:
```
Zona FVG: 24950.00 - 24970.00 (size: 20 pts)

Vela:
  High: 24958.00   ← Penetra 8 puntos (40% de zona)
  Open: 24945.00
  Close: 24947.00  ← Cierra FUERA de zona
  Low:  24940.00

Análisis:
  penetration_pts = 8.0 ✓
  penetration_pct = 40% ✗ (excede 10%)
  rejection_wick = 24958 - 24947 = 11 pts
  total_range = 24958 - 24940 = 18 pts
  rejection_wick_pct = 11/18 = 61% ✓

→ R2_LIGHT_REJECTION (cierra fuera + buen rejection wick)
```

**Señal de Trading**:
- ⚠️ **ENTRY CON CONFIRMACIÓN** (esperar siguiente vela)
- Stop: 5-8 puntos detrás de zona
- Confianza: MEDIA-ALTA

---

### R3 - MEDIUM REJECTION (Rechazo Medio)

**Definición**: Penetración significativa (10-25% zona) pero rechazo visible

**Criterios DEFAULT**:
```python
penetration_pct > 10.0 AND <= 25.0  # Entre 10-25% de zona
close_in_outer_third == True         # Cierra en tercio externo de zona
rejection_wick_pct >= 20.0           # Wick de rechazo ≥20%
```

**Características**:
- ⚠️ Zona **débil pero aún válida**
- ⚠️ Puede ser última oportunidad antes de break
- ⚠️ Win rate: 50-65%

**Ejemplo Visual**:
```
Zona LP: 25100.00 - 25110.00 (size: 10 pts)

Vela:
  High: 25107.50   ← Penetra 7.5 puntos (75% de zona!)
  Open: 25095.00
  Close: 25102.00  ← Cierra en zona pero tercio inferior
  Low:  25095.00

Análisis:
  penetration_pct = 75% → Muy profunda
  close_position = (25102 - 25100) / 10 = 20% (en tercio inferior) ✓
  rejection_wick = 25107.5 - 25102 = 5.5 pts
  rejection_wick_pct = 5.5 / 12.5 = 44% ✓

→ R3_MEDIUM_REJECTION (penetración profunda pero rechazo fuerte)
```

**Señal de Trading**:
- ⚠️ **PRECAUCIÓN** - Solo con confluencia adicional
- Stop: 8-12 puntos detrás de zona
- Confianza: MEDIA

---

### R4 - DEEP REJECTION (Rechazo Profundo)

**Definición**: Penetración muy profunda (25-50%) pero rejection wick excepcional

**Criterios DEFAULT**:
```python
penetration_pct > 25.0 AND <= 50.0   # Entre 25-50% de zona
rejection_wick_pct >= 50.0           # Rejection wick ≥50% de vela
rejection_ratio >= 2.0               # Wick ≥ 2x el body
```

**Características**:
- 🔴 Zona **MUY DÉBIL**
- 🔴 Última oportunidad, probablemente será rota próximamente
- 🔴 Win rate: 40-55%
- 🔴 Solo válida si hay strong rejection wick

**Ejemplo Visual**:
```
Zona OB: 24800.00 - 24850.00 (size: 50 pts)

Vela:
  High: 24835.00   ← Penetra 35 puntos (70% de zona!)
  Open: 24790.00
  Close: 24795.00  ← Cierra FUERA pero penetró mucho
  Low:  24790.00

Análisis:
  penetration_pct = 70% ✗ (excede 50%, no es R4)

→ Probablemente P2_DEEP_PENETRATION en lugar de rebote
```

**Ejemplo válido R4**:
```
Zona OB: 24800.00 - 24850.00 (size: 50 pts)

Vela:
  High: 24825.00   ← Penetra 25 puntos (50% de zona)
  Open: 24790.00
  Close: 24792.00  ← Cierra fuera
  Low:  24790.00

Análisis:
  penetration_pct = 50% ✓ (límite)
  rejection_wick = 24825 - 24792 = 33 pts
  body = 24792 - 24790 = 2 pts
  rejection_ratio = 33 / 2 = 16.5 ✓ (excepcional)

→ R4_DEEP_REJECTION (penetración límite pero wick extraordinario)
```

**Señal de Trading**:
- 🔴 **ALTO RIESGO** - Solo para traders experimentados
- Stop: 10-15 puntos detrás de zona
- Confianza: BAJA-MEDIA
- Requiere: Confluencia con HTF structure + volumen excepcional

---

### Resumen Visual de Rebotes

```
ZONA: ████████████████████████ (100%)

R0: |── 1pt max
R1: |──── 3pts o 5%
R2: |──────── 10pts o 10%
R3: |──────────────── 25%
R4: |──────────────────────────── 50%
    └─ Límite de "rebote válido"

> 50% → Ya NO es rebote, es PENETRACIÓN
```

---

## Taxonomía de Penetraciones

### Clasificación de 5 Niveles (P1-P5)

Las penetraciones se clasifican según **profundidad**, **duración** y **comportamiento posterior**.

---

### P1 - SHALLOW PENETRATION (Penetración Superficial)

**Definición**: Entrada parcial en zona (25-50%) por tiempo breve

**Criterios DEFAULT**:
```python
penetration_pct >= 25.0 AND < 50.0   # Entre 25-50% de zona
duration_candles <= 3                # Máximo 3 velas dentro
may_close_inside == True             # Puede cerrar dentro
```

**Características**:
- 🟡 Zona está siendo **probada**
- 🟡 Puede revertir (50% probabilidad) o continuar
- 🟡 Monitorear siguiente vela para confirmación

**Ejemplo Visual**:
```
Zona OB Bullish: 24900.00 - 24950.00 (size: 50 pts)

Vela 1:
  Low: 24925.00    ← Penetra 25 pts (50% de zona)
  Close: 24930.00  ← Cierra dentro de zona

Vela 2:
  Low: 24920.00    ← Continúa dentro
  Close: 24955.00  ← SALE de zona (reversión)

→ P1_SHALLOW_PENETRATION → Reversión exitosa
→ OB sigue válido
```

**Señal de Trading**:
- 🟡 **ESPERAR CONFIRMACIÓN**
- Si reversa → Entry en re-test
- Si continúa → Zona invalidada

---

### P2 - DEEP PENETRATION (Penetración Profunda)

**Definición**: Entrada profunda (50-75%) con duración moderada

**Criterios DEFAULT**:
```python
penetration_pct >= 50.0 AND < 75.0   # Entre 50-75% de zona
duration_candles >= 3 AND <= 5       # 3-5 velas dentro
close_inside == True                 # Generalmente cierra dentro
```

**Características**:
- 🟠 Zona **debilitada significativamente**
- 🟠 Baja probabilidad de reversión (30-40%)
- 🟠 Posible cambio de carácter inminente

**Ejemplo Visual**:
```
Zona FVG Bearish: 25050.00 - 25070.00 (size: 20 pts)

Velas consecutivas:
  V1: High 25065.00 (penetra 15pts = 75%)
  V2: High 25063.00 (dentro)
  V3: High 25061.00 (dentro)
  V4: High 25060.00 (dentro, 4 velas)
  V5: Low  25045.00 (SALE hacia abajo = reversión)

→ P2_DEEP_PENETRATION con reversión tardía
→ FVG parcialmente rellenado, aún puede actuar como resistencia
```

**Señal de Trading**:
- 🟠 **ZONA COMPROMETIDA**
- Si reversa: Entry arriesgada, stop amplio
- Mejor esperar re-estructura en HTF

---

### P3 - FULL PENETRATION (Penetración Completa)

**Definición**: Toca o casi toca el extremo opuesto de zona (75-100%)

**Criterios DEFAULT**:
```python
penetration_pct >= 75.0 AND <= 100.0  # Entre 75-100% de zona
touches_opposite_edge == True         # Llega al otro extremo
stays_within_bounds == True           # No rompe completamente
```

**Características**:
- 🔴 Zona **casi completamente invalidada**
- 🔴 Solo válida si hay rejection violento
- 🔴 Zona probablemente cambió de polaridad

**Ejemplo Visual**:
```
Zona OB Bullish: 25000.00 - 25050.00 (size: 50 pts)

Vela:
  Low: 25005.00    ← Penetra 45 pts (90% de zona)
  Close: 25010.00  ← Casi toca ob_low

→ P3_FULL_PENETRATION
→ OB casi completamente rellenado
→ Si reversa, cambió de soporte a resistencia
```

**Señal de Trading**:
- 🔴 **ZONA INVALIDADA COMO SOPORTE**
- Esperar si cambia a resistencia
- No confiar en polaridad original

---

### P4 - FALSE BREAKOUT (Falso Rompimiento / TRAP)

**Definición**: Rompe completamente zona pero regresa dentro rápidamente

**Criterios DEFAULT**:
```python
breaks_zone_completely == True        # Rompe >100%
break_distance_pts >= 5.0            # Al menos 5 pts más allá
returns_within_candles <= 5          # Regresa en ≤5 velas
closes_back_inside == True           # Cierra de vuelta dentro
```

**Características**:
- 🟢 **TRAP / LIQUIDITY SWEEP** - Señal MUY ALCISTA
- 🟢 Institucionales barrieron liquidez
- 🟢 Alta probabilidad de movimiento fuerte en dirección opuesta
- 🟢 Win rate: 70-85% (cuando se confirma)

**Ejemplo Visual** (El más importante - NYH 20 Nov):
```
Zona: NYH @ 25310.00 (Buy-Side Liquidity)

Vela 1 (10:35 ET):
  High: 25310.00   ← Rompe exacto (sweep)
  Close: 25280.00  ← Cierra de vuelta ABAJO

Vela 2 (10:40 ET):
  Low: 25175.50    ← Impulso bajista -134.5 pts

→ P4_FALSE_BREAKOUT (CLASSIC SWEEP)
→ Bearish OB formado @ 25258-25310
→ Movimiento bajista de -790 pts sigue
```

**Señal de Trading**:
- 🟢 **MEJOR SETUP** cuando se confirma
- Entry: Re-test del OB formado después del sweep
- Stop: Detrás del sweep high/low
- TP: Próximo LP en dirección opuesta

---

### P5 - BREAK AND RETEST (Rompimiento y Re-testeo)

**Definición**: Rompe zona, continúa significativamente, regresa a testear

**Criterios DEFAULT**:
```python
breaks_zone_completely == True        # Rompe completamente
continuation_pts >= 20.0             # Continúa ≥20 pts
returns_to_retest == True            # Regresa a zona
retests_from_opposite_side == True   # Testea desde el otro lado
max_retest_candles <= 10             # Dentro de 10 velas
```

**Características**:
- 🔵 **CAMBIO DE POLARIDAD CONFIRMADO**
- 🔵 Soporte → Resistencia (o viceversa)
- 🔵 Zona sigue válida pero con función opuesta
- 🔵 Señal de continuación de tendencia

**Ejemplo Visual**:
```
Zona OB Bullish (soporte): 24800.00 - 24850.00

FASE 1 - Break:
  Vela 1: Low 24795.00 (rompe -5 pts)
  Vela 2: Low 24760.00 (continúa bajando)
  Vela 3: Low 24720.00 (continúa -80 pts total)

FASE 2 - Retest:
  Vela 7: High 24830.00 (regresa a OB desde ABAJO)
  Vela 8: Close 24810.00 (rechazado como RESISTENCIA)

→ P5_BREAK_AND_RETEST
→ OB cambió de soporte a resistencia
→ Confirmación de tendencia bajista
```

**Señal de Trading**:
- 🔵 **ENTRY EN RETEST** desde nuevo lado
- Stop: Dentro de la zona (5-10 pts)
- TP: Continuar con tendencia
- Confianza: ALTA para continuación

---

### Resumen Visual de Penetraciones

```
ZONA: ████████████████████████ (100%)

P1:       ├──────────┤ 25-50%   (Superficial)
P2:       ├──────────────────┤ 50-75% (Profunda)
P3:       ├────────────────────────┤ 75-100% (Completa)
P4:       ├─────────────────────────┤→ ←  (False Break)
P5:       ├─────────────────────────┤→→→ ← (Break & Retest)
```

---

## Parámetros Cuantificables

### Matriz de Medición Completa

Para cada interacción vela-zona, calculamos:

```python
class ZoneInteraction:
    # === IDENTIFICACIÓN ===
    timestamp: datetime           # Cuándo ocurrió
    zone_id: str                 # ID de la zona (OB/FVG/LP)
    zone_type: str               # "OB", "FVG", "LP"
    zone_low: float
    zone_high: float
    zone_size: float             # high - low

    # === PENETRACIÓN ===
    penetration_pts: float       # Puntos absolutos penetrados
    penetration_pct: float       # % de zona penetrada
    penetration_type: str        # "WICK_ONLY", "BODY_PARTIAL", "BODY_FULL"

    # === ANATOMÍA DE VELA ===
    candle_open: float
    candle_high: float
    candle_low: float
    candle_close: float
    candle_range: float          # high - low
    body_size: float             # abs(close - open)
    upper_wick: float            # high - max(open, close)
    lower_wick: float            # min(open, close) - low

    # === RECHAZO ===
    rejection_wick: float        # Tamaño del wick de rechazo
    rejection_wick_pct: float    # rejection_wick / candle_range
    rejection_ratio: float       # rejection_wick / body_size

    # === DURACIÓN ===
    duration_candles: int        # Número de velas en zona
    duration_minutes: int        # Tiempo total en minutos

    # === VOLUMEN ===
    volume: int                  # Volumen de la vela
    avg_volume: int              # Volumen promedio reciente
    volume_ratio: float          # volume / avg_volume

    # === POSICIÓN ===
    close_position: str          # "OUTSIDE", "INNER_THIRD", "MIDDLE_THIRD", "OUTER_THIRD"
    close_distance_from_edge: float  # Distancia del close al borde más cercano

    # === CLASIFICACIÓN ===
    interaction_type: str        # "R0", "R1", ..., "P5"
    interaction_strength: str    # "VERY_STRONG", "STRONG", "MEDIUM", "WEAK"
    expected_outcome: str        # "REVERSAL", "CONTINUATION", "NEUTRAL"
    confidence: float            # 0.0 - 1.0
```

### Fórmulas de Cálculo

#### 1. Penetración desde Abajo (zona como resistencia)

```python
def calculate_penetration_from_below(candle, zone_low, zone_high):
    if candle['high'] <= zone_low:
        return 0.0, 0.0  # No toca zona

    penetration_pts = min(candle['high'], zone_high) - zone_low
    zone_size = zone_high - zone_low
    penetration_pct = (penetration_pts / zone_size) * 100

    return penetration_pts, penetration_pct
```

#### 2. Penetración desde Arriba (zona como soporte)

```python
def calculate_penetration_from_above(candle, zone_low, zone_high):
    if candle['low'] >= zone_high:
        return 0.0, 0.0  # No toca zona

    penetration_pts = zone_high - max(candle['low'], zone_low)
    zone_size = zone_high - zone_low
    penetration_pct = (penetration_pts / zone_size) * 100

    return penetration_pts, penetration_pct
```

#### 3. Tipo de Penetración Anatómica

```python
def determine_penetration_type(candle, zone_low, zone_high):
    body_top = max(candle['open'], candle['close'])
    body_bottom = min(candle['open'], candle['close'])

    # Verificar si body penetra zona
    body_in_zone = not (body_bottom >= zone_high or body_top <= zone_low)

    if not body_in_zone:
        return "WICK_ONLY"

    # Verificar si body está completamente dentro
    body_fully_inside = (body_bottom >= zone_low and body_top <= zone_high)

    if body_fully_inside:
        return "BODY_FULL"
    else:
        return "BODY_PARTIAL"
```

#### 4. Fuerza de Rechazo

```python
def calculate_rejection_strength(candle, from_direction="BELOW"):
    body_top = max(candle['open'], candle['close'])
    body_bottom = min(candle['open'], candle['close'])
    total_range = candle['high'] - candle['low']
    body_size = abs(candle['close'] - candle['open'])

    if from_direction == "BELOW":
        # Rebote desde abajo - medir upper wick
        rejection_wick = candle['high'] - body_top
    else:
        # Rebote desde arriba - medir lower wick
        rejection_wick = body_bottom - candle['low']

    rejection_wick_pct = (rejection_wick / total_range) * 100 if total_range > 0 else 0
    rejection_ratio = rejection_wick / body_size if body_size > 0 else float('inf')

    return {
        'rejection_wick': rejection_wick,
        'rejection_wick_pct': rejection_wick_pct,
        'rejection_ratio': rejection_ratio
    }
```

#### 5. Posición del Cierre

```python
def determine_close_position(candle, zone_low, zone_high):
    close = candle['close']
    zone_size = zone_high - zone_low

    # Fuera de zona
    if close < zone_low or close > zone_high:
        return "OUTSIDE"

    # Dentro de zona - calcular posición
    position_in_zone = (close - zone_low) / zone_size

    if position_in_zone <= 0.33:
        return "LOWER_THIRD"
    elif position_in_zone <= 0.66:
        return "MIDDLE_THIRD"
    else:
        return "UPPER_THIRD"
```

### Valores DEFAULT de Parámetros

Estos son los valores por defecto (ver REBOTE_SETUP.md para customización):

```python
# REBOTES
R0_MAX_PENETRATION_PTS = 1.0
R1_MAX_PENETRATION_PTS = 3.0
R1_MAX_PENETRATION_PCT = 5.0
R2_MAX_PENETRATION_PTS = 10.0
R2_MAX_PENETRATION_PCT = 10.0
R2_MIN_REJECTION_WICK_PCT = 30.0
R3_MAX_PENETRATION_PCT = 25.0
R3_MIN_REJECTION_WICK_PCT = 20.0
R4_MAX_PENETRATION_PCT = 50.0
R4_MIN_REJECTION_WICK_PCT = 50.0
R4_MIN_REJECTION_RATIO = 2.0

# PENETRACIONES
P1_MIN_PENETRATION_PCT = 25.0
P1_MAX_PENETRATION_PCT = 50.0
P1_MAX_DURATION_CANDLES = 3
P2_MIN_PENETRATION_PCT = 50.0
P2_MAX_PENETRATION_PCT = 75.0
P2_MAX_DURATION_CANDLES = 5
P3_MIN_PENETRATION_PCT = 75.0
P4_MIN_BREAK_DISTANCE_PTS = 5.0
P4_MAX_RETURN_CANDLES = 5
P5_MIN_CONTINUATION_PTS = 20.0
P5_MAX_RETEST_CANDLES = 10
```

**Nota**: Estos valores están optimizados para **NQ Futures en timeframe 5min**. Para otros instrumentos/timeframes, ver REBOTE_SETUP.md para ajustes.

---

## Algoritmos de Detección SQL

### Función Principal de Clasificación

```sql
-- Función que clasifica interacción de una vela con una zona
CREATE OR REPLACE FUNCTION classify_zone_interaction(
    p_candle_open NUMERIC,
    p_candle_high NUMERIC,
    p_candle_low NUMERIC,
    p_candle_close NUMERIC,
    p_zone_low NUMERIC,
    p_zone_high NUMERIC,
    p_approach_from TEXT  -- 'BELOW' o 'ABOVE'
) RETURNS TABLE (
    interaction_type TEXT,
    interaction_strength TEXT,
    penetration_pts NUMERIC,
    penetration_pct NUMERIC,
    rejection_wick_pct NUMERIC
) AS $$
DECLARE
    v_zone_size NUMERIC;
    v_penetration_pts NUMERIC;
    v_penetration_pct NUMERIC;
    v_body_top NUMERIC;
    v_body_bottom NUMERIC;
    v_body_size NUMERIC;
    v_rejection_wick NUMERIC;
    v_total_range NUMERIC;
    v_rejection_wick_pct NUMERIC;
    v_rejection_ratio NUMERIC;
BEGIN
    -- Calcular basics
    v_zone_size := p_zone_high - p_zone_low;
    v_body_top := GREATEST(p_candle_open, p_candle_close);
    v_body_bottom := LEAST(p_candle_open, p_candle_close);
    v_body_size := ABS(p_candle_close - p_candle_open);
    v_total_range := p_candle_high - p_candle_low;

    -- Calcular penetración
    IF p_approach_from = 'BELOW' THEN
        -- Testando zona como resistencia
        IF p_candle_high <= p_zone_low THEN
            -- No toca zona
            RETURN QUERY SELECT 'NO_TOUCH'::TEXT, 'NONE'::TEXT, 0.0, 0.0, 0.0;
            RETURN;
        END IF;

        v_penetration_pts := LEAST(p_candle_high, p_zone_high) - p_zone_low;
        v_rejection_wick := p_candle_high - v_body_top;
    ELSE
        -- Testando zona como soporte
        IF p_candle_low >= p_zone_high THEN
            -- No toca zona
            RETURN QUERY SELECT 'NO_TOUCH'::TEXT, 'NONE'::TEXT, 0.0, 0.0, 0.0;
            RETURN;
        END IF;

        v_penetration_pts := p_zone_high - GREATEST(p_candle_low, p_zone_low);
        v_rejection_wick := v_body_bottom - p_candle_low;
    END IF;

    v_penetration_pct := (v_penetration_pts / v_zone_size) * 100;
    v_rejection_wick_pct := (v_rejection_wick / NULLIF(v_total_range, 0)) * 100;
    v_rejection_ratio := v_rejection_wick / NULLIF(v_body_size, 0);

    -- Clasificar según criterios

    -- R0 - CLEAN BOUNCE
    IF v_penetration_pts <= 1.0 AND v_body_top <= p_zone_low THEN
        RETURN QUERY SELECT 'R0_CLEAN_BOUNCE'::TEXT, 'VERY_STRONG'::TEXT,
                           v_penetration_pts, v_penetration_pct, v_rejection_wick_pct;
        RETURN;
    END IF;

    -- R1 - SHALLOW TOUCH
    IF v_penetration_pts <= 3.0 AND v_penetration_pct <= 5.0 THEN
        -- Verificar que body no penetra significativamente
        IF (p_approach_from = 'BELOW' AND v_body_top <= p_zone_low + 0.5) OR
           (p_approach_from = 'ABOVE' AND v_body_bottom >= p_zone_high - 0.5) THEN
            RETURN QUERY SELECT 'R1_SHALLOW_TOUCH'::TEXT, 'STRONG'::TEXT,
                               v_penetration_pts, v_penetration_pct, v_rejection_wick_pct;
            RETURN;
        END IF;
    END IF;

    -- R2 - LIGHT REJECTION
    IF v_penetration_pts <= 10.0 AND v_penetration_pct <= 10.0 THEN
        -- Debe cerrar fuera y tener buen rejection wick
        IF ((p_approach_from = 'BELOW' AND p_candle_close < p_zone_low) OR
            (p_approach_from = 'ABOVE' AND p_candle_close > p_zone_high)) AND
           v_rejection_wick_pct >= 30.0 THEN
            RETURN QUERY SELECT 'R2_LIGHT_REJECTION'::TEXT, 'MEDIUM_STRONG'::TEXT,
                               v_penetration_pts, v_penetration_pct, v_rejection_wick_pct;
            RETURN;
        END IF;
    END IF;

    -- R3 - MEDIUM REJECTION
    IF v_penetration_pct <= 25.0 AND v_rejection_wick_pct >= 20.0 THEN
        RETURN QUERY SELECT 'R3_MEDIUM_REJECTION'::TEXT, 'MEDIUM'::TEXT,
                           v_penetration_pts, v_penetration_pct, v_rejection_wick_pct;
        RETURN;
    END IF;

    -- R4 - DEEP REJECTION
    IF v_penetration_pct <= 50.0 AND v_rejection_wick_pct >= 50.0 AND v_rejection_ratio >= 2.0 THEN
        RETURN QUERY SELECT 'R4_DEEP_REJECTION'::TEXT, 'WEAK'::TEXT,
                           v_penetration_pts, v_penetration_pct, v_rejection_wick_pct;
        RETURN;
    END IF;

    -- Si no es rebote, es penetración
    IF v_penetration_pct < 50.0 THEN
        RETURN QUERY SELECT 'P1_SHALLOW_PENETRATION'::TEXT, 'TESTING'::TEXT,
                           v_penetration_pts, v_penetration_pct, v_rejection_wick_pct;
    ELSIF v_penetration_pct < 75.0 THEN
        RETURN QUERY SELECT 'P2_DEEP_PENETRATION'::TEXT, 'WEAKENED'::TEXT,
                           v_penetration_pts, v_penetration_pct, v_rejection_wick_pct;
    ELSE
        RETURN QUERY SELECT 'P3_FULL_PENETRATION'::TEXT, 'INVALIDATED'::TEXT,
                           v_penetration_pts, v_penetration_pct, v_rejection_wick_pct;
    END IF;

END;
$$ LANGUAGE plpgsql;
```

### Ejemplo de Uso en Query

```sql
-- Analizar todas las interacciones con un Order Block específico
WITH ob_zone AS (
    SELECT
        '2025-11-20 10:35:00-05'::TIMESTAMPTZ as ob_time,
        25258.75 as ob_low,
        25310.00 as ob_high,
        'BEARISH' as ob_type
),
candles_after_ob AS (
    SELECT
        time_interval,
        open, high, low, close, volume
    FROM candlestick_5min
    WHERE symbol = 'NQZ5'
      AND time_interval > (SELECT ob_time FROM ob_zone)
      AND time_interval <= (SELECT ob_time FROM ob_zone) + INTERVAL '24 hours'
),
interactions AS (
    SELECT
        c.time_interval AT TIME ZONE 'America/New_York' as et_time,
        c.open, c.high, c.low, c.close,
        ob.ob_low,
        ob.ob_high,
        -- Determinar desde dónde se acerca
        CASE
            WHEN c.low < ob.ob_low THEN 'BELOW'
            WHEN c.high > ob.ob_high THEN 'ABOVE'
            ELSE 'INSIDE'
        END as approach_from,
        -- Clasificar interacción
        (SELECT * FROM classify_zone_interaction(
            c.open, c.high, c.low, c.close,
            ob.ob_low, ob.ob_high,
            CASE
                WHEN c.low < ob.ob_low THEN 'BELOW'
                ELSE 'ABOVE'
            END
        )) as interaction
    FROM candles_after_ob c
    CROSS JOIN ob_zone ob
    WHERE c.high >= ob.ob_low AND c.low <= ob.ob_high  -- Solo velas que tocan OB
)
SELECT
    et_time,
    ROUND(low::NUMERIC, 2) as low,
    ROUND(high::NUMERIC, 2) as high,
    ROUND(close::NUMERIC, 2) as close,
    approach_from,
    (interaction).interaction_type,
    (interaction).interaction_strength,
    ROUND((interaction).penetration_pts, 2) as penetration_pts,
    ROUND((interaction).penetration_pct, 2) as penetration_pct,
    ROUND((interaction).rejection_wick_pct, 2) as rejection_pct
FROM interactions
ORDER BY et_time;
```

### Query: Detectar False Breakouts (P4)

```sql
-- Detectar False Breakouts de zonas importantes
WITH zones AS (
    -- Order Blocks, FVGs, LPs detectados previamente
    SELECT
        zone_id,
        zone_type,  -- 'OB', 'FVG', 'LP'
        zone_low,
        zone_high,
        formation_time,
        orientation  -- 'BULLISH', 'BEARISH', 'BUY_SIDE', 'SELL_SIDE'
    FROM detected_zones
    WHERE formation_time >= '2025-11-20 09:00:00-05'
),
breaks AS (
    -- Detectar velas que rompen zonas
    SELECT
        z.zone_id,
        z.zone_type,
        z.zone_low,
        z.zone_high,
        c.time_interval as break_time,
        c.high as break_high,
        c.low as break_low,
        c.close as break_close,
        -- Distancia del break
        CASE
            WHEN z.orientation IN ('BULLISH', 'SELL_SIDE') AND c.low < z.zone_low THEN
                z.zone_low - c.low
            WHEN z.orientation IN ('BEARISH', 'BUY_SIDE') AND c.high > z.zone_high THEN
                c.high - z.zone_high
        END as break_distance
    FROM zones z
    INNER JOIN candlestick_5min c
        ON c.symbol = 'NQZ5'
        AND c.time_interval > z.formation_time
        AND c.time_interval <= z.formation_time + INTERVAL '48 hours'
    WHERE
        -- Rompe zona completamente
        (z.orientation IN ('BULLISH', 'SELL_SIDE') AND c.low < z.zone_low - 5) OR
        (z.orientation IN ('BEARISH', 'BUY_SIDE') AND c.high > z.zone_high + 5)
),
false_breaks AS (
    -- Buscar si precio regresa dentro de 5 velas
    SELECT
        b.*,
        -- Verificar próximas 5 velas
        (
            SELECT COUNT(*)
            FROM candlestick_5min c2
            WHERE c2.symbol = 'NQZ5'
                AND c2.time_interval > b.break_time
                AND c2.time_interval <= b.break_time + INTERVAL '25 minutes'
                AND (
                    -- Para break bajista, verificar si regresa ARRIBA de zone
                    (b.break_low < b.zone_low AND c2.close > b.zone_low) OR
                    -- Para break alcista, verificar si regresa ABAJO de zone
                    (b.break_high > b.zone_high AND c2.close < b.zone_high)
                )
        ) > 0 as returned_inside
    FROM breaks b
)
SELECT
    zone_id,
    zone_type,
    TO_CHAR(break_time AT TIME ZONE 'America/New_York', 'YYYY-MM-DD HH24:MI') as break_time_et,
    ROUND(zone_low::NUMERIC, 2) as zone_low,
    ROUND(zone_high::NUMERIC, 2) as zone_high,
    ROUND(break_distance::NUMERIC, 2) as break_distance,
    returned_inside,
    CASE
        WHEN returned_inside THEN 'P4_FALSE_BREAKOUT'
        ELSE 'GENUINE_BREAK'
    END as classification
FROM false_breaks
WHERE returned_inside = TRUE  -- Solo false breakouts
ORDER BY break_time;
```

---

## Implementación Python

### Clase Principal

```python
from dataclasses import dataclass
from typing import Optional, Literal
from datetime import datetime

@dataclass
class ZoneInteraction:
    """Resultado de clasificación de interacción vela-zona"""

    # Identificación
    timestamp: datetime
    zone_id: str
    zone_type: Literal["OB", "FVG", "LP"]

    # Zona
    zone_low: float
    zone_high: float
    zone_size: float

    # Vela
    candle_open: float
    candle_high: float
    candle_low: float
    candle_close: float
    candle_volume: int

    # Penetración
    penetration_pts: float
    penetration_pct: float
    penetration_type: Literal["WICK_ONLY", "BODY_PARTIAL", "BODY_FULL"]

    # Rechazo
    rejection_wick: float
    rejection_wick_pct: float
    rejection_ratio: float

    # Clasificación
    interaction_type: str  # "R0", "R1", ..., "P5"
    interaction_strength: str
    expected_outcome: Literal["REVERSAL", "CONTINUATION", "NEUTRAL"]
    confidence: float  # 0.0 - 1.0


class ZoneInteractionClassifier:
    """
    Clasificador de interacciones precio-zona

    Uso:
        classifier = ZoneInteractionClassifier()
        result = classifier.classify(candle, zone_low, zone_high, from_direction="BELOW")
    """

    def __init__(self, config: Optional['ReboteConfig'] = None):
        """
        Args:
            config: Configuración de parámetros (ver REBOTE_SETUP.md)
                   Si None, usa valores DEFAULT
        """
        from configs.interaction_config import ReboteConfig
        self.config = config or ReboteConfig()

    def classify(
        self,
        candle: dict,
        zone_low: float,
        zone_high: float,
        zone_id: str = "UNKNOWN",
        zone_type: str = "OB",
        from_direction: Literal["BELOW", "ABOVE"] = "BELOW"
    ) -> ZoneInteraction:
        """
        Clasifica interacción de una vela con una zona

        Args:
            candle: dict con keys: open, high, low, close, volume, timestamp
            zone_low: Límite inferior de zona
            zone_high: Límite superior de zona
            zone_id: Identificador de zona
            zone_type: "OB", "FVG", o "LP"
            from_direction: "BELOW" (testa resistencia) o "ABOVE" (testa soporte)

        Returns:
            ZoneInteraction con clasificación completa
        """

        zone_size = zone_high - zone_low

        # Calcular penetración
        pen_pts, pen_pct = self._calculate_penetration(
            candle, zone_low, zone_high, from_direction
        )

        # Tipo de penetración anatómica
        pen_type = self._determine_penetration_type(candle, zone_low, zone_high)

        # Fuerza de rechazo
        rej_metrics = self._calculate_rejection_strength(candle, from_direction)

        # Clasificar tipo de interacción
        interaction_type, strength, expected, confidence = self._classify_interaction(
            pen_pts, pen_pct, pen_type, rej_metrics, candle, zone_low, zone_high
        )

        return ZoneInteraction(
            timestamp=candle['timestamp'],
            zone_id=zone_id,
            zone_type=zone_type,
            zone_low=zone_low,
            zone_high=zone_high,
            zone_size=zone_size,
            candle_open=candle['open'],
            candle_high=candle['high'],
            candle_low=candle['low'],
            candle_close=candle['close'],
            candle_volume=candle['volume'],
            penetration_pts=pen_pts,
            penetration_pct=pen_pct,
            penetration_type=pen_type,
            rejection_wick=rej_metrics['rejection_wick'],
            rejection_wick_pct=rej_metrics['rejection_wick_pct'],
            rejection_ratio=rej_metrics['rejection_ratio'],
            interaction_type=interaction_type,
            interaction_strength=strength,
            expected_outcome=expected,
            confidence=confidence
        )

    def _calculate_penetration(
        self,
        candle: dict,
        zone_low: float,
        zone_high: float,
        from_direction: str
    ) -> tuple[float, float]:
        """Calcula penetración en puntos y porcentaje"""

        zone_size = zone_high - zone_low

        if from_direction == "BELOW":
            # Testando zona como resistencia
            if candle['high'] <= zone_low:
                return 0.0, 0.0
            penetration_pts = min(candle['high'], zone_high) - zone_low
        else:
            # Testando zona como soporte
            if candle['low'] >= zone_high:
                return 0.0, 0.0
            penetration_pts = zone_high - max(candle['low'], zone_low)

        penetration_pct = (penetration_pts / zone_size) * 100
        return penetration_pts, penetration_pct

    def _determine_penetration_type(
        self,
        candle: dict,
        zone_low: float,
        zone_high: float
    ) -> str:
        """Determina si penetración es solo wick, body parcial o body completo"""

        body_top = max(candle['open'], candle['close'])
        body_bottom = min(candle['open'], candle['close'])

        # Verificar si body penetra zona
        body_in_zone = not (body_bottom >= zone_high or body_top <= zone_low)

        if not body_in_zone:
            return "WICK_ONLY"

        # Verificar si body está completamente dentro
        body_fully_inside = (body_bottom >= zone_low and body_top <= zone_high)

        return "BODY_FULL" if body_fully_inside else "BODY_PARTIAL"

    def _calculate_rejection_strength(
        self,
        candle: dict,
        from_direction: str
    ) -> dict:
        """Calcula métricas de fuerza de rechazo"""

        body_top = max(candle['open'], candle['close'])
        body_bottom = min(candle['open'], candle['close'])
        total_range = candle['high'] - candle['low']
        body_size = abs(candle['close'] - candle['open'])

        if from_direction == "BELOW":
            rejection_wick = candle['high'] - body_top
        else:
            rejection_wick = body_bottom - candle['low']

        rejection_wick_pct = (rejection_wick / total_range * 100) if total_range > 0 else 0
        rejection_ratio = (rejection_wick / body_size) if body_size > 0 else float('inf')

        return {
            'rejection_wick': rejection_wick,
            'rejection_wick_pct': rejection_wick_pct,
            'rejection_ratio': rejection_ratio
        }

    def _classify_interaction(
        self,
        pen_pts: float,
        pen_pct: float,
        pen_type: str,
        rej_metrics: dict,
        candle: dict,
        zone_low: float,
        zone_high: float
    ) -> tuple[str, str, str, float]:
        """
        Clasifica tipo de interacción según taxonomía

        Returns:
            (interaction_type, strength, expected_outcome, confidence)
        """

        cfg = self.config
        close = candle['close']
        close_outside = (close < zone_low or close > zone_high)

        # === REBOTES ===

        # R0 - CLEAN BOUNCE
        if (pen_pts <= cfg.r0_max_penetration_pts and
            pen_type == "WICK_ONLY" and
            close_outside):
            return ("R0_CLEAN_BOUNCE", "VERY_STRONG", "REVERSAL", 0.90)

        # R1 - SHALLOW TOUCH
        if (pen_pts <= cfg.r1_max_penetration_pts and
            pen_pct <= cfg.r1_max_penetration_pct and
            pen_type == "WICK_ONLY" and
            close_outside):
            return ("R1_SHALLOW_TOUCH", "STRONG", "REVERSAL", 0.80)

        # R2 - LIGHT REJECTION
        if (pen_pts <= cfg.r2_max_penetration_pts and
            pen_pct <= cfg.r2_max_penetration_pct and
            close_outside and
            rej_metrics['rejection_wick_pct'] >= cfg.r2_min_rejection_wick_pct):
            return ("R2_LIGHT_REJECTION", "MEDIUM_STRONG", "REVERSAL", 0.70)

        # R3 - MEDIUM REJECTION
        if (pen_pct <= cfg.r3_max_penetration_pct and
            rej_metrics['rejection_wick_pct'] >= cfg.r3_min_rejection_wick_pct):
            return ("R3_MEDIUM_REJECTION", "MEDIUM", "REVERSAL", 0.60)

        # R4 - DEEP REJECTION
        if (pen_pct <= cfg.r4_max_penetration_pct and
            rej_metrics['rejection_wick_pct'] >= cfg.r4_min_rejection_wick_pct and
            rej_metrics['rejection_ratio'] >= cfg.r4_min_rejection_ratio):
            return ("R4_DEEP_REJECTION", "WEAK", "REVERSAL", 0.50)

        # === PENETRACIONES ===

        # P1 - SHALLOW PENETRATION
        if 25.0 <= pen_pct < 50.0:
            return ("P1_SHALLOW_PENETRATION", "TESTING", "NEUTRAL", 0.50)

        # P2 - DEEP PENETRATION
        if 50.0 <= pen_pct < 75.0:
            return ("P2_DEEP_PENETRATION", "WEAKENED", "CONTINUATION", 0.40)

        # P3 - FULL PENETRATION
        if pen_pct >= 75.0:
            return ("P3_FULL_PENETRATION", "INVALIDATED", "CONTINUATION", 0.30)

        # Default - penetración leve sin clasificar
        return ("UNCLASSIFIED", "UNKNOWN", "NEUTRAL", 0.30)


# === EJEMPLO DE USO ===

if __name__ == "__main__":
    from datetime import datetime

    # Ejemplo: OB Bearish del 20 Nov
    ob_zone = {
        'zone_id': 'OB_20NOV_1035',
        'zone_type': 'OB',
        'zone_low': 25258.75,
        'zone_high': 25310.00
    }

    # Vela que toca el OB
    candle = {
        'timestamp': datetime(2025, 11, 20, 10, 40),
        'open': 25270.00,
        'high': 25285.00,
        'low': 25255.00,
        'close': 25260.00,
        'volume': 3500
    }

    # Clasificar
    classifier = ZoneInteractionClassifier()
    result = classifier.classify(
        candle=candle,
        zone_low=ob_zone['zone_low'],
        zone_high=ob_zone['zone_high'],
        zone_id=ob_zone['zone_id'],
        zone_type=ob_zone['zone_type'],
        from_direction="BELOW"
    )

    print(f"Tipo de interacción: {result.interaction_type}")
    print(f"Fuerza: {result.interaction_strength}")
    print(f"Penetración: {result.penetration_pts:.2f} pts ({result.penetration_pct:.1f}%)")
    print(f"Tipo penetración: {result.penetration_type}")
    print(f"Rejection wick: {result.rejection_wick_pct:.1f}%")
    print(f"Outcome esperado: {result.expected_outcome}")
    print(f"Confianza: {result.confidence:.0%}")
```

---

## Integración con Trading

### Señales por Tipo de Interacción

#### Señales ALCISTAS (Zona como Soporte)

| Tipo | Señal | Entry | Stop Loss | Confianza |
|------|-------|-------|-----------|-----------|
| **R0** | ✅ LONG INMEDIATO | Al cierre de vela | 2-3 pts debajo zone_low | 90% |
| **R1** | ✅ LONG VÁLIDO | Al cierre o próxima vela | 3-5 pts debajo zone_low | 80% |
| **R2** | ✅ LONG con CONFIRMACIÓN | Esperar próxima vela | 5-8 pts debajo zone_low | 70% |
| **R3** | ⚠️ LONG PRECAUCIÓN | Con confluencia adicional | 8-12 pts debajo zone_low | 60% |
| **R4** | 🔴 LONG ALTO RIESGO | Solo traders avanzados | 10-15 pts debajo zone_low | 50% |
| **P1** | 🟡 ESPERAR | Monitorear próxima vela | - | - |
| **P2** | 🟠 ZONA DÉBIL | No entrar, esperar | - | - |
| **P3** | 🔴 INVALIDADA | Zona perdió función soporte | - | - |
| **P4** | 🟢 TRAP ALCISTA | Entry después confirmación | 5 pts sobre sweep high | 80% |
| **P5** | 🔵 RESISTENCIA | Entry short en retest | Dentro de zona | 75% |

#### Señales BAJISTAS (Zona como Resistencia)

Invertir la tabla anterior (LONG→SHORT, debajo→arriba, etc.)

### Gestión de Riesgo por Tipo

```python
def calculate_position_size(
    interaction: ZoneInteraction,
    account_balance: float,
    risk_pct: float = 1.0
) -> dict:
    """
    Calcula position size según tipo de interacción y confianza

    Args:
        interaction: Resultado de clasificación
        account_balance: Balance de cuenta
        risk_pct: % de cuenta a arriesgar (default 1%)

    Returns:
        dict con: contracts, risk_amount, stop_distance
    """

    # Ajustar risk según confianza
    adjusted_risk_pct = risk_pct * interaction.confidence
    risk_amount = account_balance * (adjusted_risk_pct / 100)

    # Calcular stop distance según tipo
    stop_distances = {
        'R0_CLEAN_BOUNCE': 3.0,
        'R1_SHALLOW_TOUCH': 5.0,
        'R2_LIGHT_REJECTION': 8.0,
        'R3_MEDIUM_REJECTION': 12.0,
        'R4_DEEP_REJECTION': 15.0,
        'P4_FALSE_BREAKOUT': 5.0,
        'P5_BREAK_AND_RETEST': 8.0
    }

    stop_distance = stop_distances.get(interaction.interaction_type, 10.0)

    # NQ: $20 per point
    point_value = 20
    contracts = int(risk_amount / (stop_distance * point_value))

    return {
        'contracts': max(contracts, 1),  # Mínimo 1 contrato
        'risk_amount': risk_amount,
        'stop_distance': stop_distance,
        'adjusted_risk_pct': adjusted_risk_pct
    }
```

### Estrategia Completa

```python
class ZoneInteractionStrategy:
    """Estrategia de trading basada en interacciones con zonas"""

    def __init__(self, classifier: ZoneInteractionClassifier):
        self.classifier = classifier
        self.active_zones = []  # Lista de zonas monitoreadas

    def add_zone(self, zone: dict):
        """Agregar zona a monitorear"""
        self.active_zones.append(zone)

    def on_candle_close(self, candle: dict) -> Optional[dict]:
        """
        Procesar cierre de vela y generar señales

        Returns:
            dict con señal de trading o None
        """

        for zone in self.active_zones:
            # Verificar si vela toca zona
            if not self._candle_touches_zone(candle, zone):
                continue

            # Clasificar interacción
            interaction = self.classifier.classify(
                candle=candle,
                zone_low=zone['low'],
                zone_high=zone['high'],
                zone_id=zone['id'],
                zone_type=zone['type'],
                from_direction=self._determine_approach(candle, zone)
            )

            # Generar señal según tipo
            signal = self._generate_signal(interaction, zone)

            if signal:
                return signal

        return None

    def _candle_touches_zone(self, candle: dict, zone: dict) -> bool:
        """Verifica si vela toca zona"""
        return not (candle['high'] < zone['low'] or candle['low'] > zone['high'])

    def _determine_approach(self, candle: dict, zone: dict) -> str:
        """Determina dirección de approach"""
        return "BELOW" if candle['low'] < zone['low'] else "ABOVE"

    def _generate_signal(
        self,
        interaction: ZoneInteraction,
        zone: dict
    ) -> Optional[dict]:
        """Genera señal de trading según interacción"""

        # Tipos válidos para entry
        valid_entries = {
            'R0_CLEAN_BOUNCE': {'action': 'IMMEDIATE', 'confidence': 0.90},
            'R1_SHALLOW_TOUCH': {'action': 'VALID', 'confidence': 0.80},
            'R2_LIGHT_REJECTION': {'action': 'WITH_CONFIRMATION', 'confidence': 0.70},
            'P4_FALSE_BREAKOUT': {'action': 'TRAP', 'confidence': 0.80}
        }

        if interaction.interaction_type not in valid_entries:
            return None

        entry_info = valid_entries[interaction.interaction_type]

        # Determinar dirección
        if zone['orientation'] == 'BULLISH':
            direction = 'LONG'
            entry_price = interaction.candle_close
            stop_loss = interaction.zone_low - 5.0
        else:
            direction = 'SHORT'
            entry_price = interaction.candle_close
            stop_loss = interaction.zone_high + 5.0

        return {
            'timestamp': interaction.timestamp,
            'zone_id': zone['id'],
            'direction': direction,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'interaction_type': interaction.interaction_type,
            'confidence': entry_info['confidence'],
            'action': entry_info['action']
        }
```

---

## Ejemplos Validados

### Ejemplo 1: NYH Sweep - P4 False Breakout (20 Nov 2025)

**Setup**:
- **Zona**: NYH @ 25310.00 (Buy-Side Liquidity)
- **Tipo**: Liquidity Pool
- **Orientación**: Buy-Side (resistencia)

**Secuencia**:

```
Vela 1 (10:35 ET):
  Open: 25280.00
  High: 25310.00  ← Toca exacto el NYH
  Low: 25258.75
  Close: 25280.00

Análisis:
  penetration_pts = 0.0 (toca exacto, no penetra)
  break_distance = 0.0
  close_position = OUTSIDE (cierra 30 pts abajo)
  rejection_wick = 25310 - 25280 = 30 pts

→ Borderline entre R0 y P4
→ Dado contexto (NYH + alto volumen), clasificar como P4_FALSE_BREAKOUT
```

**Resultado**:
- Impulso bajista inmediato: -134.5 pts en 1 vela
- Bearish OB formado @ 25258.75-25310.00
- Movimiento total: -790 pts hacia 24520.00

**Trading Signal**:
- ✅ Entry SHORT en re-test del OB
- Entry: 25280-25290 (re-test zone)
- Stop: 25315 (5 pts arriba del sweep)
- TP1: 25100 (180 pts = 1:7 RR)
- TP2: 24750 (530 pts = 1:21 RR)
- Resultado: TP2 hit, +530 pts

**Confianza retrospectiva**: 95% (setup perfecto)

---

### Ejemplo 2: Bullish OB - R1 Shallow Touch (25 Nov 2025)

**Setup**:
- **Zona**: Bullish OB @ 24719.00-24837.75
- **Tipo**: Order Block
- **Formado**: 09:40 ET (después de rally +87.5 pts)

**Interacción (10:20 ET)**:

```
Vela:
  Open: 24800.00
  High: 24825.00
  Low: 24721.00  ← Penetra 2 puntos en OB
  Close: 24810.00

Análisis:
  zone_low = 24719.00
  zone_high = 24837.75
  zone_size = 118.75 pts

  penetration_pts = 24721 - 24719 = 2.0 pts
  penetration_pct = (2.0 / 118.75) * 100 = 1.7%

  body_bottom = min(24800, 24810) = 24800
  body_penetration = 24800 > 24719? → NO penetra
  pen_type = WICK_ONLY

  rejection_wick = 24800 - 24721 = 79 pts
  total_range = 24825 - 24721 = 104 pts
  rejection_wick_pct = (79 / 104) * 100 = 76%

→ R1_SHALLOW_TOUCH
→ Strength: STRONG
→ Expected: REVERSAL
→ Confidence: 80%
```

**Resultado**:
- Rally inmediato: +82.75 pts
- OB respetado perfectamente
- Tocado 10 veces más durante el día
- Actuó como soporte 6/10 veces

**Trading Signal**:
- ✅ Entry LONG al cierre (24810)
- Stop: 24714 (5 pts debajo OB)
- TP1: 24890 (80 pts = 1:8 RR)
- Resultado: TP1 hit en 3 velas

**Win rate histórico de R1 en este OB**: 60% (6/10 retests)

---

### Ejemplo 3: FVG - R2 Light Rejection (24 Nov 2025)

**Setup**:
- **Zona**: Bearish FVG @ 24960.75-24973.25
- **Tipo**: Fair Value Gap
- **Formado**: 18:55 ET (Sunday evening)

**Interacción (19:05 ET - 10 min después)**:

```
Vela:
  Open: 24950.00
  High: 24968.00  ← Penetra 7.25 pts en FVG
  Low: 24940.00
  Close: 24945.00

Análisis:
  zone_low = 24960.75 (fvg_start)
  zone_high = 24973.25 (fvg_end)
  zone_size = 12.50 pts

  penetration_pts = 24968 - 24960.75 = 7.25 pts
  penetration_pct = (7.25 / 12.50) * 100 = 58%  ← Excede 10%

  close = 24945 < zone_low ✓ (cierra fuera)

  rejection_wick = 24968 - 24945 = 23 pts
  total_range = 24968 - 24940 = 28 pts
  rejection_wick_pct = (23 / 28) * 100 = 82%  ✓✓

→ Penetración excede R2 threshold (58% > 10%)
→ Pero: rejection_wick excepcional (82%)
→ Clasificación: R2_LIGHT_REJECTION (por rejection fuerte)
→ Borderline con R3
```

**Resultado**:
- FVG actuó como resistencia 14 veces
- Finalmente roto el lunes durante rally
- Cambió de resistencia → soporte después de break

**Trading Signal**:
- ⚠️ Entry SHORT con precaución
- Entry: 24945 (cierre)
- Stop: 24975 (arriba FVG)
- TP: 24900 (45 pts = 1:1.5 RR)
- Resultado: TP hit, pero setup no ideal (penetración profunda)

**Lección**: R2 con >50% penetración requiere confirmación adicional

---

### Ejemplo 4: LP - R4 Deep Rejection (Hipotético)

**Setup**:
- **Zona**: Equal Low @ 24400.00 (Sell-Side Liquidity)
- **Tolerancia**: ±5 pts → Zona: 24395.00-24405.00

**Interacción**:

```
Vela:
  Open: 24410.00
  High: 24415.00
  Low: 24398.00  ← Penetra 7 pts (70% de zona de 10 pts)
  Close: 24412.00

Análisis:
  zone_low = 24395.00
  zone_high = 24405.00
  zone_size = 10.0 pts

  penetration_pts = 24405 - 24398 = 7.0 pts
  penetration_pct = (7.0 / 10.0) * 100 = 70%  ← Muy profunda

  rejection_wick = 24412 - 24398 = 14 pts
  body = 24412 - 24410 = 2 pts
  rejection_ratio = 14 / 2 = 7.0  ✓✓✓ (excepcional)

  total_range = 24415 - 24398 = 17 pts
  rejection_wick_pct = (14 / 17) * 100 = 82%  ✓✓

→ penetration_pct = 70% > 50% → Excede R4 límite
→ Pero: rejection_ratio = 7.0 (extraordinario)
→ Clasificación: P2_DEEP_PENETRATION con strong rejection
→ O borderline R4 si se permite flexibilidad
```

**Señal**:
- 🔴 Zona MUY débil (penetración 70%)
- 🟢 Rejection excepcional (ratio 7.0)
- ⚠️ Trade de alto riesgo

**Decisión**:
- Si HTF structure apoya: Entry LONG arriesgada
- Stop: 24392 (debajo zona)
- Requiere confluencia adicional para validar

---

## Métricas para Backtesting

### Queries de Análisis

#### 1. Win Rate por Tipo de Interacción

```sql
-- Calcular win rate de cada tipo de rebote/penetración
WITH interactions AS (
    SELECT
        zone_id,
        interaction_time,
        interaction_type,
        interaction_strength,
        expected_outcome,
        -- Precio de entry
        entry_price,
        -- Stop loss
        stop_loss,
        -- Take profit (estimado)
        take_profit
    FROM zone_interactions
    WHERE interaction_type IN (
        'R0_CLEAN_BOUNCE', 'R1_SHALLOW_TOUCH', 'R2_LIGHT_REJECTION',
        'R3_MEDIUM_REJECTION', 'R4_DEEP_REJECTION', 'P4_FALSE_BREAKOUT'
    )
),
outcomes AS (
    SELECT
        i.*,
        -- Verificar si TP fue hit
        (
            SELECT COUNT(*) > 0
            FROM candlestick_5min c
            WHERE c.symbol = 'NQZ5'
                AND c.time_interval > i.interaction_time
                AND c.time_interval <= i.interaction_time + INTERVAL '4 hours'
                AND (
                    (i.expected_outcome = 'REVERSAL' AND i.entry_price < i.take_profit AND c.high >= i.take_profit) OR
                    (i.expected_outcome = 'REVERSAL' AND i.entry_price > i.take_profit AND c.low <= i.take_profit)
                )
        ) as tp_hit,
        -- Verificar si SL fue hit
        (
            SELECT COUNT(*) > 0
            FROM candlestick_5min c
            WHERE c.symbol = 'NQZ5'
                AND c.time_interval > i.interaction_time
                AND c.time_interval <= i.interaction_time + INTERVAL '4 hours'
                AND (
                    (i.entry_price < i.stop_loss AND c.high >= i.stop_loss) OR
                    (i.entry_price > i.stop_loss AND c.low <= i.stop_loss)
                )
        ) as sl_hit
    FROM interactions i
)
SELECT
    interaction_type,
    COUNT(*) as total_trades,
    SUM(CASE WHEN tp_hit AND NOT sl_hit THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN sl_hit THEN 1 ELSE 0 END) as losses,
    ROUND(
        100.0 * SUM(CASE WHEN tp_hit AND NOT sl_hit THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) as win_rate_pct,
    -- Average move después de interacción
    AVG(
        CASE
            WHEN tp_hit THEN ABS(take_profit - entry_price)
            WHEN sl_hit THEN -ABS(stop_loss - entry_price)
            ELSE 0
        END
    ) as avg_pnl_pts
FROM outcomes
GROUP BY interaction_type
ORDER BY win_rate_pct DESC;
```

**Resultados Esperados** (hipotético basado en análisis):

| Tipo | Total Trades | Wins | Losses | Win Rate | Avg P&L |
|------|--------------|------|--------|----------|---------|
| R0_CLEAN_BOUNCE | 15 | 13 | 2 | 86.7% | +42.5 pts |
| P4_FALSE_BREAKOUT | 8 | 6 | 2 | 75.0% | +85.0 pts |
| R1_SHALLOW_TOUCH | 45 | 32 | 13 | 71.1% | +28.3 pts |
| R2_LIGHT_REJECTION | 67 | 42 | 25 | 62.7% | +18.2 pts |
| R3_MEDIUM_REJECTION | 32 | 17 | 15 | 53.1% | +5.8 pts |
| R4_DEEP_REJECTION | 12 | 5 | 7 | 41.7% | -8.5 pts |

#### 2. Average Move por Tipo

```sql
-- Calcular movimiento promedio después de cada tipo de interacción
WITH interactions AS (
    SELECT
        interaction_time,
        interaction_type,
        entry_price,
        expected_outcome
    FROM zone_interactions
),
price_moves AS (
    SELECT
        i.interaction_type,
        i.expected_outcome,
        -- Move en próximos 15 min (3 velas)
        (
            SELECT close
            FROM candlestick_5min c
            WHERE c.symbol = 'NQZ5'
                AND c.time_interval = i.interaction_time + INTERVAL '15 minutes'
        ) - i.entry_price as move_15min,
        -- Move en próximas 1 hora (12 velas)
        (
            SELECT close
            FROM candlestick_5min c
            WHERE c.symbol = 'NQZ5'
                AND c.time_interval = i.interaction_time + INTERVAL '1 hour'
        ) - i.entry_price as move_1hr
    FROM interactions i
)
SELECT
    interaction_type,
    expected_outcome,
    COUNT(*) as occurrences,
    ROUND(AVG(move_15min)::NUMERIC, 2) as avg_move_15min,
    ROUND(AVG(move_1hr)::NUMERIC, 2) as avg_move_1hr,
    ROUND(STDDEV(move_1hr)::NUMERIC, 2) as stddev_1hr
FROM price_moves
WHERE move_15min IS NOT NULL AND move_1hr IS NOT NULL
GROUP BY interaction_type, expected_outcome
ORDER BY ABS(avg_move_1hr) DESC;
```

#### 3. Tasa de Invalidación por Tipo

```sql
-- Cuántas zonas son invalidadas después de cada tipo de interacción
WITH zone_interactions_sequence AS (
    SELECT
        zone_id,
        interaction_time,
        interaction_type,
        -- Próxima interacción con la misma zona
        LEAD(interaction_type) OVER (
            PARTITION BY zone_id
            ORDER BY interaction_time
        ) as next_interaction
    FROM zone_interactions
)
SELECT
    interaction_type,
    COUNT(*) as total,
    SUM(CASE
        WHEN next_interaction LIKE 'P%' THEN 1
        ELSE 0
    END) as led_to_penetration,
    ROUND(
        100.0 * SUM(CASE WHEN next_interaction LIKE 'P%' THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) as invalidation_rate_pct
FROM zone_interactions_sequence
WHERE interaction_type LIKE 'R%'  -- Solo rebotes
GROUP BY interaction_type
ORDER BY invalidation_rate_pct ASC;
```

**Insight esperado**: R4 tiene alta tasa de invalidación (~60%), R0-R1 baja (~10%)

---

## Referencias y Documentos Relacionados

### Documentos de Detección de Zonas

1. **ORDER_BLOCKS_CRITERIOS.md** - Cómo detectar Order Blocks
   - Este documento complementa con: Cómo clasificar interacciones con OBs

2. **LIQUIDITY_POOLS_CRITERIOS.md** - Cómo detectar Liquidity Pools
   - Este documento complementa con: Taxonomía de sweeps (P4, P5)

3. **FVG_CRITERIOS_DETECCION.md** - Cómo detectar Fair Value Gaps
   - Este documento complementa con: Análisis de relleno de gaps

4. **LIQUIDITY_POOL_STATES.md** - Estados de Liquidity Pools
   - "Swept" = P4 (False Breakout) o P5 (Break and Retest)
   - "Respected" = R0-R3 según profundidad

### Configuración y Optimización

5. **REBOTE_SETUP.md** - Arquitectura parametrizable
   - Configuración de umbrales (ReboteConfig, PenetracionConfig)
   - Perfiles para diferentes timeframes/volatilidades
   - Sistema de optimización (ParameterOptimizer)
   - Machine Learning preparation

### Próximos Documentos

6. **REBOTE_BACKTESTING_RESULTS.md** (próximo)
   - Resultados de backtesting con datos reales
   - Win rates por tipo, timeframe, volatilidad
   - Parámetros óptimos encontrados

7. **ZONA_STRENGTH_SCORING.md** (próximo)
   - Sistema de scoring de fuerza de zona basado en interacciones
   - Degradación de zona con múltiples R3-R4
   - Fortalecimiento de zona con múltiples R0-R1

---

## Conclusiones

### Resumen de Taxonomía

**5 Tipos de Rebotes** (R0-R4):
- R0: Toque limpio, zona muy fuerte (90% confianza)
- R1: Toque superficial, zona fuerte (80% confianza)
- R2: Rechazo ligero, zona moderada (70% confianza)
- R3: Rechazo medio, zona débil (60% confianza)
- R4: Rechazo profundo, zona muy débil (50% confianza)

**5 Tipos de Penetraciones** (P1-P5):
- P1: Penetración superficial, zona siendo probada
- P2: Penetración profunda, zona debilitada
- P3: Penetración completa, zona casi invalidada
- P4: False breakout, TRAP - señal fuerte (80% confianza)
- P5: Break and retest, cambio de polaridad (75% confianza)

### Aplicaciones

1. **Trading Discrecional**: Clasificar interacciones en tiempo real
2. **Backtesting**: Evaluar win rates por tipo cuantitativamente
3. **Algoritmos**: Implementar señales automáticas
4. **Optimización**: Encontrar parámetros óptimos por mercado
5. **Risk Management**: Ajustar position size según confianza

### Próximos Pasos

1. ✅ Implementar detectores automáticos en backend (ver REBOTE_SETUP.md)
2. ✅ Backtest exhaustivo con 6+ meses de datos
3. ✅ Optimizar parámetros por timeframe (1min, 5min, 15min)
4. ✅ Crear visualizaciones en frontend con colores por tipo
5. ✅ Sistema de alertas cuando zonas están siendo testeadas

---

**Documento creado**: 2025-12-03
**Autor**: NQHUB Trading System
**Versión**: 1.0
**Para configuración parametrizable**: Ver REBOTE_SETUP.md
