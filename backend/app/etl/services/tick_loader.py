"""
Tick Loader Service

Handles bulk insertion of tick data into market_data_ticks table.
"""
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
import hashlib

logger = logging.getLogger(__name__)


def generate_tick_hash(tick: Dict) -> str:
    """
    Generate a unique hash for a tick based on its content.

    Uses: ts_event, symbol, price, size, side
    These fields should uniquely identify a tick.

    Args:
        tick: Dictionary with tick data

    Returns:
        32-character hash string
    """
    # Create unique string from key fields
    unique_str = f"{tick['ts_event']}_{tick['symbol']}_{tick['price']}_{tick['size']}_{tick['side']}"

    # Generate MD5 hash (32 characters when hex encoded)
    return hashlib.md5(unique_str.encode()).hexdigest()


async def load_ticks_batch(session: AsyncSession, ticks: List[Dict]) -> tuple[int, int]:
    """
    Bulk insert a batch of ticks into market_data_ticks table.

    Args:
        session: Async database session
        ticks: List of tick dictionaries with all required fields

    Returns:
        Tuple of (Number of records inserted, Number of duplicates skipped)

    Raises:
        Exception: If insertion fails
    """
    if not ticks:
        logger.warning("Received empty ticks batch, skipping")
        return 0, 0

    batch_size = len(ticks)
    logger.info(f"Inserting batch of {batch_size} ticks...")

    # Generate hash for each tick
    duplicates_skipped = 0
    for tick in ticks:
        tick['tick_hash'] = generate_tick_hash(tick)

    try:
        # Use SQLAlchemy Core bulk insert for better performance
        # Note: We can't use bulk_insert_mappings with AsyncSession directly,
        # so we'll use execute with VALUES clause

        # Build INSERT statement with VALUES and ON CONFLICT for duplicate prevention
        insert_sql = """
        INSERT INTO market_data_ticks (
            tick_hash,
            ts_event, ts_recv, symbol, is_spread, is_rollover_period,
            price, size, side, action,
            bid_px, ask_px, bid_sz, ask_sz, bid_ct, ask_ct,
            rtype, publisher_id, instrument_id, sequence, flags, ts_in_delta, depth
        ) VALUES (
            :tick_hash,
            :ts_event, :ts_recv, :symbol, :is_spread, :is_rollover_period,
            :price, :size, :side, :action,
            :bid_px, :ask_px, :bid_sz, :ask_sz, :bid_ct, :ask_ct,
            :rtype, :publisher_id, :instrument_id, :sequence, :flags, :ts_in_delta, :depth
        )
        ON CONFLICT (tick_hash, ts_event) DO NOTHING
        """

        # Execute many inserts in a single transaction
        result = await session.execute(text(insert_sql), ticks)
        await session.commit()

        # rowcount will be less than batch_size if duplicates were skipped
        inserted_count = result.rowcount
        duplicates_skipped = batch_size - inserted_count

        if duplicates_skipped > 0:
            logger.warning(f"Skipped {duplicates_skipped} duplicate ticks")

        logger.info(f"Successfully inserted {inserted_count} ticks (skipped {duplicates_skipped} duplicates)")
        return inserted_count, duplicates_skipped

    except Exception as e:
        logger.error(f"Failed to insert batch: {str(e)}")
        await session.rollback()
        raise Exception(f"Tick insertion failed: {str(e)}")


async def load_all_ticks(session: AsyncSession, tick_batches: List[List[Dict]]) -> tuple[int, int]:
    """
    Load multiple batches of ticks.

    Args:
        session: Async database session
        tick_batches: List of tick batches

    Returns:
        Tuple of (Total number of records inserted, Total duplicates skipped)
    """
    total_inserted = 0
    total_duplicates = 0

    for i, batch in enumerate(tick_batches, 1):
        logger.info(f"Processing batch {i}/{len(tick_batches)}")

        try:
            count, dups = await load_ticks_batch(session, batch)
            total_inserted += count
            total_duplicates += dups
        except Exception as e:
            logger.error(f"Failed to load batch {i}: {str(e)}")
            # Continue with next batch rather than failing entire load
            continue

    logger.info(f"Completed loading {total_inserted} total ticks from {len(tick_batches)} batches (skipped {total_duplicates} duplicates)")
    return total_inserted, total_duplicates


async def get_tick_count(session: AsyncSession, symbol: str = None) -> int:
    """
    Get total number of ticks in database, optionally filtered by symbol.

    Args:
        session: Async database session
        symbol: Optional symbol filter

    Returns:
        Count of ticks
    """
    try:
        if symbol:
            query = text("SELECT COUNT(*) FROM market_data_ticks WHERE symbol = :symbol")
            result = await session.execute(query, {"symbol": symbol})
        else:
            query = text("SELECT COUNT(*) FROM market_data_ticks")
            result = await session.execute(query)

        count = result.scalar()
        return count or 0

    except Exception as e:
        logger.error(f"Failed to count ticks: {str(e)}")
        return 0


async def get_tick_date_range(session: AsyncSession, symbol: str) -> tuple:
    """
    Get the date range of ticks for a symbol.

    Args:
        session: Async database session
        symbol: Symbol to query

    Returns:
        Tuple of (min_date, max_date) or (None, None) if no data
    """
    try:
        query = text("""
            SELECT MIN(ts_event), MAX(ts_event)
            FROM market_data_ticks
            WHERE symbol = :symbol
        """)
        result = await session.execute(query, {"symbol": symbol})
        row = result.fetchone()

        if row:
            return row[0], row[1]
        return None, None

    except Exception as e:
        logger.error(f"Failed to get date range: {str(e)}")
        return None, None


async def delete_ticks_for_symbol(session: AsyncSession, symbol: str) -> int:
    """
    Delete all ticks for a symbol (useful for re-processing).

    Args:
        session: Async database session
        symbol: Symbol to delete

    Returns:
        Number of records deleted
    """
    try:
        query = text("DELETE FROM market_data_ticks WHERE symbol = :symbol")
        result = await session.execute(query, {"symbol": symbol})
        await session.commit()

        deleted_count = result.rowcount
        logger.info(f"Deleted {deleted_count} ticks for symbol {symbol}")
        return deleted_count

    except Exception as e:
        logger.error(f"Failed to delete ticks: {str(e)}")
        await session.rollback()
        raise
