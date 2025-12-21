"""
Vanna.AI tool for NL→SQL with RAG learning
"""
from typing import Optional, Dict, Any, List
import logging
import os
from sqlalchemy import text

logger = logging.getLogger(__name__)

try:
    from vanna.chromadb import ChromaDB_VectorStore
    from vanna.anthropic import Anthropic_Chat
    VANNA_AVAILABLE = True
except ImportError:
    VANNA_AVAILABLE = False
    logger.warning("Vanna not installed. NL→SQL features will be disabled.")

from app.assistant.config import assistant_config
from app.db.session import SessionLocal


class VannaNQHub:
    """Vanna.AI client customized for NQHUB database"""

    def __init__(self):
        if not assistant_config.VANNA_ENABLED or not VANNA_AVAILABLE:
            logger.warning("Vanna is disabled or not available")
            self.vn = None
            return

        try:
            # Ensure ChromaDB path exists
            os.makedirs(assistant_config.VANNA_CHROMA_PATH, exist_ok=True)

            # Create Vanna instance combining ChromaDB + Anthropic
            class VannaClient(ChromaDB_VectorStore, Anthropic_Chat):
                def __init__(self, config=None):
                    ChromaDB_VectorStore.__init__(self, config=config)
                    Anthropic_Chat.__init__(self, config=config)

            self.vn = VannaClient(config={
                'api_key': assistant_config.CLAUDE_API_KEY,
                'model': assistant_config.CLAUDE_MODEL,
                'path': assistant_config.VANNA_CHROMA_PATH,
            })

            logger.info("Vanna initialized successfully")

            # Train with NQHUB schema on first init
            self._train_schema()

        except Exception as e:
            logger.error(f"Failed to initialize Vanna: {e}")
            self.vn = None

    def _train_schema(self):
        """Train Vanna with NQHUB database schema"""
        if not self.vn:
            return

        # Complete NQHUB schema DDL for training
        schema_ddl = """
        -- Market Data - Multiple Timeframes
        -- NOTE: All candlestick tables share the same schema
        -- IMPORTANT: time_interval is TIMESTAMP WITH TIME ZONE stored in UTC
        -- User queries referring to dates/times are in Eastern Time (America/New_York)
        -- Use AT TIME ZONE conversion for accurate date filtering
        CREATE TABLE candlestick_1min (
            -- Primary key
            time_interval TIMESTAMP WITH TIME ZONE,  -- Stored in UTC
            symbol VARCHAR(20),

            -- Symbol tracking
            is_spread BOOLEAN,
            is_rollover_period BOOLEAN,

            -- OHLCV
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume DOUBLE PRECISION,

            -- Point of Control - Regular
            poc DOUBLE PRECISION,
            poc_volume DOUBLE PRECISION,
            poc_percentage DOUBLE PRECISION,
            poc_location VARCHAR,
            poc_position DOUBLE PRECISION,

            -- Point of Control - Real (exact 0.25 tick)
            real_poc DOUBLE PRECISION,
            real_poc_volume DOUBLE PRECISION,
            real_poc_percentage DOUBLE PRECISION,
            real_poc_location VARCHAR,

            -- Candle structure
            upper_wick DOUBLE PRECISION,
            lower_wick DOUBLE PRECISION,
            body DOUBLE PRECISION,
            wick_ratio DOUBLE PRECISION,
            rel_uw DOUBLE PRECISION,
            rel_lw DOUBLE PRECISION,

            -- Volume distribution
            upper_wick_volume DOUBLE PRECISION,
            lower_wick_volume DOUBLE PRECISION,
            body_volume DOUBLE PRECISION,

            -- Absorption indicators
            asellers_uwick DOUBLE PRECISION,
            asellers_lwick DOUBLE PRECISION,
            abuyers_uwick DOUBLE PRECISION,
            abuyers_lwick DOUBLE PRECISION,

            -- Order flow
            delta DOUBLE PRECISION,
            oflow_detail JSONB,  -- Footprint data at 0.25 tick granularity
            oflow_unit JSONB,    -- Footprint data at 1 point granularity

            -- Metadata
            tick_count INTEGER
        );

        -- Candlestick 5-Minute Table
        -- Velas de 5 minutos con OHLCV, POC, estructura, volumen distribuido, absorción y order flow
        -- Referencia completa: docs/DATA_DICTIONARY.md
        CREATE TABLE candlestick_5min (
            -- Identificación temporal y símbolo
            time_interval TIMESTAMP WITH TIME ZONE,  -- Inicio del intervalo en UTC. Formato: 'YYYY-MM-DD HH:MM:SS+00'. Para ET: AT TIME ZONE 'America/New_York'
            symbol VARCHAR(20),                      -- Símbolo del contrato. Formato: {PROD}{MES}{AÑO} (ej: NQZ24=Dic 2024). Mes: H=Mar,M=Jun,U=Sep,Z=Dic
            is_spread BOOLEAN,                       -- TRUE si es calendar spread (contiene '-'). Ej: 'NQZ24-NQH25'
            is_rollover_period BOOLEAN,              -- TRUE durante transición entre contratos

            -- OHLCV: Datos básicos de precio y volumen
            open DOUBLE PRECISION,   -- Precio de apertura - primer precio del intervalo. Fórmula: (array_agg(price ORDER BY ts_event))[1]
            high DOUBLE PRECISION,   -- Precio máximo alcanzado. Fórmula: MAX(price)
            low DOUBLE PRECISION,    -- Precio mínimo alcanzado. Fórmula: MIN(price)
            close DOUBLE PRECISION,  -- Precio de cierre - último precio. Fórmula: (array_agg(price ORDER BY ts_event DESC))[1]
            volume DOUBLE PRECISION, -- Volumen total de contratos negociados. Fórmula: SUM(size)

            -- Point of Control (POC) - Precisión 1.0 punto
            -- POC = nivel de precio con mayor volumen negociado
            poc DOUBLE PRECISION,           -- POC redondeado a 1.0 punto. Fórmula: FLOOR(price) con MAX(SUM(size)). Agrupa 4 ticks de 0.25
            poc_volume DOUBLE PRECISION,    -- Volumen total en el POC. Fórmula: SUM(size) en nivel POC
            poc_percentage DOUBLE PRECISION, -- % del volumen en el POC. Fórmula: (poc_volume/volume)*100
            poc_location VARCHAR,           -- Zona del POC: 'upper_wick', 'body', 'lower_wick'
            poc_position DOUBLE PRECISION,  -- Posición relativa del POC (0-1). Fórmula: (poc-low)/(high-low)

            -- Point of Control Real - Precisión exacta 0.25 tick
            real_poc DOUBLE PRECISION,           -- POC exacto sin redondeo (tick exacto de 0.25). Más preciso que 'poc'
            real_poc_volume DOUBLE PRECISION,    -- Volumen en el POC real (tick exacto)
            real_poc_percentage DOUBLE PRECISION, -- % del volumen en POC real
            real_poc_location VARCHAR,           -- Zona del POC real: 'upper_wick', 'body', 'lower_wick'

            -- Estructura de vela (geometría)
            upper_wick DOUBLE PRECISION,  -- Tamaño de mecha superior en puntos. Fórmula: high - GREATEST(open,close)
            lower_wick DOUBLE PRECISION,  -- Tamaño de mecha inferior en puntos. Fórmula: LEAST(open,close) - low
            body DOUBLE PRECISION,        -- Tamaño del cuerpo en puntos. Fórmula: ABS(close-open)
            wick_ratio DOUBLE PRECISION,  -- Ratio mechas/cuerpo. Fórmula: (upper_wick+lower_wick)/body. NULL si body=0
            rel_uw DOUBLE PRECISION,      -- Mecha superior relativa (0-1). Fórmula: upper_wick/(high-low)
            rel_lw DOUBLE PRECISION,      -- Mecha inferior relativa (0-1). Fórmula: lower_wick/(high-low)

            -- Distribución de volumen por zona
            upper_wick_volume DOUBLE PRECISION,  -- Volumen en mecha superior. Fórmula: SUM(size) WHERE price > GREATEST(open,close)
            lower_wick_volume DOUBLE PRECISION,  -- Volumen en mecha inferior. Fórmula: SUM(size) WHERE price < LEAST(open,close)
            body_volume DOUBLE PRECISION,        -- Volumen en el cuerpo. Fórmula: SUM(size) en rango del cuerpo

            -- Absorción: Órdenes agresivas (market orders) en mechas
            -- side='A': Vendedor agresivo (hit the bid) | side='B': Comprador agresivo (hit the ask)
            asellers_uwick DOUBLE PRECISION,  -- Vendedores agresivos en mecha superior (side='A'). Indica absorción de compradores en el high
            asellers_lwick DOUBLE PRECISION,  -- Vendedores agresivos en mecha inferior (side='A')
            abuyers_uwick DOUBLE PRECISION,   -- Compradores agresivos en mecha superior (side='B')
            abuyers_lwick DOUBLE PRECISION,   -- Compradores agresivos en mecha inferior (side='B'). Indica absorción de vendedores en el low

            -- Order Flow: Flujo de órdenes por nivel de precio
            delta DOUBLE PRECISION,  -- Delta neto: compras - ventas. Fórmula: SUM(CASE WHEN side='B' THEN size WHEN side='A' THEN -size). Positivo=presión compradora
            oflow_detail JSONB,      -- Order flow por tick (0.25). Formato: {"20125.25": {"asks": 150, "bids": 200}}
            oflow_unit JSONB,        -- Order flow por punto (1.0). Formato: {"20125": {"asks": 325, "bids": 405}}

            -- Metadata
            tick_count INTEGER  -- Número de ticks que componen la vela. Fórmula: COUNT(*)
        );

        CREATE TABLE candlestick_15min (
            -- Primary key
            time_interval TIMESTAMP WITH TIME ZONE,  -- Stored in UTC
            symbol VARCHAR(20),

            -- Symbol tracking
            is_spread BOOLEAN,
            is_rollover_period BOOLEAN,

            -- OHLCV
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume DOUBLE PRECISION,

            -- Point of Control - Regular
            poc DOUBLE PRECISION,
            poc_volume DOUBLE PRECISION,
            poc_percentage DOUBLE PRECISION,
            poc_location VARCHAR,
            poc_position DOUBLE PRECISION,

            -- Point of Control - Real (exact 0.25 tick)
            real_poc DOUBLE PRECISION,
            real_poc_volume DOUBLE PRECISION,
            real_poc_percentage DOUBLE PRECISION,
            real_poc_location VARCHAR,

            -- Candle structure
            upper_wick DOUBLE PRECISION,
            lower_wick DOUBLE PRECISION,
            body DOUBLE PRECISION,
            wick_ratio DOUBLE PRECISION,
            rel_uw DOUBLE PRECISION,
            rel_lw DOUBLE PRECISION,

            -- Volume distribution
            upper_wick_volume DOUBLE PRECISION,
            lower_wick_volume DOUBLE PRECISION,
            body_volume DOUBLE PRECISION,

            -- Absorption indicators
            asellers_uwick DOUBLE PRECISION,
            asellers_lwick DOUBLE PRECISION,
            abuyers_uwick DOUBLE PRECISION,
            abuyers_lwick DOUBLE PRECISION,

            -- Order flow
            delta DOUBLE PRECISION,
            oflow_detail JSONB,  -- Footprint data at 0.25 tick granularity
            oflow_unit JSONB,    -- Footprint data at 1 point granularity

            -- Metadata
            tick_count INTEGER
        );

        CREATE TABLE candlestick_1h (
            -- Primary key
            time_interval TIMESTAMP WITH TIME ZONE,  -- Stored in UTC
            symbol VARCHAR(20),

            -- Symbol tracking
            is_spread BOOLEAN,
            is_rollover_period BOOLEAN,

            -- OHLCV
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume DOUBLE PRECISION,

            -- Point of Control - Regular
            poc DOUBLE PRECISION,
            poc_volume DOUBLE PRECISION,
            poc_percentage DOUBLE PRECISION,
            poc_location VARCHAR,
            poc_position DOUBLE PRECISION,

            -- Point of Control - Real (exact 0.25 tick)
            real_poc DOUBLE PRECISION,
            real_poc_volume DOUBLE PRECISION,
            real_poc_percentage DOUBLE PRECISION,
            real_poc_location VARCHAR,

            -- Candle structure
            upper_wick DOUBLE PRECISION,
            lower_wick DOUBLE PRECISION,
            body DOUBLE PRECISION,
            wick_ratio DOUBLE PRECISION,
            rel_uw DOUBLE PRECISION,
            rel_lw DOUBLE PRECISION,

            -- Volume distribution
            upper_wick_volume DOUBLE PRECISION,
            lower_wick_volume DOUBLE PRECISION,
            body_volume DOUBLE PRECISION,

            -- Absorption indicators
            asellers_uwick DOUBLE PRECISION,
            asellers_lwick DOUBLE PRECISION,
            abuyers_uwick DOUBLE PRECISION,
            abuyers_lwick DOUBLE PRECISION,

            -- Order flow
            delta DOUBLE PRECISION,
            oflow_detail JSONB,  -- Footprint data at 0.25 tick granularity
            oflow_unit JSONB,    -- Footprint data at 1 point granularity

            -- Metadata
            tick_count INTEGER
        );

        -- ==================== CANDLESTICK TABLES (8 TIMEFRAMES) ====================

        CREATE TABLE candlestick_30s (
            -- Primary key
            time_interval TIMESTAMP WITH TIME ZONE,  -- Stored in UTC
            symbol VARCHAR(20),

            -- Symbol tracking
            is_spread BOOLEAN,
            is_rollover_period BOOLEAN,

            -- OHLCV
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume DOUBLE PRECISION,

            -- Point of Control - Regular
            poc DOUBLE PRECISION,
            poc_volume DOUBLE PRECISION,
            poc_percentage DOUBLE PRECISION,
            poc_location VARCHAR,
            poc_position DOUBLE PRECISION,

            -- Point of Control - Real (exact 0.25 tick)
            real_poc DOUBLE PRECISION,
            real_poc_volume DOUBLE PRECISION,
            real_poc_percentage DOUBLE PRECISION,
            real_poc_location VARCHAR,

            -- Candle structure
            upper_wick DOUBLE PRECISION,
            lower_wick DOUBLE PRECISION,
            body DOUBLE PRECISION,
            wick_ratio DOUBLE PRECISION,
            rel_uw DOUBLE PRECISION,
            rel_lw DOUBLE PRECISION,

            -- Volume distribution
            upper_wick_volume DOUBLE PRECISION,
            lower_wick_volume DOUBLE PRECISION,
            body_volume DOUBLE PRECISION,

            -- Absorption indicators
            asellers_uwick DOUBLE PRECISION,
            asellers_lwick DOUBLE PRECISION,
            abuyers_uwick DOUBLE PRECISION,
            abuyers_lwick DOUBLE PRECISION,

            -- Order flow
            delta DOUBLE PRECISION,
            oflow_detail JSONB,  -- Footprint data at 0.25 tick granularity
            oflow_unit JSONB,    -- Footprint data at 1 point granularity

            -- Metadata
            tick_count INTEGER
        );

        CREATE TABLE candlestick_1min (
            -- Primary key
            time_interval TIMESTAMP WITH TIME ZONE,  -- Stored in UTC
            symbol VARCHAR(20),

            -- Symbol tracking
            is_spread BOOLEAN,
            is_rollover_period BOOLEAN,

            -- OHLCV
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume DOUBLE PRECISION,

            -- Point of Control - Regular
            poc DOUBLE PRECISION,
            poc_volume DOUBLE PRECISION,
            poc_percentage DOUBLE PRECISION,
            poc_location VARCHAR,
            poc_position DOUBLE PRECISION,

            -- Point of Control - Real (exact 0.25 tick)
            real_poc DOUBLE PRECISION,
            real_poc_volume DOUBLE PRECISION,
            real_poc_percentage DOUBLE PRECISION,
            real_poc_location VARCHAR,

            -- Candle structure
            upper_wick DOUBLE PRECISION,
            lower_wick DOUBLE PRECISION,
            body DOUBLE PRECISION,
            wick_ratio DOUBLE PRECISION,
            rel_uw DOUBLE PRECISION,
            rel_lw DOUBLE PRECISION,

            -- Volume distribution
            upper_wick_volume DOUBLE PRECISION,
            lower_wick_volume DOUBLE PRECISION,
            body_volume DOUBLE PRECISION,

            -- Absorption indicators
            asellers_uwick DOUBLE PRECISION,
            asellers_lwick DOUBLE PRECISION,
            abuyers_uwick DOUBLE PRECISION,
            abuyers_lwick DOUBLE PRECISION,

            -- Order flow
            delta DOUBLE PRECISION,
            oflow_detail JSONB,  -- Footprint data at 0.25 tick granularity
            oflow_unit JSONB,    -- Footprint data at 1 point granularity

            -- Metadata
            tick_count INTEGER
        );

        CREATE TABLE candlestick_5min (
            -- Primary key
            time_interval TIMESTAMP WITH TIME ZONE,  -- Stored in UTC
            symbol VARCHAR(20),

            -- Symbol tracking
            is_spread BOOLEAN,
            is_rollover_period BOOLEAN,

            -- OHLCV
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume DOUBLE PRECISION,

            -- Point of Control - Regular
            poc DOUBLE PRECISION,
            poc_volume DOUBLE PRECISION,
            poc_percentage DOUBLE PRECISION,
            poc_location VARCHAR,
            poc_position DOUBLE PRECISION,

            -- Point of Control - Real (exact 0.25 tick)
            real_poc DOUBLE PRECISION,
            real_poc_volume DOUBLE PRECISION,
            real_poc_percentage DOUBLE PRECISION,
            real_poc_location VARCHAR,

            -- Candle structure
            upper_wick DOUBLE PRECISION,
            lower_wick DOUBLE PRECISION,
            body DOUBLE PRECISION,
            wick_ratio DOUBLE PRECISION,
            rel_uw DOUBLE PRECISION,
            rel_lw DOUBLE PRECISION,

            -- Volume distribution
            upper_wick_volume DOUBLE PRECISION,
            lower_wick_volume DOUBLE PRECISION,
            body_volume DOUBLE PRECISION,

            -- Absorption indicators
            asellers_uwick DOUBLE PRECISION,
            asellers_lwick DOUBLE PRECISION,
            abuyers_uwick DOUBLE PRECISION,
            abuyers_lwick DOUBLE PRECISION,

            -- Order flow
            delta DOUBLE PRECISION,
            oflow_detail JSONB,  -- Footprint data at 0.25 tick granularity
            oflow_unit JSONB,    -- Footprint data at 1 point granularity

            -- Metadata
            tick_count INTEGER
        );

        CREATE TABLE candlestick_15min (
            -- Primary key
            time_interval TIMESTAMP WITH TIME ZONE,  -- Stored in UTC
            symbol VARCHAR(20),

            -- Symbol tracking
            is_spread BOOLEAN,
            is_rollover_period BOOLEAN,

            -- OHLCV
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume DOUBLE PRECISION,

            -- Point of Control - Regular
            poc DOUBLE PRECISION,
            poc_volume DOUBLE PRECISION,
            poc_percentage DOUBLE PRECISION,
            poc_location VARCHAR,
            poc_position DOUBLE PRECISION,

            -- Point of Control - Real (exact 0.25 tick)
            real_poc DOUBLE PRECISION,
            real_poc_volume DOUBLE PRECISION,
            real_poc_percentage DOUBLE PRECISION,
            real_poc_location VARCHAR,

            -- Candle structure
            upper_wick DOUBLE PRECISION,
            lower_wick DOUBLE PRECISION,
            body DOUBLE PRECISION,
            wick_ratio DOUBLE PRECISION,
            rel_uw DOUBLE PRECISION,
            rel_lw DOUBLE PRECISION,

            -- Volume distribution
            upper_wick_volume DOUBLE PRECISION,
            lower_wick_volume DOUBLE PRECISION,
            body_volume DOUBLE PRECISION,

            -- Absorption indicators
            asellers_uwick DOUBLE PRECISION,
            asellers_lwick DOUBLE PRECISION,
            abuyers_uwick DOUBLE PRECISION,
            abuyers_lwick DOUBLE PRECISION,

            -- Order flow
            delta DOUBLE PRECISION,
            oflow_detail JSONB,  -- Footprint data at 0.25 tick granularity
            oflow_unit JSONB,    -- Footprint data at 1 point granularity

            -- Metadata
            tick_count INTEGER
        );

        CREATE TABLE candlestick_1hr (
            -- Primary key
            time_interval TIMESTAMP WITH TIME ZONE,  -- Stored in UTC
            symbol VARCHAR(20),

            -- Symbol tracking
            is_spread BOOLEAN,
            is_rollover_period BOOLEAN,

            -- OHLCV
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume DOUBLE PRECISION,

            -- Point of Control - Regular
            poc DOUBLE PRECISION,
            poc_volume DOUBLE PRECISION,
            poc_percentage DOUBLE PRECISION,
            poc_location VARCHAR,
            poc_position DOUBLE PRECISION,

            -- Point of Control - Real (exact 0.25 tick)
            real_poc DOUBLE PRECISION,
            real_poc_volume DOUBLE PRECISION,
            real_poc_percentage DOUBLE PRECISION,
            real_poc_location VARCHAR,

            -- Candle structure
            upper_wick DOUBLE PRECISION,
            lower_wick DOUBLE PRECISION,
            body DOUBLE PRECISION,
            wick_ratio DOUBLE PRECISION,
            rel_uw DOUBLE PRECISION,
            rel_lw DOUBLE PRECISION,

            -- Volume distribution
            upper_wick_volume DOUBLE PRECISION,
            lower_wick_volume DOUBLE PRECISION,
            body_volume DOUBLE PRECISION,

            -- Absorption indicators
            asellers_uwick DOUBLE PRECISION,
            asellers_lwick DOUBLE PRECISION,
            abuyers_uwick DOUBLE PRECISION,
            abuyers_lwick DOUBLE PRECISION,

            -- Order flow
            delta DOUBLE PRECISION,
            oflow_detail JSONB,  -- Footprint data at 0.25 tick granularity
            oflow_unit JSONB,    -- Footprint data at 1 point granularity

            -- Metadata
            tick_count INTEGER
        );

        CREATE TABLE candlestick_4hr (
            -- Primary key
            time_interval TIMESTAMP WITH TIME ZONE,  -- Stored in UTC
            symbol VARCHAR(20),

            -- Symbol tracking
            is_spread BOOLEAN,
            is_rollover_period BOOLEAN,

            -- OHLCV
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume DOUBLE PRECISION,

            -- Point of Control - Regular
            poc DOUBLE PRECISION,
            poc_volume DOUBLE PRECISION,
            poc_percentage DOUBLE PRECISION,
            poc_location VARCHAR,
            poc_position DOUBLE PRECISION,

            -- Point of Control - Real (exact 0.25 tick)
            real_poc DOUBLE PRECISION,
            real_poc_volume DOUBLE PRECISION,
            real_poc_percentage DOUBLE PRECISION,
            real_poc_location VARCHAR,

            -- Candle structure
            upper_wick DOUBLE PRECISION,
            lower_wick DOUBLE PRECISION,
            body DOUBLE PRECISION,
            wick_ratio DOUBLE PRECISION,
            rel_uw DOUBLE PRECISION,
            rel_lw DOUBLE PRECISION,

            -- Volume distribution
            upper_wick_volume DOUBLE PRECISION,
            lower_wick_volume DOUBLE PRECISION,
            body_volume DOUBLE PRECISION,

            -- Absorption indicators
            asellers_uwick DOUBLE PRECISION,
            asellers_lwick DOUBLE PRECISION,
            abuyers_uwick DOUBLE PRECISION,
            abuyers_lwick DOUBLE PRECISION,

            -- Order flow
            delta DOUBLE PRECISION,
            oflow_detail JSONB,  -- Footprint data at 0.25 tick granularity
            oflow_unit JSONB,    -- Footprint data at 1 point granularity

            -- Metadata
            tick_count INTEGER
        );

        CREATE TABLE candlestick_daily (
            -- Primary key
            time_interval TIMESTAMP WITH TIME ZONE,  -- Stored in UTC
            symbol VARCHAR(20),

            -- Symbol tracking
            is_spread BOOLEAN,
            is_rollover_period BOOLEAN,

            -- OHLCV
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume DOUBLE PRECISION,

            -- Point of Control - Regular
            poc DOUBLE PRECISION,
            poc_volume DOUBLE PRECISION,
            poc_percentage DOUBLE PRECISION,
            poc_location VARCHAR,
            poc_position DOUBLE PRECISION,

            -- Point of Control - Real (exact 0.25 tick)
            real_poc DOUBLE PRECISION,
            real_poc_volume DOUBLE PRECISION,
            real_poc_percentage DOUBLE PRECISION,
            real_poc_location VARCHAR,

            -- Candle structure
            upper_wick DOUBLE PRECISION,
            lower_wick DOUBLE PRECISION,
            body DOUBLE PRECISION,
            wick_ratio DOUBLE PRECISION,
            rel_uw DOUBLE PRECISION,
            rel_lw DOUBLE PRECISION,

            -- Volume distribution
            upper_wick_volume DOUBLE PRECISION,
            lower_wick_volume DOUBLE PRECISION,
            body_volume DOUBLE PRECISION,

            -- Absorption indicators
            asellers_uwick DOUBLE PRECISION,
            asellers_lwick DOUBLE PRECISION,
            abuyers_uwick DOUBLE PRECISION,
            abuyers_lwick DOUBLE PRECISION,

            -- Order flow
            delta DOUBLE PRECISION,
            oflow_detail JSONB,  -- Footprint data at 0.25 tick granularity
            oflow_unit JSONB,    -- Footprint data at 1 point granularity

            -- Metadata
            tick_count INTEGER
        );

        CREATE TABLE candlestick_weekly (
            -- Primary key
            time_interval TIMESTAMP WITH TIME ZONE,  -- Stored in UTC
            symbol VARCHAR(20),

            -- Symbol tracking
            is_spread BOOLEAN,
            is_rollover_period BOOLEAN,

            -- OHLCV
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume DOUBLE PRECISION,

            -- Point of Control - Regular
            poc DOUBLE PRECISION,
            poc_volume DOUBLE PRECISION,
            poc_percentage DOUBLE PRECISION,
            poc_location VARCHAR,
            poc_position DOUBLE PRECISION,

            -- Point of Control - Real (exact 0.25 tick)
            real_poc DOUBLE PRECISION,
            real_poc_volume DOUBLE PRECISION,
            real_poc_percentage DOUBLE PRECISION,
            real_poc_location VARCHAR,

            -- Candle structure
            upper_wick DOUBLE PRECISION,
            lower_wick DOUBLE PRECISION,
            body DOUBLE PRECISION,
            wick_ratio DOUBLE PRECISION,
            rel_uw DOUBLE PRECISION,
            rel_lw DOUBLE PRECISION,

            -- Volume distribution
            upper_wick_volume DOUBLE PRECISION,
            lower_wick_volume DOUBLE PRECISION,
            body_volume DOUBLE PRECISION,

            -- Absorption indicators
            asellers_uwick DOUBLE PRECISION,
            asellers_lwick DOUBLE PRECISION,
            abuyers_uwick DOUBLE PRECISION,
            abuyers_lwick DOUBLE PRECISION,

            -- Order flow
            delta DOUBLE PRECISION,
            oflow_detail JSONB,  -- Footprint data at 0.25 tick granularity
            oflow_unit JSONB,    -- Footprint data at 1 point granularity

            -- Metadata
            tick_count INTEGER
        );

        -- Fair Value Gaps
        CREATE TABLE detected_fvgs (
            id UUID PRIMARY KEY,
            formation_time TIMESTAMPTZ,
            gap_start_price NUMERIC,
            gap_end_price NUMERIC,
            gap_size NUMERIC,
            direction VARCHAR(10),           -- BULLISH or BEARISH
            status VARCHAR(20),              -- UNMITIGATED, REDELIVERED, REBALANCED
            significance VARCHAR(20),         -- MICRO, SMALL, MEDIUM, LARGE, EXTREME
            premium_level NUMERIC,           -- High boundary (resistance)
            discount_level NUMERIC,          -- Low boundary (support)
            consequent_encroachment NUMERIC, -- 50% level
            displacement_score NUMERIC,
            has_break_of_structure BOOLEAN
        );

        -- Liquidity Pools
        CREATE TABLE detected_liquidity_pools (
            id UUID PRIMARY KEY,
            pool_type VARCHAR(50),            -- EQH, EQL, NYH, NYL, ASH, ASL, LSH, LSL
            modal_level NUMERIC,             -- Price level with most touches
            zone_low NUMERIC,                -- Lower bound of pool zone
            zone_high NUMERIC,               -- Upper bound of pool zone
            start_time TIMESTAMPTZ,          -- Start of rectangle
            end_time TIMESTAMPTZ,            -- End of rectangle
            status VARCHAR(20),              -- UNMITIGATED, RESPECTED, SWEPT, MITIGATED
            sweep_detected BOOLEAN,
            touch_count INTEGER
        );

        -- Order Blocks
        CREATE TABLE detected_order_blocks (
            id UUID PRIMARY KEY,
            formation_time TIMESTAMPTZ,
            ob_high NUMERIC,
            ob_low NUMERIC,
            ob_body_midpoint NUMERIC,        -- 50% of candle body
            ob_range_midpoint NUMERIC,       -- 50% of candle range
            direction VARCHAR(10),           -- BULLISH or BEARISH
            quality VARCHAR(20),             -- HIGH, MEDIUM, LOW
            status VARCHAR(20),              -- ACTIVE, TESTED, BROKEN
            impulse_move NUMERIC,            -- Size of impulse in points
            impulse_direction VARCHAR(10)    -- UP or DOWN
        );

        -- ==================== TABLE PURPOSE COMMENTS (SQL STANDARD) ====================
        -- These comments help Vanna understand which table to use for which type of query

        -- Candlestick tables (8 timeframes)
        COMMENT ON TABLE candlestick_30s IS 'OHLCV price and volume data with 30-second timeframe. Use for: ultra-fast scalping, tick analysis, high-frequency patterns, intraday micro-structure. Keywords: 30 segundos, 30s, scalping rápido. JOIN with active_contracts when user says NQ (generic).';
        COMMENT ON TABLE candlestick_1min IS 'OHLCV price and volume data with 1-minute timeframe. Use for: scalping, very short-term trading, fine-grained intraday analysis. Keywords: 1 minuto, 1min, 1m, scalping. JOIN with active_contracts when user says NQ (generic).';
        COMMENT ON TABLE candlestick_5min IS 'OHLCV price and volume data with 5-minute timeframe. Use for: intraday trading, short-term patterns, most commonly used for general queries. Keywords: 5 minutos, 5min, 5m, intraday. MOST COMMON TABLE. JOIN with active_contracts when user says NQ (generic).';
        COMMENT ON TABLE candlestick_15min IS 'OHLCV price and volume data with 15-minute timeframe. Use for: short-term swing trading, intraday trends, session analysis. Keywords: 15 minutos, 15min, 15m, sesión. JOIN with active_contracts when user says NQ (generic).';
        COMMENT ON TABLE candlestick_1hr IS 'OHLCV price and volume data with 1-hour timeframe. Use for: medium-term analysis, hourly trends, multi-session patterns. Keywords: 1 hora, 1h, hourly, hora. JOIN with active_contracts when user says NQ (generic).';
        COMMENT ON TABLE candlestick_4hr IS 'OHLCV price and volume data with 4-hour timeframe. Use for: swing trading, medium-term analysis, daily structure. Keywords: 4 horas, 4h, 4hr, swing. JOIN with active_contracts when user says NQ (generic).';
        COMMENT ON TABLE candlestick_daily IS 'OHLCV price and volume data with daily timeframe. Use for: daily analysis, day-to-day comparisons, long-term patterns, end-of-day statistics. Keywords: diario, daily, día, EOD, end of day, por día. JOIN with active_contracts when user says NQ (generic).';
        COMMENT ON TABLE candlestick_weekly IS 'OHLCV price and volume data with weekly timeframe. Use for: long-term trends, weekly analysis, macro patterns, position trading. Keywords: semanal, weekly, semana, week, largo plazo. JOIN with active_contracts when user says NQ (generic).';

        -- TABLE HINT USAGE GUIDE (2-Stage Architecture)
        -- IMPORTANT: If the user question contains "use candlestick_XXX:",
        -- you MUST use that specific table in your SQL query.
        --
        -- Example 1:
        --   Question: "use candlestick_daily: dame el máximo de noviembre"
        --   SQL: SELECT MAX(high) FROM candlestick_daily WHERE...
        --
        -- Example 2:
        --   Question: "use candlestick_1hr: dame las 3 horas con más volumen del día 2025-11-20"
        --   SQL: SELECT time_interval, volume FROM candlestick_1hr WHERE... ORDER BY volume DESC LIMIT 3
        --
        -- DO NOT ignore table hints. They are provided by the orchestrator for optimal query performance.

        -- Pattern detection tables
        COMMENT ON TABLE detected_fvgs IS 'Fair Value Gaps (ICT pattern detection). Use for: FVG analysis, pattern counts, mitigation tracking, gap statistics. Examples: how many FVGs, unmitigated FVGs, FVG distribution.';
        COMMENT ON TABLE detected_liquidity_pools IS 'Liquidity Pool levels (EQH/EQL/Session Levels). Use for: LP analysis, sweep detection, session level tracking. Examples: how many liquidity pools, swept pools, NYH/NYL levels.';
        COMMENT ON TABLE detected_order_blocks IS 'Order Blocks (ICT pattern - last candle before impulse). Use for: OB analysis, quality classification, bullish/bearish OBs. Examples: how many order blocks, strong OBs, OB quality distribution.';
        COMMENT ON TABLE market_state_snapshots IS 'Market state capture (PDH, PDL, Killzones, etc.). Use for: market structure queries, session analysis, previous day levels. Examples: previous day high, killzone times, market state analysis.';

        -- System tables
        COMMENT ON TABLE etl_jobs IS 'Data ingestion job tracking. Use for: ETL monitoring, job status queries, ingestion tracking. Examples: ETL jobs, failed jobs, recent ingestions.';
        COMMENT ON TABLE active_contracts IS 'Contract lifecycle tracking (which NQ contract is active). Use for: contract status, rollover tracking, current contract identification. CRITICAL: When user says NQ (generic), JOIN candlestick tables with this table WHERE is_current = true.';

        -- Market State Snapshots
        CREATE TABLE market_state_snapshots (
            id UUID PRIMARY KEY,
            snapshot_time TIMESTAMPTZ,
            timeframe VARCHAR(10),
            current_price NUMERIC,
            session_type VARCHAR(20),
            fvgs_nearby INTEGER,
            lps_nearby INTEGER,
            obs_nearby INTEGER,
            metadata JSONB
        );

        -- ETL Jobs
        CREATE TABLE etl_jobs (
            id SERIAL PRIMARY KEY,
            job_type VARCHAR(50),
            status VARCHAR(20),              -- PENDING, RUNNING, COMPLETED, FAILED
            created_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            rows_processed INTEGER,
            error_message TEXT
        );

        -- Active Contracts Tracking
        -- Tabla que rastrea qué contrato está activo en cada momento
        -- REGLA CRÍTICA: Cuando el usuario menciona "NQ", SIEMPRE se refiere al contrato activo actual
        -- Referencia completa: docs/DATA_DICTIONARY.md
        CREATE TABLE active_contracts (
            -- Identificación
            id INTEGER PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,  -- Símbolo completo del contrato. Formato CME: {PROD}{MES}{AÑO} (ej: NQZ24, NQH25). Meses: H=Mar, M=Jun, U=Sep, Z=Dic

            -- Período de vigencia del contrato
            start_date DATE NOT NULL,     -- Fecha de inicio de actividad del contrato. Cuando empieza a tener volumen significativo
            end_date DATE,                -- Fecha de fin de actividad. NULL si es el contrato activo actual. Se establece cuando termina el rollover

            -- Métricas de actividad
            volume_score BIGINT,          -- Volumen total acumulado negociado en este contrato. Indica liquidez. Fórmula: SUM(volume) de todas las velas
            tick_count BIGINT,            -- Total de ticks procesados para este contrato. Indica actividad. Fórmula: COUNT(*) de market_data_ticks

            -- Estado del contrato (flags críticos)
            is_current BOOLEAN NOT NULL DEFAULT false,  -- TRUE = Contrato activo actual. REGLA: Solo UN contrato puede tener is_current=true al mismo tiempo
            rollover_period BOOLEAN NOT NULL DEFAULT false,  -- TRUE durante período de transición entre contratos (típicamente 2-5 días antes del vencimiento)

            -- Auditoría
            created_at TIMESTAMPTZ DEFAULT NOW(),  -- Cuándo se registró el contrato en el sistema
            updated_at TIMESTAMPTZ DEFAULT NOW()   -- Última actualización de métricas o estado
        );

        -- PATRÓN DE USO OBLIGATORIO:
        -- Cuando el usuario dice "NQ", SIEMPRE hacer JOIN con active_contracts WHERE is_current = true
        -- Ejemplo correcto:
        --   SELECT c.*
        --   FROM candlestick_5min c
        --   JOIN active_contracts ac ON c.symbol = ac.symbol
        --   WHERE ac.is_current = true;
        """

        try:
            self.vn.train(ddl=schema_ddl)

            # ==================== CONTEXT DOCUMENTATION ====================
            # Add critical context documentation to help Vanna understand the domain
            # NOTE: Table purposes are now defined in DDL via COMMENT ON TABLE statements

            # Doc 1: NQ Futures Specifications
            nq_specs_doc = """
**NQ Futures Specifications**

NQ (Nasdaq-100 E-mini Futures) - Especificaciones del Instrumento:
- Tick Size: 0.25 puntos (mínima fluctuación de precio)
- Valor por Tick: $5 USD por cada 0.25 puntos
- Valor por Punto: $20 USD (4 ticks x $5)
- Precisión de Precio: Siempre en múltiplos de 0.25 (ej: 20125.00, 20125.25, 20125.50, 20125.75)

Ejemplos de cálculo:
- Movimiento de 1 punto (20125.00 → 20126.00) = $20 USD
- Movimiento de 10 puntos (20125.00 → 20135.00) = $200 USD
- Movimiento de 100 puntos (20125.00 → 20225.00) = $2,000 USD
"""

            # Doc 2: Order Flow Terminology
            order_flow_doc = """
**Order Flow Terminology**

Order Flow = Flujo de órdenes que muestra compras vs ventas agresivas

Terminología Crítica:
- side='A': Vendedor agresivo (seller hit the bid) - presión vendedora
- side='B': Comprador agresivo (buyer hit the ask) - presión compradora
- Delta: compras - ventas. Fórmula: SUM(CASE WHEN side='B' THEN size WHEN side='A' THEN -size)
  * Delta positivo (+): Más compras que ventas (presión compradora)
  * Delta negativo (-): Más ventas que compras (presión vendedora)
  * Delta cerca de 0: Balance entre compras y ventas

Absorción:
- asellers_uwick: Vendedores agresivos en mecha superior → Absorción de compradores en el high
- asellers_lwick: Vendedores agresivos en mecha inferior
- abuyers_uwick: Compradores agresivos en mecha superior
- abuyers_lwick: Compradores agresivos en mecha inferior → Absorción de vendedores en el low

POC (Point of Control):
- Nivel de precio con mayor volumen negociado
- poc: Redondeado a 1.0 punto (agrupa 4 ticks de 0.25)
- real_poc: Exacto sin redondeo (tick preciso de 0.25)
- poc_percentage: % del volumen total concentrado en el POC
  * >30% indica fuerte concentración de volumen
  * <15% indica distribución dispersa
"""

            # Doc 3: Timezone Handling and Trading Sessions
            timezone_doc = """
**Timezone Handling**

Timezones:
- Storage: Todos los timestamps en UTC en la base de datos
- Query Display: Convertir a Eastern Time con AT TIME ZONE 'America/New_York'
- IMPORTANTE: time_interval es UTC, usar conversión para mostrar en ET

Ejemplo correcto de conversión:
```sql
-- Para filtrar por fecha en Eastern Time:
WHERE time_interval AT TIME ZONE 'America/New_York' >= '2024-11-01'::timestamp
  AND time_interval AT TIME ZONE 'America/New_York' < '2024-12-01'::timestamp
```

Sesiones de Trading (Eastern Time):
- Asian Session: 18:00 - 02:00 (día siguiente)
- London Session: 03:00 - 12:00
- New York Session: 09:30 - 16:00
"""

            # Doc 4: Active Contracts Resolution Pattern
            active_contracts_pattern_doc = """
**Active Contracts - Pattern de Uso OBLIGATORIO**

REGLA CRÍTICA: Cuando el usuario menciona "NQ" sin especificar contrato:
→ SIEMPRE hacer JOIN con active_contracts WHERE is_current = true

¿Por qué?
- "NQ" es un producto genérico
- Los contratos cambian cada mes (NQZ24, NQH25, NQM25, etc.)
- Solo UN contrato está activo a la vez (is_current = true)

Patrón SQL CORRECTO:
```sql
SELECT c.*
FROM candlestick_5min c
INNER JOIN active_contracts ac ON c.symbol = ac.symbol
WHERE ac.is_current = true
  -- resto de filtros...
```

Patrón SQL INCORRECTO:
```sql
-- ❌ NUNCA hacer esto:
SELECT * FROM candlestick_5min WHERE symbol = 'NQ'
```

Excepciones (cuando NO usar active_contracts):
1. Usuario especifica contrato exacto (ej: "NQZ24", "NQH25")
2. Usuario pide "todos los contratos históricos"
3. Usuario pregunta específicamente por tabla active_contracts

Formato de Símbolos CME:
- {PRODUCTO}{MES}{AÑO}: NQZ24, NQH25
- Meses: H=Marzo, M=Junio, U=Septiembre, Z=Diciembre
"""

            # Doc 5: Calendar Spreads & Rollover
            spreads_rollover_doc = """
**Calendar Spreads y Rollover Period**

Calendar Spread:
- Operación con dos contratos simultáneos
- Formato: "NQZ24-NQH25" (venta Z24, compra H25)
- Identificador: campo is_spread = true
- Contiene guión '-' en el símbolo

Rollover Period:
- Período de transición entre contratos (2-5 días antes del vencimiento)
- Durante rollover: rollover_period = true
- Ambos contratos tienen volumen
- Traders migran posiciones del contrato que vence al siguiente
- Datos pueden tener mayor volatilidad y spreads

Consultas durante Rollover:
```sql
-- Ver datos durante rollover
SELECT ac.symbol, COUNT(*) as candles
FROM candlestick_5min c
JOIN active_contracts ac ON c.symbol = ac.symbol
WHERE ac.rollover_period = true
GROUP BY ac.symbol;
```
"""

            # Train all documentation
            self.vn.train(documentation=nq_specs_doc)
            self.vn.train(documentation=order_flow_doc)
            self.vn.train(documentation=timezone_doc)
            self.vn.train(documentation=active_contracts_pattern_doc)
            self.vn.train(documentation=spreads_rollover_doc)

            logger.info("Vanna context documentation training completed (5 docs)")

            # ==================== TRAINING EXAMPLES ====================
            # Add comprehensive example questions for training
            example_queries = [
                # FVG Queries
                {
                    "question": "How many FVGs were detected yesterday?",
                    "sql": "SELECT COUNT(*) FROM detected_fvgs WHERE DATE(formation_time) = CURRENT_DATE - 1"
                },
                {
                    "question": "Show me all unmitigated FVGs",
                    "sql": "SELECT * FROM detected_fvgs WHERE status = 'UNMITIGATED' ORDER BY formation_time DESC"
                },
                {
                    "question": "What's the average gap size for bullish FVGs?",
                    "sql": "SELECT AVG(gap_size) as avg_gap FROM detected_fvgs WHERE direction = 'BULLISH'"
                },
                {
                    "question": "How many large or extreme FVGs do we have?",
                    "sql": "SELECT COUNT(*) FROM detected_fvgs WHERE significance IN ('LARGE', 'EXTREME')"
                },

                # Liquidity Pool Queries
                {
                    "question": "What are the active liquidity pools?",
                    "sql": "SELECT * FROM detected_liquidity_pools WHERE status = 'UNMITIGATED' ORDER BY zone_high DESC"
                },
                {
                    "question": "How many liquidity pools were swept this week?",
                    "sql": "SELECT COUNT(*) FROM detected_liquidity_pools WHERE sweep_detected = true AND start_time >= CURRENT_DATE - 7"
                },
                {
                    "question": "Show me all EQH liquidity pools",
                    "sql": "SELECT * FROM detected_liquidity_pools WHERE pool_type = 'EQH' ORDER BY modal_level DESC"
                },

                # Order Block Queries
                {
                    "question": "How many active order blocks are there?",
                    "sql": "SELECT COUNT(*) FROM detected_order_blocks WHERE status = 'ACTIVE'"
                },
                {
                    "question": "Show me high quality bullish order blocks",
                    "sql": "SELECT * FROM detected_order_blocks WHERE quality = 'HIGH' AND direction = 'BULLISH' ORDER BY formation_time DESC"
                },
                {
                    "question": "What's the largest impulse move in order blocks?",
                    "sql": "SELECT MAX(impulse_move) as max_impulse FROM detected_order_blocks"
                },

                # ETL Queries
                {
                    "question": "Show me recent ETL jobs",
                    "sql": "SELECT * FROM etl_jobs ORDER BY created_at DESC LIMIT 10"
                },
                {
                    "question": "How many ETL jobs failed today?",
                    "sql": "SELECT COUNT(*) FROM etl_jobs WHERE status = 'FAILED' AND DATE(created_at) = CURRENT_DATE"
                },
                {
                    "question": "What's the total rows processed by ETL today?",
                    "sql": "SELECT SUM(rows_processed) FROM etl_jobs WHERE DATE(created_at) = CURRENT_DATE"
                },

                # Candlestick Queries
                {
                    "question": "How many candles are in the 1min table?",
                    "sql": "SELECT COUNT(*) FROM candlestick_1min"
                },
                {
                    "question": "Show me the latest 5 candles from 1h timeframe",
                    "sql": "SELECT * FROM candlestick_1h ORDER BY time_interval DESC LIMIT 5"
                },
                {
                    "question": "What's the highest volume candle in the daily timeframe?",
                    "sql": "SELECT * FROM candlestick_daily ORDER BY volume DESC LIMIT 1"
                },

                # Combined Queries
                {
                    "question": "How many patterns were detected in the last 24 hours?",
                    "sql": """SELECT
                        (SELECT COUNT(*) FROM detected_fvgs WHERE formation_time >= NOW() - INTERVAL '24 hours') as fvgs,
                        (SELECT COUNT(*) FROM detected_liquidity_pools WHERE start_time >= NOW() - INTERVAL '24 hours') as lps,
                        (SELECT COUNT(*) FROM detected_order_blocks WHERE formation_time >= NOW() - INTERVAL '24 hours') as obs"""
                },
                {
                    "question": "Show me FVGs with BOS detected",
                    "sql": "SELECT * FROM detected_fvgs WHERE has_break_of_structure = true ORDER BY formation_time DESC"
                },

                # Time-based Queries (5min candles)
                {
                    "question": "How many 5min candles are in November 2024?",
                    "sql": "SELECT COUNT(*) FROM candlestick_5min WHERE EXTRACT(YEAR FROM time_interval) = 2024 AND EXTRACT(MONTH FROM time_interval) = 11"
                },
                {
                    "question": "Cuantas velas de 5min hay en noviembre 2024",
                    "sql": "SELECT COUNT(*) FROM candlestick_5min WHERE EXTRACT(YEAR FROM time_interval) = 2024 AND EXTRACT(MONTH FROM time_interval) = 11"
                },
                {
                    "question": "Show me candles from December 2024 in 5min timeframe",
                    "sql": "SELECT * FROM candlestick_5min WHERE EXTRACT(YEAR FROM time_interval) = 2024 AND EXTRACT(MONTH FROM time_interval) = 12 ORDER BY time_interval DESC LIMIT 100"
                },
                {
                    "question": "Count candles by month in 2024 for 5min",
                    "sql": "SELECT EXTRACT(MONTH FROM time_interval) as month, COUNT(*) as count FROM candlestick_5min WHERE EXTRACT(YEAR FROM time_interval) = 2024 GROUP BY month ORDER BY month"
                },
                {
                    "question": "How many days of data are in candlestick_5min?",
                    "sql": "SELECT COUNT(DISTINCT DATE(time_interval)) as unique_days FROM candlestick_5min"
                },
                # ==================== ACTIVE CONTRACTS EXAMPLES ====================
                # These examples demonstrate the MANDATORY pattern for generic "NQ" queries
                {
                    "question": "What's the maximum price of NQ in November 2024?",
                    "sql": """SELECT MAX(c.high) as max_price
                        FROM candlestick_5min c
                        INNER JOIN active_contracts ac ON c.symbol = ac.symbol
                        WHERE ac.is_current = true
                        AND EXTRACT(YEAR FROM c.time_interval) = 2024
                        AND EXTRACT(MONTH FROM c.time_interval) = 11"""
                },
                {
                    "question": "dame el maximo valor de NQ en noviembre 2024",
                    "sql": """SELECT MAX(c.high) as max_price
                        FROM candlestick_5min c
                        INNER JOIN active_contracts ac ON c.symbol = ac.symbol
                        WHERE ac.is_current = true
                        AND EXTRACT(YEAR FROM c.time_interval) = 2024
                        AND EXTRACT(MONTH FROM c.time_interval) = 11"""
                },
                {
                    "question": "Show me NQ candles from today",
                    "sql": """SELECT c.*
                        FROM candlestick_5min c
                        INNER JOIN active_contracts ac ON c.symbol = ac.symbol
                        WHERE ac.is_current = true
                        AND DATE(c.time_interval) = CURRENT_DATE
                        ORDER BY c.time_interval DESC"""
                },
                {
                    "question": "What's the average volume for NQ?",
                    "sql": """SELECT AVG(c.volume) as avg_volume
                        FROM candlestick_5min c
                        INNER JOIN active_contracts ac ON c.symbol = ac.symbol
                        WHERE ac.is_current = true"""
                },
                {
                    "question": "dame el promedio de volumen de las velas de NQ a las 9:30 AM EST en noviembre 2025",
                    "sql": """SELECT AVG(c.volume) as avg_volume
                        FROM candlestick_5min c
                        INNER JOIN active_contracts ac ON c.symbol = ac.symbol
                        WHERE ac.is_current = true
                        AND EXTRACT(YEAR FROM c.time_interval AT TIME ZONE 'America/New_York') = 2025
                        AND EXTRACT(MONTH FROM c.time_interval AT TIME ZONE 'America/New_York') = 11
                        AND EXTRACT(HOUR FROM c.time_interval AT TIME ZONE 'America/New_York') = 9
                        AND EXTRACT(MINUTE FROM c.time_interval AT TIME ZONE 'America/New_York') = 30"""
                },
                {
                    "question": "What's the average volume at 9:30 AM EST in November 2025?",
                    "sql": """SELECT AVG(c.volume) as avg_volume
                        FROM candlestick_5min c
                        INNER JOIN active_contracts ac ON c.symbol = ac.symbol
                        WHERE ac.is_current = true
                        AND EXTRACT(YEAR FROM c.time_interval AT TIME ZONE 'America/New_York') = 2025
                        AND EXTRACT(MONTH FROM c.time_interval AT TIME ZONE 'America/New_York') = 11
                        AND EXTRACT(HOUR FROM c.time_interval AT TIME ZONE 'America/New_York') = 9
                        AND EXTRACT(MINUTE FROM c.time_interval AT TIME ZONE 'America/New_York') = 30"""
                },
                {
                    "question": "Show me NQ data for December 2024",
                    "sql": """SELECT c.*
                        FROM candlestick_5min c
                        INNER JOIN active_contracts ac ON c.symbol = ac.symbol
                        WHERE ac.is_current = true
                        AND EXTRACT(YEAR FROM c.time_interval) = 2024
                        AND EXTRACT(MONTH FROM c.time_interval) = 12
                        ORDER BY c.time_interval DESC
                        LIMIT 100"""
                },

                # Timezone Conversion Queries with active_contracts
                {
                    "question": "Show me NQ candles from New York session on November 15, 2024",
                    "sql": """SELECT c.* FROM candlestick_5min c
                        INNER JOIN active_contracts ac ON c.symbol = ac.symbol
                        WHERE ac.is_current = true
                        AND c.time_interval AT TIME ZONE 'America/New_York' >= '2024-11-15 09:30:00'::timestamp
                        AND c.time_interval AT TIME ZONE 'America/New_York' < '2024-11-15 16:00:00'::timestamp
                        ORDER BY c.time_interval"""
                },
                {
                    "question": "How many 5min candles in November 2024 Eastern Time?",
                    "sql": """SELECT COUNT(*) FROM candlestick_5min
                        WHERE time_interval AT TIME ZONE 'America/New_York' >= '2024-11-01'::timestamp
                        AND time_interval AT TIME ZONE 'America/New_York' < '2024-12-01'::timestamp"""
                },
                {
                    "question": "Show me candles during Asian session on November 20, 2024",
                    "sql": """SELECT * FROM candlestick_5min
                        WHERE time_interval AT TIME ZONE 'America/New_York' >= '2024-11-20 18:00:00'::timestamp
                        AND time_interval AT TIME ZONE 'America/New_York' < '2024-11-21 02:00:00'::timestamp
                        ORDER BY time_interval"""
                },

                # New Columns - POC Real Queries
                {
                    "question": "Show me candles where real POC is at upper third",
                    "sql": "SELECT * FROM candlestick_5min WHERE real_poc_location = 'UPPER_THIRD' ORDER BY time_interval DESC LIMIT 50"
                },
                {
                    "question": "What's the average real POC volume for 5min candles?",
                    "sql": "SELECT AVG(real_poc_volume) as avg_real_poc_vol FROM candlestick_5min WHERE real_poc_volume IS NOT NULL"
                },
                {
                    "question": "Find candles with high real POC percentage",
                    "sql": "SELECT * FROM candlestick_5min WHERE real_poc_percentage > 30 ORDER BY real_poc_percentage DESC LIMIT 20"
                },

                # New Columns - Candle Structure Queries
                {
                    "question": "Show me candles with long upper wicks (> 20 points)",
                    "sql": "SELECT * FROM candlestick_5min WHERE upper_wick > 20 ORDER BY time_interval DESC LIMIT 50"
                },
                {
                    "question": "Find candles with small body and high wick ratio",
                    "sql": "SELECT * FROM candlestick_5min WHERE body < 5 AND wick_ratio > 3 ORDER BY time_interval DESC LIMIT 30"
                },
                {
                    "question": "What's the average wick ratio for NQ candles?",
                    "sql": "SELECT AVG(wick_ratio) as avg_wick_ratio FROM candlestick_5min WHERE symbol = 'NQ' AND wick_ratio IS NOT NULL"
                },
                {
                    "question": "Show me doji candles (small body, large wicks)",
                    "sql": "SELECT * FROM candlestick_5min WHERE body < 2 AND (upper_wick + lower_wick) > 15 ORDER BY time_interval DESC LIMIT 50"
                },

                # New Columns - Volume Distribution Queries
                {
                    "question": "Find candles with most volume in upper wick",
                    "sql": "SELECT * FROM candlestick_5min WHERE upper_wick_volume > body_volume AND upper_wick_volume > lower_wick_volume ORDER BY upper_wick_volume DESC LIMIT 30"
                },
                {
                    "question": "Show me candles with volume concentrated in body",
                    "sql": "SELECT * FROM candlestick_5min WHERE body_volume > upper_wick_volume + lower_wick_volume ORDER BY body_volume DESC LIMIT 50"
                },

                # New Columns - Absorption Indicators
                {
                    "question": "Find candles with strong absorption by sellers in upper wick",
                    "sql": "SELECT * FROM candlestick_5min WHERE asellers_uwick > 10000 ORDER BY asellers_uwick DESC LIMIT 30"
                },
                {
                    "question": "Show me candles with buyer absorption in lower wick",
                    "sql": "SELECT * FROM candlestick_5min WHERE abuyers_lwick > 10000 ORDER BY abuyers_lwick DESC LIMIT 30"
                },
                {
                    "question": "Find rejection candles (high absorption in wicks)",
                    "sql": "SELECT * FROM candlestick_5min WHERE (asellers_uwick + abuyers_lwick) > 20000 ORDER BY time_interval DESC LIMIT 50"
                },

                # New Columns - Footprint Data (JSONB)
                {
                    "question": "Show me candles with footprint data",
                    "sql": "SELECT time_interval, symbol, oflow_detail, oflow_unit FROM candlestick_5min WHERE oflow_detail IS NOT NULL LIMIT 10"
                },
                {
                    "question": "Count candles that have detailed footprint data",
                    "sql": "SELECT COUNT(*) FROM candlestick_5min WHERE oflow_detail IS NOT NULL"
                },

                # Active Contracts - NQ Resolution
                # When user mentions "NQ", use JOIN with active_contracts to get the current contract
                {
                    "question": "Dame el maximo valor de NQ en noviembre",
                    "sql": """SELECT MAX(c.high) as max_price
                        FROM candlestick_5min c
                        INNER JOIN active_contracts ac ON c.symbol = ac.symbol
                        WHERE ac.is_current = true
                        AND EXTRACT(MONTH FROM c.time_interval AT TIME ZONE 'America/New_York') = 11"""
                },
                {
                    "question": "Cuantas velas de NQ tenemos hoy?",
                    "sql": """SELECT COUNT(*) as candle_count
                        FROM candlestick_5min c
                        INNER JOIN active_contracts ac ON c.symbol = ac.symbol
                        WHERE ac.is_current = true
                        AND DATE(c.time_interval AT TIME ZONE 'America/New_York') = CURRENT_DATE"""
                },
                {
                    "question": "Muestra candles de NQ de 5min en la sesion de NY del 15 de noviembre",
                    "sql": """SELECT c.*
                        FROM candlestick_5min c
                        INNER JOIN active_contracts ac ON c.symbol = ac.symbol
                        WHERE ac.is_current = true
                        AND c.time_interval AT TIME ZONE 'America/New_York' >= '2024-11-15 09:30:00'::timestamp
                        AND c.time_interval AT TIME ZONE 'America/New_York' < '2024-11-15 16:00:00'::timestamp
                        ORDER BY c.time_interval"""
                },
                {
                    "question": "Cual es el contrato activo de NQ actualmente?",
                    "sql": "SELECT symbol, start_date, volume_score FROM active_contracts WHERE is_current = true"
                },
                {
                    "question": "Dame el volumen promedio de NQ esta semana",
                    "sql": """SELECT AVG(c.volume) as avg_volume
                        FROM candlestick_5min c
                        INNER JOIN active_contracts ac ON c.symbol = ac.symbol
                        WHERE ac.is_current = true
                        AND c.time_interval >= CURRENT_DATE - 7"""
                },
                {
                    "question": "Muestra FVGs del contrato activo",
                    "sql": """SELECT f.*
                        FROM detected_fvgs f
                        INNER JOIN candlestick_5min c ON DATE(f.formation_time) = DATE(c.time_interval)
                        INNER JOIN active_contracts ac ON c.symbol = ac.symbol
                        WHERE ac.is_current = true
                        AND f.status = 'UNMITIGATED'
                        ORDER BY f.formation_time DESC"""
                },
                {
                    "question": "Dame el POC real de las ultimas 10 velas de NQ",
                    "sql": """SELECT c.time_interval, c.real_poc, c.real_poc_volume
                        FROM candlestick_5min c
                        INNER JOIN active_contracts ac ON c.symbol = ac.symbol
                        WHERE ac.is_current = true
                        ORDER BY c.time_interval DESC
                        LIMIT 10"""
                },
                {
                    "question": "Cual fue el ultimo contrato antes del actual?",
                    "sql": """SELECT symbol, start_date, end_date, volume_score
                        FROM active_contracts
                        WHERE is_current = false
                        ORDER BY end_date DESC
                        LIMIT 1"""
                },
            ]

            for example in example_queries:
                self.vn.train(question=example["question"], sql=example["sql"])

            logger.info(f"Vanna schema training completed with {len(example_queries)} examples")

        except Exception as e:
            logger.error(f"Failed to train Vanna schema: {e}")

    def generate_sql(self, question: str) -> Optional[str]:
        """
        Generate SQL from natural language question

        Args:
            question: Natural language question

        Returns:
            Generated SQL query or None if failed
        """
        if not self.vn:
            return None

        try:
            sql = self.vn.generate_sql(question)

            # Handle intermediate_sql responses from Vanna
            if sql and 'intermediate_sql' in sql.lower():
                # Extract SQL from intermediate response
                lines = sql.split('\n')
                sql_lines = []
                capture = False

                for line in lines:
                    line_stripped = line.strip()
                    # Start capturing after 'intermediate_sql' marker
                    if 'intermediate_sql' in line_stripped.lower():
                        capture = True
                        continue
                    # Stop at explanatory text (Spanish or English)
                    if capture and (line_stripped.startswith('Basado') or
                                   line_stripped.startswith('Based') or
                                   line_stripped.startswith('Sin conocer')):
                        break
                    # Capture SQL lines
                    if capture and line_stripped and line_stripped.upper().startswith('SELECT'):
                        sql_lines.append(line_stripped)
                    elif capture and sql_lines:  # Continue multi-line SQL
                        sql_lines.append(line_stripped)

                if sql_lines:
                    sql = '\n'.join(sql_lines)
                else:
                    # If we couldn't extract SQL, return None to indicate failure
                    logger.warning(f"Could not extract SQL from intermediate_sql response: {sql[:200]}")
                    return None

            return sql
        except Exception as e:
            logger.error(f"Failed to generate SQL: {e}")
            return None

    def _validate_sql(self, sql: str) -> tuple[bool, Optional[str]]:
        """
        Validate SQL query for safety

        Args:
            sql: SQL query to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not sql:
            return False, "Empty SQL query"

        sql_upper = sql.upper().strip()

        # Block dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False, f"Dangerous operation detected: {keyword}"

        # Must be a SELECT query or CTE (WITH ... SELECT)
        if not (sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')):
            return False, "Only SELECT queries (including CTEs) are allowed"

        return True, None

    def ask(
        self,
        question: str,
        table_hint: Optional[str] = None,
        auto_train: bool = True,
        timeout_seconds: int = 120
    ) -> Dict[str, Any]:
        """
        Ask a question in natural language and get results

        Args:
            question: Natural language question
            table_hint: Optional hint about which table to use (e.g., "candlestick_daily")
            auto_train: Automatically train Vanna with successful query
            timeout_seconds: Query timeout in seconds (default 120)

        Returns:
            Dict with 'sql', 'results', 'success', 'error'
        """
        if not self.vn:
            return {
                "success": False,
                "error": "Vanna is not available. Please check API keys.",
                "sql": None,
                "results": None
            }

        try:
            # If table_hint provided, prepend to question
            enhanced_question = question
            if table_hint:
                enhanced_question = f"use {table_hint}: {question}"
                logger.info(f"Enhanced question with table hint: {enhanced_question}")

            # Generate SQL
            sql = self.generate_sql(enhanced_question)
            if not sql:
                return {
                    "success": False,
                    "error": "Failed to generate SQL from your question",
                    "sql": None,
                    "results": None
                }

            # Validate SQL for safety
            is_valid, error_msg = self._validate_sql(sql)
            if not is_valid:
                return {
                    "success": False,
                    "error": f"SQL validation failed: {error_msg}",
                    "sql": sql,
                    "results": None
                }

            # Execute query without timeout
            db = SessionLocal()
            try:
                # No timeout - let queries run as long as needed
                result = db.execute(text(sql))
                rows = result.fetchall()

                # Convert to list of dicts
                if rows:
                    columns = result.keys()
                    results = [dict(zip(columns, row)) for row in rows]
                else:
                    results = []

                # Auto-train on successful query
                if auto_train:
                    try:
                        self.vn.train(question=question, sql=sql)
                        logger.info(f"Auto-trained Vanna with: {question[:50]}...")
                    except Exception as train_error:
                        logger.warning(f"Failed to auto-train: {train_error}")

                return {
                    "success": True,
                    "sql": sql,
                    "results": results,
                    "error": None
                }

            finally:
                db.close()

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to execute query: {error_msg}")

            # Provide user-friendly error messages
            if "timeout" in error_msg.lower():
                error_msg = f"Query timed out after {timeout_seconds} seconds"
            elif "syntax error" in error_msg.lower():
                error_msg = "SQL syntax error in generated query"

            return {
                "success": False,
                "error": error_msg,
                "sql": sql if 'sql' in locals() else None,
                "results": None
            }

    def train_from_feedback(
        self,
        question: str,
        sql: str,
        was_successful: bool,
        feedback_score: Optional[int] = None
    ):
        """
        Train Vanna from user feedback

        Args:
            question: Original question
            sql: Generated SQL
            was_successful: Whether query executed successfully
            feedback_score: User rating 1-5
        """
        if not self.vn or not was_successful:
            return

        try:
            self.vn.train(question=question, sql=sql)
            logger.info(f"Trained Vanna from feedback: {question[:50]}...")
        except Exception as e:
            logger.error(f"Failed to train from feedback: {e}")


# Create singleton instance
_vanna_client: Optional[VannaNQHub] = None


def get_vanna_client() -> VannaNQHub:
    """Get or create Vanna client singleton"""
    global _vanna_client
    if _vanna_client is None:
        _vanna_client = VannaNQHub()
    return _vanna_client
