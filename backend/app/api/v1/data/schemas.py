"""
Pydantic schemas for Data Platform API responses.

AUT-362: OpenAPI documentation schemas for all endpoints.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CandleSchema(BaseModel):
    """Individual candlestick data point."""
    timestamp: datetime = Field(..., description="Candle timestamp in UTC")
    symbol: str = Field(..., description="Contract symbol (e.g., NQH26)")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price")
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")
    delta: Optional[int] = Field(None, description="Buy volume - Sell volume")
    poc: Optional[float] = Field(None, description="Point of Control price level")
    footprint: Optional[Dict[str, Any]] = Field(None, description="Footprint chart data")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-01-15T09:30:00Z",
                "symbol": "NQH26",
                "open": 19850.25,
                "high": 19875.50,
                "low": 19845.00,
                "close": 19865.75,
                "volume": 1250,
                "delta": 125,
                "poc": 19860.00
            }
        }


class CandlesResponse(BaseModel):
    """Response for candles endpoint with pagination support."""
    candles: List[CandleSchema] = Field(..., description="Array of candlestick data")
    next_cursor: Optional[str] = Field(None, description="Pagination cursor for next page")
    total: Optional[int] = Field(None, description="Total number of candles in current page")

    class Config:
        json_schema_extra = {
            "example": {
                "candles": [],
                "next_cursor": "2026-01-15T10:30:00Z",
                "total": 100
            }
        }


class TickSchema(BaseModel):
    """Individual tick data in TBBO format."""
    timestamp: str = Field(..., description="Tick timestamp with microsecond precision")
    symbol: str = Field(..., description="Contract symbol")
    bid_price: float = Field(..., description="Best bid price")
    bid_size: int = Field(..., description="Best bid size")
    ask_price: float = Field(..., description="Best ask price")
    ask_size: int = Field(..., description="Best ask size")
    last_price: Optional[float] = Field(None, description="Last traded price")
    last_size: Optional[int] = Field(None, description="Last traded size")


class TicksResponse(BaseModel):
    """Response for ticks endpoint with pagination support."""
    ticks: List[TickSchema] = Field(..., description="Array of tick data")
    next_cursor: Optional[str] = Field(None, description="Pagination cursor")


class CoverageResponse(BaseModel):
    """Data coverage statistics response."""
    earliest: Optional[str] = Field(None, description="Earliest available data timestamp")
    latest: Optional[str] = Field(None, description="Latest available data timestamp")
    total_candles: Dict[str, int] = Field(..., description="Total candles per timeframe")
    gaps: List[Dict[str, Any]] = Field(default_factory=list, description="Data gaps if any")


class ActiveContractResponse(BaseModel):
    """Active NQ contract information."""
    symbol: str = Field(..., description="Contract symbol (e.g., NQM26)")
    expiry: str = Field(..., description="Expiration date in ISO format")
    roll_date: str = Field(..., description="Recommended roll date")


class RolloverPeriod(BaseModel):
    """Historical rollover period information."""
    from_contract: str = Field(..., alias="from", description="Previous contract symbol")
    to_contract: str = Field(..., alias="to", description="New contract symbol")
    date: str = Field(..., description="Rollover date in ISO format")

    class Config:
        populate_by_name = True


class ExportRequest(BaseModel):
    """Request schema for data export."""
    timeframe: str = Field(..., description="Timeframe to export", pattern="^(30s|1min|5min|15min|1h|4h|1d|1w)$")
    start: str = Field(..., description="Start date in ISO format")
    end: str = Field(..., description="End date in ISO format")
    format: str = Field(default="parquet", description="Export format", pattern="^(parquet|csv)$")


class ExportResponse(BaseModel):
    """Response for export job creation."""
    task_id: str = Field(..., description="Unique task identifier for tracking")
    status: str = Field(..., description="Current job status")


class ErrorResponse(BaseModel):
    """Standard error response format."""
    detail: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code for specific errors")


class TimeframeEnum(str, Enum):
    """Valid timeframes for candle data."""
    THIRTY_SECONDS = "30s"
    ONE_MINUTE = "1min"
    FIVE_MINUTES = "5min"
    FIFTEEN_MINUTES = "15min"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"