"""
Candle Builder Service

Aggregates tick data into candlesticks for different timeframes.
Calculates OHLCV, Delta, CVD, and volume profile metrics.
"""
from typing import List, Dict
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

# Timeframe interval mappings
TIMEFRAME_INTERVALS = {
    '30s': '30 seconds',
    '1min': '1 minute',
    '5min': '5 minutes',
    '15min': '15 minutes',
    '1hr': '1 hour',
    '4hr': '4 hours',
    'daily': '1 day',
    'weekly': '7 days',
}


async def build_candles_for_day(
    session: AsyncSession,
    symbol: str,
    day: date,
    timeframes: List[str]
) -> Dict[str, int]:
    """
    Build candles for a specific day and selected timeframes.

    Args:
        session: Async database session
        symbol: Trading symbol
        day: Date to process
        timeframes: List of timeframe strings (e.g., ['5min', '1hr'])

    Returns:
        Dictionary with candle counts per timeframe
    """
    results = {}

    logger.info(f"🔨 build_candles_for_day() called: symbol={symbol}, day={day}, timeframes={timeframes}")

    # Verify we have tick data for this day
    tick_count = await count_ticks_for_day(session, symbol, day)
    logger.info(f"📊 count_ticks_for_day() returned: {tick_count} ticks for {symbol} on {day}")

    if tick_count == 0:
        logger.warning(f"⚠️ No ticks found for {symbol} on {day} - skipping candle generation")
        return results

    logger.info(f"✅ Found {tick_count} ticks for {symbol} on {day} - proceeding with candle generation")

    # Build candles for each timeframe
    for timeframe in timeframes:
        try:
            logger.info(f"🔄 Calling build_candles_for_timeframe() for {symbol}/{day}/{timeframe}")
            count = await build_candles_for_timeframe(session, symbol, day, timeframe)
            results[timeframe] = count
            logger.info(f"✅ Built {count} {timeframe} candles for {symbol} on {day}")

        except Exception as e:
            logger.error(f"❌ Failed to build {timeframe} candles for {symbol} on {day}: {str(e)}", exc_info=True)
            results[timeframe] = 0

    logger.info(f"📦 build_candles_for_day() returning results for {symbol}/{day}: {results}")
    return results


async def build_candles_for_timeframe(
    session: AsyncSession,
    symbol: str,
    day: date,
    timeframe: str
) -> int:
    """
    Build candles for a specific timeframe using PostgreSQL time_bucket.

    Args:
        session: Async database session
        symbol: Trading symbol
        day: Date to process
        timeframe: Timeframe string

    Returns:
        Number of candles created
    """
    if timeframe not in TIMEFRAME_INTERVALS:
        raise ValueError(f"Invalid timeframe: {timeframe}")

    table_name = f"candlestick_{timeframe}"
    interval = TIMEFRAME_INTERVALS[timeframe]

    # Start and end of day
    start_time = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_time = start_time + timedelta(days=1)

    logger.info(f"🔧 build_candles_for_timeframe(): symbol={symbol}, timeframe={timeframe}, day={day}")
    logger.info(f"   Table: {table_name}, Interval: {interval}, Start: {start_time}, End: {end_time}")

    # Build comprehensive aggregation query using TimescaleDB time_bucket with CTEs
    # Note: interval is interpolated directly (safe, from our dict), not a bind parameter
    query = text(f"""
        WITH base_candles AS (
            -- Step 1: Calculate basic OHLCV and delta
            SELECT
                time_bucket('{interval}'::interval, ts_event) AS time_interval,
                (array_agg(price ORDER BY ts_event))[1] AS open,
                MAX(price) AS high,
                MIN(price) AS low,
                (array_agg(price ORDER BY ts_event DESC))[1] AS close,
                SUM(size) AS volume,
                SUM(CASE WHEN side = 'B' THEN size WHEN side = 'A' THEN -size ELSE 0 END) AS delta,
                COUNT(*) AS tick_count
            FROM market_data_ticks
            WHERE symbol = :symbol
              AND ts_event >= :start_time
              AND ts_event < :end_time
            GROUP BY time_interval
        ),
        candle_structure AS (
            -- Step 2: Calculate candle structure metrics
            SELECT
                time_interval,
                open, high, low, close, volume, delta, tick_count,
                -- Candle structure
                high - GREATEST(open, close) AS upper_wick,
                LEAST(open, close) - low AS lower_wick,
                ABS(close - open) AS body,
                -- Ratios (handle divide by zero)
                CASE
                    WHEN ABS(close - open) > 0 THEN
                        (high - GREATEST(open, close) + LEAST(open, close) - low) / ABS(close - open)
                    ELSE NULL
                END AS wick_ratio,
                CASE
                    WHEN (high - low) > 0 THEN (high - GREATEST(open, close)) / (high - low)
                    ELSE NULL
                END AS rel_uw,
                CASE
                    WHEN (high - low) > 0 THEN (LEAST(open, close) - low) / (high - low)
                    ELSE NULL
                END AS rel_lw
            FROM base_candles
        ),
        volume_by_price AS (
            -- Step 3: Group volume by exact price (0.25 tick precision) for POC and volume distribution
            SELECT
                time_bucket('{interval}'::interval, ts_event) AS time_bucket_interval,
                price,
                SUM(size) AS total_volume,
                SUM(CASE WHEN side = 'A' THEN size ELSE 0 END) AS ask_volume,
                SUM(CASE WHEN side = 'B' THEN size ELSE 0 END) AS bid_volume
            FROM market_data_ticks
            WHERE symbol = :symbol
              AND ts_event >= :start_time
              AND ts_event < :end_time
            GROUP BY time_bucket_interval, price
        ),
        volume_by_point AS (
            -- Step 4: Group volume by whole point (1.0 precision) for POC calculation
            SELECT
                time_bucket_interval,
                FLOOR(price) AS price_point,
                SUM(total_volume) AS total_volume
            FROM volume_by_price
            GROUP BY time_bucket_interval, FLOOR(price)
        ),
        poc_calc AS (
            -- Step 5: Calculate Point of Control (1.0 point precision)
            SELECT DISTINCT ON (time_bucket_interval)
                time_bucket_interval,
                price_point AS poc,
                total_volume AS poc_volume
            FROM volume_by_point
            ORDER BY time_bucket_interval, total_volume DESC, price_point DESC
        ),
        poc_real_calc AS (
            -- Step 6: Calculate Real POC (exact 0.25 tick precision)
            SELECT DISTINCT ON (time_bucket_interval)
                time_bucket_interval,
                price AS real_poc,
                total_volume AS real_poc_volume
            FROM volume_by_price
            ORDER BY time_bucket_interval, total_volume DESC, price DESC
        ),
        volume_distribution AS (
            -- Step 7: Calculate volume distribution in body/wicks
            SELECT
                cs.time_interval,
                -- Upper wick volume (prices above body)
                COALESCE(SUM(
                    CASE
                        WHEN vbp.price > GREATEST(cs.open, cs.close) AND vbp.price <= cs.high
                        THEN vbp.total_volume
                        ELSE 0
                    END
                ), 0) AS upper_wick_volume,
                -- Lower wick volume (prices below body)
                COALESCE(SUM(
                    CASE
                        WHEN vbp.price < LEAST(cs.open, cs.close) AND vbp.price >= cs.low
                        THEN vbp.total_volume
                        ELSE 0
                    END
                ), 0) AS lower_wick_volume,
                -- Body volume (prices within body)
                COALESCE(SUM(
                    CASE
                        WHEN vbp.price >= LEAST(cs.open, cs.close)
                         AND vbp.price <= GREATEST(cs.open, cs.close)
                        THEN vbp.total_volume
                        ELSE 0
                    END
                ), 0) AS body_volume
            FROM candle_structure cs
            LEFT JOIN volume_by_price vbp ON cs.time_interval = vbp.time_bucket_interval
            GROUP BY cs.time_interval
        ),
        absorption_metrics AS (
            -- Step 8: Calculate absorption indicators (aggressive sellers/buyers in wicks)
            SELECT
                cs.time_interval,
                -- Aggressive sellers in upper wick (side='A')
                COALESCE(SUM(
                    CASE
                        WHEN vbp.price > GREATEST(cs.open, cs.close) AND vbp.price <= cs.high
                        THEN vbp.ask_volume
                        ELSE 0
                    END
                ), 0) AS asellers_uwick,
                -- Aggressive sellers in lower wick
                COALESCE(SUM(
                    CASE
                        WHEN vbp.price < LEAST(cs.open, cs.close) AND vbp.price >= cs.low
                        THEN vbp.ask_volume
                        ELSE 0
                    END
                ), 0) AS asellers_lwick,
                -- Aggressive buyers in upper wick (side='B')
                COALESCE(SUM(
                    CASE
                        WHEN vbp.price > GREATEST(cs.open, cs.close) AND vbp.price <= cs.high
                        THEN vbp.bid_volume
                        ELSE 0
                    END
                ), 0) AS abuyers_uwick,
                -- Aggressive buyers in lower wick
                COALESCE(SUM(
                    CASE
                        WHEN vbp.price < LEAST(cs.open, cs.close) AND vbp.price >= cs.low
                        THEN vbp.bid_volume
                        ELSE 0
                    END
                ), 0) AS abuyers_lwick
            FROM candle_structure cs
            LEFT JOIN volume_by_price vbp ON cs.time_interval = vbp.time_bucket_interval
            GROUP BY cs.time_interval
        ),
        orderflow_detail AS (
            -- Step 9: Build orderflow detail JSONB (0.25 tick precision)
            SELECT
                time_bucket_interval AS time_interval,
                jsonb_object_agg(
                    price::text,
                    jsonb_build_object(
                        'asks', ask_volume,
                        'bids', bid_volume
                    )
                ) AS oflow_detail
            FROM volume_by_price
            GROUP BY time_bucket_interval
        ),
        orderflow_unit AS (
            -- Step 10: Build orderflow unit JSONB (1.0 point precision)
            SELECT
                time_bucket_interval AS time_interval,
                jsonb_object_agg(
                    price_point::text,
                    jsonb_build_object(
                        'asks', ask_volume,
                        'bids', bid_volume
                    )
                ) AS oflow_unit
            FROM (
                SELECT
                    time_bucket_interval,
                    FLOOR(price) AS price_point,
                    SUM(ask_volume) AS ask_volume,
                    SUM(bid_volume) AS bid_volume
                FROM volume_by_price
                GROUP BY time_bucket_interval, FLOOR(price)
            ) grouped
            GROUP BY time_bucket_interval
        )
        -- Final INSERT combining all CTEs
        INSERT INTO {table_name} (
            time_interval, symbol, is_spread, is_rollover_period,
            open, high, low, close, volume,
            poc, poc_volume, poc_percentage, poc_location, poc_position,
            real_poc, real_poc_volume, real_poc_percentage, real_poc_location,
            upper_wick, lower_wick, body, wick_ratio, rel_uw, rel_lw,
            upper_wick_volume, lower_wick_volume, body_volume,
            asellers_uwick, asellers_lwick, abuyers_uwick, abuyers_lwick,
            delta, oflow_detail, oflow_unit,
            tick_count
        )
        SELECT
            cs.time_interval,
            CAST(:symbol AS VARCHAR) AS symbol,
            false AS is_spread,
            false AS is_rollover_period,
            -- OHLCV
            cs.open, cs.high, cs.low, cs.close, cs.volume,
            -- POC (1.0 point precision)
            poc.poc,
            poc.poc_volume,
            CASE WHEN cs.volume > 0 THEN (poc.poc_volume::numeric / cs.volume * 100.0) ELSE NULL END AS poc_percentage,
            CASE
                WHEN poc.poc > GREATEST(cs.open, cs.close) THEN 'upper_wick'
                WHEN poc.poc < LEAST(cs.open, cs.close) THEN 'lower_wick'
                ELSE 'body'
            END AS poc_location,
            CASE
                WHEN (cs.high - cs.low) > 0 THEN (poc.poc - cs.low) / (cs.high - cs.low)
                ELSE 0.5
            END AS poc_position,
            -- Real POC (0.25 tick precision)
            poc_real.real_poc,
            poc_real.real_poc_volume,
            CASE WHEN cs.volume > 0 THEN (poc_real.real_poc_volume::numeric / cs.volume * 100.0) ELSE NULL END AS real_poc_percentage,
            CASE
                WHEN poc_real.real_poc > GREATEST(cs.open, cs.close) THEN 'upper_wick'
                WHEN poc_real.real_poc < LEAST(cs.open, cs.close) THEN 'lower_wick'
                ELSE 'body'
            END AS real_poc_location,
            -- Candle structure
            cs.upper_wick, cs.lower_wick, cs.body,
            cs.wick_ratio, cs.rel_uw, cs.rel_lw,
            -- Volume distribution
            vd.upper_wick_volume, vd.lower_wick_volume, vd.body_volume,
            -- Absorption
            am.asellers_uwick, am.asellers_lwick,
            am.abuyers_uwick, am.abuyers_lwick,
            -- Order flow
            cs.delta,
            ofd.oflow_detail,
            ofu.oflow_unit,
            -- Metadata
            cs.tick_count
        FROM candle_structure cs
        LEFT JOIN poc_calc poc ON cs.time_interval = poc.time_bucket_interval
        LEFT JOIN poc_real_calc poc_real ON cs.time_interval = poc_real.time_bucket_interval
        LEFT JOIN volume_distribution vd ON cs.time_interval = vd.time_interval
        LEFT JOIN absorption_metrics am ON cs.time_interval = am.time_interval
        LEFT JOIN orderflow_detail ofd ON cs.time_interval = ofd.time_interval
        LEFT JOIN orderflow_unit ofu ON cs.time_interval = ofu.time_interval
        ORDER BY cs.time_interval
        ON CONFLICT (time_interval, symbol) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume,
            poc = EXCLUDED.poc,
            poc_volume = EXCLUDED.poc_volume,
            poc_percentage = EXCLUDED.poc_percentage,
            poc_location = EXCLUDED.poc_location,
            poc_position = EXCLUDED.poc_position,
            real_poc = EXCLUDED.real_poc,
            real_poc_volume = EXCLUDED.real_poc_volume,
            real_poc_percentage = EXCLUDED.real_poc_percentage,
            real_poc_location = EXCLUDED.real_poc_location,
            upper_wick = EXCLUDED.upper_wick,
            lower_wick = EXCLUDED.lower_wick,
            body = EXCLUDED.body,
            wick_ratio = EXCLUDED.wick_ratio,
            rel_uw = EXCLUDED.rel_uw,
            rel_lw = EXCLUDED.rel_lw,
            upper_wick_volume = EXCLUDED.upper_wick_volume,
            lower_wick_volume = EXCLUDED.lower_wick_volume,
            body_volume = EXCLUDED.body_volume,
            asellers_uwick = EXCLUDED.asellers_uwick,
            asellers_lwick = EXCLUDED.asellers_lwick,
            abuyers_uwick = EXCLUDED.abuyers_uwick,
            abuyers_lwick = EXCLUDED.abuyers_lwick,
            delta = EXCLUDED.delta,
            oflow_detail = EXCLUDED.oflow_detail,
            oflow_unit = EXCLUDED.oflow_unit,
            tick_count = EXCLUDED.tick_count
    """)

    try:
        logger.info(f"🔄 Executing comprehensive SQL INSERT for {timeframe} candles (33 fields)...")
        result = await session.execute(query, {
            'symbol': symbol,
            'start_time': start_time,
            'end_time': end_time
        })
        logger.info(f"✅ SQL executed successfully, rowcount: {result.rowcount}")

        await session.commit()
        logger.info(f"✅ Transaction committed")

        candle_count = result.rowcount
        logger.info(f"📊 Created/updated {candle_count} {timeframe} candles for {symbol} on {day}")

        # Update candle_coverage table
        logger.info(f"📝 Updating candle_coverage for {symbol}/{timeframe}/{day}")
        await update_candle_coverage(session, symbol, timeframe, day, candle_count)

        logger.info(f"✅ Returning candle_count={candle_count}")
        return candle_count

    except Exception as e:
        await session.rollback()
        logger.error(f"❌ Failed to build {timeframe} candles for {symbol} on {day}: {str(e)}", exc_info=True)
        raise


async def count_ticks_for_day(session: AsyncSession, symbol: str, day: date) -> int:
    """
    Count ticks available for a specific day.

    Args:
        session: Async database session
        symbol: Trading symbol
        day: Date to check

    Returns:
        Number of ticks
    """
    start_time = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_time = start_time + timedelta(days=1)

    query = text("""
        SELECT COUNT(*)
        FROM market_data_ticks
        WHERE symbol = :symbol
          AND ts_event >= :start_time
          AND ts_event < :end_time
    """)

    result = await session.execute(query, {
        'symbol': symbol,
        'start_time': start_time,
        'end_time': end_time
    })

    return result.scalar() or 0


async def update_candle_coverage(
    session: AsyncSession,
    symbol: str,
    timeframe: str,
    day: date,
    candle_count: int
):
    """
    Update or create candle_coverage record.

    Args:
        session: Async database session
        symbol: Trading symbol
        timeframe: Timeframe string
        day: Date processed
        candle_count: Number of candles created
    """
    query = text("""
        INSERT INTO candle_coverage (symbol, timeframe, date, status, candle_count)
        VALUES (:symbol, :timeframe, :date, :status, :candle_count)
        ON CONFLICT (symbol, timeframe, date) DO UPDATE SET
            status = EXCLUDED.status,
            candle_count = EXCLUDED.candle_count,
            updated_at = NOW()
    """)

    status = 'completed' if candle_count > 0 else 'no_data'

    try:
        await session.execute(query, {
            'symbol': symbol,
            'timeframe': timeframe,
            'date': day,
            'status': status,
            'candle_count': candle_count
        })
        await session.commit()
        logger.info(f"Updated candle_coverage: {symbol}/{timeframe}/{day} = {candle_count} candles")

    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to update candle_coverage: {str(e)}")


async def get_available_dates(session: AsyncSession, symbol: str) -> List[date]:
    """
    Get list of dates with tick data available for a symbol.

    Args:
        session: Async database session
        symbol: Trading symbol

    Returns:
        List of dates
    """
    query = text("""
        SELECT DISTINCT DATE(ts_event) as date
        FROM market_data_ticks
        WHERE symbol = :symbol
        ORDER BY date
    """)

    result = await session.execute(query, {'symbol': symbol})
    rows = result.fetchall()

    return [row[0] for row in rows]


async def delete_candles_for_symbol(
    session: AsyncSession,
    symbol: str,
    timeframe: str
) -> int:
    """
    Delete all candles for a symbol in a specific timeframe.

    Args:
        session: Async database session
        symbol: Trading symbol
        timeframe: Timeframe to delete

    Returns:
        Number of candles deleted
    """
    table_name = f"candlestick_{timeframe}"

    query = text(f"DELETE FROM {table_name} WHERE symbol = :symbol")

    try:
        result = await session.execute(query, {'symbol': symbol})
        await session.commit()

        deleted_count = result.rowcount
        logger.info(f"Deleted {deleted_count} {timeframe} candles for {symbol}")

        return deleted_count

    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to delete candles: {str(e)}")
        raise


async def get_unique_symbols_for_date_range(
    session: AsyncSession,
    start_date: date,
    end_date: date
) -> List[str]:
    """
    Obtiene todos los símbolos únicos presentes en un rango de fechas.

    Args:
        session: Async database session
        start_date: Fecha inicial
        end_date: Fecha final

    Returns:
        Lista de símbolos únicos ordenados
    """
    query = text("""
        SELECT DISTINCT symbol
        FROM market_data_ticks
        WHERE DATE(ts_event) BETWEEN :start_date AND :end_date
        ORDER BY symbol
    """)

    result = await session.execute(query, {
        "start_date": start_date,
        "end_date": end_date
    })

    symbols = [row[0] for row in result.fetchall()]
    logger.info(f"Found {len(symbols)} unique symbols between {start_date} and {end_date}: {symbols}")

    return symbols


def is_spread_symbol(symbol: str) -> bool:
    """
    Detecta si un símbolo es un calendar spread (contiene '-').

    Args:
        symbol: Símbolo a verificar (ej: "NQM4-NQU4")

    Returns:
        True si es spread, False si es contrato outright
    """
    return '-' in symbol


# TODO: Advanced candle calculations for future implementation
async def calculate_volume_profile(session: AsyncSession, candle_id: int):
    """
    Calculate POC, volume distribution, and absorption metrics.
    This is a placeholder for future implementation.
    """
    pass


async def calculate_orderflow_detail(session: AsyncSession, candle_id: int):
    """
    Calculate detailed orderflow metrics (oflow_detail, oflow_unit).
    This is a placeholder for future implementation.
    """
    pass
