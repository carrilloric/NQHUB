# Candlestick Schema

Esquema completo de las tablas de velas (candlestick) para datos de trading NQ Futures.

## Tablas Disponibles

Se crean 8 tablas con el mismo esquema para diferentes timeframes:
- `candlestick_30s`
- `candlestick_1min`
- `candlestick_5min`
- `candlestick_15min`
- `candlestick_1hr`
- `candlestick_4hr`
- `candlestick_daily`
- `candlestick_weekly`

## Primary Key

Clave compuesta: `(time_interval, symbol)`

## Campos (33 columnas)

### Identificacion Temporal (1 columna)

| Campo | Tipo | Nullable | Descripcion |
|-------|------|----------|-------------|
| `time_interval` | TIMESTAMP WITH TIME ZONE | NOT NULL | Inicio del intervalo temporal |

**Fuente:** `time_bucket('{interval}'::interval, ts_event)` de TimescaleDB

---

### Tracking de Simbolo (3 columnas)

| Campo | Tipo | Default | Descripcion |
|-------|------|---------|-------------|
| `symbol` | VARCHAR(20) | NOT NULL | Simbolo del instrumento (ej: NQH24, NQM24) |
| `is_spread` | BOOLEAN | false | True si es calendar spread (ej: NQM4-NQU4) |
| `is_rollover_period` | BOOLEAN | false | True si esta en periodo de rollover |

**Formula `is_spread`:** `'-' in symbol`

---

### OHLCV (5 columnas)

| Campo | Tipo | Formula | Descripcion |
|-------|------|---------|-------------|
| `open` | FLOAT | `(array_agg(price ORDER BY ts_event))[1]` | Primer precio del intervalo |
| `high` | FLOAT | `MAX(price)` | Precio maximo del intervalo |
| `low` | FLOAT | `MIN(price)` | Precio minimo del intervalo |
| `close` | FLOAT | `(array_agg(price ORDER BY ts_event DESC))[1]` | Ultimo precio del intervalo |
| `volume` | FLOAT | `SUM(size)` | Volumen total de contratos |

---

### Point of Control - Regular (5 columnas)

POC calculado con precision de 1.0 punto (agrupando por `FLOOR(price)`).

| Campo | Tipo | Formula | Descripcion |
|-------|------|---------|-------------|
| `poc` | FLOAT | `FLOOR(price)` del nivel con `MAX(SUM(size))` | Precio del POC (1.0 punto precision) |
| `poc_volume` | FLOAT | `SUM(size)` en el nivel POC | Volumen total en el POC |
| `poc_percentage` | FLOAT | `(poc_volume / volume) * 100` | % del volumen total en el POC |
| `poc_location` | TEXT | Ver formula abajo | Zona donde esta el POC |
| `poc_position` | FLOAT | `(poc - low) / (high - low)` | Posicion relativa (0=low, 1=high) |

**Formula `poc_location`:**
```sql
CASE
    WHEN poc > GREATEST(open, close) THEN 'upper_wick'
    WHEN poc < LEAST(open, close) THEN 'lower_wick'
    ELSE 'body'
END
```

---

### Point of Control - Real (4 columnas)

POC calculado con precision exacta de tick (0.25 puntos).

| Campo | Tipo | Formula | Descripcion |
|-------|------|---------|-------------|
| `real_poc` | FLOAT | `price` exacto del nivel con `MAX(SUM(size))` | Precio exacto del POC (0.25 tick) |
| `real_poc_volume` | FLOAT | `SUM(size)` en el nivel real POC | Volumen en el POC real |
| `real_poc_percentage` | FLOAT | `(real_poc_volume / volume) * 100` | % del volumen en el POC real |
| `real_poc_location` | TEXT | Misma logica que `poc_location` | Zona donde esta el POC real |

---

### Estructura de Vela (6 columnas)

| Campo | Tipo | Formula | Descripcion |
|-------|------|---------|-------------|
| `upper_wick` | FLOAT | `high - GREATEST(open, close)` | Tamano de mecha superior (puntos) |
| `lower_wick` | FLOAT | `LEAST(open, close) - low` | Tamano de mecha inferior (puntos) |
| `body` | FLOAT | `ABS(close - open)` | Tamano del cuerpo (puntos) |
| `wick_ratio` | FLOAT | `(upper_wick + lower_wick) / body` | Ratio mechas/cuerpo (NULL si body=0) |
| `rel_uw` | FLOAT | `upper_wick / (high - low)` | Mecha superior relativa al rango (0-1) |
| `rel_lw` | FLOAT | `lower_wick / (high - low)` | Mecha inferior relativa al rango (0-1) |

**Nota:** `wick_ratio`, `rel_uw`, `rel_lw` son NULL cuando el divisor es 0.

---

### Distribucion de Volumen (3 columnas)

Volumen distribuido por zona de la vela.

| Campo | Tipo | Formula | Descripcion |
|-------|------|---------|-------------|
| `upper_wick_volume` | FLOAT | `SUM(size) WHERE price > GREATEST(open,close) AND price <= high` | Volumen en mecha superior |
| `lower_wick_volume` | FLOAT | `SUM(size) WHERE price < LEAST(open,close) AND price >= low` | Volumen en mecha inferior |
| `body_volume` | FLOAT | `SUM(size) WHERE price >= LEAST(open,close) AND price <= GREATEST(open,close)` | Volumen en el cuerpo |

---

### Indicadores de Absorcion (4 columnas)

Volumen agresivo (market orders) en las mechas.

| Campo | Tipo | Formula | Descripcion |
|-------|------|---------|-------------|
| `asellers_uwick` | FLOAT | `SUM(size) WHERE side='A' AND price > GREATEST(open,close)` | Vendedores agresivos en mecha superior |
| `asellers_lwick` | FLOAT | `SUM(size) WHERE side='A' AND price < LEAST(open,close)` | Vendedores agresivos en mecha inferior |
| `abuyers_uwick` | FLOAT | `SUM(size) WHERE side='B' AND price > GREATEST(open,close)` | Compradores agresivos en mecha superior |
| `abuyers_lwick` | FLOAT | `SUM(size) WHERE side='B' AND price < LEAST(open,close)` | Compradores agresivos en mecha inferior |

**Interpretacion:**
- `asellers_uwick` alto: Vendedores absorbieron compradores en el high (resistencia)
- `abuyers_lwick` alto: Compradores absorbieron vendedores en el low (soporte)

---

### Order Flow (3 columnas)

| Campo | Tipo | Formula | Descripcion |
|-------|------|---------|-------------|
| `delta` | FLOAT | `SUM(CASE WHEN side='B' THEN size WHEN side='A' THEN -size ELSE 0 END)` | Delta neto (compras - ventas) |
| `oflow_detail` | JSONB | Ver estructura abajo | Detalle de order flow por tick (0.25) |
| `oflow_unit` | JSONB | Ver estructura abajo | Order flow agregado por punto (1.0) |

**Estructura `oflow_detail`** (precision 0.25):
```json
{
  "21450.25": {"asks": 150, "bids": 200},
  "21450.50": {"asks": 80, "bids": 120},
  "21450.75": {"asks": 95, "bids": 85}
}
```

**Estructura `oflow_unit`** (precision 1.0):
```json
{
  "21450": {"asks": 325, "bids": 405},
  "21451": {"asks": 280, "bids": 310}
}
```

---

### Metadata (1 columna)

| Campo | Tipo | Formula | Descripcion |
|-------|------|---------|-------------|
| `tick_count` | INTEGER | `COUNT(*)` de ticks | Numero de ticks que componen la vela |

---

## Indices

| Nombre | Columna(s) | Tipo |
|--------|------------|------|
| `{timeframe}_pkey` | `(time_interval, symbol)` | Primary Key |
| `idx_{timeframe}_time` | `time_interval` | B-tree |
| `idx_{timeframe}_symbol` | `symbol` | B-tree |
| `idx_{timeframe}_rollover` | `is_rollover_period` | B-tree |

---

## Tabla Fuente: market_data_ticks

Los candlesticks se construyen a partir de la tabla `market_data_ticks`:

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `ts_event` | TIMESTAMP WITH TIME ZONE | Timestamp del tick |
| `symbol` | VARCHAR(20) | Simbolo |
| `price` | FLOAT | Precio del tick |
| `size` | INTEGER | Tamano (contratos) |
| `side` | CHAR(1) | 'B' = Buy (bid), 'A' = Ask (sell) |

---

## Notas Importantes

1. **TimescaleDB**: Las tablas son hypertables particionadas por tiempo para mejor rendimiento.

2. **Upsert**: Los candles usan `ON CONFLICT DO UPDATE` para permitir recalculo sin duplicados.

3. **Precision de Precio**:
   - NQ Futures tick size = 0.25 puntos
   - `poc` usa precision de 1.0 punto (agrupa 4 ticks)
   - `real_poc` usa precision exacta de 0.25

4. **Side Values**:
   - `'B'` = Buyer initiated (hit the ask)
   - `'A'` = Seller initiated (hit the bid)

5. **NULL Handling**: Campos de ratio son NULL cuando el divisor es 0 para evitar division por cero.

---

## Archivo de Migracion

`backend/alembic/versions/20251102_0904-0cac37df50d1_create_candlestick_tables.py`

## Servicio de Construccion

`backend/app/etl/services/candle_builder.py`
