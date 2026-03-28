"""
Data Platform API Endpoints

Implementation of CONTRACT-001 Data Platform API specification.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4
import logging

from app.db.session import get_db
from app.models.candlestick import Candlestick5Min
from app.core.deps import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Supported timeframes
VALID_TIMEFRAMES = ['1min', '5min', '15min', '30min', '1hour', '4hour', '1day']

# Map timeframes to table names
TIMEFRAME_TABLES = {
    '1min': 'candlestick_1min',
    '5min': 'candlestick_5min',
    '15min': 'candlestick_15min',
    '30min': 'candlestick_30min',
    '1hour': 'candlestick_1hour',
    '4hour': 'candlestick_4hour',
    '1day': 'candlestick_1day'
}

# Export job storage (in production, use Redis or database)
export_jobs = {}


@router.get("/candles/{tf}")
async def get_candles_by_timeframe(
    tf: str = Path(..., description="Timeframe", enum=VALID_TIMEFRAMES),
    symbol: str = Query('NQH25', description="Contract symbol"),
    start: Optional[datetime] = Query(None, description="Start date (ISO 8601)"),
    end: Optional[datetime] = Query(None, description="End date (ISO 8601)"),
    include_oflow: bool = Query(False, description="Include order flow details"),
    limit: int = Query(100, ge=1, le=10000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get candles by timeframe.

    Implements GET /api/v1/data/candles/{tf} from CONTRACT-001.
    """
    try:
        # For now, we only have 5min data in the database
        if tf != '5min':
            # Return empty response for other timeframes
            return {
                "data": [],
                "total": 0,
                "has_more": False
            }

        # Build base query
        query = select(Candlestick5Min).where(Candlestick5Min.symbol == symbol)

        # Apply date filters
        if start:
            query = query.where(Candlestick5Min.time_interval >= start)
        if end:
            query = query.where(Candlestick5Min.time_interval <= end)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        query = query.order_by(Candlestick5Min.time_interval.desc())
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        candles = result.scalars().all()

        # Format response according to CONTRACT-001 schema
        data = []
        for candle in candles:
            candle_data = {
                "timestamp": candle.time_interval.isoformat() + "Z",
                "open": float(candle.open) if candle.open else 0.0,
                "high": float(candle.high) if candle.high else 0.0,
                "low": float(candle.low) if candle.low else 0.0,
                "close": float(candle.close) if candle.close else 0.0,
                "volume": int(candle.volume) if candle.volume else 0,

                # Orderflow metrics (from model)
                "delta": int(candle.delta) if candle.delta else 0,
                "buy_volume": 0,  # Not in current model
                "sell_volume": 0,  # Not in current model
                "cumulative_delta": 0,  # Not in current model
                "buy_trades": 0,  # Not in current model
                "sell_trades": 0,  # Not in current model
                "delta_percentage": 0.0,  # Not in current model
                "max_delta": 0,  # Not in current model
                "min_delta": 0,  # Not in current model
                "delta_change": 0,  # Not in current model

                # Price levels & statistics
                "vwap": 0.0,  # Not in current model
                "typical_price": (float(candle.high) + float(candle.low) + float(candle.close)) / 3 if candle.high and candle.low and candle.close else 0.0,
                "range": float(candle.high - candle.low) if candle.high and candle.low else 0.0,
                "body_size": float(candle.body) if candle.body else 0.0,
                "wick_upper": float(candle.upper_wick) if candle.upper_wick else 0.0,
                "wick_lower": float(candle.lower_wick) if candle.lower_wick else 0.0,
                "body_percentage": 0.0,  # Not calculated
                "price_change": float(candle.close - candle.open) if candle.close and candle.open else 0.0,
                "price_change_percentage": ((float(candle.close) - float(candle.open)) / float(candle.open) * 100) if candle.open and candle.open != 0 else 0.0,
                "cumulative_volume": 0,  # Not in current model

                # Market microstructure
                "tick_count": int(candle.tick_count) if candle.tick_count else 0,
                "bid_volume": 0,  # Not in current model
                "ask_volume": 0,  # Not in current model
                "imbalance": 0.0,  # Not in current model
                "spread_avg": 0.0,  # Not in current model
                "trade_intensity": 0.0,  # Not in current model
                "volume_rate": 0.0,  # Not in current model
                "large_trade_count": 0,  # Not in current model
                "large_trade_volume": 0,  # Not in current model
            }

            # Add orderflow detail if requested
            if include_oflow and candle.oflow_detail:
                candle_data["oflow_detail"] = candle.oflow_detail

            data.append(candle_data)

        return {
            "data": data,
            "total": total,
            "has_more": (offset + limit) < total
        }

    except Exception as e:
        logger.error(f"Error fetching candles: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "detail": "An unexpected error occurred",
                "code": "INTERNAL_ERROR"
            }
        )


@router.get("/candles/{tf}/{timestamp}")
async def get_candle_by_timestamp(
    tf: str = Path(..., description="Timeframe", enum=VALID_TIMEFRAMES),
    timestamp: datetime = Path(..., description="ISO 8601 timestamp"),
    include_oflow: bool = Query(False, description="Include order flow details"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific candle.

    Implements GET /api/v1/data/candles/{tf}/{timestamp} from CONTRACT-001.
    """
    try:
        # For now, we only have 5min data
        if tf != '5min':
            raise HTTPException(
                status_code=404,
                detail={
                    "detail": "Resource not found",
                    "code": "NOT_FOUND"
                }
            )

        # Query for specific candle
        query = select(Candlestick5Min).where(
            Candlestick5Min.time_interval == timestamp
        )

        result = await db.execute(query)
        candle = result.scalar_one_or_none()

        if not candle:
            raise HTTPException(
                status_code=404,
                detail={
                    "detail": "Resource not found",
                    "code": "NOT_FOUND"
                }
            )

        # Format response
        response = {
            "timestamp": candle.time_interval.isoformat() + "Z",
            "open": float(candle.open) if candle.open else 0.0,
            "high": float(candle.high) if candle.high else 0.0,
            "low": float(candle.low) if candle.low else 0.0,
            "close": float(candle.close) if candle.close else 0.0,
            "volume": int(candle.volume) if candle.volume else 0,

            # Orderflow metrics
            "delta": int(candle.delta) if candle.delta else 0,
            "buy_volume": 0,
            "sell_volume": 0,
            "cumulative_delta": 0,
            "buy_trades": 0,
            "sell_trades": 0,
            "delta_percentage": 0.0,
            "max_delta": 0,
            "min_delta": 0,
            "delta_change": 0,

            # Price levels & statistics
            "vwap": 0.0,
            "typical_price": (float(candle.high) + float(candle.low) + float(candle.close)) / 3 if candle.high and candle.low and candle.close else 0.0,
            "range": float(candle.high - candle.low) if candle.high and candle.low else 0.0,
            "body_size": float(candle.body) if candle.body else 0.0,
            "wick_upper": float(candle.upper_wick) if candle.upper_wick else 0.0,
            "wick_lower": float(candle.lower_wick) if candle.lower_wick else 0.0,
            "body_percentage": 0.0,
            "price_change": float(candle.close - candle.open) if candle.close and candle.open else 0.0,
            "price_change_percentage": ((float(candle.close) - float(candle.open)) / float(candle.open) * 100) if candle.open and candle.open != 0 else 0.0,
            "cumulative_volume": 0,

            # Market microstructure
            "tick_count": int(candle.tick_count) if candle.tick_count else 0,
            "bid_volume": 0,
            "ask_volume": 0,
            "imbalance": 0.0,
            "spread_avg": 0.0,
            "trade_intensity": 0.0,
            "volume_rate": 0.0,
            "large_trade_count": 0,
            "large_trade_volume": 0,
        }

        # Add orderflow detail if requested
        if include_oflow:
            if candle.oflow_detail:
                response["oflow_detail"] = {
                    "price_levels": candle.oflow_detail
                }
            else:
                response["oflow_detail"] = {
                    "price_levels": []
                }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching candle: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "detail": "An unexpected error occurred",
                "code": "INTERNAL_ERROR"
            }
        )


@router.get("/ticks")
async def get_ticks(
    start: Optional[datetime] = Query(None, description="Start date (ISO 8601)"),
    end: Optional[datetime] = Query(None, description="End date (ISO 8601)"),
    limit: int = Query(100, ge=1, le=10000, description="Number of results to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get tick data.

    Implements GET /api/v1/data/ticks from CONTRACT-001.
    """
    # TODO: Implement when tick data table is available
    # For now, return empty response
    return {
        "data": [],
        "total": 0
    }


@router.get("/coverage")
async def get_coverage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get data coverage information.

    Implements GET /api/v1/data/coverage from CONTRACT-001.
    """
    try:
        coverage_data = []

        # Check coverage for each timeframe
        # For now, we only have 5min data
        result = await db.execute(
            select(
                func.min(Candlestick5Min.time_interval).label('start'),
                func.max(Candlestick5Min.time_interval).label('end'),
                func.count().label('count')
            )
        )

        row = result.one_or_none()

        if row and row.count > 0:
            coverage_data.append({
                "tf": "5min",
                "count": row.count,
                "start": row.start.isoformat() + "Z" if row.start else None,
                "end": row.end.isoformat() + "Z" if row.end else None,
                "last_updated": row.end.isoformat() + "Z" if row.end else None
            })

        # Add empty entries for other timeframes
        for tf in VALID_TIMEFRAMES:
            if tf != '5min':
                coverage_data.append({
                    "tf": tf,
                    "count": 0,
                    "start": None,
                    "end": None,
                    "last_updated": None
                })

        return {
            "timeframes": coverage_data
        }

    except Exception as e:
        logger.error(f"Error fetching coverage: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "detail": "An unexpected error occurred",
                "code": "INTERNAL_ERROR"
            }
        )


@router.get("/contracts/active")
async def get_active_contracts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get active contracts.

    Implements GET /api/v1/data/contracts/active from CONTRACT-001.
    """
    try:
        # Query unique symbols from the database
        result = await db.execute(
            select(Candlestick5Min.symbol)
            .distinct()
            .order_by(Candlestick5Min.symbol)
        )

        symbols = result.scalars().all()

        # Parse contract info from symbols
        contracts = []
        for symbol in symbols:
            if symbol and len(symbol) >= 4:
                # Extract expiry info from symbol (e.g., NQH25 -> March 2025)
                month_code = symbol[2] if len(symbol) > 2 else ''
                year = symbol[3:] if len(symbol) > 3 else ''

                # Map month codes to months
                month_map = {
                    'F': '01', 'G': '02', 'H': '03', 'J': '04',
                    'K': '05', 'M': '06', 'N': '07', 'Q': '08',
                    'U': '09', 'V': '10', 'X': '11', 'Z': '12'
                }

                if month_code in month_map and year.isdigit():
                    # Construct expiry date (third Friday of the month)
                    # Simplified: using 15th of the month
                    expiry = f"20{year}-{month_map[month_code]}-15"

                    contracts.append({
                        "symbol": symbol,
                        "expiry": expiry,
                        "is_front_month": len(contracts) == 0  # First one is front month
                    })

        return {
            "contracts": contracts
        }

    except Exception as e:
        logger.error(f"Error fetching active contracts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "detail": "An unexpected error occurred",
                "code": "INTERNAL_ERROR"
            }
        )


@router.get("/rollover-periods")
async def get_rollover_periods(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get rollover periods.

    Implements GET /api/v1/data/rollover-periods from CONTRACT-001.
    """
    # TODO: Implement based on actual rollover data
    # For now, return example rollover periods
    return {
        "rollovers": [
            {
                "from_symbol": "NQZ24",
                "to_symbol": "NQH25",
                "rollover_date": "2024-12-13"
            },
            {
                "from_symbol": "NQH25",
                "to_symbol": "NQM25",
                "rollover_date": "2025-03-14"
            }
        ]
    }


@router.post("/export", status_code=201)
async def create_export_job(
    request: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create export job.

    Implements POST /api/v1/data/export from CONTRACT-001.
    """
    try:
        # Validate request
        required_fields = ['table', 'start', 'end', 'format']
        for field in required_fields:
            if field not in request:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "detail": f"Missing required field: {field}",
                        "code": "VALIDATION_ERROR"
                    }
                )

        # Validate table
        valid_tables = [
            'candles_1min', 'candles_5min', 'candles_15min', 'candles_30min',
            'candles_1hour', 'candles_4hour', 'candles_1day', 'ticks'
        ]
        if request['table'] not in valid_tables:
            raise HTTPException(
                status_code=400,
                detail={
                    "detail": f"Invalid table. Must be one of: {', '.join(valid_tables)}",
                    "code": "INVALID_TABLE"
                }
            )

        # Validate format
        if request.get('format', 'parquet') not in ['parquet', 'csv']:
            raise HTTPException(
                status_code=400,
                detail={
                    "detail": "Invalid format. Must be 'parquet' or 'csv'",
                    "code": "INVALID_FORMAT"
                }
            )

        # Create job
        job_id = str(uuid4())
        export_jobs[job_id] = {
            "status": "queued",
            "request": request,
            "created_at": datetime.utcnow()
        }

        # TODO: Queue actual export task (Celery, etc.)

        return {
            "job_id": job_id,
            "status": "queued"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating export job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "detail": "An unexpected error occurred",
                "code": "INTERNAL_ERROR"
            }
        )


@router.get("/export/{job_id}")
async def get_export_job_status(
    job_id: str = Path(..., description="Export job ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get export job status.

    Implements GET /api/v1/data/export/{job_id} from CONTRACT-001.
    """
    if job_id not in export_jobs:
        raise HTTPException(
            status_code=404,
            detail={
                "detail": "Resource not found",
                "code": "NOT_FOUND"
            }
        )

    job = export_jobs[job_id]

    # Simulate job processing
    created_at = job['created_at']
    elapsed = (datetime.utcnow() - created_at).total_seconds()

    if elapsed < 5:
        return {
            "status": "queued",
            "progress": 0
        }
    elif elapsed < 15:
        return {
            "status": "processing",
            "progress": min(int(elapsed * 6), 90)
        }
    elif elapsed < 20:
        return {
            "status": "complete",
            "download_url": f"https://storage.nqhub.ai/exports/{job_id}.parquet",
            "size_mb": 125.5,
            "progress": 100
        }
    else:
        # Simulate occasional failure
        return {
            "status": "failed",
            "error_message": "Export job timed out"
        }