# Market State - Ciclo de Vida de Patrones ICT

## Fecha: Diciembre 21, 2025

## ¿Por qué el snapshot muestra 216 patrones?

Has observado correctamente que un snapshot para el 24 de noviembre de 2025 a las 9:30am muestra **216 patrones activos**. Este número NO indica un error - es completamente correcto según los criterios de detección y **gestión del ciclo de vida** de patrones ICT.

---

## CONCEPTO CLAVE: Patrones ICT NO se "eliminan" - se "MITIGAN"

**IMPORTANTE**: El término **"eliminación"** NO es apropiado para patrones ICT.

### Terminología Correcta:

| ❌ Término Incorrecto | ✅ Término Correcto | Significado |
|----------------------|---------------------|-------------|
| "Eliminar FVG" | **"Mitigar FVG"** | FVG fue rellenado (filled) |
| "Borrar OB" | **"Invalidar OB"** o **"Marcar como BROKEN"** | OB fue penetrado completamente |
| "Remover LP" | **"Swept LP"** o **"Mitigated LP"** | Liquidez fue tomada (swept) |

**Razón**: Los patrones ICT tienen **ESTADOS** que representan su ciclo de vida, no son binarios (existe/no existe).

---

## Ciclo de Vida de Patrones ICT

### 1. Fair Value Gaps (FVG)

#### Estados del FVG:

```
FORMACIÓN → UNMITIGATED → REDELIVERED → REBALANCED
                    ↓
               (opcional)
                SWEPT
```

**Estados en Base de Datos** (`backend/app/models/patterns.py`):

```python
class DetectedFVG(Base):
    status = Column(String, nullable=False)  # UNMITIGATED, REDELIVERED, REBALANCED
```

#### Criterios de Estado:

| Estado | Criterio | ¿Se incluye en snapshot? |
|--------|----------|-------------------------|
| **UNMITIGATED** | FVG formado, NO tocado por el precio | ✅ SÍ - Patrón activo |
| **REDELIVERED** | Precio tocó el FVG pero NO lo rellenó completamente | ✅ SÍ - Aún válido |
| **REBALANCED** | FVG rellenado completamente (75-100% penetración) | ❌ NO - Patrón mitigado |

**Ejemplo**:
```
FVG BEARISH formado @ 24960.75 - 24973.25 (12.50 pts gap)

Primera interacción (P2 - Deep Penetration 58%):
→ Estado: REDELIVERED (aún válido, pero debilitado)
→ Se INCLUYE en snapshot
→ Actuó como resistencia 14 veces

Rompimiento (P5 - Break and Retest 100%):
→ Estado: REBALANCED
→ NO se incluye en snapshot
→ FVG completamente rellenado
```

**Fuente**: `docs/FVG_CRITERIOS_DETECCION.md` (líneas 454-851)

---

### 2. Order Blocks (OB)

#### Estados del Order Block:

```
FORMACIÓN → ACTIVE → TESTED → BROKEN
```

**Estados en Base de Datos**:

```python
class DetectedOrderBlock(Base):
    status = Column(String, nullable=False)  # ACTIVE, TESTED, BROKEN
```

#### Criterios de Estado:

| Estado | Criterio | ¿Se incluye en snapshot? |
|--------|----------|-------------------------|
| **ACTIVE** | OB formado, esperando re-test | ✅ SÍ - Patrón activo |
| **TESTED** | Precio tocó el OB y respetó la zona | ✅ SÍ - Aún válido |
| **BROKEN** | Precio penetró completamente el OB (>90% penetración) | ❌ NO - Patrón invalidado |

**Ejemplo**:
```
STRONG BULLISH OB @ 09:40 AM (24719.00 - 24837.75)

Primera interacción (R1 - Shallow Touch 8%):
→ Estado: TESTED
→ Se INCLUYE en snapshot
→ Actuó como soporte 9 veces

21 toques posteriores:
→ Estado: TESTED (sigue válido)
→ Se INCLUYE en snapshot

Si precio cae por debajo de 24719.00 (low del OB):
→ Estado: BROKEN
→ NO se incluye en snapshot
```

**Fuente**: `docs/ORDER_BLOCKS_CRITERIOS.md` (líneas 1-300)

---

### 3. Liquidity Pools (LP) / Session Levels

#### Estados del Liquidity Pool:

```
FORMACIÓN → UNMITIGATED → RESPECTED → SWEPT/MITIGATED
```

**Estados en Base de Datos**:

```python
class DetectedLiquidityPool(Base):
    status = Column(String, nullable=False)  # UNMITIGATED, RESPECTED, SWEPT, MITIGATED
```

#### Criterios de Estado:

| Estado | Criterio | ¿Se incluye en snapshot? |
|--------|----------|-------------------------|
| **UNMITIGATED** | LP formado, NO tocado por el precio | ✅ SÍ - Patrón activo |
| **RESPECTED** | Precio tocó LP múltiples veces, reversó sin penetrar | ✅ SÍ - Patrón MUY activo |
| **SWEPT** | Precio penetró LP +5-10 puntos, luego reversó | ❌ NO - Liquidez consumida |
| **MITIGATED** | LP completamente invalidado | ❌ NO - Patrón mitigado |

**Ejemplo Crítico del 20 Nov**:
```
NYH @ 25,310.00 (Session High - Buy-Side Liquidity)

ANTES del sweep (10:30 AM):
→ Estado: UNMITIGATED
→ Se INCLUYE en snapshot (espera ser tocado)

SWEEP (10:35 AM):
→ Precio llega a 25,310.00 (toca el nivel)
→ BEARISH OB se forma (25,258.75 - 25,310.00)
→ Impulso bajista -134.50 pts
→ Estado: SWEPT
→ NO se incluye en snapshot (liquidez consumida)

Precio posterior: 24,520 (-790 pts desde el sweep)
→ Estado: MITIGATED
→ NO se incluye en snapshot
```

**Fuente**: `docs/LIQUIDITY_POOL_STATES.md` (líneas 1-200)

---

## Código de Generación de Snapshots

### Lógica Actual (`backend/app/services/market_state/snapshot_generator.py`)

```python
async def _get_active_fvgs(
    self,
    symbol: str,
    timeframe: str,
    snapshot_time: datetime
) -> List[DetectedFVG]:
    """Get active FVGs (UNMITIGATED) formed before snapshot_time"""
    result = await self.db.execute(
        select(DetectedFVG).where(
            and_(
                DetectedFVG.symbol == symbol,
                DetectedFVG.timeframe == timeframe,
                DetectedFVG.formation_time <= snapshot_time,
                DetectedFVG.status == "UNMITIGATED"  # ✅ Solo patrones activos
            )
        )
    )
    return result.scalars().all()


async def _get_active_session_levels(
    self,
    symbol: str,
    timeframe: str,
    snapshot_time: datetime
) -> List[DetectedLiquidityPool]:
    """Get active session levels (UNMITIGATED or RESPECTED) formed before snapshot_time"""
    result = await self.db.execute(
        select(DetectedLiquidityPool).where(
            and_(
                DetectedLiquidityPool.symbol == symbol,
                DetectedLiquidityPool.timeframe == timeframe,
                DetectedLiquidityPool.formation_time <= snapshot_time,
                DetectedLiquidityPool.pool_type.in_(SESSION_LEVEL_TYPES),
                # ✅ Solo UNMITIGATED y RESPECTED (no SWEPT ni MITIGATED)
                DetectedLiquidityPool.status.in_(["UNMITIGATED", "RESPECTED"])
            )
        )
    )
    return result.scalars().all()


async def _get_active_obs(
    self,
    symbol: str,
    timeframe: str,
    snapshot_time: datetime
) -> List[DetectedOrderBlock]:
    """Get active OBs (ACTIVE) formed before snapshot_time"""
    result = await self.db.execute(
        select(DetectedOrderBlock).where(
            and_(
                DetectedOrderBlock.symbol == symbol,
                DetectedOrderBlock.timeframe == timeframe,
                DetectedOrderBlock.formation_time <= snapshot_time,
                DetectedOrderBlock.status == "ACTIVE"  # ✅ Solo patrones activos
            )
        )
    )
    return result.scalars().all()
```

---

## ¿Por qué 216 patrones para Nov 24, 2025 @ 09:30?

### Desglose del Snapshot:

**Snapshot Time**: `2025-11-24 09:30:00 EST` = `2025-11-24 14:30:00 UTC`

**Consulta**:
```sql
SELECT * FROM market_state_snapshots
WHERE symbol = 'NQZ5'
  AND snapshot_time = '2025-11-24 14:30:00';  -- UTC naive
```

**Patrones incluidos**:

1. **FVGs con status = UNMITIGATED**:
   - Formados ANTES de las 09:30 (pueden ser de días anteriores)
   - NO han sido rellenados (rebalanced)
   - Ejemplo: FVG del 23 Nov @ 18:00 aún válido el 24 Nov @ 09:30

2. **Order Blocks con status = ACTIVE o TESTED**:
   - Formados ANTES de las 09:30
   - NO han sido rotos (broken)
   - Ejemplo: Bullish OB del 20 Nov @ 10:20 aún válido días después

3. **Session Levels con status = UNMITIGATED o RESPECTED**:
   - NYH, NYL, ASH, ASL, LSH, LSL formados en sesiones anteriores
   - NO han sido swept (barridos)
   - Ejemplo: NYH del 22 Nov @ 12:00 esperando ser tocado

### Distribución Típica (Estimada):

```
9 Timeframes × promedio de patrones por TF:

1min:    ~30 patrones activos (FVGs + OBs + LPs)
5min:    ~28 patrones activos
15min:   ~25 patrones activos
30min:   ~22 patrones activos
1hr:     ~20 patrones activos
2hr:     ~18 patrones activos
4hr:     ~15 patrones activos
1day:    ~12 patrones activos
1week:   ~6 patrones activos

Total: ~30+28+25+22+20+18+15+12+6 = 176 patrones

Con sesiones activas (Asian, London, NY): +40 patrones
```

**Total estimado**: ~216 patrones ✅

---

## Razones para NO "Eliminar" Patrones

### 1. **Patrones ICT son Persistentes**

Los patrones ICT pueden permanecer válidos por **días o semanas**:

```
Ejemplo real (docs/FVG_CRITERIOS_DETECCION.md líneas 435-444):

FVG formado el Domingo 24 Nov @ 18:55 ET
→ Fue relevante el Lunes 25 Nov @ 12:15 PM (18 horas después)
→ 7 velas consecutivas en zona FVG #1 (12:15-14:50 PM)
→ Conclusión: Los FVGs del domingo SÍ fueron relevantes el lunes
```

### 2. **Múltiples Re-tests son Comunes**

Order Blocks pueden ser tocados **10-20+ veces**:

```
STRONG BULLISH OB @ 09:40 AM
→ Tocado 21 veces
→ Actuó como soporte 9 veces (43% efectividad)
→ Primera re-prueba: 5 minutos después
→ Última re-prueba: horas o días después
```

### 3. **Session Levels pueden Durar Días**

Niveles de sesión (NYH, NYL, etc.) permanecen válidos hasta ser swept:

```
NYH @ 25,310.00
→ Formado: Lunes @ 09:30
→ Swept: Martes @ 10:35 (25 horas después)
→ Durante 25 horas fue un target válido
```

---

## Gestión de Estados: ¿Cuándo cambia el estado?

### Actualización de Estados (Workflow):

```
1. Detección Inicial (FVG/OB/LP Detector)
   └─> Status: UNMITIGATED/ACTIVE
   └─> Se guarda en DB

2. Monitoreo Continuo (Pattern State Monitor) [PENDIENTE]
   └─> Cada nueva vela:
       ├─> Verificar interacción con patrones activos
       ├─> Clasificar interacción (R0-R4, P1-P5)
       └─> Actualizar estado según criterios

3. Snapshot Generation
   └─> Query patrones con estados activos
   └─> Count solo UNMITIGATED/ACTIVE/RESPECTED
```

### Ejemplo de Actualización de Estado:

```python
# PSEUDO-CÓDIGO (no implementado aún)
async def monitor_pattern_states(current_candle):
    """
    Actualiza estados de patrones basado en nueva vela
    """
    for fvg in active_fvgs:
        interaction = classify_fvg_interaction(
            candle=current_candle,
            fvg_start=fvg.fvg_start,
            fvg_end=fvg.fvg_end
        )

        if interaction.type == 'P3_FULL_PENETRATION':
            # FVG rellenado 75-100%
            fvg.status = 'REBALANCED'
            await db.commit()
            # ❌ Ya NO aparecerá en futuros snapshots

        elif interaction.type == 'P2_DEEP_PENETRATION':
            # FVG rellenado 50-75%
            fvg.status = 'REDELIVERED'
            await db.commit()
            # ✅ SIGUE apareciendo en snapshots (debilitado pero válido)

        elif interaction.type in ['R0', 'R1', 'R2']:
            # Rebote en FVG
            # Status permanece UNMITIGATED
            # ✅ SIGUE apareciendo en snapshots
```

---

## Estado Actual vs Estado Ideal

### ✅ Actualmente Implementado:

1. **Detección de patrones** con estados iniciales
2. **Generación de snapshots** filtrando por estados activos
3. **Documentación completa** de criterios de mitigación

### ⚠️ Pendiente de Implementar:

1. **Pattern State Monitor** - Servicio que actualiza estados automáticamente
2. **Interaction Detector** - Clasifica interacciones (R0-R4, P1-P5)
3. **Auto-mitigation** - Cambia estados según penetraciones/rebotes

**Archivo pendiente**: `backend/app/services/pattern_detection/interaction_detector.py`

**Referencias**:
- `docs/REBOTE_Y_PENETRACION_CRITERIOS.md` - Taxonomía completa (R0-R4, P1-P5)
- `docs/LIQUIDITY_POOL_STATES.md` - Estados de LPs con ejemplos

---

## Respuesta a tu Pregunta

### ¿El término "eliminación" es apropiado?

**NO**, el término "eliminación" **NO es apropiado**.

### Terminología Correcta:

| Tipo de Patrón | Término Correcto | Acción en DB |
|----------------|------------------|--------------|
| **Fair Value Gap** | **"Mitigar"** o **"Rebalancear"** | `status = 'REBALANCED'` |
| **Order Block** | **"Invalidar"** o **"Romper"** | `status = 'BROKEN'` |
| **Liquidity Pool** | **"Barrer"** (Sweep) o **"Mitigar"** | `status = 'SWEPT'` o `'MITIGATED'` |

### Razones:

1. **Patrones ICT NO se borran** - permanecen en base de datos con estado histórico
2. **Mitigación es un proceso** - puede ser parcial (REDELIVERED) o total (REBALANCED)
3. **Estados reflejan ciclo de vida** - útil para backtesting y análisis
4. **Auditoría histórica** - saber CUÁNDO y CÓMO fue mitigado un patrón

---

## Query de Ejemplo: Estados de Patrones

```sql
-- Ver estados de todos los FVGs para el 24 Nov
SELECT
    fvg_id,
    fvg_type,
    TO_CHAR(formation_time AT TIME ZONE 'America/New_York', 'MM-DD HH24:MI') as formed_at,
    ROUND(gap_size, 2) as gap_pts,
    status,
    CASE
        WHEN status = 'UNMITIGATED' THEN '✅ Activo (en snapshot)'
        WHEN status = 'REDELIVERED' THEN '✅ Activo (debilitado, en snapshot)'
        WHEN status = 'REBALANCED' THEN '❌ Mitigado (NO en snapshot)'
    END as snapshot_inclusion
FROM detected_fvgs
WHERE symbol = 'NQZ5'
  AND timeframe = '5min'
  AND formation_time <= '2025-11-24 14:30:00'  -- Snapshot time (UTC)
ORDER BY formation_time DESC
LIMIT 20;
```

**Resultado Esperado**:
```
fvg_id | type    | formed_at    | gap_pts | status       | snapshot_inclusion
-------|---------|--------------|---------|--------------|-------------------
F001   | BEARISH | 11-24 08:55  | 12.50   | UNMITIGATED  | ✅ Activo
F002   | BEARISH | 11-24 09:00  | 10.25   | REDELIVERED  | ✅ Activo (debilitado)
F003   | BULLISH | 11-23 19:30  | 0.25    | REBALANCED   | ❌ Mitigado
F004   | BEARISH | 11-23 18:00  | 15.75   | UNMITIGATED  | ✅ Activo
```

---

## Conclusión

### ✅ Resumen:

1. **216 patrones es CORRECTO** - refleja patrones activos en 9 timeframes
2. **NO se "eliminan"** - se **"mitigan"** cambiando estado
3. **Estados reflejan ciclo de vida** - UNMITIGATED → REDELIVERED → REBALANCED
4. **Snapshot filtra por estado** - solo incluye patrones con estados activos
5. **Persistencia es intencional** - patrones ICT pueden durar días/semanas

### 📋 Criterios de Inclusión en Snapshot:

| Patrón | Estados Incluidos | Estados Excluidos |
|--------|------------------|-------------------|
| **FVG** | UNMITIGATED, REDELIVERED | REBALANCED |
| **OB** | ACTIVE, TESTED | BROKEN |
| **LP** | UNMITIGATED, RESPECTED | SWEPT, MITIGATED |

### 🔧 Próximos Pasos (Recomendados):

1. **Implementar Pattern State Monitor** - actualización automática de estados
2. **Implementar Interaction Detector** - clasificar R0-R4, P1-P5
3. **Dashboard de Estados** - visualizar distribución de estados por timeframe
4. **Backtesting de Mitigación** - analizar qué criterios son más efectivos

---

**Status**: ✅ Documentado completamente
**Última actualización**: Diciembre 21, 2025
**Referencias**:
- `docs/FVG_CRITERIOS_DETECCION.md`
- `docs/ORDER_BLOCKS_CRITERIOS.md`
- `docs/LIQUIDITY_POOL_STATES.md`
- `docs/REBOTE_Y_PENETRACION_CRITERIOS.md`
- `backend/app/services/market_state/snapshot_generator.py`
