"""System Information Endpoints"""
from fastapi import APIRouter
from datetime import datetime
import pytz
from pydantic import BaseModel

router = APIRouter()


class ServerTimeResponse(BaseModel):
    """Server time response model"""
    utc: datetime  # UTC time (timezone-aware)
    et: datetime   # Eastern Time (timezone-aware)
    et_naive: str  # ET time as string without timezone info (for display)
    timezone: str  # Current timezone setting (e.g., "America/New_York")
    offset_hours: float  # Current offset from UTC in hours
    is_dst: bool  # Whether DST is currently in effect

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemConfigResponse(BaseModel):
    """System configuration response"""
    default_timezone: str
    available_timezones: list[str]
    server_time: ServerTimeResponse


@router.get("/time", response_model=ServerTimeResponse)
async def get_server_time():
    """
    Get current server time in UTC and Eastern Time.

    This endpoint is the single source of truth for time in the application.
    All time-sensitive operations should reference this endpoint.

    Returns:
        - UTC time (timezone-aware)
        - Eastern Time (timezone-aware)
        - ET naive string for display
        - Timezone configuration
        - DST status
    """
    # Get current UTC time
    utc_now = datetime.now(pytz.UTC)

    # Convert to Eastern Time
    eastern = pytz.timezone('America/New_York')
    et_now = utc_now.astimezone(eastern)

    # Get offset from UTC
    offset = et_now.utcoffset()
    offset_hours = offset.total_seconds() / 3600 if offset else -5

    # Check if DST is in effect
    is_dst = bool(et_now.dst())

    return ServerTimeResponse(
        utc=utc_now,
        et=et_now,
        et_naive=et_now.strftime("%Y-%m-%d %H:%M:%S"),
        timezone="America/New_York",
        offset_hours=offset_hours,
        is_dst=is_dst
    )


@router.get("/config", response_model=SystemConfigResponse)
async def get_system_config():
    """
    Get system configuration including timezone settings.

    This endpoint provides:
    - Current server time
    - Default timezone configuration
    - List of available timezones (for future settings page)
    """
    # Get current server time
    server_time = await get_server_time()

    # List of commonly used trading timezones
    available_timezones = [
        "America/New_York",    # Eastern Time (US Markets)
        "America/Chicago",     # Central Time (CME)
        "America/Los_Angeles", # Pacific Time
        "Europe/London",       # London (LSE)
        "Europe/Frankfurt",    # Frankfurt (Eurex)
        "Asia/Tokyo",         # Tokyo (TSE)
        "Asia/Hong_Kong",     # Hong Kong (HKEX)
        "Asia/Singapore",     # Singapore (SGX)
        "Australia/Sydney",   # Sydney (ASX)
    ]

    return SystemConfigResponse(
        default_timezone="America/New_York",
        available_timezones=available_timezones,
        server_time=server_time
    )


@router.get("/heartbeat")
async def heartbeat():
    """
    Simple heartbeat endpoint for connection checks.
    Also returns current server time for sync purposes.
    """
    utc_now = datetime.now(pytz.UTC)
    eastern = pytz.timezone('America/New_York')
    et_now = utc_now.astimezone(eastern)

    return {
        "status": "ok",
        "timestamp": utc_now.isoformat(),
        "et_time": et_now.strftime("%Y-%m-%d %H:%M:%S ET")
    }