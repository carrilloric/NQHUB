# Estados de Liquidity Pools - Clasificación y Detección

**Documento técnico**: Ciclo de vida de un Liquidity Pool
**Versión**: 1.0
**Fecha**: 2025-11-30

---

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Estados de Liquidity Pools](#estados-de-liquidity-pools)
3. [Swept Liquidity Pools](#swept-liquidity-pools)
4. [Detección Algorítmica](#detección-algorítmica)
5. [Ejemplos del 20 de Noviembre](#ejemplos-del-20-de-noviembre)

---

## Introducción

Un **Liquidity Pool** no es estático - tiene un ciclo de vida:

```
FORMACIÓN → ACTIVE → SWEPT/RESPECTED → MITIGATED/ACTIVE
```

Entender en qué estado está un LP es **crítico** para trading.

---

## Estados de Liquidity Pools

### 1. **Unmitigated LP** (Active/Pendiente)

**Definición:**
- LP que ha sido formado pero AÚN NO ha sido tocado por el precio
- Liquidez está "disponible" esperando ser tomada

**Características:**
- Precio no ha regresado al nivel
- Stops/órdenes siguen acumuladas
- Alta probabilidad de ser objetivo futuro

**Ejemplo:**
```
08:00 ET - EQH formado @ 25,180
08:05 ET - Precio baja a 25,100
→ EQH sigue UNMITIGATED (precio no ha regresado)
→ Estado: ACTIVE, esperando interacción
```

**En trading:**
- ✅ Válido para usar como target
- ✅ Esperar que precio regrese
- ⚠️ Puede tardar horas o días

---

### 2. **Swept Liquidity Pool** (Liquidity Grab/Mitigated)

**Definición:**
- LP que fue tocado/penetrado Y precio reversó
- Liquidez fue "tomada" (stops activados)
- Generalmente seguido por Order Block formation

**Criterios para considerar "swept":**
```
1. Precio rompe el LP nivel ±5-10 puntos
2. Permanece arriba/abajo brevemente (1-3 velas)
3. Reversa en dirección opuesta
4. Generalmente forma Order Block
```

**También llamado:**
- **Liquidity Grab**: Institucionales "agarran" la liquidez
- **Stop Hunt**: Caza de stops
- **Mitigated LP**: LP "mitigado" (liquidez consumida)
- **Liquidity Sweep**: Barrido de liquidez

**Ejemplo (el MÁS IMPORTANTE del 20 Nov):**
```
NYH @ 25,310.00 (Session High - Buy-Side Liquidity)

10:30 ET - Precio llega a 25,300 (cerca del NYH)
10:35 ET - Precio rompe 25,310 → Llega a 25,310.00 (SWEEP) 🔥
10:35 ET - BEARISH OB se forma (25,258.75-25,310.00) 📦
10:40 ET - Impulso bajista -134.50 pts
12:00 ET - Precio en 24,520 (-790 pts desde el sweep)

→ NYH fue SWEPT
→ Estado: MITIGATED (liquidez consumida)
→ Ya NO es válido como target alcista
```

**En trading:**
- ✅ MEJOR setup: Swept LP + OB = Alta probabilidad
- ✅ Entry en re-test del OB (NO del LP)
- ❌ NO esperar que LP sea respetado (ya fue usado)

**Señales visuales en ATAS:**
- Wick que penetra el nivel
- Vela con high/low arriba/abajo del LP
- Volumen alto en la vela del sweep
- Reversión inmediata (1-2 velas)

---

### 3. **Respected Liquidity Pool** (Defended/Still Active)

**Definición:**
- LP tocado múltiples veces pero NUNCA penetrado
- Precio reversa cada vez que toca el nivel
- Liquidez "respetada" (protegida)

**Criterios:**
```
1. Precio toca el LP (±2-3 puntos)
2. NO penetra significativamente
3. Reversa inmediatamente
4. Puede repetirse 2-5+ veces
```

**Ejemplo:**
```
Triple Low @ 24,400 formado (Sell-Side Liquidity)

12:20 ET - Precio baja a 24,405 (toca -1)
12:20 ET - Reversa alcista +20 pts

13:10 ET - Precio baja a 24,402 (toca -2)
13:10 ET - Reversa alcista +15 pts

14:00 ET - Precio baja a 24,398 (toca -3)
14:00 ET - Reversa alcista +25 pts

→ Triple Low RESPECTED 3 veces
→ Estado: STILL ACTIVE (sigue válido)
→ Institucionales "defienden" el nivel
```

**En trading:**
- ✅ Nivel sigue siendo válido
- ✅ Puede ser usado como support/resistance
- ⚠️ Eventualmente SERÁ swept (3rd/4th touch común)

**Diferencia con Swept:**
- **Respected**: Toca pero NO penetra, reversa inmediata
- **Swept**: PENETRA +5-10 pts, luego reversa

---

### 4. **Temporary/Intraday Liquidity Pool**

**Definición:**
- LP formado y barrido en la MISMA sesión
- Corta duración (minutos a 2-3 horas)
- Típico en alta volatilidad

**Características:**
- Formación rápida (2 toques en <1 hora)
- Sweep rápido (dentro de 2-3 horas)
- No es válido para días siguientes

**Ejemplo:**
```
ASIAN SESSION:
23:00 ET - Equal High formado @ 25,190 (toque 1)
00:30 ET - High toca 25,190 (toque 2)
→ EQH formado

LONDON OPEN:
03:15 ET - Precio sweeps 25,195 (barrido)
03:20 ET - BEARISH OB formado
03:30 ET - Precio en 25,150

→ Temporary LP (vida: 4.5 horas)
→ Formado en Asian, swept en London
→ Típico patrón intraday
```

**En trading:**
- ✅ Válido para scalping/intraday
- ❌ NO usar para swing trading
- ⚠️ Menor confiabilidad que Session LPs

---

## Swept Liquidity Pools

### Anatomía de un Liquidity Sweep

```
FASE 1: LP Formation
  ├─ Equal/Triple Highs formados
  ├─ Stops acumulados arriba
  └─ Retail coloca órdenes

FASE 2: Price Approaches LP
  ├─ Precio sube hacia el LP
  ├─ Institucionales observan
  └─ Esperan momento óptimo

FASE 3: SWEEP (Liquidity Grab) 🔥
  ├─ Precio rompe LP +5-10 pts
  ├─ Buy Stops se activan (fuel)
  ├─ Institucionales usan esa liquidez
  └─ Duración: 1-3 velas (5-15 min)

FASE 4: Order Block Formation 📦
  ├─ BEARISH candle se forma
  ├─ Institucionales distribuyen
  └─ OB marca "last supply before drop"

FASE 5: Impulso Direccional
  ├─ Precio cae fuertemente
  ├─ Institucionales en posición
  └─ Retail atrapado (sus stops fueron hit)
```

### Por qué los institucionales hacen sweeps

1. **Necesitan liquidez**
   - Órdenes grandes requieren contraparte
   - Stops de retail proveen esa liquidez

2. **Mejor precio**
   - Sweep les da entry más favorable
   - "Compran bajo, venden alto" (al revés que retail)

3. **Camuflaje**
   - Sweep parece "breakout alcista"
   - Retail entra largo (institucionales cortan)

4. **Fuel para movimiento**
   - Stops activados impulsan el precio
   - Institucionales usan ese momentum

---

## Detección Algorítmica

### Algoritmo: Detectar Swept LPs

```sql
-- Detectar Equal Highs que fueron swept
WITH equal_highs AS (
    -- Detectar EQH (ver LIQUIDITY_POOLS_CRITERIOS.md)
    ...
),
potential_sweeps AS (
    SELECT
        lp.avg_level as lp_level,
        lp.last_touch as lp_time,
        c.time_interval as sweep_time,
        c.high as sweep_high,
        c.close as sweep_close,
        c.volume as sweep_volume
    FROM equal_highs lp
    INNER JOIN candlestick_5min c
        ON c.symbol = 'NQZ5'
        -- Vela DESPUÉS del último toque del LP
        AND c.time_interval > lp.last_touch
        -- Máximo 2 horas después
        AND c.time_interval <= lp.last_touch + INTERVAL '2 hours'
        -- PENETRÓ el LP al menos 5 puntos
        AND c.high >= lp.avg_level + 5
),
sweeps_with_reversal AS (
    SELECT
        ps.*,
        -- Buscar reversión (velas siguientes van ABAJO)
        LEAD(close, 1) OVER (ORDER BY sweep_time) as next1_close,
        LEAD(close, 3) OVER (ORDER BY sweep_time) as next3_close,
        -- Confirmar que hubo reversión
        LEAD(close, 3) OVER (ORDER BY sweep_time) - ps.sweep_close as reversal_magnitude
    FROM potential_sweeps ps
)
SELECT
    lp_level,
    TO_CHAR(lp_time AT TIME ZONE 'America/New_York', 'HH24:MI') as lp_formed,
    TO_CHAR(sweep_time AT TIME ZONE 'America/New_York', 'HH24:MI') as swept_at,
    sweep_high,
    sweep_volume,
    reversal_magnitude,
    CASE
        WHEN reversal_magnitude < -30 THEN 'STRONG SWEEP + REVERSAL'
        WHEN reversal_magnitude < -15 THEN 'SWEEP + REVERSAL'
        ELSE 'SWEEP (weak reversal)'
    END as sweep_type
FROM sweeps_with_reversal
WHERE reversal_magnitude IS NOT NULL
    AND reversal_magnitude < -10  -- Mínimo -10 pts de reversión
ORDER BY ABS(reversal_magnitude) DESC;
```

### Criterios de Validación

Un LP se considera **SWEPT** si:

1. ✅ Precio penetra LP ≥ 5 puntos
2. ✅ Permanece arriba ≤ 3 velas (15 min en 5min TF)
3. ✅ Reversa ≥ 15 puntos en dirección opuesta
4. ✅ (Opcional) Order Block se forma en/después del sweep

**Confianza:**
- **Alta**: Sweep + BEARISH OB + Impulso > 30 pts
- **Media**: Sweep + Reversión > 15 pts
- **Baja**: Sweep + Reversión débil < 15 pts

---

## Ejemplos del 20 de Noviembre

### Ejemplo 1: NYH Sweep (CLÁSICO)

```
LP FORMATION:
- NYH @ 25,310.00 formado durante sesión NY
- Máximo del día establecido @ 10:35 ET

SWEEP:
- 10:35 ET: High = 25,310.00 (exacto)
- Volumen: 8,414 contratos (alto)
- Duración en nivel: 1 vela (5 min)

ORDER BLOCK:
- 10:35 ET: BEARISH OB (25,258.75-25,310.00)
- Impulso 3V: -98.25 pts

RESULTADO:
- 10:40 ET: -134.50 pts
- 11:45 ET: -550 pts (llegada a 24,760)
- 12:00 ET: -790 pts (llegada a 24,520)

→ SWEPT LP confirmado
→ Estado: MITIGATED
→ Trade perfecto: Entry short en OB re-test
```

### Ejemplo 2: Triple High @ 25,188.75 (Respected)

```
LP FORMATION:
- 22:05 ET: Toque 1 @ 25,188
- 22:50 ET: Toque 2 @ 25,188
- 23:30 ET: Toque 3 @ 25,188
- 00:40 ET: Toque 4 @ 25,188
→ STRONG TRIPLE HIGH formado

INTERACCIONES:
- Cada toque: Reversión inmediata
- NO hubo penetración significativa
- Precio respetó el nivel 4 veces

ESTADO ACTUAL:
→ RESPECTED (no swept)
→ Estado: STILL ACTIVE
→ Potencial target futuro para sweep
```

### Ejemplo 3: Temporary LP en Asian Session

```
LP FORMATION:
- 23:00 ET: EQH @ 25,185 (toque 1)
- 00:30 ET: EQH @ 25,185 (toque 2)
→ Equal High formado

SWEEP:
- 03:15 ET: Precio rompe 25,190 (London open)
- OB formado inmediatamente
- Reversión -35 pts

DURACIÓN:
- Formación a Sweep: 4.25 horas
→ TEMPORARY/INTRADAY LP
→ Típico de Asian → London transition
```

---

## Clasificación Visual en ATAS

### Marcado por Estado

**Unmitigated LPs:**
```
Color: Amarillo (#FFFF00)
Estilo: Línea punteada
Label: "LP - ACTIVE"
```

**Swept LPs:**
```
Color: Rojo (#FF0000)
Estilo: Línea sólida + X en punto de sweep
Label: "LP - SWEPT @ [time]"
Marcar también: OB que se formó después
```

**Respected LPs:**
```
Color: Verde (#00FF00)
Estilo: Línea sólida gruesa
Label: "LP - RESPECTED ([n] toques)"
```

**Temporary LPs:**
```
Color: Gris (#808080)
Estilo: Línea fina
Label: "LP - TEMP (intraday)"
```

---

## Trading Strategies por Estado

### 1. Trading Unmitigated LPs

**Setup:**
- Identificar LP activo
- Esperar que precio se acerque
- Preparar entrada cuando toque

**Entry:**
- NO entrar antes del toque
- Esperar confirmación (sweep o respect)

**Ejemplo:**
```
08:00 - EQH @ 25,200 identificado (ACTIVE)
...
10:00 - Precio llega a 25,195
10:05 - Esperar: ¿sweep o respect?
```

### 2. Trading Swept LPs (MEJOR SETUP)

**Setup:**
- LP es swept (confirmado)
- Order Block formado después
- Impulso direccional comenzó

**Entry:**
- Entry en RE-TEST del OB (no del LP)
- Stop detrás del OB
- TP: Próximo LP opuesto

**Ejemplo:**
```
NYH @ 25,310 swept → OB @ 25,258-25,310

Entry: 25,280 (re-test del OB)
Stop: 25,315 (arriba del OB)
TP1: 25,100 (LSH)
TP2: 24,500 (estimado)

Risk: 35 pts
Reward: 180 pts (TP1) / 780 pts (TP2)
RR: 1:5 / 1:22
```

### 3. Trading Respected LPs

**Setup:**
- LP tocado 2-3 veces sin sweep
- Cada vez reversa
- Institucionales "defienden" nivel

**Entry:**
- Entry en próximo touch (expecting respect)
- Tight stop (si penetra = sweep incoming)

**Riesgo:**
- 3rd-4th touch suele ser swept
- No confiar ciegamente

---

## Conclusiones

### Estado de LP → Trading Decision

| Estado | Acción | Confiabilidad |
|--------|--------|---------------|
| **Unmitigated** | Esperar | Media - puede tardar |
| **Swept** | ✅ **ENTRAR** | ⭐ Alta - mejor setup |
| **Respected** | Precaución | Media - puede cambiar |
| **Temporary** | Scalp only | Baja - corto plazo |

### Reglas de Oro

1. **Swept LP + OB** = Setup perfecto (85%+ win rate)
2. **3-4 respects** = Probable sweep próximo
3. **Temporary LPs** = Solo intraday
4. **Session LPs** = Más confiables que intraday LPs

### Próximos Pasos

1. Implementar detección automática de sweeps
2. Calcular win rate por tipo de LP state
3. Backtesting: Swept LPs vs Respected LPs
4. Alert system: Cuando LP está siendo swept

---

## Integración con Taxonomía de Rebotes y Penetraciones

### Mapeo: Estados de LP → Tipos de Interacción

Los **estados de LP** (Unmitigated, Swept, Respected) pueden **descomponerse** en tipos más granulares usando la taxonomía de REBOTE_Y_PENETRACION_CRITERIOS.md:

#### Estado: RESPECTED → Rebotes R0-R4

```
RESPECTED (clasificación tradicional)
  └─ Subdividir en 5 niveles de fuerza:

├─ R0 - CLEAN BOUNCE (Respeto Perfecto)
│  └─ Penetración: 0-1 punto
│  └─ Fuerza: MUY FUERTE (90% confianza)
│  └─ Ejemplo: Triple High @ 25188, precio 25189 → reversa
│
├─ R1 - SHALLOW TOUCH (Respeto Fuerte)
│  └─ Penetración: 1-3 puntos (solo wicks)
│  └─ Fuerza: FUERTE (80% confianza)
│  └─ Ejemplo: EQH @ 25100, wick penetra 2 pts → reversa
│
├─ R2 - LIGHT REJECTION (Respeto Moderado)
│  └─ Penetración: 3-10 puntos, cierra fuera
│  └─ Fuerza: MODERADA (70% confianza)
│  └─ Ejemplo: NYH penetra 7 pts pero rechazo fuerte
│
├─ R3 - MEDIUM REJECTION (Respeto Débil)
│  └─ Penetración: 10-25% de zona LP
│  └─ Fuerza: DÉBIL (60% confianza)
│  └─ Señal: LP se está debilitando, próximo sweep probable
│
└─ R4 - DEEP REJECTION (Respeto Muy Débil)
   └─ Penetración: 25-50% de zona LP
   └─ Fuerza: MUY DÉBIL (50% confianza)
   └─ Señal: LP punto de romper, ESPERAR sweep
```

**Insight**: Si LP tiene múltiples R3-R4, **próximo toque será sweep** (85% probabilidad)

#### Estado: SWEPT → Penetraciones P4-P5

```
SWEPT (clasificación tradicional)
  └─ Subdividir en 2 tipos principales:

├─ P4 - FALSE BREAKOUT (Sweep Clásico)
│  └─ Rompe LP ≥5 pts más allá
│  └─ Regresa dentro en ≤5 velas
│  └─ Cierra del lado original
│  └─ ESTE ES EL "LIQUIDITY SWEEP" TÍPICO
│  └─ Señal: MUY FUERTE para reversión (85% confianza)
│  └─ Ejemplo: NYH 20 Nov - toca 25310, cierra 25280, impulso -790 pts
│
└─ P5 - BREAK AND RETEST (Genuine Break)
   └─ Rompe LP completamente
   └─ Continúa ≥20 pts en dirección break
   └─ Regresa a testear desde otro lado
   └─ Cambio de polaridad: Buy-Side → Sell-Side
   └─ Señal: FUERTE para continuación (75% confianza)
   └─ Ejemplo: LSH roto, continúa +50 pts, retesta como soporte
```

**Diferencia Crítica**:
- **P4**: Reversión inminente (trap de retail)
- **P5**: Continuación de tendencia (break genuino)

### Flujo de Degradación de LP

Un LP sigue un **ciclo de degradación** medible:

```
FASE 1: UNMITIGATED
└─ LP formado, no tocado
└─ Fuerza: POTENCIAL

FASE 2: STRONG RESPECTED (R0-R1)
└─ Primeros toques con penetración mínima
└─ Fuerza: MUY ALTA (90-80% confianza)
└─ Acción: Entry válidas

FASE 3: MEDIUM RESPECTED (R2)
└─ Penetraciones moderadas
└─ Fuerza: MEDIA (70% confianza)
└─ Acción: Entry con confirmación

FASE 4: WEAK RESPECTED (R3-R4)
└─ Penetraciones profundas
└─ Fuerza: BAJA (60-50% confianza)
└─ Acción: ESPERAR sweep inminente

FASE 5: SWEPT (P4 o P5)
└─ LP finalmente roto
└─ Si P4: Entry en reversión (85% confianza)
└─ Si P5: Entry en continuación (75% confianza)

FASE 6: MITIGATED
└─ Liquidez consumida
└─ LP ya no es válido para futuras operaciones
```

### Query de Clasificación Avanzada

```sql
-- Clasificar estado de LP con granularidad completa
WITH lp_interactions AS (
    SELECT
        lp.lp_id,
        lp.lp_level,
        lp.formation_time,
        c.time_interval,
        c.open, c.high, c.low, c.close,
        -- Clasificar interacción
        (SELECT * FROM classify_zone_interaction(
            c.open, c.high, c.low, c.close,
            lp.lp_level - 5,  -- zone_low (tolerance)
            lp.lp_level + 5,  -- zone_high (tolerance)
            CASE WHEN c.low < lp.lp_level THEN 'BELOW' ELSE 'ABOVE' END
        )) as interaction
    FROM liquidity_pools lp
    INNER JOIN candlestick_5min c
        ON c.symbol = lp.symbol
        AND c.time_interval > lp.formation_time
        AND c.time_interval <= lp.formation_time + INTERVAL '48 hours'
        AND (c.high >= lp.lp_level - 10 OR c.low <= lp.lp_level + 10)
),
lp_state_analysis AS (
    SELECT
        lp_id,
        lp_level,
        formation_time,
        -- Contar por tipo de interacción
        COUNT(*) as total_touches,
        COUNT(*) FILTER (WHERE (interaction).interaction_type = 'R0_CLEAN_BOUNCE') as r0_count,
        COUNT(*) FILTER (WHERE (interaction).interaction_type = 'R1_SHALLOW_TOUCH') as r1_count,
        COUNT(*) FILTER (WHERE (interaction).interaction_type = 'R2_LIGHT_REJECTION') as r2_count,
        COUNT(*) FILTER (WHERE (interaction).interaction_type = 'R3_MEDIUM_REJECTION') as r3_count,
        COUNT(*) FILTER (WHERE (interaction).interaction_type = 'R4_DEEP_REJECTION') as r4_count,
        COUNT(*) FILTER (WHERE (interaction).interaction_type = 'P4_FALSE_BREAKOUT') as p4_count,
        COUNT(*) FILTER (WHERE (interaction).interaction_type = 'P5_BREAK_AND_RETEST') as p5_count,

        -- Calcular fuerza promedio
        AVG(
            CASE
                WHEN (interaction).interaction_type = 'R0_CLEAN_BOUNCE' THEN 5
                WHEN (interaction).interaction_type = 'R1_SHALLOW_TOUCH' THEN 4
                WHEN (interaction).interaction_type = 'R2_LIGHT_REJECTION' THEN 3
                WHEN (interaction).interaction_type = 'R3_MEDIUM_REJECTION' THEN 2
                WHEN (interaction).interaction_type = 'R4_DEEP_REJECTION' THEN 1
                ELSE 0
            END
        ) as avg_strength_score,

        -- Primer y último toque
        MIN(time_interval) as first_touch,
        MAX(time_interval) as last_touch
    FROM lp_interactions
    GROUP BY lp_id, lp_level, formation_time
)
SELECT
    lp_id,
    ROUND(lp_level::NUMERIC, 2) as level,
    TO_CHAR(formation_time AT TIME ZONE 'America/New_York', 'YYYY-MM-DD HH24:MI') as formed_at,
    total_touches,

    -- Detalle de toques
    r0_count, r1_count, r2_count, r3_count, r4_count,
    p4_count as swept_count,

    -- Clasificación de estado
    CASE
        -- Swept
        WHEN p4_count > 0 OR p5_count > 0 THEN
            CASE
                WHEN p4_count > 0 THEN 'SWEPT (P4 - False Breakout)'
                ELSE 'SWEPT (P5 - Break and Retest)'
            END

        -- Unmitigated
        WHEN total_touches = 0 THEN 'UNMITIGATED'

        -- Respected (graduar por fuerza)
        WHEN avg_strength_score >= 4.0 THEN 'STRONG RESPECTED (R0-R1 dominant)'
        WHEN avg_strength_score >= 3.0 THEN 'MEDIUM RESPECTED (R2 dominant)'
        WHEN avg_strength_score >= 2.0 THEN 'WEAK RESPECTED (R3 dominant)'
        ELSE 'VERY WEAK RESPECTED (R4 dominant) - SWEEP INMINENTE'
    END as lp_state,

    -- Fuerza numérica
    ROUND(avg_strength_score::NUMERIC, 2) as strength_score,

    -- Confianza para próximo toque
    CASE
        WHEN avg_strength_score >= 4.0 THEN '85-90%'
        WHEN avg_strength_score >= 3.0 THEN '70-75%'
        WHEN avg_strength_score >= 2.0 THEN '60-65%'
        WHEN avg_strength_score >= 1.0 THEN '50-55% (alto riesgo)'
        ELSE 'EVITAR (próximo sweep)'
    END as confidence_next_touch,

    -- Tiempo desde último toque
    EXTRACT(EPOCH FROM (NOW() - last_touch)) / 3600 as hours_since_last_touch

FROM lp_state_analysis
ORDER BY lp_id;
```

**Output Example**:
```
lp_id | level     | state                            | r0 | r1 | r2 | r3 | swept | strength | confidence
------|-----------|----------------------------------|----|----|----|----|-------|----------|------------
LP001 | 25188.00  | STRONG RESPECTED (R0-R1)        | 3  | 1  | 0  | 0  | 0     | 4.75     | 85-90%
LP002 | 25310.00  | SWEPT (P4 - False Breakout)     | 0  | 0  | 0  | 0  | 1     | N/A      | N/A
LP003 | 24400.00  | WEAK RESPECTED (R3 dominant)    | 0  | 0  | 1  | 2  | 0     | 2.33     | 60-65%
```

**Interpretación**:
- **LP001**: MUY FUERTE (3 R0 + 1 R1), próximo toque confianza 85-90%
- **LP002**: SWEPT (P4), ya no usar este LP
- **LP003**: DÉBIL (mayormente R3), **esperar P4 sweep pronto**

### Alertas Basadas en Degradación

```python
class LPDegradationMonitor:
    """Monitor de degradación de Liquidity Pools"""

    def analyze_lp_health(self, lp_interactions: List[dict]) -> dict:
        """
        Analiza salud del LP basado en interacciones recientes

        Returns:
            dict con estado, alerta, confianza
        """

        # Contar por tipo
        r0_count = sum(1 for i in lp_interactions if i['type'] == 'R0')
        r1_count = sum(1 for i in lp_interactions if i['type'] == 'R1')
        r2_count = sum(1 for i in lp_interactions if i['type'] == 'R2')
        r3_count = sum(1 for i in lp_interactions if i['type'] == 'R3')
        r4_count = sum(1 for i in lp_interactions if i['type'] == 'R4')

        # Calcular score
        strength_score = (
            r0_count * 5 +
            r1_count * 4 +
            r2_count * 3 +
            r3_count * 2 +
            r4_count * 1
        ) / len(lp_interactions)

        # Detectar degradación
        if len(lp_interactions) >= 3:
            last_3 = lp_interactions[-3:]
            recent_score = sum(
                {'R0': 5, 'R1': 4, 'R2': 3, 'R3': 2, 'R4': 1}.get(i['type'], 0)
                for i in last_3
            ) / 3

            is_degrading = recent_score < strength_score - 1.0

        else:
            is_degrading = False

        # Generar alerta
        if is_degrading and recent_score <= 2.0:
            alert = {
                'level': 'HIGH',
                'message': 'LP degrading rapidly - R3/R4 dominant. SWEEP INMINENTE',
                'action': 'WAIT_FOR_P4_SWEEP',
                'confidence': 0.85  # Alta confianza de que próximo toque es sweep
            }
        elif strength_score >= 4.0:
            alert = {
                'level': 'INFO',
                'message': 'LP very strong - R0/R1 dominant',
                'action': 'ENTRY_ON_NEXT_TOUCH',
                'confidence': 0.85
            }
        elif strength_score <= 2.0:
            alert = {
                'level': 'WARNING',
                'message': 'LP weak - R3/R4 dominant. Sweep probable',
                'action': 'WAIT_FOR_P4_CONFIRMATION',
                'confidence': 0.70
            }
        else:
            alert = {
                'level': 'INFO',
                'message': 'LP moderate strength',
                'action': 'ENTRY_WITH_CONFIRMATION',
                'confidence': 0.70
            }

        return {
            'strength_score': strength_score,
            'is_degrading': is_degrading,
            'alert': alert,
            'breakdown': {
                'r0': r0_count, 'r1': r1_count, 'r2': r2_count,
                'r3': r3_count, 'r4': r4_count
            }
        }
```

### Referencias

📄 **REBOTE_Y_PENETRACION_CRITERIOS.md** → Taxonomía completa (R0-R4, P1-P5)
📄 **REBOTE_SETUP.md** → Configuración y optimización de thresholds
📄 **LIQUIDITY_POOLS_CRITERIOS.md** → Detección de Liquidity Pools

**Integración**:
- **Estados** (este doc) + **Tipos de Interacción** (REBOTE...) = Sistema completo
- Permite medir **degradación** de LP objetivamente
- Genera **alertas cuantificables** (no subjetivas)

---

**Documento creado**: 2025-11-30
**Actualizado**: 2025-12-03 (integrada taxonomía de interacciones)
**Autor**: NQHUB Trading System
**Versión**: 1.0

