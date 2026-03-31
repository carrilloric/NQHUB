"""
WebSocket /ws/live endpoint for real-time trading data.

Provides 8 channels:
- price: CandleEvent data
- orderflow: Delta, POC from CandleEvent
- patterns: ICT pattern detections
- orders: Order status changes
- positions: Position updates
- portfolio: Portfolio snapshots
- risk: Risk checks (HIGHEST PRIORITY - never throttled)
- bot: Bot status updates

Auth: JWT via query parameter ?token={jwt}
Protocol: JSON messages for subscribe/unsubscribe
Redis: psubscribe("nqhub.*", "exec.*") for broadcasting
"""
import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Optional

import redis.asyncio as redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.ws.connection_manager import ConnectionManager
from app.config import settings
from app.core.security import verify_token
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

# Global singleton ConnectionManager instance
# Initialized in lifespan context
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """
    Get the global ConnectionManager singleton.

    Returns:
        ConnectionManager instance

    Raises:
        RuntimeError: If ConnectionManager not initialized
    """
    if _connection_manager is None:
        raise RuntimeError("ConnectionManager not initialized. Check lifespan setup.")
    return _connection_manager


async def authenticate_websocket(token: str, db: AsyncSession) -> Optional[User]:
    """
    Authenticate WebSocket connection via JWT token.

    Args:
        token: JWT token from query parameter
        db: Database session

    Returns:
        User if authenticated, None otherwise
    """
    # Verify JWT token
    user_id = verify_token(token)
    if user_id is None:
        logger.warning("WebSocket authentication failed: Invalid token")
        return None

    # Get user from database
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        logger.warning(f"WebSocket authentication failed: User {user_id} not found or inactive")
        return None

    logger.info(f"WebSocket authenticated: user_id={user.id}, email={user.email}")
    return user


def map_redis_to_ws_channel(redis_channel: str) -> Optional[str]:
    """
    Map Redis pub/sub channel to WebSocket channel.

    Redis channel patterns:
    - nqhub.candle.*     → price + orderflow (both channels receive CandleEvent)
    - nqhub.pattern.*    → patterns
    - nqhub.risk.check   → risk
    - nqhub.risk.kill_switch → risk (HIGHEST PRIORITY)
    - exec.order.*       → orders
    - exec.position.*    → positions

    Args:
        redis_channel: Redis channel name (e.g., "nqhub.candle.1min")

    Returns:
        WebSocket channel name or None if no mapping
    """
    # CandleEvent → broadcast to both price AND orderflow
    if redis_channel.startswith("nqhub.candle."):
        # Return special marker to broadcast to both channels
        return "price+orderflow"

    # PatternEvent → patterns channel
    if redis_channel.startswith("nqhub.pattern."):
        return "patterns"

    # Risk events → risk channel (NEVER throttled)
    if redis_channel.startswith("nqhub.risk."):
        return "risk"

    # OrderEvent → orders channel
    if redis_channel.startswith("exec.order."):
        return "orders"

    # PositionEvent → positions channel
    if redis_channel.startswith("exec.position."):
        return "positions"

    # No mapping found
    logger.debug(f"No WebSocket channel mapping for Redis channel: {redis_channel}")
    return None


async def redis_listener_task(manager: ConnectionManager, redis_url: str):
    """
    Background task that subscribes to Redis pub/sub and broadcasts to WebSocket clients.

    Subscribes to:
    - nqhub.* (all NQHUB events: candles, patterns, risk)
    - exec.* (all execution events: orders, positions)

    This task runs for the lifetime of the application.

    Args:
        manager: ConnectionManager instance
        redis_url: Redis connection URL
    """
    logger.info("Redis listener task starting...")

    try:
        # Connect to Redis
        redis_client = redis.from_url(redis_url, decode_responses=True)
        pubsub = redis_client.pubsub()

        # Subscribe to pattern channels
        await pubsub.psubscribe("nqhub.*", "exec.*")
        logger.info("Redis listener subscribed to patterns: nqhub.*, exec.*")

        # Listen for messages
        async for message in pubsub.listen():
            if message["type"] != "pmessage":
                continue

            try:
                redis_channel = message["channel"]
                data = message["data"]

                # Map Redis channel to WebSocket channel(s)
                ws_channel = map_redis_to_ws_channel(redis_channel)

                if ws_channel is None:
                    continue

                # Special case: CandleEvent goes to both price and orderflow
                if ws_channel == "price+orderflow":
                    # Send to both channels
                    await manager.broadcast("price", data)
                    await manager.broadcast("orderflow", data)
                    logger.debug(f"Broadcast CandleEvent to price + orderflow: {len(data)} bytes")
                # Risk channel has highest priority
                elif ws_channel == "risk":
                    count = await manager.broadcast("risk", data, is_risk=True)
                    logger.info(f"Broadcast RISK event to {count} client(s): {redis_channel}")
                # All other channels
                else:
                    count = await manager.broadcast(ws_channel, data)
                    logger.debug(f"Broadcast to '{ws_channel}': {count} client(s)")

            except Exception as e:
                logger.error(f"Error processing Redis message: {e}")
                continue

    except asyncio.CancelledError:
        logger.info("Redis listener task cancelled")
        raise
    except Exception as e:
        logger.error(f"Fatal error in Redis listener task: {e}")
        raise
    finally:
        logger.info("Redis listener task shutting down...")
        try:
            await redis_client.close()
        except Exception as e:
            logger.error(f"Error closing Redis client: {e}")


@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for real-time trading data.

    Authentication:
        JWT token via query parameter: /ws/live?token={jwt}

    Protocol:
        Client → Server:
            {"action": "subscribe", "channels": ["price", "risk"]}
            {"action": "unsubscribe", "channels": ["orderflow"]}

        Server → Client:
            {"type": "subscribed", "channels": ["price", "risk"]}
            {"type": "unsubscribed", "channels": ["orderflow"]}
            {"type": "error", "message": "Invalid channel: xyz"}
            {event data from Redis} (varies by channel)

    Channels:
        - price: Real-time candlestick data
        - orderflow: Order flow metrics (delta, POC)
        - patterns: ICT pattern detections
        - orders: Order status changes
        - positions: Position updates
        - portfolio: Portfolio snapshots
        - risk: Risk checks (HIGHEST PRIORITY)
        - bot: Bot status updates

    Args:
        websocket: WebSocket connection
        token: JWT authentication token (query parameter)

    Raises:
        WebSocketDisconnect: When client disconnects
    """
    manager = get_connection_manager()

    # Authenticate before accepting connection
    async for db in get_db():
        user = await authenticate_websocket(token, db)
        break

    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        logger.warning("WebSocket connection rejected: Invalid authentication")
        return

    # Accept WebSocket connection
    await websocket.accept()
    logger.info(f"WebSocket connected: user_id={user.id}")

    try:
        # Main message loop
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                action = message.get("action")
                channels = message.get("channels", [])

                if action == "subscribe":
                    # Subscribe to channels
                    response = await manager.subscribe(websocket, channels)
                    await websocket.send_text(json.dumps(response))

                elif action == "unsubscribe":
                    # Unsubscribe from channels
                    response = await manager.unsubscribe(websocket, channels)
                    await websocket.send_text(json.dumps(response))

                else:
                    # Unknown action
                    error_response = {
                        "type": "error",
                        "message": f"Unknown action: {action}"
                    }
                    await websocket.send_text(json.dumps(error_response))
                    logger.warning(f"Unknown WebSocket action: {action}")

            except json.JSONDecodeError:
                error_response = {
                    "type": "error",
                    "message": "Invalid JSON message"
                }
                await websocket.send_text(json.dumps(error_response))
                logger.warning("Received invalid JSON from WebSocket client")

            except Exception as e:
                error_response = {
                    "type": "error",
                    "message": f"Server error: {str(e)}"
                }
                await websocket.send_text(json.dumps(error_response))
                logger.error(f"Error processing WebSocket message: {e}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user_id={user.id}")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket handler: {e}")
    finally:
        # Clean up: remove connection from all channels
        await manager.disconnect(websocket)


@asynccontextmanager
async def websocket_lifespan(app):
    """
    FastAPI lifespan context manager for WebSocket infrastructure.

    Initializes:
    - ConnectionManager singleton
    - Redis listener background task

    Usage in main.py:
        from app.api.v1.ws.live import websocket_lifespan

        app = FastAPI(lifespan=websocket_lifespan)

    Args:
        app: FastAPI application instance

    Yields:
        None (startup complete)
    """
    global _connection_manager

    logger.info("WebSocket lifespan: Starting up...")

    # Initialize ConnectionManager
    _connection_manager = ConnectionManager()
    logger.info("ConnectionManager initialized")

    # Start Redis listener background task
    redis_task = asyncio.create_task(
        redis_listener_task(_connection_manager, settings.REDIS_URL)
    )
    logger.info("Redis listener background task started")

    try:
        yield
    finally:
        logger.info("WebSocket lifespan: Shutting down...")

        # Cancel Redis listener task
        redis_task.cancel()
        try:
            await redis_task
        except asyncio.CancelledError:
            pass

        logger.info("WebSocket lifespan: Shutdown complete")
