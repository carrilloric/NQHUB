"""
ConnectionManager - Thread-safe WebSocket connection and subscription manager.

Manages active WebSocket connections and their subscriptions to channels.
Implements singleton pattern via FastAPI lifespan for the entire application.

The 8 channels:
- price: Real-time candlestick data
- orderflow: Order flow metrics (delta, POC)
- patterns: ICT pattern detections
- orders: Order status changes
- positions: Position updates
- portfolio: Portfolio snapshots
- risk: Risk checks (NEVER throttled - highest priority)
- bot: Bot status updates
"""
import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Valid WebSocket channels
VALID_CHANNELS = {
    "price",
    "orderflow",
    "patterns",
    "orders",
    "positions",
    "portfolio",
    "risk",
    "bot",
}


class ConnectionManager:
    """
    Thread-safe WebSocket connection manager.

    Manages subscriptions per channel and broadcasts messages to subscribed clients.
    The 'risk' channel has highest priority and is never throttled.

    Usage:
        manager = ConnectionManager()
        await manager.subscribe(websocket, ["price", "risk"])
        await manager.broadcast("price", json_data)
        await manager.disconnect(websocket)
    """

    def __init__(self):
        """
        Initialize the connection manager with empty subscription sets.

        Each channel maintains a set of WebSocket connections subscribed to it.
        Using sets ensures O(1) lookup and automatic deduplication.
        """
        self._connections: Dict[str, Set[WebSocket]] = {
            channel: set() for channel in VALID_CHANNELS
        }
        # Map from WebSocket to all channels it's subscribed to (for cleanup)
        self._ws_channels: Dict[WebSocket, Set[str]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        logger.info("ConnectionManager initialized with 8 channels")

    async def subscribe(self, ws: WebSocket, channels: list[str]) -> dict:
        """
        Subscribe a WebSocket connection to one or more channels.

        Args:
            ws: WebSocket connection
            channels: List of channel names to subscribe to

        Returns:
            dict: Response with 'type' and 'channels' or 'error' message

        Examples:
            >>> await manager.subscribe(ws, ["price", "risk"])
            {"type": "subscribed", "channels": ["price", "risk"]}

            >>> await manager.subscribe(ws, ["invalid"])
            {"type": "error", "message": "Invalid channel: invalid"}
        """
        # Validate channels
        invalid_channels = [ch for ch in channels if ch not in VALID_CHANNELS]
        if invalid_channels:
            error_msg = f"Invalid channel(s): {', '.join(invalid_channels)}"
            logger.warning(f"Subscribe rejected - {error_msg}")
            return {"type": "error", "message": error_msg}

        async with self._lock:
            # Track all channels for this WebSocket
            if ws not in self._ws_channels:
                self._ws_channels[ws] = set()

            # Add WebSocket to each channel's subscription set
            for channel in channels:
                self._connections[channel].add(ws)
                self._ws_channels[ws].add(channel)

            logger.info(f"WebSocket subscribed to {len(channels)} channel(s): {channels}")

        return {"type": "subscribed", "channels": channels}

    async def unsubscribe(self, ws: WebSocket, channels: list[str]) -> dict:
        """
        Unsubscribe a WebSocket connection from one or more channels.

        Args:
            ws: WebSocket connection
            channels: List of channel names to unsubscribe from

        Returns:
            dict: Response with 'type' and 'channels'

        Example:
            >>> await manager.unsubscribe(ws, ["orderflow"])
            {"type": "unsubscribed", "channels": ["orderflow"]}
        """
        # Validate channels
        invalid_channels = [ch for ch in channels if ch not in VALID_CHANNELS]
        if invalid_channels:
            error_msg = f"Invalid channel(s): {', '.join(invalid_channels)}"
            logger.warning(f"Unsubscribe rejected - {error_msg}")
            return {"type": "error", "message": error_msg}

        async with self._lock:
            for channel in channels:
                self._connections[channel].discard(ws)
                if ws in self._ws_channels:
                    self._ws_channels[ws].discard(channel)

            logger.info(f"WebSocket unsubscribed from {len(channels)} channel(s): {channels}")

        return {"type": "unsubscribed", "channels": channels}

    async def broadcast(self, channel: str, message: str, is_risk: bool = False) -> int:
        """
        Broadcast a message to all WebSocket clients subscribed to a channel.

        The 'risk' channel has special priority and is never throttled.
        For other channels, we send asynchronously to avoid blocking.

        Args:
            channel: Channel name
            message: Message to broadcast (JSON string)
            is_risk: Whether this is a risk channel message (highest priority)

        Returns:
            int: Number of clients that received the message

        Example:
            >>> data = json.dumps({"type": "candle", "price": 15000.0})
            >>> count = await manager.broadcast("price", data)
            >>> print(f"Sent to {count} clients")
        """
        if channel not in VALID_CHANNELS:
            logger.warning(f"Broadcast to invalid channel: {channel}")
            return 0

        # Get snapshot of current connections (to avoid holding lock during sends)
        async with self._lock:
            connections = self._connections[channel].copy()

        if not connections:
            return 0

        # For risk channel, send immediately (never throttle)
        # For other channels, send concurrently with error handling
        sent_count = 0
        failed_connections = []

        for ws in connections:
            try:
                if is_risk or channel == "risk":
                    # Risk messages are sent synchronously (highest priority)
                    await ws.send_text(message)
                else:
                    # Other messages are sent asynchronously
                    await ws.send_text(message)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send to WebSocket on channel '{channel}': {e}")
                failed_connections.append(ws)

        # Clean up failed connections
        if failed_connections:
            async with self._lock:
                for ws in failed_connections:
                    self._connections[channel].discard(ws)
                    if ws in self._ws_channels:
                        self._ws_channels[ws].discard(channel)
            logger.warning(f"Removed {len(failed_connections)} dead connection(s) from channel '{channel}'")

        logger.debug(f"Broadcast to channel '{channel}': {sent_count} client(s)")
        return sent_count

    async def disconnect(self, ws: WebSocket) -> None:
        """
        Disconnect a WebSocket and remove it from all subscribed channels.

        Args:
            ws: WebSocket connection to disconnect

        Example:
            >>> await manager.disconnect(websocket)
        """
        async with self._lock:
            # Get all channels this WebSocket is subscribed to
            channels = self._ws_channels.get(ws, set()).copy()

            # Remove from all channels
            for channel in channels:
                self._connections[channel].discard(ws)

            # Remove from tracking
            if ws in self._ws_channels:
                del self._ws_channels[ws]

            logger.info(f"WebSocket disconnected from {len(channels)} channel(s)")

    def get_channel_stats(self) -> dict:
        """
        Get statistics about current connections per channel.

        Returns:
            dict: Channel names mapped to number of connected clients

        Example:
            >>> stats = manager.get_channel_stats()
            >>> print(stats)
            {"price": 5, "risk": 3, "orders": 2, ...}
        """
        return {
            channel: len(connections)
            for channel, connections in self._connections.items()
        }
