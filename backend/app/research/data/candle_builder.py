"""
Candle Builder

Genera candles OHLCV + order flow aggregado por timeframe
desde los ticks en TimescaleDB.

Este módulo es un thin wrapper sobre app.etl.services.candle_builder
para cumplir con la interfaz especificada en AUT-329.
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.services.candle_builder import (
    build_candles_for_day,
    build_candles_for_timeframe,
    get_available_dates,
    get_unique_symbols_for_date_range,
    TIMEFRAME_INTERVALS
)
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class CandleBuilder:
    """
    Genera candles OHLCV + order flow aggregado por timeframe
    desde los ticks en TimescaleDB.
    """

    # Timeframes según AUT-329 (mapeados a los nombres internos existentes)
    TIMEFRAMES = ['30s', '1min', '5min', '15min', '1h', '4h', '1d', '1w']

    # Mapping entre nombres del issue y nombres internos
    TIMEFRAME_MAPPING = {
        '30s': '30s',
        '1min': '1min',
        '5min': '5min',
        '15min': '15min',
        '1h': '1hr',      # Issue usa '1h', código usa '1hr'
        '4h': '4hr',      # Issue usa '4h', código usa '4hr'
        '1d': 'daily',    # Issue usa '1d', código usa 'daily'
        '1w': 'weekly',   # Issue usa '1w', código usa 'weekly'
    }

    def __init__(self, session: AsyncSession = None):
        """
        Initialize candle builder.

        Args:
            session: Optional async database session. If not provided,
                     will create new session for each operation.
        """
        self.session = session

    async def build_candles(
        self,
        timeframe: str,
        start: datetime,
        end: datetime,
        symbol: str = None
    ) -> int:
        """
        Agrega ticks → candles para el timeframe dado.

        Persiste en tabla candles_{timeframe} en TimescaleDB.
        Los 35 campos de oflow se agregan como JSONB.

        Args:
            timeframe: Timeframe string ('30s', '1min', '5min', '15min', '1h', '4h', '1d', '1w')
            start: Fecha/hora inicial
            end: Fecha/hora final
            symbol: Optional symbol filter. If not provided, processes all symbols in date range.

        Returns:
            Número de candles generados

        Raises:
            ValueError: Si el timeframe no es válido
        """
        if timeframe not in self.TIMEFRAMES:
            raise ValueError(
                f"Invalid timeframe: {timeframe}. "
                f"Valid options: {', '.join(self.TIMEFRAMES)}"
            )

        # Map to internal timeframe name
        internal_timeframe = self.TIMEFRAME_MAPPING[timeframe]

        logger.info(
            f"Building {timeframe} candles from {start} to {end}"
            f"{f' for symbol {symbol}' if symbol else ''}"
        )

        total_candles = 0

        if self.session:
            session = self.session
            should_close = False
        else:
            session = AsyncSessionLocal()
            should_close = True

        try:
            # Get date range
            current_date = start.date()
            end_date = end.date()

            # Get symbols to process
            if symbol:
                symbols = [symbol]
            else:
                symbols = await get_unique_symbols_for_date_range(
                    session, current_date, end_date
                )
                logger.info(f"Found {len(symbols)} symbols to process: {symbols}")

            # Process each day
            while current_date <= end_date:
                logger.info(f"Processing {current_date} for {len(symbols)} symbols...")

                for sym in symbols:
                    try:
                        count = await build_candles_for_timeframe(
                            session,
                            sym,
                            current_date,
                            internal_timeframe
                        )
                        total_candles += count
                        logger.info(f"  {sym}: {count} {timeframe} candles")
                    except Exception as e:
                        logger.error(
                            f"Failed to build {timeframe} candles for {sym} on {current_date}: {e}"
                        )
                        continue

                current_date += timedelta(days=1)

            logger.info(
                f"Built {total_candles} {timeframe} candles "
                f"from {start.date()} to {end.date()}"
            )
            return total_candles

        finally:
            if should_close:
                await session.close()

    async def build_all_timeframes(
        self,
        start: datetime,
        end: datetime,
        symbol: str = None
    ) -> Dict[str, int]:
        """
        Corre build_candles() para todos los timeframes.

        Args:
            start: Fecha/hora inicial
            end: Fecha/hora final
            symbol: Optional symbol filter

        Returns:
            Dictionary {timeframe: candles_count}
        """
        logger.info(
            f"Building ALL timeframes from {start} to {end}"
            f"{f' for symbol {symbol}' if symbol else ''}"
        )

        results = {}

        for timeframe in self.TIMEFRAMES:
            try:
                count = await self.build_candles(timeframe, start, end, symbol)
                results[timeframe] = count
            except Exception as e:
                logger.error(f"Failed to build {timeframe} candles: {e}")
                results[timeframe] = 0
                continue

        total = sum(results.values())
        logger.info(f"Built {total} total candles across {len(self.TIMEFRAMES)} timeframes")

        return results

    async def build_candles_for_day(
        self,
        symbol: str,
        day: date,
        timeframes: List[str] = None
    ) -> Dict[str, int]:
        """
        Build candles for a specific day and selected timeframes.

        Args:
            symbol: Trading symbol
            day: Date to process
            timeframes: List of timeframe strings. If None, builds all timeframes.

        Returns:
            Dictionary with candle counts per timeframe
        """
        if timeframes is None:
            timeframes = self.TIMEFRAMES

        # Validate and map timeframes
        internal_timeframes = []
        for tf in timeframes:
            if tf not in self.TIMEFRAMES:
                raise ValueError(f"Invalid timeframe: {tf}")
            internal_timeframes.append(self.TIMEFRAME_MAPPING[tf])

        if self.session:
            session = self.session
            should_close = False
        else:
            session = AsyncSessionLocal()
            should_close = True

        try:
            # Use existing service function
            results = await build_candles_for_day(
                session,
                symbol,
                day,
                internal_timeframes
            )

            # Map back to external timeframe names
            external_results = {}
            reverse_mapping = {v: k for k, v in self.TIMEFRAME_MAPPING.items()}
            for internal_tf, count in results.items():
                external_tf = reverse_mapping.get(internal_tf, internal_tf)
                external_results[external_tf] = count

            return external_results

        finally:
            if should_close:
                await session.close()

    async def get_available_dates(self, symbol: str) -> List[date]:
        """
        Get list of dates with tick data available for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            List of dates
        """
        if self.session:
            dates = await get_available_dates(self.session, symbol)
            return dates
        else:
            async with AsyncSessionLocal() as session:
                dates = await get_available_dates(session, symbol)
                return dates
