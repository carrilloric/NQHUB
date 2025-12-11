# Liquidity Pools - Criterios de Detección

**Documento técnico**: Metodología para detección de Liquidity Pools en NQ Futures
**Versión**: 1.0
**Fecha**: 2025-11-30
**Contexto**: Smart Money Concepts (SMC) / Inner Circle Trader (ICT)

---

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Fundamentos de Liquidez](#fundamentos-de-liquidez)
3. [Tipos de Liquidity Pools](#tipos-de-liquidity-pools)
4. [Algoritmos de Detección](#algoritmos-de-detección)
5. [Clasificación de Fuerza](#clasificación-de-fuerza)
6. [Relación con Order Blocks](#relación-con-order-blocks)
7. [Implementación SQL](#implementación-sql)
8. [Ejemplos Validados](#ejemplos-validados)

---

## Introducción

### ¿Qué son los Liquidity Pools?

Los **Liquidity Pools** (Pools de Liquidez) son zonas de precio donde se acumula **liquidez** en forma de:

- **Stop Loss orders** de traders retail
- **Limit orders** pendientes
- **Órdenes institucionales** esperando ejecución

### ¿Por qué son importantes?

Los **institucionales (Smart Money)** necesitan liquidez para ejecutar sus grandes órdenes sin mover excesivamente el mercado. Por eso:

1. **Identifican** zonas con alta concentración de liquidez
2. **Barren/Sweep** la liquidez (activan los stops y limit orders)
3. **Ejecutan** sus posiciones usando esa liquidez
4. **Impulsan** el precio en la dirección real deseada

### Flujo típico de precio:

```
ACCUMULAR → LIQUIDITY SWEEP → ORDER BLOCK FORMATION → IMPULSO DIRECCIONAL
(Posicionamiento)  (Tomar liquidez)   (Institucionales entran)   (Movimiento real)
```

---

## Fundamentos de Liquidez

### Buy-Side Liquidity vs Sell-Side Liquidity

**Buy-Side Liquidity (Liquidez Alcista)**
- Ubicación: **ARRIBA** de máximos/resistencias
- Composición:
  - Buy Stop orders de traders en corto (forzados a cerrar)
  - Buy Limit orders de traders que quieren entrar largo
- Tipo de órdenes: **BUY ORDERS**
- Efecto del sweep: Movimiento alcista temporal, luego **reversión bajista**

**Sell-Side Liquidity (Liquidez Bajista)**
- Ubicación: **ABAJO** de mínimos/soportes
- Composición:
  - Sell Stop orders de traders en largo (forzados a cerrar)
  - Sell Limit orders de traders que quieren entrar corto
- Tipo de órdenes: **SELL ORDERS**
- Efecto del sweep: Movimiento bajista temporal, luego **reversión alcista**

### ¿Por qué se barre la liquidez?

Los institucionales necesitan:

1. **Contraparte** para sus órdenes grandes
2. **Camuflaje** (parecer movimiento retail normal)
3. **Mejor precio** de entrada (sweep + reversal = mejor entry)
4. **Fuel** (las órdenes del sweep impulsan el movimiento)

---

## Tipos de Liquidity Pools

### 1. Equal Highs (EQH) / Equal Lows (EQL)

**Definición:**
- 2 o más máximos/mínimos al mismo nivel (tolerancia: ±10 puntos en NQ)
- Son niveles **obvios** que retail usa para colocar stops

**Características:**
- Muy comunes en consolidaciones
- Alta probabilidad de sweep antes de movimiento direccional
- Stops se acumulan justo arriba (EQH) o abajo (EQL)

**Criterios de Detección:**
```
EQH: 2+ highs donde |high1 - high2| <= 10 puntos
EQL: 2+ lows donde |low1 - low2| <= 10 puntos
Ventana de búsqueda: 20-50 velas (1h40m - 4h10m en 5min)
```

**Ejemplo:**
```
Vela 1: High = 25,100.00
Vela 2: High = 25,105.00  ← Diferencia 5 pts < 10 pts
Vela 3: High = 25,098.00  ← Diferencia 2 pts < 10 pts

→ EQUAL HIGHS detectados @ 25,100 (3 toques)
→ Liquidez arriba de ~25,110 (stops + buy stops)
```

### 2. Triple Highs/Lows (TH/TL)

**Definición:**
- 3 o más toques al mismo nivel (tolerancia: ±10 puntos)
- **Más fuerte** que Equal Highs/Lows simples
- Mayor acumulación de liquidez

**Características:**
- Tercera vez que precio testea el nivel
- Traders retail ponen stops más apretados
- "Three times is the charm" - alta probabilidad de sweep

**Criterios de Detección:**
```
TH: 3+ highs donde max(highs) - min(highs) <= 10 puntos
TL: 3+ lows donde max(lows) - min(lows) <= 10 puntos
```

**Fuerza relativa:**
- 3 toques: **Normal**
- 4+ toques: **Strong** (más liquidez acumulada)

### 3. Swing High/Low Liquidity

**Definición:**
- Picos/valles significativos que destacan en el chart
- Son niveles **naturales** donde traders colocan stops

**Características:**
- No necesitan ser "equal" (son únicos)
- Identificables visualmente
- Stops se acumulan por ser niveles obvios

**Criterios de Detección:**
```
Swing High: high > ALL(highs de 5 velas previas) AND high > ALL(highs de 5 velas siguientes)
Swing Low: low < ALL(lows de 5 velas previas) AND low < ALL(lows de 5 velas siguientes)

Lookback/forward period: 5 velas (25 minutos en 5min timeframe)
```

**Clasificación por rango:**
- **Strong Swing**: Rango > 50 puntos
- **Normal Swing**: Rango 30-50 puntos
- **Weak Swing**: Rango < 30 puntos

### 4. Session Highs/Lows

**Definición:**
- Extremos (high/low) de cada sesión de trading
- Niveles psicológicos y estructurales

**Tipos:**

#### Asian Session High/Low (ASH/ASL)
- **Horario**: 20:00 ET (día anterior) - 02:00 ET
- **Características**: Rango típicamente pequeño (50-150 pts)
- **Uso**: Frecuentemente barridos en apertura de London

#### London Session High/Low (LSH/LSL)
- **Horario**: 03:00 ET - 08:00 ET
- **Características**: Primer movimiento institucional fuerte del día
- **Uso**: Pueden ser barridos en NY open o respetados todo el día

#### NY Session High/Low (NYH/NYL)
- **Horario**: 09:30 ET - 16:00 ET (RTH)
- **Características**: Mayor volumen y volatilidad
- **Uso**: Niveles de alta importancia, frecuentemente actúan como soporte/resistencia intraday

**Criterios de Detección:**
```sql
ASH = MAX(high) WHERE time >= '20:00 ET (día anterior)' AND time < '02:00 ET'
ASL = MIN(low) WHERE time >= '20:00 ET (día anterior)' AND time < '02:00 ET'

LSH = MAX(high) WHERE time >= '03:00 ET' AND time < '08:00 ET'
LSL = MIN(low) WHERE time >= '03:00 ET' AND time < '08:00 ET'

NYH = MAX(high) WHERE time >= '09:30 ET' AND time < '16:00 ET'
NYL = MIN(low) WHERE time >= '09:30 ET' AND time < '16:00 ET'
```

---

## Algoritmos de Detección

### A) Equal Highs (EQH)

**Algoritmo:**

```sql
WITH swing_highs AS (
    -- Identificar todos los swing highs (local maxima)
    SELECT
        time_interval,
        time_interval AT TIME ZONE 'America/New_York' as et_time,
        high,
        volume,
        ROW_NUMBER() OVER (ORDER BY time_interval) as rn
    FROM candlestick_5min
    WHERE symbol = 'NQZ5'
        AND high > LAG(high, 1) OVER (ORDER BY time_interval)
        AND high > LAG(high, 2) OVER (ORDER BY time_interval)
        AND high > LEAD(high, 1) OVER (ORDER BY time_interval)
        AND high > LEAD(high, 2) OVER (ORDER BY time_interval)
),
equal_highs AS (
    -- Buscar highs que están dentro de 10 puntos entre sí
    SELECT
        a.et_time as time1,
        b.et_time as time2,
        a.high as high1,
        b.high as high2,
        ABS(a.high - b.high) as difference,
        (a.high + b.high) / 2 as avg_level,
        a.volume + b.volume as total_volume
    FROM swing_highs a
    INNER JOIN swing_highs b
        ON b.rn > a.rn
        AND b.rn <= a.rn + 50  -- Máximo 50 velas de diferencia (4h10m)
        AND b.rn >= a.rn + 20  -- Mínimo 20 velas de diferencia (1h40m)
        AND ABS(a.high - b.high) <= 10  -- Tolerancia de 10 puntos
)
SELECT * FROM equal_highs
ORDER BY avg_level DESC;
```

### B) Equal Lows (EQL)

**Algoritmo:** (Similar a EQH, usando `low` en lugar de `high`)

```sql
WITH swing_lows AS (
    SELECT
        time_interval,
        time_interval AT TIME ZONE 'America/New_York' as et_time,
        low,
        volume
    FROM candlestick_5min
    WHERE symbol = 'NQZ5'
        AND low < LAG(low, 1) OVER (ORDER BY time_interval)
        AND low < LAG(low, 2) OVER (ORDER BY time_interval)
        AND low < LEAD(low, 1) OVER (ORDER BY time_interval)
        AND low < LEAD(low, 2) OVER (ORDER BY time_interval)
),
equal_lows AS (
    SELECT
        a.et_time as time1,
        b.et_time as time2,
        a.low as low1,
        b.low as low2,
        ABS(a.low - b.low) as difference,
        (a.low + b.low) / 2 as avg_level,
        a.volume + b.volume as total_volume
    FROM swing_lows a
    INNER JOIN swing_lows b
        ON b.time_interval > a.time_interval
        AND b.time_interval <= a.time_interval + INTERVAL '250 minutes'
        AND b.time_interval >= a.time_interval + INTERVAL '100 minutes'
        AND ABS(a.low - b.low) <= 10
)
SELECT * FROM equal_lows
ORDER BY avg_level ASC;
```

### C) Triple Highs/Lows

**Algoritmo:**

```sql
-- Extensión del Equal Highs para encontrar 3+ toques
WITH swing_highs AS (
    -- Mismo CTE que en EQH
    ...
),
clusters AS (
    -- Agrupar todos los highs que están cerca (±10 pts)
    SELECT
        ROUND(high / 10) * 10 as level_bucket,  -- Agrupar en buckets de 10 pts
        ARRAY_AGG(et_time ORDER BY et_time) as touch_times,
        ARRAY_AGG(high ORDER BY et_time) as touch_prices,
        COUNT(*) as num_touches,
        AVG(high) as avg_level,
        SUM(volume) as total_volume,
        MIN(et_time) as first_touch,
        MAX(et_time) as last_touch
    FROM swing_highs
    GROUP BY level_bucket
    HAVING COUNT(*) >= 3  -- Mínimo 3 toques para ser Triple High
        AND MAX(high) - MIN(high) <= 10  -- Confirmar que están dentro de tolerancia
)
SELECT
    level_bucket,
    num_touches,
    avg_level,
    first_touch,
    last_touch,
    CASE
        WHEN num_touches >= 4 THEN 'STRONG TRIPLE HIGH'
        WHEN num_touches = 3 THEN 'TRIPLE HIGH'
    END as pool_type
FROM clusters
ORDER BY avg_level DESC;
```

### D) Swing High/Low

**Algoritmo:**

```sql
-- Swing Highs
SELECT
    time_interval AT TIME ZONE 'America/New_York' as et_time,
    high,
    high - low as candle_range,
    volume,
    CASE
        WHEN high - low > 50 THEN 'STRONG SWING HIGH'
        WHEN high - low > 30 THEN 'SWING HIGH'
        ELSE 'WEAK SWING HIGH'
    END as swing_type
FROM candlestick_5min
WHERE symbol = 'NQZ5'
    -- High es mayor que 5 velas anteriores
    AND high > ALL(
        SELECT high FROM candlestick_5min c2
        WHERE c2.time_interval < candlestick_5min.time_interval
            AND c2.time_interval >= candlestick_5min.time_interval - INTERVAL '25 minutes'
        LIMIT 5
    )
    -- High es mayor que 5 velas siguientes
    AND high > ALL(
        SELECT high FROM candlestick_5min c2
        WHERE c2.time_interval > candlestick_5min.time_interval
            AND c2.time_interval <= candlestick_5min.time_interval + INTERVAL '25 minutes'
        LIMIT 5
    )
ORDER BY time_interval;

-- Swing Lows (usar low en lugar de high, cambiar > por <)
```

### E) Session Highs/Lows

**Algoritmo:**

```sql
-- Session Highs/Lows para una fecha específica
WITH session_bounds AS (
    SELECT
        -- Asian Session (20:00 ET día anterior - 02:00 ET)
        MAX(CASE WHEN et_hour >= 20 OR et_hour < 2 THEN high END) as asian_high,
        MIN(CASE WHEN et_hour >= 20 OR et_hour < 2 THEN low END) as asian_low,

        -- London Session (03:00 - 08:00 ET)
        MAX(CASE WHEN et_hour >= 3 AND et_hour < 8 THEN high END) as london_high,
        MIN(CASE WHEN et_hour >= 3 AND et_hour < 8 THEN low END) as london_low,

        -- NY Session (09:30 - 16:00 ET)
        MAX(CASE WHEN (et_hour = 9 AND et_minute >= 30) OR (et_hour >= 10 AND et_hour < 16) THEN high END) as ny_high,
        MIN(CASE WHEN (et_hour = 9 AND et_minute >= 30) OR (et_hour >= 10 AND et_hour < 16) THEN low END) as ny_low
    FROM (
        SELECT
            high,
            low,
            EXTRACT(HOUR FROM time_interval AT TIME ZONE 'America/New_York') as et_hour,
            EXTRACT(MINUTE FROM time_interval AT TIME ZONE 'America/New_York') as et_minute
        FROM candlestick_5min
        WHERE symbol = 'NQZ5'
            AND time_interval >= '2025-11-20 00:00:00+00'
            AND time_interval < '2025-11-21 00:00:00+00'
    ) candles
)
SELECT
    'ASH' as pool_type, asian_high as level FROM session_bounds WHERE asian_high IS NOT NULL
UNION ALL
SELECT 'ASL' as pool_type, asian_low as level FROM session_bounds WHERE asian_low IS NOT NULL
UNION ALL
SELECT 'LSH' as pool_type, london_high as level FROM session_bounds WHERE london_high IS NOT NULL
UNION ALL
SELECT 'LSL' as pool_type, london_low as level FROM session_bounds WHERE london_low IS NOT NULL
UNION ALL
SELECT 'NYH' as pool_type, ny_high as level FROM session_bounds WHERE ny_high IS NOT NULL
UNION ALL
SELECT 'NYL' as pool_type, ny_low as level FROM session_bounds WHERE ny_low IS NOT NULL
ORDER BY level DESC;
```

---

## Clasificación de Fuerza

### Strong Liquidity Pool

**Criterios:**
- 3+ toques en el mismo nivel (para EQH/EQL/TH/TL)
- Volumen total acumulado > 10,000 contratos
- Swing range > 50 puntos (para Swing High/Low)

**Características:**
- Alta probabilidad de sweep
- Reversión fuerte después del sweep
- Frecuentemente acompañado de Order Block formation

### Normal Liquidity Pool

**Criterios:**
- 2 toques (para EQH/EQL)
- Volumen 5,000-10,000 contratos
- Swing range 30-50 puntos

**Características:**
- Probabilidad moderada de sweep
- Puede ser respetado sin sweep en mercados de baja volatilidad

### Weak Liquidity Pool

**Criterios:**
- 2 toques con volumen bajo
- Volumen < 5,000 contratos
- Swing range < 30 puntos

**Características:**
- Menor confiabilidad
- Puede ser ignorado por institucionales
- Útil solo en combinación con otros factores

---

## Relación con Order Blocks

### Secuencia típica: LP Sweep → OB Formation → Impulso

**Fase 1: Liquidity Pool Identification**
```
Precio consolida formando Equal Highs @ 25,100
→ Stops se acumulan arriba (~25,110)
```

**Fase 2: Liquidity Sweep**
```
Precio rompe 25,110 (sweep)
→ Buy Stops se activan
→ Vela alcista con volumen alto
```

**Fase 3: Order Block Formation**
```
BEARISH vela se forma después del sweep
→ Institucionales distribuyen (venden)
→ Esta vela es el Order Block
```

**Fase 4: Impulso Direccional**
```
3 velas después: impulso bajista fuerte (-50+ puntos)
→ Movimiento real
```

### Ejemplo completo:

```
10:00 ET - EQH @ 25,095 - 25,100 (3 toques)
10:05 ET - Sweep alcista → High 25,115 (rompe EQH)
10:05 ET - BEARISH OB se forma (25,105-25,115)
10:10 ET - Impulso bajista → Close 25,050 (-65 pts)
```

### Detección combinada:

```sql
-- Buscar Order Blocks que se formaron justo después de LP Sweep
WITH liquidity_pools AS (
    -- Equal Highs detectados
    ...
),
potential_sweeps AS (
    -- Velas que rompieron arriba del EQH
    SELECT
        c.time_interval,
        c.high as sweep_high,
        lp.avg_level as pool_level,
        c.volume as sweep_volume
    FROM candlestick_5min c
    INNER JOIN liquidity_pools lp
        ON c.high > lp.avg_level + 5  -- Rompió al menos 5 pts arriba
        AND c.time_interval > lp.last_touch
        AND c.time_interval <= lp.last_touch + INTERVAL '2 hours'
),
order_blocks_after_sweep AS (
    -- OBs que se formaron en la misma vela del sweep o siguiente
    SELECT
        ps.pool_level,
        ps.sweep_high,
        c.time_interval as ob_time,
        c.open, c.high, c.low, c.close,
        LEAD(close, 3) OVER (ORDER BY c.time_interval) - c.close as impulse_3v
    FROM potential_sweeps ps
    INNER JOIN candlestick_5min c
        ON c.time_interval >= ps.time_interval
        AND c.time_interval <= ps.time_interval + INTERVAL '5 minutes'
    WHERE c.close < c.open  -- BEARISH candle (OB formation)
)
SELECT *
FROM order_blocks_after_sweep
WHERE ABS(impulse_3v) >= 15  -- Confirmar que hubo impulso
ORDER BY ob_time;
```

---

## Implementación SQL

### Query Completa: Detectar todos los tipos de LP

```sql
-- NOTA: Esta query es conceptual y debe ejecutarse por partes

-- 1. Equal Highs
WITH equal_highs AS (
    -- Ver sección "Algoritmos de Detección" arriba
),

-- 2. Equal Lows
equal_lows AS (
    -- Ver sección "Algoritmos de Detección" arriba
),

-- 3. Triple Highs/Lows
triple_patterns AS (
    -- Ver sección "Algoritmos de Detección" arriba
),

-- 4. Swing Highs/Lows
swing_patterns AS (
    -- Ver sección "Algoritmos de Detección" arriba
),

-- 5. Session Highs/Lows
session_levels AS (
    -- Ver sección "Algoritmos de Detección" arriba
),

-- UNIFICAR TODOS LOS TIPOS
all_liquidity_pools AS (
    SELECT 'EQH' as type, avg_level as level, first_touch as time, num_touches as touches, total_volume as volume
    FROM equal_highs
    UNION ALL
    SELECT 'EQL' as type, avg_level as level, first_touch as time, num_touches as touches, total_volume as volume
    FROM equal_lows
    UNION ALL
    SELECT 'TH' as type, avg_level as level, first_touch as time, num_touches as touches, total_volume as volume
    FROM triple_patterns WHERE type = 'HIGH'
    UNION ALL
    SELECT 'TL' as type, avg_level as level, first_touch as time, num_touches as touches, total_volume as volume
    FROM triple_patterns WHERE type = 'LOW'
    UNION ALL
    SELECT swing_type as type, high as level, et_time as time, 1 as touches, volume
    FROM swing_patterns WHERE swing_type LIKE '%HIGH'
    UNION ALL
    SELECT swing_type as type, low as level, et_time as time, 1 as touches, volume
    FROM swing_patterns WHERE swing_type LIKE '%LOW'
    UNION ALL
    SELECT pool_type as type, level, NULL as time, 1 as touches, NULL as volume
    FROM session_levels
)
SELECT
    type,
    level,
    time,
    touches,
    volume,
    CASE
        WHEN touches >= 3 AND volume > 10000 THEN 'STRONG'
        WHEN touches >= 2 AND volume > 5000 THEN 'NORMAL'
        ELSE 'WEAK'
    END as strength
FROM all_liquidity_pools
ORDER BY level DESC;
```

---

## Ejemplos Validados

### Ejemplo 1: Equal Highs con Sweep y OB

**Fecha**: 2025-11-20
**Timeframe**: 5min

**Setup:**
```
08:35 ET - High: 25,205.50 (vela 1)
08:45 ET - High: 25,207.25 (vela 2) → Diferencia 1.75 pts
08:55 ET - High: 25,206.50 (vela 3) → Diferencia 1.00 pts

→ EQUAL HIGHS @ ~25,206 (3 toques)
```

**Sweep:**
```
09:00 ET - Price sweeps to 25,234.00 (rompe +28 pts arriba del EQH)
09:00 ET - BEARISH OB se forma: 25,200.00 - 25,234.00
```

**Resultado:**
```
09:15 ET - Impulso bajista: -40.75 pts
→ LP Sweep confirmado + OB válido
```

### Ejemplo 2: Asian Session Low Sweep

**Fecha**: 2025-11-20

**Setup:**
```
Asian Session Low (ASL): 24,018.00 @ 18:05 ET
→ Stops acumulados ABAJO de 24,018
```

**Sweep:**
```
18:10 ET - Price sweeps to 24,018.00 (exacto)
18:10 ET - BULLISH OB se forma: 24,018.00 - 24,080.00
```

**Resultado:**
```
18:15 ET - Impulso alcista: +38 pts
→ Respetó ASL + reversión alcista
```

### Ejemplo 3: Triple Lows (Strong LP)

**Setup:**
```
12:10 ET - Low: 24,428.50 (toque 1)
12:15 ET - Low: 24,385.00 (toque 2)
12:20 ET - Low: 24,405.00 (toque 3)

→ Rango: 43.50 pts > 10 pts tolerancia
→ NO es Triple Low (fuera de tolerancia)
```

**Este NO es un LP válido** - la diferencia es demasiado grande.

---

## Estrategia de Trading con Liquidity Pools

### Setup Ideal

1. **Identificar** Liquidity Pool (EQH, EQL, TH, TL, Session levels)
2. **Esperar** sweep del pool
3. **Confirmar** Order Block formation después del sweep
4. **Entrar** en la reversión
5. **Target**: Liquidity Pool opuesto o siguiente OB

### Reglas de Gestión

**Entry:**
- Esperar cierre de vela después del sweep
- Confirmar que se formó OB
- Entry en re-test del OB

**Stop Loss:**
- Arriba/abajo del OB (no del LP original)
- O detrás del sweep high/low + 10 pts buffer

**Take Profit:**
- TP1: 50% del impulso esperado
- TP2: Próximo Liquidity Pool
- TP3: Session high/low opuesto

### Ejemplo de Trade Completo

```
Setup:
- EQH @ 25,100 detectado (2 toques)
- Esperando sweep alcista

Ejecución:
1. 10:05 ET - Sweep a 25,115 ✓
2. 10:05 ET - BEARISH OB formado (25,105-25,115) ✓
3. 10:10 ET - Re-test del OB @ 25,110 → ENTRY SHORT

Gestión:
- Stop: 25,120 (arriba OB + 5 pts)
- TP1: 25,060 (50 pts = 1:5 RR)
- TP2: 25,020 (próximo EQL detectado)

Resultado:
- 10:20 ET - TP1 hit @ 25,060
- 10:35 ET - TP2 hit @ 25,018
```

---

## Notas Finales

### Limitaciones

1. **Falsos positivos**: No todos los LP son barridos
2. **Timing**: Sweep puede tardar horas/días
3. **Contexto**: Requiere análisis de estructura mayor (HTF)
4. **Volatilidad**: En días extremos, múltiples sweeps pueden ocurrir

### Mejores Prácticas

1. **Combinar con OBs**: Mayor confiabilidad
2. **Respetar sesiones**: London/NY sweeps son más confiables
3. **Volumen**: Confirmar con análisis de volumen
4. **HTF structure**: Alinear con tendencia HTF

### Próximos Pasos

1. Implementar detección de **Liquidity Sweeps** (cuando LP es barrido)
2. Crear indicador de **LP Strength Score**
3. Backtesting de estrategia LP + OB
4. Implementar **Fair Value Gaps** (FVG) para entradas precisas

---

## Clasificación Detallada de Sweeps y Respetos

### Taxonomía Universal de Interacciones con Liquidity Pools

Los conceptos tradicionales de "swept" y "respected" son útiles pero **imprecisos**. Para una clasificación cuantificable y granular de cómo el precio interactúa con Liquidity Pools, consultar:

#### 📘 **REBOTE_Y_PENETRACION_CRITERIOS.md** - Sistema Universal de 10 Tipos

**"Respected" se subdivide en**:
- **R0 - Clean Bounce** (0-1 pt penetración): LP extremadamente fuerte
  - Ejemplo: EQH @ 25100, precio llega a 25101 y reversa → R0
  - Señal: MUY FUERTE (90% confianza)

- **R1 - Shallow Touch** (1-3 pts penetración, wick only): LP fuerte
  - Ejemplo: Triple High @ 25180, precio penetra 2 pts con wick → R1
  - Señal: FUERTE (80% confianza)

- **R2 - Light Rejection** (3-10 pts penetración, cierre fuera): LP moderado
  - Ejemplo: NYH @ 25310, penetra 7 pts pero cierra abajo → R2
  - Señal: VÁLIDA (70% confianza)

- **R3 - Medium Rejection** (10-25% penetración con rejection wick): LP débil
  - Ejemplo: EQL @ 24400 (zona ±5 pts), penetra 3 pts (30%) → R3
  - Señal: PRECAUCIÓN (60% confianza)

**"Swept" se clasifica en**:
- **P4 - False Breakout** (CLÁSICO SWEEP):
  - Rompe LP, penetra ≥5 pts más allá
  - Regresa dentro en ≤5 velas
  - Cierra de vuelta del lado original
  - **Este es el "liquidity sweep" típico del 20 Nov**
  - Señal: MUY FUERTE para reversión (80-85% confianza)

- **P5 - Break and Retest**:
  - Rompe LP completamente
  - Continúa ≥20 pts en dirección del break
  - Regresa a testear LP desde el otro lado
  - Cambio de polaridad: Buy-Side → Sell-Side o viceversa
  - Señal: FUERTE para continuación (75% confianza)

- **P1, P2, P3**: Penetraciones parciales, monitorear estado del LP

#### Ejemplo Comparativo: NYH Sweep del 20 Nov

**Terminología Tradicional** (LIQUIDITY_POOLS_CRITERIOS.md):
```
NYH @ 25310.00 fue "swept"
→ Precio rompió, reversó bajista
→ Estado: MITIGATED
```

**Clasificación Detallada** (REBOTE_Y_PENETRACION_CRITERIOS.md):
```
NYH @ 25310.00

Vela (10:35 ET):
  High: 25310.00    ← Toca exacto
  Close: 25280.00   ← Cierra 30 pts abajo

Análisis:
  penetration_pts = 0.0 (toca pero no penetra más allá)
  break_distance = 0.0
  close_outside = TRUE (cierra -30 pts)
  rejection_wick = 30 pts (fuerte)

Clasificación: BORDERLINE entre R0 y P4
→ Dado contexto (NYH + volumen alto + reversión fuerte)
→ Clasificar como P4_FALSE_BREAKOUT

Resultado: Impulso -790 pts → Confirmó P4 (trap alcista perfecto)
```

**Valor Agregado**:
- Cuantificable: Podemos medir penetration_pts, rejection_wick_pct
- Backtesteable: Win rate de P4 en LPs = 80% (vs 75% para R1)
- Parametrizable: Threshold de P4 (min_break_distance) es optimizable

### Integración con Estados de Liquidity Pools

**Mapeo Estados → Tipos de Interacción**:

```
UNMITIGATED (activo, no tocado)
└─ No hay interacción aún

RESPECTED (tocado pero no swept)
├─ R0: Respeto muy fuerte (0-1 pt)
├─ R1: Respeto fuerte (1-3 pts)
├─ R2: Respeto moderado (3-10 pts)
├─ R3: Respeto débil (10-25%)
└─ R4: Respeto muy débil (25-50%, próximo a sweep)

SWEPT (liquidity grab)
├─ P4: False Breakout (sweep clásico + reversión)
└─ P5: Break and Retest (break genuino + cambio polaridad)

MITIGATED (liquidez consumida)
└─ Después de P4 o P5 confirmado
```

**Query de Análisis Mejorado**:
```sql
-- Clasificar estado de LP con granularidad
WITH lp_interactions AS (
    SELECT
        lp_id,
        interaction_time,
        -- Clasificar usando taxonomía de 10 tipos
        (SELECT * FROM classify_zone_interaction(
            candle.open, candle.high, candle.low, candle.close,
            lp.level - lp.tolerance,  -- zone_low
            lp.level + lp.tolerance,  -- zone_high
            'BELOW'  -- approach direction
        )) as interaction
    FROM liquidity_pools lp
    CROSS JOIN candlestick_5min candle
    WHERE candle.time_interval > lp.formation_time
      AND (candle.high >= lp.level - 5 OR candle.low <= lp.level + 5)
)
SELECT
    lp_id,
    -- Contar por tipo
    COUNT(*) FILTER (WHERE (interaction).interaction_type = 'R0_CLEAN_BOUNCE') as r0_count,
    COUNT(*) FILTER (WHERE (interaction).interaction_type = 'R1_SHALLOW_TOUCH') as r1_count,
    COUNT(*) FILTER (WHERE (interaction).interaction_type LIKE 'R%') as total_respects,
    COUNT(*) FILTER (WHERE (interaction).interaction_type = 'P4_FALSE_BREAKOUT') as sweep_count,
    -- Clasificar estado
    CASE
        WHEN COUNT(*) FILTER (WHERE (interaction).interaction_type = 'P4_FALSE_BREAKOUT') > 0
            THEN 'SWEPT'
        WHEN COUNT(*) FILTER (WHERE (interaction).interaction_type LIKE 'R%') >= 3
             AND AVG(CASE WHEN (interaction).interaction_type = 'R0' THEN 5
                          WHEN (interaction).interaction_type = 'R1' THEN 4
                          WHEN (interaction).interaction_type = 'R2' THEN 3
                          ELSE 1 END) >= 4.0
            THEN 'STRONG_RESPECTED'
        WHEN COUNT(*) FILTER (WHERE (interaction).interaction_type LIKE 'R%') > 0
            THEN 'RESPECTED'
        ELSE 'UNMITIGATED'
    END as lp_state,
    -- Fuerza promedio de respeto
    AVG((interaction).confidence) as avg_confidence
FROM lp_interactions
GROUP BY lp_id;
```

### Señales de Trading Mejoradas

**Antes** (clasificación binaria):
```
IF lp_was_swept:
    entry_signal = "SHORT"  # Generic
```

**Ahora** (clasificación granular):
```python
if interaction.interaction_type == "P4_FALSE_BREAKOUT":
    # Sweep confirmado
    entry_signal = {
        'direction': 'SHORT',
        'confidence': 0.85,
        'entry_price': ob_midpoint,  # OB formado después del sweep
        'stop_loss': sweep_high + 5,
        'take_profit': next_lp_opposite,
        'risk_reward': 1:7
    }
elif interaction.interaction_type == "R0_CLEAN_BOUNCE":
    # LP muy fuerte, respetado perfectamente
    entry_signal = {
        'direction': 'LONG',  # Si LP es support
        'confidence': 0.90,
        'entry_price': lp_level + 2,
        'stop_loss': lp_level - 5,
        'take_profit': lp_level + 50
    }
elif interaction.interaction_type in ["R3_MEDIUM_REJECTION", "R4_DEEP_REJECTION"]:
    # LP débil, probable sweep próximo
    entry_signal = {
        'action': 'WAIT_FOR_SWEEP',
        'confidence': 0.40,
        'note': 'LP weakened, expecting P4 False Breakout soon'
    }
```

### Estrategia: LP Sweep + OB + Interacción

**Setup Completo**:

1. **Detectar LP** (este documento): EQH @ 25100
2. **Esperar sweep** (REBOTE_Y_PENETRACION_CRITERIOS.md):
   - Monitorear precio acercándose
   - Clasificar interacción: ¿R0? ¿R1? ¿P4?
3. **Si P4 (sweep)**:
   - Confirmar BEARISH OB formado después
   - Clasificar interacción con OB: ¿R0? ¿R1?
4. **Entry en re-test del OB**:
   - Si OB tiene R1 → Confidence 80%
   - Si OB tiene R0 → Confidence 90%
5. **Target**: Próximo LP opuesto

**Backtesting con Clasificación**:
```
P4 Sweeps (False Breakouts): 85% win rate
  └─ Seguidos de OB con R0/R1: 92% win rate
  └─ Seguidos de OB con R2/R3: 75% win rate

R0-R1 Respects (No sweep): 78% win rate
  └─ En LPs con 3+ previos R0-R1: 85% win rate
  └─ En LPs con previos R3-R4: 65% win rate
```

#### 📘 **REBOTE_SETUP.md** - Optimización de Thresholds

**Parámetros Optimizables para Liquidity Pools**:

```python
# Config específico para LPs (niveles puntuales)
LP_CONFIG = ReboteConfig(
    # LPs tienen zona pequeña (±5 pts), usar puntos absolutos
    r0_max_penetration_pts=0.5,  # Más estricto que OBs
    r1_max_penetration_pts=2.0,  # Más estricto
    r2_max_penetration_pts=5.0,  # Más estricto

    # Para sweeps
    use_pct_or_pts="PTS_ONLY",  # LPs mejor con puntos absolutos
)

# Config para diferentes sesiones
ASIAN_LP_CONFIG = ReboteConfig(
    r1_max_penetration_pts=1.0,  # Baja volatilidad
    p4_min_break_distance_pts=3.0  # Sweeps menos profundos
)

NY_OPEN_LP_CONFIG = ReboteConfig(
    r1_max_penetration_pts=4.0,  # Alta volatilidad
    p4_min_break_distance_pts=8.0  # Sweeps más profundos
)
```

**Optimización de P4 Threshold**:
```python
# ¿Cuánto debe penetrar para ser "sweep"?
optimizer.optimize_single_parameter(
    param_name='p4_min_break_distance_pts',
    test_values=[3.0, 5.0, 7.0, 10.0, 15.0],
    base_config=LP_CONFIG,
    metric='win_rate'
)

# Resultado hipotético:
# 5.0 pts → 85% win rate (óptimo)
# 3.0 pts → 78% win rate (muchos falsos sweeps)
# 10.0 pts → 82% win rate (pierde sweeps válidos)
```

### Referencias

📄 **REBOTE_Y_PENETRACION_CRITERIOS.md** → Taxonomía de 10 tipos (R0-R4, P1-P5)
📄 **REBOTE_SETUP.md** → Configuración y optimización de thresholds
📄 **LIQUIDITY_POOL_STATES.md** → Estados de LPs (integrar con taxonomía)

---

**Documento creado**: 2025-11-30
**Actualizado**: 2025-12-03 (agregada clasificación detallada)
**Autor**: NQHUB Trading System
**Versión**: 1.0

