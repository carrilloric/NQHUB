"""
Candles API Endpoints

Endpoints for retrieving candlestick data.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from app.db.session import get_db
from app.models.candlestick import Candlestick5Min
from app.schemas.candle import CandleResponse, CandleDetailResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{symbol}", response_model=List[CandleResponse])
async def get_candles(
    symbol: str,
    start_datetime: datetime = Query(..., description="Start datetime (ISO format)"),
    end_datetime: Optional[datetime] = Query(None, description="End datetime (ISO format). Defaults to start + 12 hours"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get candlestick data for a symbol within a date range.

    Args:
        symbol: Futures symbol (e.g., "NQZ5", "NQH6")
        start_datetime: Start datetime in ISO format
        end_datetime: End datetime in ISO format (optional, defaults to start + 12 hours)
        db: Database session

    Returns:
        List of candles in TradingView Lightweight Charts format

    Example:
        GET /api/v1/candles/NQZ5?start_datetime=2025-11-20T09:30:00&end_datetime=2025-11-20T21:30:00
    """
    try:
        # Default end_datetime to start + 12 hours if not provided
        if end_datetime is None:
            end_datetime = start_datetime + timedelta(hours=12)

        logger.info(f"Fetching candles for {symbol} from {start_datetime} to {end_datetime}")

        # Query candlestick_5min table
        stmt = (
            select(Candlestick5Min)
            .where(Candlestick5Min.symbol == symbol)
            .where(Candlestick5Min.time_interval >= start_datetime)
            .where(Candlestick5Min.time_interval <= end_datetime)
            .order_by(Candlestick5Min.time_interval)
        )

        result = await db.execute(stmt)
        candles = result.scalars().all()

        if not candles:
            logger.warning(f"No candles found for {symbol} in range {start_datetime} to {end_datetime}")
            return []

        # Convert to TradingView format
        response = []
        for candle in candles:
            # Convert datetime to UNIX timestamp (seconds)
            unix_timestamp = int(candle.time_interval.timestamp())

            response.append(CandleResponse(
                time=unix_timestamp,
                open=candle.open,
                high=candle.high,
                low=candle.low,
                close=candle.close,
                volume=candle.volume
            ))

        logger.info(f"Retrieved {len(response)} candles for {symbol}")
        return response

    except Exception as e:
        logger.error(f"Error fetching candles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching candles: {str(e)}")


@router.get("/{symbol}/detailed", response_model=List[CandleDetailResponse])
async def get_candles_detailed(
    symbol: str,
    start_datetime: datetime = Query(..., description="Start datetime (ISO format)"),
    end_datetime: Optional[datetime] = Query(None, description="End datetime (ISO format). Defaults to start + 12 hours"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed candlestick data including delta, POC, and footprint data.

    Args:
        symbol: Futures symbol (e.g., "NQZ5", "NQH6")
        start_datetime: Start datetime in ISO format
        end_datetime: End datetime in ISO format (optional, defaults to start + 12 hours)
        db: Database session

    Returns:
        List of detailed candles with orderflow data

    Example:
        GET /api/v1/candles/NQZ5/detailed?start_datetime=2025-11-20T09:30:00
    """
    try:
        # Default end_datetime to start + 12 hours if not provided
        if end_datetime is None:
            end_datetime = start_datetime + timedelta(hours=12)

        logger.info(f"Fetching detailed candles for {symbol} from {start_datetime} to {end_datetime}")

        # Query candlestick_5min table
        stmt = (
            select(Candlestick5Min)
            .where(Candlestick5Min.symbol == symbol)
            .where(Candlestick5Min.time_interval >= start_datetime)
            .where(Candlestick5Min.time_interval <= end_datetime)
            .order_by(Candlestick5Min.time_interval)
        )

        result = await db.execute(stmt)
        candles = result.scalars().all()

        if not candles:
            logger.warning(f"No candles found for {symbol} in range {start_datetime} to {end_datetime}")
            return []

        # Convert to detailed response format
        response = []
        for candle in candles:
            # Convert datetime to UNIX timestamp (seconds)
            unix_timestamp = int(candle.time_interval.timestamp())

            response.append(CandleDetailResponse(
                time=unix_timestamp,
                symbol=candle.symbol,
                open=candle.open,
                high=candle.high,
                low=candle.low,
                close=candle.close,
                volume=candle.volume,
                delta=candle.delta,
                poc=candle.poc,
                real_poc=candle.real_poc,
                oflow_detail=candle.oflow_detail,
                tick_count=candle.tick_count
            ))

        logger.info(f"Retrieved {len(response)} detailed candles for {symbol}")
        return response

    except Exception as e:
        logger.error(f"Error fetching detailed candles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching detailed candles: {str(e)}")


@router.get("/symbols/available")
async def get_available_symbols(db: AsyncSession = Depends(get_db)):
    """
    Get list of available symbols in the database.

    Returns:
        List of available symbols with date ranges and candle counts
    """
    try:
        from sqlalchemy import func

        stmt = (
            select(
                Candlestick5Min.symbol,
                func.min(Candlestick5Min.time_interval).label('first_candle'),
                func.max(Candlestick5Min.time_interval).label('last_candle'),
                func.count().label('total_candles')
            )
            .group_by(Candlestick5Min.symbol)
            .order_by(Candlestick5Min.symbol)
        )

        result = await db.execute(stmt)
        symbols = result.all()

        return [
            {
                "symbol": row.symbol,
                "first_candle": row.first_candle.isoformat() if row.first_candle else None,
                "last_candle": row.last_candle.isoformat() if row.last_candle else None,
                "total_candles": row.total_candles
            }
            for row in symbols
        ]

    except Exception as e:
        logger.error(f"Error fetching available symbols: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching symbols: {str(e)}")
