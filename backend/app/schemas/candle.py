"""
Candle Schemas

Pydantic models for API request/response validation.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any


class CandleQuery(BaseModel):
    """Query parameters for candle requests"""
    start_datetime: datetime = Field(..., description="Start datetime (ISO format)")
    end_datetime: Optional[datetime] = Field(None, description="End datetime (ISO format). If not provided, defaults to start_datetime + 12 hours")


class CandleResponse(BaseModel):
    """
    Candle data response compatible with TradingView Lightweight Charts

    Format expected by lightweight-charts:
    {
        time: number (UNIX timestamp in seconds) | string (ISO),
        open: number,
        high: number,
        low: number,
        close: number,
        volume?: number
    }
    """
    time: int = Field(..., description="UNIX timestamp in seconds")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Closing price")
    volume: Optional[float] = Field(None, description="Volume")

    class Config:
        json_schema_extra = {
            "example": {
                "time": 1700000000,
                "open": 20600.0,
                "high": 20610.5,
                "low": 20595.25,
                "close": 20605.75,
                "volume": 1250.0
            }
        }


class CandleDetailResponse(BaseModel):
    """
    Extended candle response with additional fields for advanced charting
    """
    time: int = Field(..., description="UNIX timestamp in seconds")
    symbol: str = Field(..., description="Symbol")
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None
    delta: Optional[float] = Field(None, description="Buy volume - Sell volume")
    poc: Optional[float] = Field(None, description="Point of Control price")
    real_poc: Optional[float] = Field(None, description="Real POC at 0.25 tick granularity")
    oflow_detail: Optional[Any] = Field(None, description="Footprint data (JSONB)")
    tick_count: Optional[int] = Field(None, description="Number of ticks in candle")

    class Config:
        from_attributes = True
