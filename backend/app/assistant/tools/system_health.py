"""
System health monitoring
"""
from typing import Dict, Any
import logging
import psutil

logger = logging.getLogger(__name__)


def get_system_health() -> Dict[str, Any]:
    """Get system health status"""
    try:
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage = {
            "total_gb": round(memory.total / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent": memory.percent,
        }

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Disk usage
        disk = psutil.disk_usage('/')
        disk_usage = {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "percent": disk.percent,
        }

        return {
            "api_status": "healthy",
            "database_status": "connected",  # Will check connection in actual implementation
            "redis_status": "connected",     # Will check Redis connection
            "workers_active": 4,              # Placeholder - check actual workers
            "workers_total": 4,
            "memory_usage": memory_usage,
            "cpu_percent": cpu_percent,
            "disk_usage": disk_usage,
        }

    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        return {
            "api_status": "degraded",
            "database_status": "unknown",
            "redis_status": "unknown",
            "workers_active": 0,
            "workers_total": 0,
            "error": str(e)
        }
