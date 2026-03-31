"""
Data Platform API routes.

REST endpoints for querying historical NQ data from TimescaleDB.
AUT-330 - M1.3 Data Platform API.
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db_sync
from app.data.candle_store import (
    CandleStore,
    VALID_TIMEFRAMES,
    get_active_nq_contract,
    get_nq_rollover_history
)


router = APIRouter(prefix="/data", tags=["data"])


# Request/Response schemas
class ExportRequest(BaseModel):
    """Export request schema."""
    timeframe: str = Field(..., description="Timeframe to export")
    start: str = Field(..., description="Start date (ISO format)")
    end: str = Field(..., description="End date (ISO format)")
    format: str = Field(default="parquet", description="Export format (parquet, csv)")


class ExportResponse(BaseModel):
    """Export response schema."""
    task_id: str
    status: str


class CandlesResponse(BaseModel):
    """Candles response schema."""
    candles: List[Dict[str, Any]]
    next_cursor: Optional[str]
    total: Optional[int]


class CoverageResponse(BaseModel):
    """Coverage response schema."""
    earliest: Optional[str]
    latest: Optional[str]
    total_candles: Dict[str, int]
    gaps: List[Dict[str, Any]]


class TicksResponse(BaseModel):
    """Ticks response schema."""
    ticks: List[Dict[str, Any]]
    next_cursor: Optional[str]


class ActiveContractResponse(BaseModel):
    """Active contract response schema."""
    symbol: str
    expiry: str
    roll_date: str


class RolloverPeriod(BaseModel):
    """Rollover period schema."""
    from_contract: str = Field(..., alias="from")
    to_contract: str = Field(..., alias="to")
    date: str

    class Config:
        populate_by_name = True


@router.get("/candles/{timeframe}", response_model=CandlesResponse)
async def get_candles(
    timeframe: str,
    start: datetime = Query(..., description="Start datetime"),
    end: datetime = Query(..., description="End datetime"),
    limit: int = Query(default=500, le=5000, description="Maximum candles to return"),
    cursor: Optional[str] = Query(None, description="Pagination cursor (timestamp)"),
    include_orderflow: bool = Query(False, description="Include delta, poc, and footprint"),
    db: Session = Depends(get_db_sync)
):
    """
    Get candlestick data for a specific timeframe.

    Supports cursor-based pagination for efficient TimescaleDB queries.

    **Valid timeframes:** 30s, 1min, 5min, 15min, 1h, 4h, 1d, 1w

    **Pagination:** Use the `next_cursor` from the response in subsequent requests.

    **Order flow data:** Set `include_orderflow=true` to include delta, POC, and footprint.
    Note: This is slower due to JSONB field loading.
    """
    # Validate timeframe
    if timeframe not in VALID_TIMEFRAMES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid timeframe '{timeframe}'. Valid options: {', '.join(VALID_TIMEFRAMES)}"
        )

    # Initialize CandleStore
    store = CandleStore(db)

    # Get candles
    df = store.get_candles(
        timeframe=timeframe,
        start=start,
        end=end,
        limit=limit,
        cursor=cursor,
        include_orderflow=include_orderflow
    )

    # Convert DataFrame to list of dicts
    if df.empty:
        return CandlesResponse(candles=[], next_cursor=None, total=0)

    # Convert timestamps to ISO format
    candles = []
    for _, row in df.iterrows():
        candle = {
            "timestamp": row['timestamp'].isoformat(),
            "symbol": row['symbol'],
            "open": float(row['open']) if row['open'] is not None else None,
            "high": float(row['high']) if row['high'] is not None else None,
            "low": float(row['low']) if row['low'] is not None else None,
            "close": float(row['close']) if row['close'] is not None else None,
            "volume": float(row['volume']) if row['volume'] is not None else None
        }

        # Add orderflow if requested
        if include_orderflow:
            candle["delta"] = float(row['delta']) if row['delta'] is not None else None
            candle["poc"] = float(row['poc']) if row['poc'] is not None else None
            candle["footprint"] = row['footprint']

        candles.append(candle)

    # Determine next cursor
    next_cursor = None
    if len(candles) == limit:
        # More data might be available
        last_timestamp = candles[-1]["timestamp"]
        next_cursor = last_timestamp

    return CandlesResponse(
        candles=candles,
        next_cursor=next_cursor,
        total=len(candles)
    )


@router.get("/ticks", response_model=TicksResponse)
async def get_ticks(
    start: datetime = Query(..., description="Start datetime"),
    end: datetime = Query(..., description="End datetime"),
    limit: int = Query(default=1000, le=10000, description="Maximum ticks to return"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    db: Session = Depends(get_db_sync)
):
    """
    Get tick data in TBBO (Top of Book) format.

    Returns bid/ask prices and sizes with microsecond timestamps.

    **Note:** Tick data is very granular. Use pagination to retrieve large datasets.
    """
    # Initialize CandleStore
    store = CandleStore(db)

    # Get ticks
    result = store.get_ticks(
        start=start,
        end=end,
        limit=limit,
        cursor=cursor
    )

    return TicksResponse(
        ticks=result["ticks"],
        next_cursor=result["next_cursor"]
    )


@router.get("/coverage", response_model=CoverageResponse)
async def get_coverage(db: Session = Depends(get_db_sync)):
    """
    Get data coverage statistics.

    Returns the date range of available data and candle counts per timeframe.

    **Use this endpoint** to determine what data is available before querying candles.
    """
    # Initialize CandleStore
    store = CandleStore(db)

    # Get coverage
    coverage = store.get_coverage()

    return CoverageResponse(
        earliest=coverage["earliest"],
        latest=coverage["latest"],
        total_candles=coverage["total_candles"],
        gaps=coverage["gaps"]
    )


@router.get("/contracts/active", response_model=ActiveContractResponse)
async def get_active_contract():
    """
    Get the currently active NQ contract (front month).

    Returns the symbol, expiry date, and recommended roll date.

    **Roll date:** Typically 8 trading days before expiry to avoid low liquidity.
    """
    contract = get_active_nq_contract()

    return ActiveContractResponse(
        symbol=contract["symbol"],
        expiry=contract["expiry"],
        roll_date=contract["roll_date"]
    )


@router.get("/rollover-periods", response_model=List[RolloverPeriod])
async def get_rollover_periods():
    """
    Get historical NQ rollover periods.

    Returns a list of contract rollovers with dates.

    **Use this** to identify rollover periods when analyzing historical data.
    Rollover periods may have irregular price behavior.
    """
    history = get_nq_rollover_history()

    return [
        RolloverPeriod(
            from_contract=item["from"],
            to_contract=item["to"],
            date=item["date"]
        )
        for item in history
    ]


@router.post("/export", response_model=ExportResponse)
async def export_to_gcs(
    export_request: ExportRequest,
    db: Session = Depends(get_db_sync)
):
    """
    Export data to Google Cloud Storage (GCS).

    Triggers an async Celery task to export data in the specified format.

    **Returns:** Task ID for tracking the export progress.

    **Supported formats:**
    - parquet: Columnar format, best for analytics
    - csv: Text format, universal compatibility

    **Note:** This is an async operation. Use the task_id to check status via /jobs/{task_id}.
    """
    # TODO: Import and use export_to_gcs_task from AUT-334
    # For now, mock the task
    try:
        # Validate timeframe
        if export_request.timeframe not in VALID_TIMEFRAMES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid timeframe. Valid options: {', '.join(VALID_TIMEFRAMES)}"
            )

        # Validate format
        if export_request.format not in ["parquet", "csv"]:
            raise HTTPException(
                status_code=422,
                detail="Invalid format. Valid options: parquet, csv"
            )

        # Mock task submission
        # task = export_to_gcs_task.delay(
        #     timeframe=export_request.timeframe,
        #     start=export_request.start,
        #     end=export_request.end,
        #     format=export_request.format
        # )

        # Return mock task_id for now
        import uuid
        task_id = str(uuid.uuid4())

        return ExportResponse(
            task_id=task_id,
            status="queued"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue export task: {str(e)}"
        )


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for data platform API."""
    return {
        "status": "healthy",
        "service": "data-platform-api",
        "version": "1.0.0"
    }
