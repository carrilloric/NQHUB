"""
CandleStore - Data access layer for candlestick data.

Provides methods to query candlestick data from TimescaleDB across different timeframes.
AUT-330 requires using this service instead of direct queries in routes.
"""

import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.candlestick import Candlestick5Min


# Timeframe to model mapping
TIMEFRAME_MODELS = {
    "30s": None,  # Not implemented yet
    "1min": None,  # Not implemented yet
    "5min": Candlestick5Min,
    "15min": None,  # Not implemented yet
    "1h": None,  # Not implemented yet
    "4h": None,  # Not implemented yet
    "1d": None,  # Not implemented yet
    "1w": None  # Not implemented yet
}

VALID_TIMEFRAMES = ["30s", "1min", "5min", "15min", "1h", "4h", "1d", "1w"]


class CandleStore:
    """
    Data access layer for candlestick data from TimescaleDB.

    Provides cursor-based pagination and orderflow data inclusion.
    """

    def __init__(self, db_session: Session):
        """
        Initialize CandleStore.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session

    def get_candles(
        self,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: int = 500,
        cursor: Optional[str] = None,
        include_orderflow: bool = False
    ) -> pd.DataFrame:
        """
        Get candlestick data for a specific timeframe.

        Args:
            timeframe: Timeframe string (1min, 5min, etc.)
            start: Start datetime
            end: End datetime
            limit: Maximum number of candles to return
            cursor: Pagination cursor (timestamp)
            include_orderflow: Include delta, poc, and footprint data

        Returns:
            DataFrame with candlestick data
        """
        # Get model for timeframe
        model = TIMEFRAME_MODELS.get(timeframe)
        if model is None:
            # For now, use 5min as default for all timeframes
            model = Candlestick5Min

        # Build query
        query = self.db.query(model).filter(
            and_(
                model.time_interval >= start,
                model.time_interval <= end
            )
        )

        # Apply cursor pagination if provided
        if cursor:
            cursor_dt = datetime.fromisoformat(cursor.replace('Z', '+00:00'))
            query = query.filter(model.time_interval > cursor_dt)

        # Order by timestamp
        query = query.order_by(model.time_interval)

        # Limit results
        query = query.limit(limit)

        # Execute query
        results = query.all()

        # Convert to DataFrame
        if not results:
            return pd.DataFrame()

        # Build DataFrame
        data = {
            'timestamp': [r.time_interval for r in results],
            'symbol': [r.symbol for r in results],
            'open': [r.open for r in results],
            'high': [r.high for r in results],
            'low': [r.low for r in results],
            'close': [r.close for r in results],
            'volume': [r.volume for r in results]
        }

        # Add orderflow data if requested
        if include_orderflow:
            data['delta'] = [r.delta for r in results]
            data['poc'] = [r.poc for r in results]
            data['footprint'] = [r.oflow_detail for r in results]

        df = pd.DataFrame(data)
        return df

    def get_coverage(self) -> Dict[str, Any]:
        """
        Get data coverage statistics.

        Returns:
            Dictionary with earliest/latest dates and candle counts
        """
        # Query for 5min timeframe stats
        earliest = self.db.query(func.min(Candlestick5Min.time_interval)).scalar()
        latest = self.db.query(func.max(Candlestick5Min.time_interval)).scalar()
        total_5min = self.db.query(func.count(Candlestick5Min.time_interval)).scalar()

        return {
            "earliest": earliest.isoformat() if earliest else None,
            "latest": latest.isoformat() if latest else None,
            "total_candles": {
                "1min": total_5min * 5 if total_5min else 0,  # Estimate
                "5min": total_5min or 0,
                "15min": total_5min // 3 if total_5min else 0,  # Estimate
                "1h": total_5min // 12 if total_5min else 0,  # Estimate
                "4h": total_5min // 48 if total_5min else 0,  # Estimate
                "1d": total_5min // 288 if total_5min else 0  # Estimate
            },
            "gaps": []  # TODO: Implement gap detection
        }

    def get_ticks(
        self,
        start: datetime,
        end: datetime,
        limit: int = 1000,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get tick data (TBBO format).

        Args:
            start: Start datetime
            end: End datetime
            limit: Maximum number of ticks
            cursor: Pagination cursor

        Returns:
            Dictionary with ticks and next_cursor
        """
        # TODO: Implement tick data retrieval
        # For now, return mock data
        return {
            "ticks": [],
            "next_cursor": None
        }


def get_active_nq_contract() -> Dict[str, str]:
    """
    Get the active NQ contract (front month).

    Returns:
        Dictionary with symbol, expiry, and roll_date
    """
    # TODO: Implement dynamic contract calculation
    # For now, return hardcoded
    return {
        "symbol": "NQM26",
        "expiry": "2026-06-20",
        "roll_date": "2026-06-13"
    }


def get_nq_rollover_history() -> List[Dict[str, str]]:
    """
    Get historical NQ rollover periods.

    Returns:
        List of rollover events
    """
    # TODO: Query from database
    # For now, return hardcoded history
    return [
        {"from": "NQZ25", "to": "NQH26", "date": "2025-12-13"},
        {"from": "NQH26", "to": "NQM26", "date": "2026-03-14"},
        {"from": "NQM26", "to": "NQU26", "date": "2026-06-13"}
    ]
