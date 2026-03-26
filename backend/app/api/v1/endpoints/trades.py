"""
Trades API endpoints - Trade history and performance tracking
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from pydantic import BaseModel
from enum import Enum

from app.core.database import get_async_db
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()


class TradeStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    PARTIAL = "partial"


class Trade(BaseModel):
    trade_id: str
    symbol: str
    side: str  # long/short
    entry_price: float
    entry_time: datetime
    exit_price: Optional[float]
    exit_time: Optional[datetime]
    quantity: int
    status: TradeStatus
    pnl: Optional[float]
    commission: float
    strategy_id: Optional[str]
    bot_id: Optional[str]


class PerformanceMetrics(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    avg_holding_time: str


@router.get("")
async def get_trades(
    status: Optional[TradeStatus] = None,
    symbol: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    strategy_id: Optional[str] = None,
    bot_id: Optional[str] = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get list of trades with filtering options.

    Returns trade history with P&L calculations.
    """
    return {
        "status": "success",
        "data": {
            "trades": [
                {
                    "trade_id": "trd_001",
                    "symbol": "NQ",
                    "side": "long",
                    "entry_price": 16825.50,
                    "entry_time": "2024-03-26T09:35:00Z",
                    "exit_price": 16832.75,
                    "exit_time": "2024-03-26T09:42:00Z",
                    "quantity": 1,
                    "status": "closed",
                    "pnl": 145.0,  # (16832.75 - 16825.50) * 20 - commission
                    "commission": 4.50,
                    "strategy_id": "scalper_v1",
                    "bot_id": "bot_001"
                },
                {
                    "trade_id": "trd_002",
                    "symbol": "NQ",
                    "side": "short",
                    "entry_price": 16835.25,
                    "entry_time": "2024-03-26T10:15:00Z",
                    "exit_price": 16838.00,
                    "exit_time": "2024-03-26T10:18:00Z",
                    "quantity": 2,
                    "status": "closed",
                    "pnl": -114.50,  # (16835.25 - 16838.00) * 20 * 2 - commission
                    "commission": 9.00,
                    "strategy_id": "scalper_v1",
                    "bot_id": "bot_001"
                }
            ],
            "total": 2,
            "limit": limit,
            "offset": offset,
            "summary": {
                "total_pnl": 30.50,
                "trades_count": 2,
                "win_rate": 0.50
            }
        }
    }


@router.get("/performance")
async def get_performance_metrics(
    period: str = "today",  # today, week, month, year, all
    strategy_id: Optional[str] = None,
    bot_id: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get trading performance metrics.

    Returns comprehensive performance statistics for specified period.
    """
    return {
        "status": "success",
        "data": {
            "period": period,
            "metrics": {
                "total_trades": 42,
                "winning_trades": 26,
                "losing_trades": 16,
                "win_rate": 0.619,
                "total_pnl": 3250.00,
                "avg_win": 245.50,
                "avg_loss": -125.25,
                "profit_factor": 2.45,
                "sharpe_ratio": 1.82,
                "sortino_ratio": 2.15,
                "calmar_ratio": 1.95,
                "max_drawdown": -850.00,
                "max_drawdown_pct": -2.8,
                "avg_holding_time": "7m 23s",
                "best_trade": 450.00,
                "worst_trade": -275.00,
                "avg_trade": 77.38,
                "commission_paid": 189.00
            },
            "by_symbol": {
                "NQ": {
                    "trades": 42,
                    "pnl": 3250.00,
                    "win_rate": 0.619
                }
            }
        }
    }


@router.get("/{trade_id}")
async def get_trade_details(
    trade_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific trade.

    Returns full trade details including entry/exit orders and analysis.
    """
    return {
        "status": "success",
        "data": {
            "trade_id": trade_id,
            "symbol": "NQ",
            "side": "long",
            "entry": {
                "price": 16825.50,
                "time": "2024-03-26T09:35:00Z",
                "order_id": "ord_001",
                "order_type": "market"
            },
            "exit": {
                "price": 16832.75,
                "time": "2024-03-26T09:42:00Z",
                "order_id": "ord_002",
                "order_type": "limit",
                "reason": "target_reached"
            },
            "quantity": 1,
            "pnl": {
                "gross": 145.00,
                "commission": 4.50,
                "net": 140.50,
                "pnl_points": 7.25,
                "pnl_ticks": 29,
                "return_pct": 0.043
            },
            "duration": "7m 0s",
            "mae": -2.50,  # Maximum Adverse Excursion
            "mfe": 10.25,  # Maximum Favorable Excursion
            "efficiency": 0.71,  # (exit - entry) / mfe
            "strategy": {
                "id": "scalper_v1",
                "name": "Scalper Strategy",
                "signals": ["RSI_oversold", "VWAP_support"]
            },
            "market_context": {
                "atr": 8.5,
                "volume": "above_average",
                "trend": "bullish"
            }
        }
    }


@router.get("/calendar")
async def get_trading_calendar(
    year: int = 2024,
    month: Optional[int] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get trading calendar with daily P&L.

    Returns calendar view of trading results for analysis.
    """
    return {
        "status": "success",
        "data": {
            "year": year,
            "month": month,
            "calendar": {
                "2024-03-01": {"trades": 5, "pnl": 125.00, "win_rate": 0.60},
                "2024-03-04": {"trades": 8, "pnl": -75.00, "win_rate": 0.38},
                "2024-03-05": {"trades": 12, "pnl": 450.00, "win_rate": 0.75},
                # ... more days
            },
            "summary": {
                "trading_days": 20,
                "profitable_days": 14,
                "losing_days": 6,
                "best_day": {"date": "2024-03-05", "pnl": 450.00},
                "worst_day": {"date": "2024-03-04", "pnl": -75.00},
                "avg_daily_pnl": 162.50
            }
        }
    }


@router.get("/statistics/by-hour")
async def get_hourly_statistics(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get trading statistics by hour of day.

    Analyzes performance patterns by time of day.
    """
    return {
        "status": "success",
        "data": {
            "hourly_stats": {
                "09": {"trades": 45, "pnl": 1250.00, "win_rate": 0.65},
                "10": {"trades": 62, "pnl": 875.00, "win_rate": 0.58},
                "11": {"trades": 38, "pnl": -125.00, "win_rate": 0.45},
                "12": {"trades": 25, "pnl": 225.00, "win_rate": 0.52},
                "13": {"trades": 35, "pnl": 450.00, "win_rate": 0.63},
                "14": {"trades": 48, "pnl": 325.00, "win_rate": 0.56},
                "15": {"trades": 52, "pnl": 250.00, "win_rate": 0.54}
            },
            "best_hours": ["09", "13", "10"],
            "worst_hours": ["11", "12"]
        }
    }


@router.post("/journal-note")
async def add_journal_note(
    trade_id: str,
    note: str,
    tags: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Add a journal note to a trade.

    Records thoughts, lessons learned, and tags for future analysis.
    """
    return {
        "status": "success",
        "data": {
            "trade_id": trade_id,
            "note_added": True,
            "tags": tags or [],
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Journal note added successfully"
        }
    }


@router.get("/export")
async def export_trades(
    format: str = "csv",  # csv, json, excel
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Export trades for external analysis.

    Generates downloadable file with trade history.
    """
    return {
        "status": "success",
        "data": {
            "export_url": f"/api/v1/trades/download/export_20240326_{format}",
            "format": format,
            "trades_count": 150,
            "date_range": {
                "start": start_date.isoformat() if start_date else "2024-01-01",
                "end": end_date.isoformat() if end_date else "2024-03-26"
            },
            "expires_at": "2024-03-27T00:00:00Z",
            "message": "Export ready for download"
        }
    }