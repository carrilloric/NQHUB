# Detección de Fair Value Gaps (FVG) - Documentación Técnica

## 1. Introducción

### ¿Qué es un Fair Value Gap?

Un Fair Value Gap (FVG) es un concepto de price action que identifica zonas donde el mercado se movió tan rápidamente que dejó un "vacío" o desequilibrio de precio. Representa un área donde no hubo suficiente interacción entre compradores y vendedores, creando una ineficiencia que el mercado típicamente vuelve a visitar para "rellenar" o rebalancear.

### Importancia en Trading

- **Zonas de Soporte/Resistencia**: Los FVGs actúan como niveles dinámicos donde el precio tiende a reaccionar
- **Entrada en Tendencia**: Ofrecen puntos óptimos para entrar en la dirección de la tendencia principal
- **Gestión de Riesgo**: Proporcionan niveles claros para stop-loss y take-profit
- **Confirmación Institucional**: Indican actividad de grandes participantes del mercado

### Origen del Concepto

El concepto de FVG fue popularizado por ICT (Inner Circle Trader) como parte de los Smart Money Concepts, representando áreas donde las instituciones movieron el precio agresivamente.

## 2. Identificación de Fair Value Gaps

### El Patrón de 3 Velas

Un FVG se forma a través de un patrón específico de 3 velas consecutivas:

```
      Vela 1         Vela 2         Vela 3
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │         │   │         │   │         │
    │    ╷    │   │         │   │    ╷    │
    │    │    │   │    ▲    │   │    │    │
    ├────┼────┤   │    │    │   ├────┼────┤
    │    │    │   │    │    │   │    │    │
    │    ╵    │   │ Impulso │   │    ╵    │
    │         │   │         │   │         │
    └─────────┘   └─────────┘   └─────────┘
```

### FVG Bullish (Alcista)

**Condición**: `High de Vela 1 < Low de Vela 3`

- **Vela 1**: Inicio del movimiento alcista
- **Vela 2**: Vela de impulso fuerte alcista (gran cuerpo)
- **Vela 3**: Continuación alcista que NO toca el high de Vela 1
- **Gap**: Zona entre el High de Vela 1 y el Low de Vela 3
- **Función**: Actúa como SOPORTE en retrocesos

### FVG Bearish (Bajista)

**Condición**: `Low de Vela 1 > High de Vela 3`

- **Vela 1**: Inicio del movimiento bajista
- **Vela 2**: Vela de impulso fuerte bajista (gran cuerpo)
- **Vela 3**: Continuación bajista que NO toca el low de Vela 1
- **Gap**: Zona entre el Low de Vela 1 y el High de Vela 3
- **Función**: Actúa como RESISTENCIA en rebotes

## 3. Algoritmo de Detección

### SQL Query para Detección de FVGs

```sql
-- Detección de Fair Value Gaps en cualquier timeframe
WITH candles_with_neighbors AS (
    SELECT
        time_interval,
        time_interval AT TIME ZONE 'America/New_York' as et_time,
        symbol,
        open,
        high,
        low,
        close,
        volume,
        -- Vela anterior (Vela 1)
        LAG(high, 1) OVER (PARTITION BY symbol ORDER BY time_interval) as prev_high,
        LAG(low, 1) OVER (PARTITION BY symbol ORDER BY time_interval) as prev_low,
        LAG(close, 1) OVER (PARTITION BY symbol ORDER BY time_interval) as prev_close,
        -- Vela siguiente (Vela 3)
        LEAD(high, 1) OVER (PARTITION BY symbol ORDER BY time_interval) as next_high,
        LEAD(low, 1) OVER (PARTITION BY symbol ORDER BY time_interval) as next_low,
        LEAD(open, 1) OVER (PARTITION BY symbol ORDER BY time_interval) as next_open
    FROM candlestick_5min  -- Cambiar tabla según timeframe
    WHERE symbol = :symbol
      AND time_interval BETWEEN :start_time AND :end_time
),
fvg_detection AS (
    SELECT
        et_time as formation_time,
        symbol,
        -- Tipo de FVG
        CASE
            WHEN prev_high < next_low THEN 'BULLISH'
            WHEN prev_low > next_high THEN 'BEARISH'
            ELSE NULL
        END as fvg_type,

        -- Rango del FVG (zona de trading)
        CASE
            WHEN prev_high < next_low THEN prev_high  -- Bullish: desde high de vela 1
            WHEN prev_low > next_high THEN next_high   -- Bearish: desde high de vela 3
            ELSE NULL
        END as fvg_start,

        CASE
            WHEN prev_high < next_low THEN next_low    -- Bullish: hasta low de vela 3
            WHEN prev_low > next_high THEN prev_low    -- Bearish: hasta low de vela 1
            ELSE NULL
        END as fvg_end,

        -- Tamaño del gap
        CASE
            WHEN prev_high < next_low THEN next_low - prev_high
            WHEN prev_low > next_high THEN prev_low - next_high
            ELSE 0
        END as gap_size,

        -- Punto medio del FVG (nivel óptimo de entrada)
        CASE
            WHEN prev_high < next_low THEN (prev_high + next_low) / 2
            WHEN prev_low > next_high THEN (prev_low + next_high) / 2
            ELSE NULL
        END as fvg_midpoint,

        -- Contexto adicional
        high - low as candle2_range,
        volume as candle2_volume,

        -- Detalles de las 3 velas
        prev_high, prev_low, prev_close,
        low as candle2_low, high as candle2_high,
        next_high, next_low, next_open

    FROM candles_with_neighbors
    WHERE prev_high < next_low  -- Condición Bullish FVG
       OR prev_low > next_high   -- Condición Bearish FVG
)
SELECT
    formation_time,
    fvg_type,
    ROUND(fvg_start::numeric, 2) as fvg_start,
    ROUND(fvg_end::numeric, 2) as fvg_end,
    ROUND(gap_size::numeric, 2) as gap_size_points,
    ROUND(fvg_midpoint::numeric, 2) as fvg_midpoint,
    ROUND(candle2_range::numeric, 2) as impulse_candle_range,
    candle2_volume as impulse_candle_volume
FROM fvg_detection
WHERE gap_size > 0.25  -- Filtrar gaps muy pequeños (1 tick en NQ)
ORDER BY formation_time;
```

### Parámetros de Filtrado

- **Gap Mínimo**: 0.25 puntos (1 tick) para eliminar ruido
- **Gap Significativo**: > 2 puntos para FVGs de alta probabilidad
- **Timeframe**: Más confiables en 5min, 15min, 1hr
- **Volumen**: Mayor volumen en vela 2 = mayor validez

## 4. Casos Validados - 25 de Noviembre 2025

### Resumen de Detección

- **Total FVGs detectados**: 18
- **FVGs Bullish**: 13 (72%)
- **FVGs Bearish**: 5 (28%)
- **Timeframe**: 5 minutos
- **Símbolo**: NQZ5 (NQ Futures Diciembre 2025)

### FVGs Bullish Significativos

| Hora (ET) | Gap Start | Gap End | Tamaño | Midpoint | Observaciones |
|-----------|-----------|---------|--------|----------|---------------|
| 09:50 AM | 24729.25 | 24735.00 | 5.75 | 24732.13 | Reversión después de gap bearish |
| 11:15 AM | 24809.25 | 24827.75 | 18.50 | 24818.50 | Gap grande, inicio de rally |
| 12:15 PM | 24952.25 | 24965.00 | 12.75 | 24958.63 | Continuación de tendencia |
| 12:20 PM | 24967.50 | 24984.25 | 16.75 | 24975.88 | Aceleración alcista |
| 12:30 PM | 25017.00 | 25031.25 | 14.25 | 25024.13 | Pre-máximo del día |
| 13:45 PM | 25020.00 | 25033.50 | 13.50 | 25026.75 | Consolidación en máximos |
| 14:50 PM | 24974.00 | 24991.75 | 17.75 | 24982.88 | Recuperación post-corrección |
| 15:30 PM | 25053.00 | 25071.00 | 18.00 | 25062.00 | Rally de cierre |

### FVGs Bearish Significativos

| Hora (ET) | Gap Start | Gap End | Tamaño | Midpoint | Observaciones |
|-----------|-----------|---------|--------|----------|---------------|
| 09:40 AM | 24729.25 | 24835.50 | 106.25 | 24782.38 | **GAP MASIVO** - Caída de apertura |
| 13:55 PM | 25033.25 | 25033.50 | 0.25 | 25033.38 | Micro-gap en máximos |
| 14:15 PM | 24990.75 | 25002.75 | 12.00 | 24996.75 | Inicio de corrección |
| 14:35 PM | 24968.00 | 24968.25 | 0.25 | 24968.13 | Micro-gap continuación |

### Análisis de Patrones

1. **Sesgo Alcista Claro**: 72% de FVGs fueron bullish, indicando presión compradora dominante
2. **Gap Bearish Masivo**: El gap de 106 puntos a las 9:40 AM fue excepcional
3. **FVGs en Rally**: La mayoría de gaps bullish ocurrieron durante el rally de mediodía (11:15 AM - 12:30 PM)
4. **Micro-gaps**: Algunos gaps de 0.25 puntos son técnicamente válidos pero poco tradeable

## 5. Trading con Fair Value Gaps

### Estrategias de Entrada

#### Estrategia 1: Retroceso al FVG
1. Identificar FVG en dirección de la tendencia
2. Esperar retroceso del precio hacia el FVG
3. Entrada en el midpoint (50% del gap)
4. Stop loss debajo/arriba del FVG
5. Target en el swing high/low previo

#### Estrategia 2: FVG como Confirmación
1. Usar FVG para confirmar cambio de estructura
2. Entrada cuando el precio respeta el FVG
3. Agregar posición si el FVG se mantiene

### Gestión de Riesgo

- **Stop Loss**:
  - Bullish FVG: Por debajo del fvg_start
  - Bearish FVG: Por encima del fvg_end
- **Take Profit**:
  - TP1: 1:1 risk/reward
  - TP2: Siguiente FVG o nivel de liquidez
- **Invalidación**: FVG se invalida si el precio lo cruza completamente

## 6. Implementación Propuesta

### Schema de Base de Datos

```sql
-- Tabla para almacenar Fair Value Gaps detectados
CREATE TABLE fair_value_gaps (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    formation_time TIMESTAMPTZ NOT NULL,
    fvg_type VARCHAR(7) NOT NULL CHECK (fvg_type IN ('BULLISH', 'BEARISH')),

    -- Rango del FVG
    fvg_start DECIMAL(10, 2) NOT NULL,
    fvg_end DECIMAL(10, 2) NOT NULL,
    fvg_midpoint DECIMAL(10, 2) NOT NULL,
    gap_size DECIMAL(10, 2) NOT NULL,

    -- Estado del FVG
    status VARCHAR(20) DEFAULT 'UNFILLED' CHECK (status IN ('UNFILLED', 'PARTIAL', 'FILLED')),
    fill_percentage DECIMAL(5, 2) DEFAULT 0,
    first_test_time TIMESTAMPTZ,
    fill_time TIMESTAMPTZ,

    -- Contexto
    impulse_candle_range DECIMAL(10, 2),
    impulse_candle_volume INTEGER,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para búsquedas eficientes
CREATE INDEX idx_fvg_symbol_time ON fair_value_gaps(symbol, formation_time);
CREATE INDEX idx_fvg_type_status ON fair_value_gaps(fvg_type, status);
CREATE INDEX idx_fvg_price_range ON fair_value_gaps(fvg_start, fvg_end);

-- Trigger para actualizar updated_at
CREATE OR REPLACE FUNCTION update_fvg_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_fvg_timestamp
BEFORE UPDATE ON fair_value_gaps
FOR EACH ROW
EXECUTE FUNCTION update_fvg_timestamp();
```

### Función Python para Detección

```python
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from sqlalchemy import text
import numpy as np

class FairValueGapDetector:
    """
    Detector de Fair Value Gaps basado en el patrón de 3 velas
    """

    def __init__(
        self,
        min_gap_size: float = 0.25,
        significant_gap_size: float = 2.0,
        timeframe: str = '5min'
    ):
        self.min_gap_size = min_gap_size
        self.significant_gap_size = significant_gap_size
        self.timeframe = timeframe
        self.table_map = {
            '30s': 'candlestick_30s',
            '1min': 'candlestick_1min',
            '5min': 'candlestick_5min',
            '15min': 'candlestick_15min',
            '1hr': 'candlestick_1hr',
            '4hr': 'candlestick_4hr',
            'daily': 'candlestick_daily'
        }

    def detect_fvgs(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        db_session
    ) -> pd.DataFrame:
        """
        Detecta Fair Value Gaps en un rango de tiempo

        Returns:
            DataFrame con FVGs detectados
        """
        table_name = self.table_map.get(self.timeframe)
        if not table_name:
            raise ValueError(f"Timeframe {self.timeframe} no soportado")

        query = text(f"""
            WITH candles_with_neighbors AS (
                SELECT
                    time_interval,
                    time_interval AT TIME ZONE 'America/New_York' as et_time,
                    high, low, close, volume,
                    LAG(high, 1) OVER (ORDER BY time_interval) as prev_high,
                    LAG(low, 1) OVER (ORDER BY time_interval) as prev_low,
                    LEAD(high, 1) OVER (ORDER BY time_interval) as next_high,
                    LEAD(low, 1) OVER (ORDER BY time_interval) as next_low
                FROM {table_name}
                WHERE symbol = :symbol
                  AND time_interval BETWEEN :start_time AND :end_time
            )
            SELECT
                et_time as formation_time,
                CASE
                    WHEN prev_high < next_low THEN 'BULLISH'
                    WHEN prev_low > next_high THEN 'BEARISH'
                END as fvg_type,
                CASE
                    WHEN prev_high < next_low THEN prev_high
                    WHEN prev_low > next_high THEN next_high
                END as fvg_start,
                CASE
                    WHEN prev_high < next_low THEN next_low
                    WHEN prev_low > next_high THEN prev_low
                END as fvg_end,
                CASE
                    WHEN prev_high < next_low THEN next_low - prev_high
                    WHEN prev_low > next_high THEN prev_low - next_high
                END as gap_size,
                high - low as impulse_range,
                volume as impulse_volume
            FROM candles_with_neighbors
            WHERE (prev_high < next_low OR prev_low > next_high)
              AND CASE
                    WHEN prev_high < next_low THEN next_low - prev_high
                    WHEN prev_low > next_high THEN prev_low - next_high
                  END >= :min_gap
        """)

        result = db_session.execute(
            query,
            {
                'symbol': symbol,
                'start_time': start_time,
                'end_time': end_time,
                'min_gap': self.min_gap_size
            }
        )

        df = pd.DataFrame(result.fetchall())

        if not df.empty:
            # Calcular midpoint
            df['fvg_midpoint'] = (df['fvg_start'] + df['fvg_end']) / 2

            # Clasificar por tamaño
            df['significance'] = df['gap_size'].apply(
                lambda x: 'HIGH' if x >= self.significant_gap_size else 'NORMAL'
            )

            # Ordenar por tiempo
            df = df.sort_values('formation_time')

        return df

    def check_fvg_status(
        self,
        fvg: Dict,
        current_price: float
    ) -> str:
        """
        Verifica el estado de un FVG con respecto al precio actual

        Returns:
            'UNFILLED', 'PARTIAL', or 'FILLED'
        """
        if fvg['fvg_type'] == 'BULLISH':
            if current_price > fvg['fvg_end']:
                return 'UNFILLED'
            elif current_price < fvg['fvg_start']:
                return 'FILLED'
            else:
                return 'PARTIAL'
        else:  # BEARISH
            if current_price < fvg['fvg_start']:
                return 'UNFILLED'
            elif current_price > fvg['fvg_end']:
                return 'FILLED'
            else:
                return 'PARTIAL'

    def calculate_fill_percentage(
        self,
        fvg: Dict,
        price_low: float,
        price_high: float
    ) -> float:
        """
        Calcula qué porcentaje del FVG ha sido rellenado
        """
        gap_range = abs(fvg['fvg_end'] - fvg['fvg_start'])

        if fvg['fvg_type'] == 'BULLISH':
            # Para bullish, medimos desde fvg_end hacia fvg_start
            if price_low <= fvg['fvg_start']:
                return 100.0
            elif price_low >= fvg['fvg_end']:
                return 0.0
            else:
                filled = fvg['fvg_end'] - price_low
                return (filled / gap_range) * 100
        else:  # BEARISH
            # Para bearish, medimos desde fvg_start hacia fvg_end
            if price_high >= fvg['fvg_end']:
                return 100.0
            elif price_high <= fvg['fvg_start']:
                return 0.0
            else:
                filled = price_high - fvg['fvg_start']
                return (filled / gap_range) * 100

    def find_trading_opportunities(
        self,
        fvgs: pd.DataFrame,
        current_price: float,
        trend_direction: str = 'BULLISH'
    ) -> pd.DataFrame:
        """
        Identifica FVGs que presentan oportunidades de trading
        """
        opportunities = []

        for _, fvg in fvgs.iterrows():
            # Solo buscar FVGs en dirección de la tendencia
            if fvg['fvg_type'] != trend_direction:
                continue

            # Verificar si el precio está cerca del FVG
            distance_to_midpoint = abs(current_price - fvg['fvg_midpoint'])
            gap_size = fvg['gap_size']

            # Si el precio está dentro de 2x el tamaño del gap
            if distance_to_midpoint <= gap_size * 2:
                opportunity = {
                    'formation_time': fvg['formation_time'],
                    'fvg_type': fvg['fvg_type'],
                    'entry_level': fvg['fvg_midpoint'],
                    'stop_loss': fvg['fvg_start'] if trend_direction == 'BULLISH' else fvg['fvg_end'],
                    'distance_to_entry': distance_to_midpoint,
                    'gap_size': gap_size,
                    'significance': fvg['significance']
                }
                opportunities.append(opportunity)

        return pd.DataFrame(opportunities)

# Ejemplo de uso
if __name__ == "__main__":
    detector = FairValueGapDetector(
        min_gap_size=0.25,
        significant_gap_size=5.0,
        timeframe='5min'
    )

    # Detectar FVGs
    fvgs = detector.detect_fvgs(
        symbol='NQZ5',
        start_time=datetime(2025, 11, 25, 14, 0),  # 9 AM ET
        end_time=datetime(2025, 11, 25, 21, 0),    # 4 PM ET
        db_session=session
    )

    print(f"FVGs detectados: {len(fvgs)}")
    print(f"Bullish: {len(fvgs[fvgs['fvg_type'] == 'BULLISH'])}")
    print(f"Bearish: {len(fvgs[fvgs['fvg_type'] == 'BEARISH'])}")
```

## 7. Validación y Backtesting

### Métricas de Efectividad

Para validar la efectividad de los FVGs, medimos:

1. **Fill Rate**: Porcentaje de FVGs que se rellenan
2. **Time to Fill**: Tiempo promedio hasta el relleno
3. **Respect Rate**: Frecuencia con que actúan como soporte/resistencia
4. **Win Rate**: Éxito de trades basados en FVGs

### Query de Validación

```sql
-- Analizar efectividad de FVGs históricos
WITH fvg_performance AS (
    SELECT
        f.formation_time,
        f.fvg_type,
        f.fvg_start,
        f.fvg_end,
        f.gap_size,
        -- Buscar si el precio volvió al FVG
        EXISTS (
            SELECT 1 FROM candlestick_5min c
            WHERE c.symbol = f.symbol
              AND c.time_interval > f.formation_time
              AND c.time_interval <= f.formation_time + interval '24 hours'
              AND (
                  (f.fvg_type = 'BULLISH' AND c.low <= f.fvg_midpoint) OR
                  (f.fvg_type = 'BEARISH' AND c.high >= f.fvg_midpoint)
              )
        ) as was_tested,
        -- Tiempo hasta el test
        (
            SELECT MIN(c.time_interval) - f.formation_time
            FROM candlestick_5min c
            WHERE c.symbol = f.symbol
              AND c.time_interval > f.formation_time
              AND (
                  (f.fvg_type = 'BULLISH' AND c.low <= f.fvg_midpoint) OR
                  (f.fvg_type = 'BEARISH' AND c.high >= f.fvg_midpoint)
              )
        ) as time_to_test
    FROM fair_value_gaps f
    WHERE f.gap_size >= 2.0  -- Solo gaps significativos
)
SELECT
    fvg_type,
    COUNT(*) as total_fvgs,
    SUM(CASE WHEN was_tested THEN 1 ELSE 0 END) as tested_fvgs,
    ROUND(100.0 * SUM(CASE WHEN was_tested THEN 1 ELSE 0 END) / COUNT(*), 2) as test_rate,
    AVG(EXTRACT(EPOCH FROM time_to_test) / 3600) as avg_hours_to_test
FROM fvg_performance
GROUP BY fvg_type;
```

## 8. Comparación con Otros Conceptos

### FVG vs Imbalance
- **FVG**: Gap visible entre velas en el gráfico
- **Imbalance**: Desequilibrio en el order flow (no siempre visible)

### FVG vs Liquidity Void
- **FVG**: Basado en estructura de 3 velas
- **Liquidity Void**: Área sin trading significativo (puede ser más amplia)

### FVG vs Order Block
- **FVG**: Zona de desequilibrio para retests
- **Order Block**: Última vela antes de movimiento fuerte (origen)

## 9. Limitaciones y Consideraciones

### Limitaciones del Algoritmo

1. **Solo detecta estructura**: No considera contexto de mercado
2. **Timeframe dependency**: Efectividad varía según timeframe
3. **No considera volumen profile**: Podría mejorarse con datos de profundidad
4. **Gaps muy pequeños**: Pueden ser ruido en mercados volátiles

### Mejoras Futuras

1. **Machine Learning**: Entrenar modelo para predecir FVGs más probables de funcionar
2. **Contexto de Mercado**: Incorporar tendencia, volatilidad, hora del día
3. **Multi-timeframe**: Validar FVGs con timeframes superiores
4. **Order Flow**: Combinar con datos de delta y footprint

## 10. Referencias

- ICT (Inner Circle Trader) - Conceptos originales de FVG
- Smart Money Concepts Trading
- ATAS Platform - Visualización de gaps e ineficiencias
- CME Group - Microestructura de mercados de futuros

---

*Documento creado: 2025-11-29*
*Última actualización: 2025-11-29*
*Autor: NQHUB Development Team*

### Changelog:
- **v1.0** (2025-11-29): Versión inicial con 18 FVGs validados del 25 de noviembre