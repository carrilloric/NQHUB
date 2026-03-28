# NQHUB Data Dictionary

**Catálogo Completo de Metadatos del Sistema NQHUB**

**Versión**: 1.0
**Fecha**: 2024-12-14
**Base de Datos**: PostgreSQL 15 + TimescaleDB
**Puerto**: 5433

---

## Propósito

Este documento sirve como referencia autoritaria de todos los metadatos del sistema NQHUB, incluyendo:
- Esquemas de tablas con descripciones detalladas de campos
- Tipos de datos y constraints
- Fórmulas de cálculo
- Ejemplos de valores
- Reglas de negocio
- Relaciones entre tablas

**Audiencia**: Desarrolladores, analistas de datos, IA asistentes (Vanna, Claude Code)

---

## Índice

1. [Candlestick Tables (8 timeframes)](#1-candlestick-tables)
2. [market_data_ticks](#2-market_data_ticks)
3. [active_contracts](#3-active_contracts)
4. [Pattern Detection Tables](#4-pattern-detection-tables)
5. [ETL Tables](#5-etl-tables)
6. [Authentication Tables](#6-authentication-tables)
7. [Field Details](#7-field-details)
8. [Business Rules](#8-business-rules)

---

## 1. Candlestick Tables

### Overview

Se mantienen **8 tablas de candlestick** con timeframes diferentes, todas con el mismo esquema de **33 columnas**:

- `candlestick_30s` - Velas de 30 segundos
- `candlestick_1min` - Velas de 1 minuto
- `candlestick_5min` - Velas de 5 minutos
- `candlestick_15min` - Velas de 15 minutos
- `candlestick_1hr` - Velas de 1 hora
- `candlestick_4hr` - Velas de 4 horas
- `candlestick_daily` - Velas diarias
- `candlestick_weekly` - Velas semanales

**Primary Key**: `(time_interval, symbol)` - Compuesta

**Propósito**: Almacenar datos agregados de velas OHLCV con métricas avanzadas de order flow, POC, estructura de vela, distribución de volumen y absorción.

---

### 1.1 Metadata Table - candlestick_5min

(Esquema idéntico para las 8 tablas, solo cambia el timeframe)

| Table | Column | Type | Nullable | Default | Description | Example | Formula | Business Rules |
|-------|--------|------|----------|---------|-------------|---------|---------|----------------|
| candlestick_5min | time_interval | TIMESTAMP WITH TIME ZONE | NOT NULL | - | Inicio del intervalo temporal en UTC. Formato: 'YYYY-MM-DD HH:MM:SS+00'. Representa el timestamp de inicio del bucket de tiempo para la vela de 5 minutos | '2024-11-05 14:30:00+00' | `time_bucket('5 minutes'::interval, ts_event)` | Para queries en Eastern Time usar: `time_interval AT TIME ZONE 'America/New_York'` que devuelve timestamp sin zona horaria en ET |
| candlestick_5min | symbol | VARCHAR(20) | NOT NULL | - | Símbolo del contrato en formato estándar CME. Para contratos simples: {PRODUCTO}{MES}{AÑO}. Para spreads: {CONTRATO1}-{CONTRATO2} | 'NQZ24', 'NQH25', 'NQZ24-NQH25' | - | Códigos de mes: H=Marzo, M=Junio, U=Septiembre, Z=Diciembre. Año en 2 dígitos. Spreads se identifican por contener '-' |
| candlestick_5min | is_spread | BOOLEAN | - | false | TRUE si el símbolo representa un calendar spread (contrato compuesto de dos meses) | true (para 'NQZ24-NQH25'), false (para 'NQZ24') | `'-' in symbol` | Los spreads se excluyen típicamente de backtesting. Filtrar con: `WHERE is_spread = false` |
| candlestick_5min | is_rollover_period | BOOLEAN | - | false | TRUE si la vela pertenece a un período de transición entre contratos (rollover period) | true, false | Marcado automáticamente durante detección de rollover | Durante rollover puede haber múltiples contratos activos simultáneamente |
| candlestick_5min | open | DOUBLE PRECISION | - | - | Precio de apertura de la vela - primer precio negociado en el intervalo | 20125.50 | `(array_agg(price ORDER BY ts_event))[1]` | Primer tick del intervalo de 5 minutos |
| candlestick_5min | high | DOUBLE PRECISION | - | - | Precio máximo alcanzado durante el intervalo de 5 minutos | 20135.75 | `MAX(price)` | Precio más alto de todos los ticks en el intervalo |
| candlestick_5min | low | DOUBLE PRECISION | - | - | Precio mínimo alcanzado durante el intervalo de 5 minutos | 20118.25 | `MIN(price)` | Precio más bajo de todos los ticks en el intervalo |
| candlestick_5min | close | DOUBLE PRECISION | - | - | Precio de cierre de la vela - último precio negociado en el intervalo | 20130.00 | `(array_agg(price ORDER BY ts_event DESC))[1]` | Último tick del intervalo de 5 minutos |
| candlestick_5min | volume | DOUBLE PRECISION | - | - | Volumen total de contratos negociados durante el intervalo | 1250 | `SUM(size)` | Suma de todos los tamaños (size) de ticks en el intervalo |
| candlestick_5min | poc | DOUBLE PRECISION | - | - | Point of Control - nivel de precio con mayor volumen negociado. Redondea a 1.0 punto usando FLOOR para agrupar 4 ticks de 0.25 | 20125.0 | `FLOOR(price)` del nivel con `MAX(SUM(size))` | Agrupa 4 ticks de 0.25 en 1.0 punto. Más rápido de calcular que real_poc. Útil para análisis macro |
| candlestick_5min | poc_volume | DOUBLE PRECISION | - | - | Volumen total negociado en el nivel del POC (precision 1.0 punto) | 425 | `SUM(size)` donde `FLOOR(price) = poc` | Suma de volumen de todos los ticks en el nivel POC redondeado |
| candlestick_5min | poc_percentage | DOUBLE PRECISION | - | - | Porcentaje del volumen total de la vela que se concentró en el nivel POC | 34.0 | `(poc_volume / volume) * 100` | Valores >30% indican alta concentración de actividad. >40% es muy significativo |
| candlestick_5min | poc_location | TEXT | - | - | Zona de la vela donde se encuentra el POC: 'upper_wick' (mecha superior), 'body' (cuerpo), 'lower_wick' (mecha inferior) | 'upper_wick', 'body', 'lower_wick' | `CASE WHEN poc > GREATEST(open,close) THEN 'upper_wick' WHEN poc < LEAST(open,close) THEN 'lower_wick' ELSE 'body' END` | POC en upper_wick = absorción en high. POC en lower_wick = absorción en low |
| candlestick_5min | poc_position | DOUBLE PRECISION | - | - | Posición relativa del POC dentro del rango de la vela. 0 = en el mínimo, 1 = en el máximo, 0.5 = en el centro | 0.65 | `(poc - low) / (high - low)` | NULL si high = low (vela sin rango) |
| candlestick_5min | real_poc | DOUBLE PRECISION | - | - | Point of Control real - precio exacto con mayor volumen sin redondeo. Precisión exacta de 0.25 tick | 20125.25 | Precio exacto del nivel con `MAX(SUM(size))` sin FLOOR | Más preciso que 'poc'. Útil para entradas exactas y análisis micro |
| candlestick_5min | real_poc_volume | DOUBLE PRECISION | - | - | Volumen negociado en el POC real (tick exacto de 0.25) | 412 | `SUM(size)` donde `price = real_poc` | Volumen en el tick exacto, no agrupado por punto |
| candlestick_5min | real_poc_percentage | DOUBLE PRECISION | - | - | Porcentaje del volumen total en el POC real (tick exacto) | 32.96 | `(real_poc_volume / volume) * 100` | Típicamente ligeramente menor que poc_percentage debido a mayor precisión |
| candlestick_5min | real_poc_location | TEXT | - | - | Zona de la vela donde se encuentra el POC real | 'body' | Misma lógica que poc_location usando real_poc | Puede diferir de poc_location si el redondeo mueve el POC de zona |
| candlestick_5min | upper_wick | DOUBLE PRECISION | - | - | Tamaño de la mecha superior en puntos. Distancia entre el high y el máximo entre open/close | 5.75 | `high - GREATEST(open, close)` | 0 si vela cierra en el high (no hay mecha superior) |
| candlestick_5min | lower_wick | DOUBLE PRECISION | - | - | Tamaño de la mecha inferior en puntos. Distancia entre el mínimo entre open/close y el low | 6.75 | `LEAST(open, close) - low` | 0 si vela cierra en el low (no hay mecha inferior) |
| candlestick_5min | body | DOUBLE PRECISION | - | - | Tamaño del cuerpo de la vela en puntos. Distancia entre open y close | 4.50 | `ABS(close - open)` | 0 para velas doji (open = close) |
| candlestick_5min | wick_ratio | DOUBLE PRECISION | - | NULL | Ratio entre el tamaño total de las mechas y el tamaño del cuerpo | 2.78 | `(upper_wick + lower_wick) / body` | NULL si body = 0 (velas doji). Valores >3 indican rechazo fuerte |
| candlestick_5min | rel_uw | DOUBLE PRECISION | - | NULL | Mecha superior relativa - fracción del rango total que ocupa la mecha superior | 0.33 | `upper_wick / (high - low)` | Rango 0-1. NULL si high = low. >0.5 indica rechazo significativo en high |
| candlestick_5min | rel_lw | DOUBLE PRECISION | - | NULL | Mecha inferior relativa - fracción del rango total que ocupa la mecha inferior | 0.38 | `lower_wick / (high - low)` | Rango 0-1. NULL si high = low. >0.5 indica rechazo significativo en low |
| candlestick_5min | upper_wick_volume | DOUBLE PRECISION | - | - | Volumen total negociado en la zona de la mecha superior | 320 | `SUM(size) WHERE price > GREATEST(open,close) AND price <= high` | Volumen en zona de rechazo superior |
| candlestick_5min | lower_wick_volume | DOUBLE PRECISION | - | - | Volumen total negociado en la zona de la mecha inferior | 380 | `SUM(size) WHERE price < LEAST(open,close) AND price >= low` | Volumen en zona de rechazo inferior |
| candlestick_5min | body_volume | DOUBLE PRECISION | - | - | Volumen total negociado dentro del cuerpo de la vela (entre open y close) | 550 | `SUM(size) WHERE price >= LEAST(open,close) AND price <= GREATEST(open,close)` | Volumen en zona de aceptación (dentro del cuerpo) |
| candlestick_5min | asellers_uwick | DOUBLE PRECISION | - | - | Vendedores agresivos en mecha superior - órdenes de venta agresivas (market orders) ejecutadas en la zona de la mecha superior | 180 | `SUM(size) WHERE side='A' AND price > GREATEST(open,close)` | side='A' = Ask (vendedor agresivo hit the bid). Alto valor indica absorción de compradores en el high |
| candlestick_5min | asellers_lwick | DOUBLE PRECISION | - | - | Vendedores agresivos en mecha inferior - órdenes de venta agresivas ejecutadas en la zona de la mecha inferior | 120 | `SUM(size) WHERE side='A' AND price < LEAST(open,close)` | Vendedores tomando ganancias o cerrando longs en el low |
| candlestick_5min | abuyers_uwick | DOUBLE PRECISION | - | - | Compradores agresivos en mecha superior - órdenes de compra agresivas ejecutadas en la zona de la mecha superior | 140 | `SUM(size) WHERE side='B' AND price > GREATEST(open,close)` | side='B' = Bid (comprador agresivo hit the ask). Compradores cazando stops o entrando agresivamente |
| candlestick_5min | abuyers_lwick | DOUBLE PRECISION | - | - | Compradores agresivos en mecha inferior - órdenes de compra agresivas ejecutadas en la zona de la mecha inferior | 260 | `SUM(size) WHERE side='B' AND price < LEAST(open,close)` | Alto valor indica absorción de vendedores en el low (posible soporte) |
| candlestick_5min | delta | DOUBLE PRECISION | - | - | Delta neto de la vela - diferencia entre volumen de compradores agresivos y vendedores agresivos | 125 | `SUM(CASE WHEN side='B' THEN size WHEN side='A' THEN -size ELSE 0 END)` | Positivo = presión compradora (más agresividad de compra). Negativo = presión vendedora |
| candlestick_5min | oflow_detail | JSONB | - | - | Order flow detallado por tick (precisión 0.25). Estructura JSONB con asks/bids por cada nivel de precio | `{"20125.00":{"asks":125,"bids":98},"20125.25":{"asks":87,"bids":142}}` | Agregación de volumen ask/bid por precio exacto (0.25 tick) | Usado para análisis micro de footprint. asks = ventas agresivas, bids = compras agresivas |
| candlestick_5min | oflow_unit | JSONB | - | - | Order flow agregado por punto (precisión 1.0). Estructura JSONB con asks/bids por cada punto completo | `{"20125":{"asks":268,"bids":443},"20126":{"asks":156,"bids":321}}` | Agregación de volumen ask/bid por punto (1.0, agrupa 4 ticks) | Usado para análisis macro de order flow. Más rápido de procesar que oflow_detail |
| candlestick_5min | tick_count | INTEGER | - | - | Número total de ticks que componen la vela | 1842 | `COUNT(*)` de ticks en el intervalo | Indicador de actividad. Valores bajos pueden indicar baja liquidez |

---

## 2. market_data_ticks

**Propósito**: Almacena datos tick-by-tick de mercado en tiempo real provenientes de Databento.

**Tipo**: TimescaleDB Hypertable (particionada por `ts_event`, chunks de 1 día)

**Primary Key**: `(id, ts_event)` - Compuesta

| Column | Type | Nullable | Default | Description | Example | Business Rules |
|--------|------|----------|---------|-------------|---------|----------------|
| id | BIGINT | NOT NULL | AUTO_INCREMENT | Identificador único del tick | 1234567 | Auto-incrementado |
| ts_recv | TIMESTAMP WITH TIME ZONE | NOT NULL | - | Timestamp de recepción por Databento (cuando fue recibido) | '2024-07-19 09:30:00.123456+00' | UTC timezone |
| ts_event | TIMESTAMP WITH TIME ZONE | NOT NULL | - | Timestamp del evento real (cuando ocurrió el trade) | '2024-07-19 09:30:00.123000+00' | UTC timezone. Usado para particionamiento |
| symbol | VARCHAR(20) | NOT NULL | - | Símbolo del contrato o spread | 'NQU4', 'NQH4-NQM4' | - |
| is_spread | BOOLEAN | - | false | TRUE si es calendar spread | true, false | `'-' in symbol` |
| is_rollover_period | BOOLEAN | - | false | TRUE durante rollover | true, false | - |
| price | DOUBLE PRECISION | NOT NULL | - | Precio del tick | 19875.25 | Múltiplo de 0.25 (tick size de NQ) |
| size | INTEGER | NOT NULL | - | Cantidad de contratos | 5 | >0 |
| side | VARCHAR(1) | NOT NULL | - | Lado del mercado: 'A' = Ask (venta), 'B' = Bid (compra) | 'A', 'B' | A = vendedor agresivo, B = comprador agresivo |
| action | VARCHAR(1) | - | - | Acción de orden: 'A'=Add, 'C'=Cancel, 'M'=Modify, 'F'=Fill, 'T'=Trade | 'T' | - |
| bid_px | DOUBLE PRECISION | - | - | Precio del mejor bid (para order book snapshots) | 19875.00 | - |
| ask_px | DOUBLE PRECISION | - | - | Precio del mejor ask | 19875.25 | - |
| bid_sz | INTEGER | - | - | Tamaño del mejor bid | 12 | - |
| ask_sz | INTEGER | - | - | Tamaño del mejor ask | 8 | - |
| bid_ct | INTEGER | - | - | Número de órdenes bid | 3 | - |
| ask_ct | INTEGER | - | - | Número de órdenes ask | 2 | - |

---

## 3. active_contracts

**Propósito**: Tracking del contrato NQ activo del mes (front month). Usado para resolver "NQ" → símbolo real del contrato activo.

**Primary Key**: `id`

**Regla Crítica**: Solo un contrato puede tener `is_current = true` a la vez.

| Column | Type | Nullable | Default | Description | Example | Formula | Business Rules |
|--------|------|----------|---------|-------------|---------|---------|----------------|
| id | INTEGER | NOT NULL | AUTO_INCREMENT | Identificador único | 1 | - | Primary Key |
| symbol | VARCHAR(10) | NOT NULL | - | Símbolo del contrato CME. Formato: {PROD}{MES}{AÑO} | 'NQZ24', 'NQH25' | - | Mes: H=Mar, M=Jun, U=Sep, Z=Dic |
| start_date | DATE | NOT NULL | - | Fecha de inicio de actividad del contrato | '2024-09-10' | - | Cuando el contrato se vuelve activo |
| end_date | DATE | - | - | Fecha de fin de actividad (NULL si aún activo) | '2024-12-12', NULL | - | NULL para contratos actualmente activos |
| volume_score | BIGINT | - | - | Score acumulado de volumen para este contrato | 15847293 | `SUM(volume)` | Usado para determinar cuándo hacer rollover |
| tick_count | BIGINT | - | - | Total de ticks registrados | 8932471 | `COUNT(*)` | Indicador de actividad del contrato |
| is_current | BOOLEAN | NOT NULL | false | TRUE para el contrato activo actual (front month) | true, false | - | **Solo uno = true a la vez**. Usar en JOIN: `WHERE ac.is_current = true` |
| rollover_period | BOOLEAN | NOT NULL | false | TRUE durante período de transición entre contratos | true, false | - | TRUE durante 2-4 días antes de expiración |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | Timestamp de creación del registro | '2024-11-02 10:15:32+00' | - | UTC |
| updated_at | TIMESTAMPTZ | - | - | Última actualización | '2024-11-05 14:22:18+00' | - | UTC |

---

## 4. Pattern Detection Tables

### 4.1 detected_fvgs

**Propósito**: Fair Value Gaps detectados con metodología ICT.

**Primary Key**: `id`

| Column | Type | Nullable | Default | Description | Example | Business Rules |
|--------|------|----------|---------|-------------|---------|----------------|
| id | SERIAL | NOT NULL | AUTO_INCREMENT | Identificador único del FVG | 1 | - |
| symbol | VARCHAR(20) | NOT NULL | - | Símbolo del contrato | 'NQZ24' | - |
| timeframe | VARCHAR(10) | NOT NULL | - | Timeframe de detección | '5min', '15min' | - |
| formation_time | TIMESTAMP | NOT NULL | - | Timestamp de formación (UTC naive) | '2024-11-05 14:30:00' | UTC naive (sin timezone) |
| gap_low | DOUBLE PRECISION | NOT NULL | - | Límite inferior del gap | 20110.00 | - |
| gap_high | DOUBLE PRECISION | NOT NULL | - | Límite superior del gap | 20150.00 | - |
| gap_size | DOUBLE PRECISION | NOT NULL | - | Tamaño del gap en puntos | 40.00 | `gap_high - gap_low` |
| premium_level | DOUBLE PRECISION | NOT NULL | - | Nivel premium (límite superior, actúa como resistencia en FVG alcista) | 20150.00 | Para BULLISH FVG = gap_high |
| discount_level | DOUBLE PRECISION | NOT NULL | - | Nivel discount (límite inferior, actúa como soporte en FVG alcista) | 20110.00 | Para BULLISH FVG = gap_low |
| consequent_encroachment | DOUBLE PRECISION | NOT NULL | - | Nivel del 50% del FVG - objetivo más importante de retracement | 20130.00 | `(gap_high + gap_low) / 2` |
| fvg_type | VARCHAR(10) | NOT NULL | - | Tipo: 'BULLISH' o 'BEARISH' | 'BULLISH', 'BEARISH' | BULLISH = gap alcista, BEARISH = gap bajista |
| significance | VARCHAR(10) | NOT NULL | - | Clasificación: 'MICRO', 'SMALL', 'MEDIUM', 'LARGE', 'EXTREME' | 'LARGE' | Basado en gap_size vs ATR |
| displacement_score | DOUBLE PRECISION | - | - | Score de energía del movimiento | 42.5 | Mayor = movimiento más fuerte |
| has_break_of_structure | BOOLEAN | - | false | TRUE si causó Break of Structure | true, false | Indicador ICT importante |
| status | VARCHAR(20) | - | 'UNMITIGATED' | Estado: 'UNMITIGATED', 'REDELIVERED', 'REBALANCED' | 'UNMITIGATED' | Lifecycle tracking |

### 4.2 detected_liquidity_pools

**Propósito**: Liquidity Pools (EQH/EQL, session levels) con lifecycle tracking.

**Primary Key**: `id`

| Column | Type | Nullable | Default | Description | Example | Business Rules |
|--------|------|----------|---------|-------------|---------|----------------|
| id | SERIAL | NOT NULL | AUTO_INCREMENT | Identificador único del LP | 1 | - |
| symbol | VARCHAR(20) | NOT NULL | - | Símbolo del contrato | 'NQZ24' | - |
| timeframe | VARCHAR(10) | NOT NULL | - | Timeframe de detección | '5min' | - |
| formation_time | TIMESTAMP | NOT NULL | - | Timestamp de formación (UTC naive) | '2024-11-05 14:30:00' | - |
| pool_type | VARCHAR(10) | NOT NULL | - | Tipo: 'EQH', 'EQL', 'NYH', 'NYL', 'ASH', 'ASL', 'LSH', 'LSL' | 'EQH' | EQH=Equal Highs, NYH=NY High, etc. |
| zone_low | DOUBLE PRECISION | NOT NULL | - | Límite inferior de la zona rectangular | 20120.00 | - |
| zone_high | DOUBLE PRECISION | NOT NULL | - | Límite superior de la zona rectangular | 20130.00 | - |
| modal_level | DOUBLE PRECISION | NOT NULL | - | Nivel con más touches (más tocado por precio) | 20125.00 | Precio más importante del pool |
| start_time | TIMESTAMP | NOT NULL | - | Inicio de la zona (primera vela) | '2024-11-05 14:00:00' | UTC naive |
| end_time | TIMESTAMP | NOT NULL | - | Fin de la zona (última vela) | '2024-11-05 16:30:00' | UTC naive |
| touch_count | INTEGER | - | 0 | Número de veces que el precio tocó el pool | 3 | >=2 para EQH/EQL válidos |
| sweep_detected | BOOLEAN | - | false | TRUE si se detectó sweep de liquidez | true, false | Sweep = stop-loss hunt |
| sweep_time | TIMESTAMP | - | - | Timestamp del sweep | '2024-11-05 17:15:00' | UTC naive |
| sweep_penetration | DOUBLE PRECISION | - | - | Puntos de penetración más allá del modal level | 8.5 | Qué tan profundo fue el sweep |
| status | VARCHAR(20) | - | 'UNMITIGATED' | 'UNMITIGATED', 'RESPECTED', 'SWEPT', 'MITIGATED' | 'SWEPT' | Lifecycle |

### 4.3 detected_order_blocks

**Propósito**: Order Blocks con quality classification y midpoints ICT.

**Primary Key**: `id`

| Column | Type | Nullable | Default | Description | Example | Business Rules |
|--------|------|----------|---------|-------------|---------|----------------|
| id | SERIAL | NOT NULL | AUTO_INCREMENT | Identificador único del OB | 1 | - |
| symbol | VARCHAR(20) | NOT NULL | - | Símbolo del contrato | 'NQZ24' | - |
| timeframe | VARCHAR(10) | NOT NULL | - | Timeframe de detección | '5min' | - |
| formation_time | TIMESTAMP | NOT NULL | - | Timestamp de formación (UTC naive) | '2024-11-05 14:30:00' | - |
| ob_high | DOUBLE PRECISION | NOT NULL | - | High de la vela OB | 20135.00 | - |
| ob_low | DOUBLE PRECISION | NOT NULL | - | Low de la vela OB | 20118.00 | - |
| ob_open | DOUBLE PRECISION | NOT NULL | - | Open de la vela OB | 20125.00 | - |
| ob_close | DOUBLE PRECISION | NOT NULL | - | Close de la vela OB | 20130.00 | - |
| ob_body_midpoint | DOUBLE PRECISION | NOT NULL | - | 50% del cuerpo = (open + close) / 2 | 20127.50 | `(ob_open + ob_close) / 2` |
| ob_range_midpoint | DOUBLE PRECISION | NOT NULL | - | 50% del rango = (high + low) / 2 | 20126.50 | `(ob_high + ob_low) / 2` |
| ob_type | VARCHAR(20) | NOT NULL | - | 'BULLISH', 'BEARISH', 'STRONG_BULLISH', 'STRONG_BEARISH' | 'BULLISH' | STRONG si impulso >1.5x threshold |
| quality | VARCHAR(10) | NOT NULL | - | 'HIGH', 'MEDIUM', 'LOW' | 'HIGH' | Basado en impulso + volumen + rango |
| impulse_move | DOUBLE PRECISION | NOT NULL | - | Tamaño del impulso en puntos | 52.5 | Movimiento fuerte después de OB |
| impulse_direction | VARCHAR(10) | NOT NULL | - | 'UP' o 'DOWN' | 'UP' | Dirección del impulso |
| status | VARCHAR(20) | - | 'ACTIVE' | 'ACTIVE', 'TESTED', 'BROKEN' | 'ACTIVE' | Lifecycle |

---

## 5. ETL Tables

(No incluido en detalle - ver `DATABASE_SCHEMA.md`)

- `etl_jobs` - Jobs de ETL
- `etl_job_logs` - Logs de jobs
- `processed_files` - Archivos procesados
- `candle_coverage` - Cobertura de datos

---

## 6. Authentication Tables

(No incluido en detalle - ver `DATABASE_SCHEMA.md`)

- `users` - Usuarios
- `invitations` - Códigos de invitación
- `password_reset_tokens` - Tokens de reset

---

## 7. Field Details

### 7.1 time_interval

**Tipo**: `TIMESTAMP WITH TIME ZONE` (PostgreSQL timestamptz)

**Zona horaria de almacenamiento**: UTC

**Formato**: `'YYYY-MM-DD HH:MM:SS+00'`

**Ejemplos por timeframe**:
```
candlestick_30s:   '2024-11-05 14:30:00+00', '2024-11-05 14:30:30+00'
candlestick_1min:  '2024-11-05 14:30:00+00', '2024-11-05 14:31:00+00'
candlestick_5min:  '2024-11-05 14:30:00+00', '2024-11-05 14:35:00+00'
candlestick_15min: '2024-11-05 14:30:00+00', '2024-11-05 14:45:00+00'
candlestick_1hr:   '2024-11-05 14:00:00+00', '2024-11-05 15:00:00+00'
candlestick_4hr:   '2024-11-05 12:00:00+00', '2024-11-05 16:00:00+00'
candlestick_daily: '2024-11-05 00:00:00+00', '2024-11-06 00:00:00+00'
candlestick_weekly:'2024-11-04 00:00:00+00' (lunes)
```

**Conversión a Eastern Time**:
```sql
time_interval AT TIME ZONE 'America/New_York'
-- Resultado: '2024-11-05 09:30:00' (sin zona horaria, en ET)

-- Ejemplo completo:
-- '2024-11-05 14:30:00+00' (UTC) → '2024-11-05 09:30:00' (ET, sin TZ)
-- '2024-11-05 18:00:00+00' (UTC) → '2024-11-05 13:00:00' (ET, sin TZ)
```

---

### 7.2 symbol

**Formato de contratos simples**: `{PRODUCTO}{MES}{AÑO}`

**Códigos de mes CME** (futuros):
```
F = Enero    (January)
G = Febrero  (February)
H = Marzo    (March)
J = Abril    (April)
K = Mayo     (May)
M = Junio    (June)
N = Julio    (July)
Q = Agosto   (August)
U = Septiembre (September)
V = Octubre  (October)
X = Noviembre (November)
Z = Diciembre (December)
```

**Ejemplos**:
- `'NQZ24'` = NQ Diciembre 2024
- `'NQH25'` = NQ Marzo 2025
- `'NQM25'` = NQ Junio 2025

**Formato de spreads**: `{CONTRATO1}-{CONTRATO2}`
- `'NQZ24-NQH25'` = Calendar spread (Diciembre 2024 - Marzo 2025)

---

### 7.3 POC vs real_POC

**Diferencias clave**:

| Aspecto | poc | real_poc |
|---------|-----|----------|
| Precisión | 1.0 punto (redondea con FLOOR) | 0.25 tick (exacto) |
| Fórmula | `FLOOR(price)` agrupa 4 ticks | Precio exacto sin redondeo |
| Velocidad | Más rápido de calcular | Más lento |
| Uso | Análisis macro, trading de swing | Análisis micro, entradas precisas |
| Ejemplo | 20125.0 (agrupa 20125.00, .25, .50, .75) | 20125.25 (tick exacto) |

**Cuándo usar cada uno**:
- **poc**: Para análisis de tendencia, identificación rápida de zonas de valor
- **real_poc**: Para entradas precisas, scalping, footprint analysis

---

### 7.4 oflow_detail / oflow_unit

**oflow_detail** (precisión 0.25 tick):
```json
{
  "20125.00": {"asks": 125, "bids": 98},
  "20125.25": {"asks": 87, "bids": 142},
  "20125.50": {"asks": 56, "bids": 203},
  "20125.75": {"asks": 45, "bids": 67}
}
```
- **asks**: Volumen de ventas agresivas (side='A', hit the bid)
- **bids**: Volumen de compras agresivas (side='B', hit the ask)
- **Uso**: Footprint charts, análisis tick-by-tick

**oflow_unit** (precisión 1.0 punto):
```json
{
  "20125": {"asks": 313, "bids": 510},
  "20126": {"asks": 156, "bids": 321}
}
```
- Agrupa 4 ticks de 0.25 en 1 punto completo
- **Uso**: Análisis más rápido, identificación de desequilibrios por punto

**Interpretación**:
- `bids > asks` → Presión compradora (alcista)
- `asks > bids` → Presión vendedora (bajista)
- Diferencia >2:1 → Desequilibrio significativo (imbalance)

---

### 7.5 Delta

**Fórmula**: `SUM(CASE WHEN side='B' THEN size WHEN side='A' THEN -size ELSE 0 END)`

**Interpretación**:
- **Delta > 0**: Más compradores agresivos (presión alcista)
- **Delta < 0**: Más vendedores agresivos (presión bajista)
- **Delta ≈ 0**: Equilibrio entre compradores y vendedores

**Divergencias importantes**:
- Precio sube + Delta negativo = Debilidad (posible reversión)
- Precio baja + Delta positivo = Fortaleza (posible reversión)

---

### 7.6 Absorción (asellers_uwick, abuyers_lwick, etc.)

**Conceptos clave**:

**side='A'**: Vendedor agresivo (hit the bid)
- Orden de mercado de venta
- "Toma" el precio bid más alto disponible

**side='B'**: Comprador agresivo (hit the ask)
- Orden de mercado de compra
- "Toma" el precio ask más bajo disponible

**Absorción en mechas**:

| Campo | Qué indica | Implicación |
|-------|------------|-------------|
| `asellers_uwick` alto | Vendedores absorbieron compradores en el high | Posible resistencia, rechazo de precio alto |
| `abuyers_lwick` alto | Compradores absorbieron vendedores en el low | Posible soporte, defensa de precio bajo |
| `abuyers_uwick` alto | Compradores cazando stops en high | Agresividad alcista extrema |
| `asellers_lwick` alto | Vendedores cazando stops en low | Agresividad bajista extrema |

---

## 8. Business Rules

### 8.1 NQ Futures Specifications

- **Tick size**: 0.25 puntos
- **Valor por tick**: $5 USD
- **1 punto**: 4 ticks = $20 USD
- **Precisión de precios**: Todos los precios son múltiplos de 0.25
- **Horario de trading**:
  - Domingo 18:00 ET - Viernes 17:00 ET
  - Cierre diario: 17:00-18:00 ET

---

### 8.2 Timezone Handling

**Regla crítica**:
- **Almacenamiento en candlestick tables**: `TIMESTAMP WITH TIME ZONE` (UTC)
- **Almacenamiento en pattern tables**: `TIMESTAMP WITHOUT TIME ZONE` (UTC naive)

**Conversión a Eastern Time**:
```sql
-- Para queries:
time_interval AT TIME ZONE 'America/New_York'

-- Para display:
-- Formato: "YYYY-MM-DD HH:MM:SS EST (HH:MM:SS UTC)"
-- Ejemplo: "2024-11-05 09:30:00 EST (14:30:00 UTC)"
```

**Importante**: `AT TIME ZONE` devuelve timestamp **sin zona horaria** (naive) en ET.

---

### 8.3 Active Contracts

**Regla de unicidad**: Solo un contrato puede tener `is_current = true` a la vez.

**Resolución de "NQ"**:
```sql
-- Patrón obligatorio cuando usuario menciona "NQ":
FROM candlestick_5min c
INNER JOIN active_contracts ac ON c.symbol = ac.symbol
WHERE ac.is_current = true
```

**Rollover period**:
- Durante rollover, `rollover_period = true` para contratos en transición
- Puede haber múltiples contratos activos (old + new)
- `is_current` se mueve del contrato viejo al nuevo cuando el volumen del nuevo supera al viejo

---

### 8.4 Calendar Spreads

**Identificación**: `is_spread = true` si el símbolo contiene `'-'`

**Backtesting**: Excluir spreads con:
```sql
WHERE is_spread = false
```

**Uso**: Spreads útiles para:
- Análisis de rollover periods
- Estrategias de arbitraje
- No útiles para backtesting de tendencia

---

### 8.5 Data Availability

**Período disponible**: Julio 2024 - Diciembre 2024

**Año actual para queries**: 2024 (NO usar 2025)

**Contratos incluidos**:
- NQU24 (Septiembre 2024)
- NQZ24 (Diciembre 2024)
- Spreads: NQU24-NQZ24 (durante rollover)

---

## Changelog

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2024-12-14 | Versión inicial - Catálogo completo de metadatos |

---

**Generado por**: Claude Code
**Última actualización**: 2024-12-14

**Referencias**:
- `DATABASE_SCHEMA.md` - Esquema completo de base de datos
- `CANDLESTICK_SCHEMA.md` - Esquema detallado de velas
- `ICT_DICTIONARY_v2.md` - Terminología ICT y Order Flow
