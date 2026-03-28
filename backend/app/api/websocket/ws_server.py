"""
WebSocket Server Implementation

Implementation of CONTRACT-005 WebSocket API with FastAPI and Redis bridge.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from fastapi.exceptions import WebSocketException
import redis.asyncio as redis
from typing import Optional, Dict, Any
import json
import asyncio
from datetime import datetime
import logging
from jose import jwt, JWTError

from app.config import settings
from app.core.security import verify_token
from app.db.redis import get_redis_client
from .connection_manager import manager
from .throttle import throttler

logger = logging.getLogger(__name__)

router = APIRouter()

# Redis channel mappings
REDIS_CHANNEL_MAPPING = {
    'price': ['nqhub.candle.*'],
    'orderflow': ['nqhub.candle.*'],
    'patterns': ['nqhub.pattern.*'],
    'orders': ['exec.order.*'],
    'positions': ['exec.position.*'],
    'portfolio': ['exec.position.*', 'exec.order.*'],
    'risk': ['nqhub.risk.*'],
    'bot': ['bot.status.*']
}

# Page subscription bundles
PAGE_SUBSCRIPTIONS = {
    'dashboard': ['price', 'positions', 'risk'],
    'data-module': ['price', 'orderflow', 'patterns'],
    'trading': ['price', 'orderflow', 'orders', 'positions', 'risk'],
    'bot': ['bot', 'positions', 'risk']
}


class WebSocketHandler:
    """
    Handles WebSocket connection lifecycle and message processing.
    """

    def __init__(self, websocket: WebSocket, session_id: str, user_id: str):
        """
        Initialize WebSocket handler.

        Args:
            websocket: The WebSocket connection
            session_id: Unique session identifier
            user_id: Authenticated user ID
        """
        self.websocket = websocket
        self.session_id = session_id
        self.user_id = user_id
        self.redis_client: Optional[redis.Redis] = None
        self.redis_pubsub: Optional[redis.client.PubSub] = None
        self.tasks: list[asyncio.Task] = []
        self._running = True

    async def start(self):
        """Start the WebSocket handler with all background tasks."""
        try:
            # Initialize Redis client
            self.redis_client = await get_redis_client()
            self.redis_pubsub = self.redis_client.pubsub()

            # Start background tasks
            self.tasks.append(asyncio.create_task(self._heartbeat_loop()))
            self.tasks.append(asyncio.create_task(self._redis_listener()))
            self.tasks.append(asyncio.create_task(self._message_receiver()))

            # Wait for any task to complete (usually due to disconnection)
            await asyncio.gather(*self.tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"WebSocket handler error for session {self.session_id}: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Clean up resources on disconnection."""
        self._running = False

        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()

        # Clean up Redis pubsub
        if self.redis_pubsub:
            await self.redis_pubsub.unsubscribe()
            await self.redis_pubsub.close()

        # Clean up throttler data
        await throttler.cleanup_session(self.session_id)

        # Disconnect from manager
        await manager.disconnect(self.session_id)

        logger.info(f"WebSocket cleanup completed for session {self.session_id}")

    async def _heartbeat_loop(self):
        """Send heartbeat pings every 30 seconds."""
        sequence = 0
        while self._running:
            try:
                # Wait 30 seconds
                await asyncio.sleep(30)

                # Send ping
                ping_message = {
                    "event": "ping",
                    "data": {
                        "sequence": sequence,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                }
                await manager.send_personal_message(ping_message, self.session_id)

                sequence += 1

                # Check if connection is stale
                connection = manager.get_connection(self.session_id)
                if connection and connection.is_stale:
                    logger.warning(f"Connection {self.session_id} is stale, disconnecting")
                    self._running = False
                    break

            except Exception as e:
                logger.error(f"Heartbeat error for session {self.session_id}: {e}")
                break

    async def _redis_listener(self):
        """Listen to Redis pub/sub and forward messages to WebSocket."""
        if not self.redis_pubsub:
            return

        try:
            while self._running:
                # Get connection to check subscribed channels
                connection = manager.get_connection(self.session_id)
                if not connection:
                    break

                # Subscribe to Redis channels based on WebSocket subscriptions
                redis_channels = set()
                for ws_channel in connection.subscribed_channels:
                    if ws_channel in REDIS_CHANNEL_MAPPING:
                        redis_channels.update(REDIS_CHANNEL_MAPPING[ws_channel])

                # Update Redis subscriptions
                current_channels = set(self.redis_pubsub.channels.keys())
                to_subscribe = redis_channels - current_channels
                to_unsubscribe = current_channels - redis_channels

                if to_subscribe:
                    await self.redis_pubsub.psubscribe(*to_subscribe)
                    logger.debug(f"Session {self.session_id} subscribed to Redis: {to_subscribe}")

                if to_unsubscribe:
                    await self.redis_pubsub.punsubscribe(*to_unsubscribe)
                    logger.debug(f"Session {self.session_id} unsubscribed from Redis: {to_unsubscribe}")

                # Listen for messages with timeout
                try:
                    message = await asyncio.wait_for(
                        self.redis_pubsub.get_message(ignore_subscribe_messages=True),
                        timeout=0.1
                    )

                    if message and message['type'] in ('message', 'pmessage'):
                        await self._handle_redis_message(message)

                except asyncio.TimeoutError:
                    continue

        except Exception as e:
            logger.error(f"Redis listener error for session {self.session_id}: {e}")

    async def _handle_redis_message(self, message: dict):
        """
        Process a message from Redis and forward to WebSocket.

        Args:
            message: Redis pub/sub message
        """
        try:
            # Parse Redis message
            redis_channel = message['channel']
            if isinstance(redis_channel, bytes):
                redis_channel = redis_channel.decode('utf-8')

            data = message['data']
            if isinstance(data, bytes):
                data = data.decode('utf-8')

            # Parse JSON data
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from Redis channel {redis_channel}: {data}")
                return

            # Determine WebSocket channel from Redis channel
            ws_channel = self._map_redis_to_ws_channel(redis_channel)
            if not ws_channel:
                return

            # Check if client is subscribed to this channel
            connection = manager.get_connection(self.session_id)
            if not connection or ws_channel not in connection.subscribed_channels:
                return

            # Check throttling
            if not await throttler.should_allow_message(self.session_id, ws_channel):
                return

            # Format message according to CONTRACT-005
            ws_message = {
                "channel": ws_channel,
                "event": payload.get("event", "update"),
                "data": payload.get("data", payload),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

            # Add bot_id if present
            if "bot_id" in payload:
                ws_message["bot_id"] = payload["bot_id"]

            # Send to client
            await manager.send_personal_message(ws_message, self.session_id)

        except Exception as e:
            logger.error(f"Error handling Redis message for session {self.session_id}: {e}")

    def _map_redis_to_ws_channel(self, redis_channel: str) -> Optional[str]:
        """
        Map Redis channel pattern to WebSocket channel.

        Args:
            redis_channel: Redis channel name

        Returns:
            WebSocket channel name or None
        """
        # Map based on prefix
        if redis_channel.startswith('nqhub.candle'):
            # Candle data goes to both price and orderflow
            return 'price'  # Primary channel
        elif redis_channel.startswith('nqhub.pattern'):
            return 'patterns'
        elif redis_channel.startswith('exec.order'):
            return 'orders'
        elif redis_channel.startswith('exec.position'):
            return 'positions'
        elif redis_channel.startswith('nqhub.risk'):
            return 'risk'
        elif redis_channel.startswith('bot.status'):
            return 'bot'

        return None

    async def _message_receiver(self):
        """Receive and process messages from the WebSocket client."""
        try:
            while self._running:
                # Receive message from client
                data = await self.websocket.receive_text()

                # Parse message
                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    await self._send_error("Invalid JSON format")
                    continue

                # Handle message based on action
                action = message.get('action')

                if action == 'subscribe':
                    await self._handle_subscribe(message)
                elif action == 'unsubscribe':
                    await self._handle_unsubscribe(message)
                elif action == 'subscribe_page':
                    await self._handle_subscribe_page(message)
                elif action == 'pong':
                    await self._handle_pong(message)
                else:
                    await self._send_error(f"Unknown action: {action}")

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: session {self.session_id}")
            self._running = False
        except Exception as e:
            logger.error(f"Message receiver error for session {self.session_id}: {e}")
            self._running = False

    async def _handle_subscribe(self, message: dict):
        """Handle subscribe action from client."""
        channels = message.get('channels', [])
        if not isinstance(channels, list):
            await self._send_error("channels must be an array")
            return

        # Subscribe through manager
        subscribed = await manager.subscribe(self.session_id, channels)

        # Send confirmation
        response = {
            "action": "subscribed",
            "channels": subscribed
        }
        await manager.send_personal_message(response, self.session_id)

        logger.info(f"Session {self.session_id} subscribed to: {subscribed}")

    async def _handle_unsubscribe(self, message: dict):
        """Handle unsubscribe action from client."""
        channels = message.get('channels', [])
        if not isinstance(channels, list):
            await self._send_error("channels must be an array")
            return

        # Unsubscribe through manager
        unsubscribed = await manager.unsubscribe(self.session_id, channels)

        # Send confirmation
        response = {
            "action": "unsubscribed",
            "channels": unsubscribed
        }
        await manager.send_personal_message(response, self.session_id)

        logger.info(f"Session {self.session_id} unsubscribed from: {unsubscribed}")

    async def _handle_subscribe_page(self, message: dict):
        """Handle page subscription (convenience method)."""
        page = message.get('page')
        if page not in PAGE_SUBSCRIPTIONS:
            await self._send_error(f"Unknown page: {page}")
            return

        # Get channels for page
        channels = PAGE_SUBSCRIPTIONS[page]

        # Subscribe through manager
        subscribed = await manager.subscribe(self.session_id, channels)

        # Send confirmation
        response = {
            "action": "subscribed",
            "page": page,
            "channels": subscribed
        }
        await manager.send_personal_message(response, self.session_id)

        logger.info(f"Session {self.session_id} subscribed to page '{page}': {subscribed}")

    async def _handle_pong(self, message: dict):
        """Handle pong response from client."""
        connection = manager.get_connection(self.session_id)
        if connection:
            connection.update_heartbeat()
            logger.debug(f"Received pong from session {self.session_id}")

    async def _send_error(self, error: str):
        """Send error message to client."""
        error_message = {
            "event": "error",
            "data": {
                "message": error,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        await manager.send_personal_message(error_message, self.session_id)


@router.websocket("/live")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT authentication token")
):
    """
    WebSocket endpoint for live data streaming.

    Implements CONTRACT-005 WebSocket API specification.

    Query Parameters:
        token: JWT authentication token

    Connection Flow:
    1. Validate JWT token
    2. Accept WebSocket connection
    3. Register with connection manager
    4. Start message handlers
    5. Clean up on disconnection
    """
    # Validate JWT token
    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return

    # Decode and validate token
    user_id = verify_token(token)
    if not user_id:
        logger.warning(f"JWT validation failed for token")
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Accept connection and register with manager
    session_id = await manager.connect(websocket, user_id)

    logger.info(f"WebSocket connected: session={session_id}, user={user_id}")

    # Create and start handler
    handler = WebSocketHandler(websocket, session_id, user_id)
    await handler.start()

    logger.info(f"WebSocket handler completed for session={session_id}")