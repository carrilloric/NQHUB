"""
Redis connection and client management
"""

import redis.asyncio as redis
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """
    Get Redis client instance.

    Creates a new client if one doesn't exist.

    Returns:
        Redis client instance
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = await redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        logger.info(f"Connected to Redis at {settings.REDIS_URL}")

    return _redis_client


async def close_redis_client():
    """
    Close Redis client connection.
    """
    global _redis_client

    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")