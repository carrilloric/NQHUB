"""
WebSocket Connection Manager

Manages active WebSocket connections and subscriptions.
"""

from typing import Dict, Set, List, Optional
from fastapi import WebSocket
from datetime import datetime
import json
import asyncio
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and channel subscriptions.

    Implements:
    - Connection tracking by session ID
    - Channel subscription management
    - Message broadcasting
    - Connection cleanup
    """

    def __init__(self):
        # Map session_id -> Connection
        self.active_connections: Dict[str, "Connection"] = {}
        # Map channel -> Set[session_id]
        self.channel_subscriptions: Dict[str, Set[str]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            user_id: Authenticated user ID from JWT

        Returns:
            Session ID for this connection
        """
        await websocket.accept()
        session_id = str(uuid4())

        async with self._lock:
            connection = Connection(
                session_id=session_id,
                websocket=websocket,
                user_id=user_id,
                connected_at=datetime.utcnow()
            )
            self.active_connections[session_id] = connection

        logger.info(f"WebSocket connected: session_id={session_id}, user_id={user_id}")

        # Send connection established message
        await self.send_personal_message({
            "event": "connection_established",
            "data": {
                "session_id": session_id,
                "server_time": datetime.utcnow().isoformat() + "Z",
                "version": "1.0.0"
            }
        }, session_id)

        return session_id

    async def disconnect(self, session_id: str):
        """
        Handle WebSocket disconnection.

        Args:
            session_id: Session ID to disconnect
        """
        async with self._lock:
            if session_id in self.active_connections:
                connection = self.active_connections[session_id]

                # Remove from all channel subscriptions
                for channel, subscribers in self.channel_subscriptions.items():
                    if session_id in subscribers:
                        subscribers.remove(session_id)

                # Remove connection
                del self.active_connections[session_id]

                logger.info(f"WebSocket disconnected: session_id={session_id}")

    async def subscribe(self, session_id: str, channels: List[str]) -> List[str]:
        """
        Subscribe a connection to channels.

        Args:
            session_id: Session ID
            channels: List of channel names to subscribe to

        Returns:
            List of successfully subscribed channels
        """
        subscribed = []

        async with self._lock:
            if session_id not in self.active_connections:
                return subscribed

            connection = self.active_connections[session_id]

            for channel in channels:
                # Validate channel name
                if not self._is_valid_channel(channel):
                    continue

                # Add to channel subscriptions
                if channel not in self.channel_subscriptions:
                    self.channel_subscriptions[channel] = set()

                self.channel_subscriptions[channel].add(session_id)
                connection.subscribed_channels.add(channel)
                subscribed.append(channel)

        logger.info(f"Session {session_id} subscribed to channels: {subscribed}")
        return subscribed

    async def unsubscribe(self, session_id: str, channels: List[str]) -> List[str]:
        """
        Unsubscribe a connection from channels.

        Args:
            session_id: Session ID
            channels: List of channel names to unsubscribe from

        Returns:
            List of successfully unsubscribed channels
        """
        unsubscribed = []

        async with self._lock:
            if session_id not in self.active_connections:
                return unsubscribed

            connection = self.active_connections[session_id]

            for channel in channels:
                if channel in self.channel_subscriptions:
                    if session_id in self.channel_subscriptions[channel]:
                        self.channel_subscriptions[channel].remove(session_id)
                        connection.subscribed_channels.discard(channel)
                        unsubscribed.append(channel)

        logger.info(f"Session {session_id} unsubscribed from channels: {unsubscribed}")
        return unsubscribed

    async def send_personal_message(self, message: dict, session_id: str):
        """
        Send a message to a specific connection.

        Args:
            message: Message dictionary to send
            session_id: Target session ID
        """
        if session_id in self.active_connections:
            connection = self.active_connections[session_id]
            try:
                await connection.websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")
                await self.disconnect(session_id)

    async def broadcast_to_channel(
        self,
        channel: str,
        message: dict,
        exclude_session: Optional[str] = None
    ):
        """
        Broadcast a message to all subscribers of a channel.

        Args:
            channel: Channel name
            message: Message dictionary to broadcast
            exclude_session: Optional session ID to exclude from broadcast
        """
        if channel not in self.channel_subscriptions:
            return

        # Get copy of subscribers to avoid modification during iteration
        subscribers = list(self.channel_subscriptions[channel])

        # Send to all subscribers
        tasks = []
        for session_id in subscribers:
            if session_id == exclude_session:
                continue

            if session_id in self.active_connections:
                connection = self.active_connections[session_id]
                tasks.append(self._send_with_error_handling(connection, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_with_error_handling(self, connection: "Connection", message: dict):
        """
        Send message with error handling.

        Args:
            connection: Connection to send to
            message: Message to send
        """
        try:
            await connection.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to {connection.session_id}: {e}")
            await self.disconnect(connection.session_id)

    def _is_valid_channel(self, channel: str) -> bool:
        """
        Validate channel name.

        Args:
            channel: Channel name to validate

        Returns:
            True if channel is valid
        """
        valid_channels = [
            'price', 'orderflow', 'patterns', 'orders',
            'positions', 'portfolio', 'risk', 'bot'
        ]
        return channel in valid_channels

    def get_connection(self, session_id: str) -> Optional["Connection"]:
        """
        Get connection by session ID.

        Args:
            session_id: Session ID

        Returns:
            Connection or None if not found
        """
        return self.active_connections.get(session_id)

    @property
    def connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.active_connections)


class Connection:
    """
    Represents a WebSocket connection.
    """

    def __init__(
        self,
        session_id: str,
        websocket: WebSocket,
        user_id: str,
        connected_at: datetime
    ):
        self.session_id = session_id
        self.websocket = websocket
        self.user_id = user_id
        self.connected_at = connected_at
        self.subscribed_channels: Set[str] = set()
        self.last_heartbeat: Optional[datetime] = None
        self.heartbeat_sequence: int = 0

    def update_heartbeat(self):
        """Update heartbeat timestamp and sequence."""
        self.last_heartbeat = datetime.utcnow()
        self.heartbeat_sequence += 1

    @property
    def is_stale(self) -> bool:
        """Check if connection is stale (no heartbeat in 60 seconds)."""
        if not self.last_heartbeat:
            # Allow 60 seconds for first heartbeat
            return (datetime.utcnow() - self.connected_at).total_seconds() > 60

        return (datetime.utcnow() - self.last_heartbeat).total_seconds() > 60


# Global connection manager instance
manager = ConnectionManager()