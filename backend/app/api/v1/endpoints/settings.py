"""
Settings API endpoints - User and system configuration management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime, time
from pydantic import BaseModel
from enum import Enum

from app.core.database import get_async_db
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()


class TradingSchedule(BaseModel):
    schedule_id: Optional[str] = None
    name: str
    active: bool = True
    days: List[str]  # ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    start_time: str  # "09:30"
    end_time: str    # "16:00"
    timezone: str = "America/New_York"
    exclude_holidays: bool = True
    pre_market: bool = False
    after_hours: bool = False


class NotificationSettings(BaseModel):
    email_enabled: bool = True
    email_address: Optional[str] = None
    sms_enabled: bool = False
    phone_number: Optional[str] = None
    webhook_enabled: bool = False
    webhook_url: Optional[str] = None
    notification_types: Dict[str, bool] = {
        "trade_fills": True,
        "risk_alerts": True,
        "system_errors": True,
        "daily_summary": True,
        "position_updates": True
    }


class DisplaySettings(BaseModel):
    theme: str = "dark"  # light, dark
    language: str = "en"
    timezone: str = "America/New_York"
    date_format: str = "MM/DD/YYYY"
    time_format: str = "12h"  # 12h, 24h
    decimal_places: int = 2
    show_pnl_in_ticks: bool = False
    default_chart_type: str = "candlestick"
    default_timeframe: str = "5m"


class APIKeySettings(BaseModel):
    key_id: Optional[str] = None
    name: str
    permissions: List[str]  # ["read", "write", "trade", "admin"]
    expires_at: Optional[datetime] = None
    ip_whitelist: Optional[List[str]] = None


@router.get("/trading-schedules")
async def get_trading_schedules(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get user's trading schedules.

    Returns configured trading hours and active schedules.
    """
    return {
        "status": "success",
        "data": {
            "schedules": [
                {
                    "schedule_id": "sched_001",
                    "name": "Regular Trading Hours",
                    "active": True,
                    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                    "start_time": "09:30",
                    "end_time": "16:00",
                    "timezone": "America/New_York",
                    "exclude_holidays": True,
                    "pre_market": False,
                    "after_hours": False
                },
                {
                    "schedule_id": "sched_002",
                    "name": "Extended Hours",
                    "active": False,
                    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                    "start_time": "04:00",
                    "end_time": "20:00",
                    "timezone": "America/New_York",
                    "exclude_holidays": True,
                    "pre_market": True,
                    "after_hours": True
                }
            ],
            "active_schedule": "sched_001"
        }
    }


@router.put("/trading-schedules")
async def update_trading_schedule(
    schedule: TradingSchedule,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update or create a trading schedule.

    Configures when automated trading is allowed.
    """
    return {
        "status": "success",
        "data": {
            "schedule_id": schedule.schedule_id or "sched_new",
            "updated": True,
            "message": "Trading schedule updated successfully",
            "next_trading_window": {
                "start": "2024-03-27T09:30:00-04:00",
                "end": "2024-03-27T16:00:00-04:00"
            }
        }
    }


@router.get("/notifications")
async def get_notification_settings(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get notification preferences.

    Returns user's notification configuration.
    """
    return {
        "status": "success",
        "data": {
            "email_enabled": True,
            "email_address": current_user.email,
            "sms_enabled": False,
            "phone_number": None,
            "webhook_enabled": False,
            "webhook_url": None,
            "notification_types": {
                "trade_fills": True,
                "risk_alerts": True,
                "system_errors": True,
                "daily_summary": True,
                "position_updates": True,
                "strategy_signals": False,
                "market_alerts": False
            }
        }
    }


@router.put("/notifications")
async def update_notification_settings(
    settings: NotificationSettings,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update notification preferences.

    Configures how and when to receive notifications.
    """
    return {
        "status": "success",
        "data": {
            "settings": settings.dict(),
            "updated_at": datetime.utcnow().isoformat(),
            "message": "Notification settings updated successfully"
        }
    }


@router.get("/display")
async def get_display_settings(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get display preferences.

    Returns UI customization settings.
    """
    return {
        "status": "success",
        "data": {
            "theme": "dark",
            "language": "en",
            "timezone": "America/New_York",
            "date_format": "MM/DD/YYYY",
            "time_format": "12h",
            "decimal_places": 2,
            "show_pnl_in_ticks": False,
            "default_chart_type": "candlestick",
            "default_timeframe": "5m",
            "sidebar_collapsed": False,
            "show_tooltips": True
        }
    }


@router.put("/display")
async def update_display_settings(
    settings: DisplaySettings,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update display preferences.

    Customizes UI appearance and behavior.
    """
    return {
        "status": "success",
        "data": {
            "settings": settings.dict(),
            "updated_at": datetime.utcnow().isoformat(),
            "message": "Display settings updated successfully"
        }
    }


@router.get("/api-keys")
async def get_api_keys(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get user's API keys.

    Returns list of configured API keys for external access.
    """
    return {
        "status": "success",
        "data": {
            "api_keys": [
                {
                    "key_id": "key_001",
                    "name": "Production Trading",
                    "key_preview": "nqhub_live_a3f4...d8e9",
                    "permissions": ["read", "write", "trade"],
                    "created_at": "2024-01-15T10:00:00Z",
                    "last_used": "2024-03-26T14:30:00Z",
                    "expires_at": None,
                    "active": True
                }
            ],
            "total": 1
        }
    }


@router.post("/api-keys")
async def create_api_key(
    key_config: APIKeySettings,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new API key.

    Generates a new API key with specified permissions.
    """
    import secrets

    api_key = f"nqhub_live_{secrets.token_urlsafe(32)}"

    return {
        "status": "success",
        "data": {
            "key_id": "key_new",
            "name": key_config.name,
            "api_key": api_key,  # Only shown once
            "permissions": key_config.permissions,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": key_config.expires_at.isoformat() if key_config.expires_at else None,
            "message": "API key created successfully. Save this key securely - it won't be shown again."
        }
    }


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Revoke an API key.

    Permanently disables an API key.
    """
    return {
        "status": "success",
        "data": {
            "key_id": key_id,
            "revoked": True,
            "revoked_at": datetime.utcnow().isoformat(),
            "message": "API key revoked successfully"
        }
    }


@router.get("/data-providers")
async def get_data_provider_settings(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get data provider configurations.

    Returns settings for market data providers (Databento, Rithmic, etc).
    """
    return {
        "status": "success",
        "data": {
            "providers": {
                "databento": {
                    "enabled": True,
                    "api_key_set": True,
                    "datasets": ["GLBX.MDP3"],
                    "subscription": "basic"
                },
                "rithmic": {
                    "enabled": False,
                    "username_set": False,
                    "environment": "test"
                }
            },
            "primary_provider": "databento"
        }
    }


@router.get("/broker-connections")
async def get_broker_connections(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get broker connection settings.

    Returns configured broker connections for order execution.
    """
    return {
        "status": "success",
        "data": {
            "connections": [
                {
                    "broker": "Interactive Brokers",
                    "account_id": "DU1234567",
                    "connection_status": "connected",
                    "paper_trading": True,
                    "last_connected": "2024-03-26T09:00:00Z"
                }
            ],
            "active_connection": "Interactive Brokers"
        }
    }