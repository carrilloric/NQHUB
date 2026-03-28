"""
WebSocket Message Throttling

Implements per-channel and per-client rate limiting according to CONTRACT-005.
"""

import time
from typing import Dict, Optional
from collections import defaultdict, deque
import asyncio
import logging

logger = logging.getLogger(__name__)


class MessageThrottler:
    """
    Manages message throttling for WebSocket connections.

    Implements rate limiting per CONTRACT-005:
    - price/orderflow: 10 messages/second per client
    - positions: 1 message/second per client
    - risk: NEVER throttled (highest priority)
    """

    def __init__(self):
        """Initialize the throttler with default rate limits."""
        # Rate limits per channel (messages per second)
        self.rate_limits = {
            'price': 10,
            'orderflow': 10,
            'patterns': 10,  # Not specified, using same as price
            'orders': 5,     # Not specified, using moderate limit
            'positions': 1,
            'portfolio': 1,  # Not specified, using same as positions
            'risk': None,    # Never throttled
            'bot': 5         # Not specified, using moderate limit
        }

        # Track message timestamps per client per channel
        # Structure: {session_id: {channel: deque([timestamps])}}
        self._client_timestamps: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def should_allow_message(self, session_id: str, channel: str) -> bool:
        """
        Check if a message should be allowed based on throttling rules.

        Args:
            session_id: Client session ID
            channel: Channel name

        Returns:
            True if message should be sent, False if throttled
        """
        # Risk channel is never throttled
        if channel == 'risk':
            return True

        # Get rate limit for channel
        rate_limit = self.rate_limits.get(channel)
        if rate_limit is None:
            # No throttling for unknown channels (shouldn't happen with validation)
            return True

        async with self._lock:
            now = time.time()
            timestamps = self._client_timestamps[session_id][channel]

            # Remove timestamps older than 1 second
            while timestamps and timestamps[0] < now - 1.0:
                timestamps.popleft()

            # Check if we've exceeded the rate limit
            if len(timestamps) >= rate_limit:
                # Log throttling event
                logger.debug(
                    f"Throttling message for session={session_id}, "
                    f"channel={channel}, limit={rate_limit}/s"
                )
                return False

            # Add current timestamp and allow message
            timestamps.append(now)
            return True

    async def cleanup_session(self, session_id: str):
        """
        Clean up throttling data for a disconnected session.

        Args:
            session_id: Session ID to clean up
        """
        async with self._lock:
            if session_id in self._client_timestamps:
                del self._client_timestamps[session_id]
                logger.debug(f"Cleaned up throttling data for session={session_id}")

    def get_channel_limit(self, channel: str) -> Optional[int]:
        """
        Get the rate limit for a channel.

        Args:
            channel: Channel name

        Returns:
            Messages per second limit, or None if no limit
        """
        return self.rate_limits.get(channel)

    async def get_session_stats(self, session_id: str) -> Dict[str, int]:
        """
        Get current message counts for a session.

        Args:
            session_id: Session ID

        Returns:
            Dictionary of channel -> message count in current window
        """
        async with self._lock:
            now = time.time()
            stats = {}

            if session_id in self._client_timestamps:
                for channel, timestamps in self._client_timestamps[session_id].items():
                    # Count messages in the last second
                    recent_count = sum(1 for ts in timestamps if ts >= now - 1.0)
                    stats[channel] = recent_count

            return stats


class BatchThrottler:
    """
    Manages batch message throttling for efficient bulk operations.

    This is useful when processing multiple messages from Redis
    and deciding which ones to send to each client.
    """

    def __init__(self, throttler: MessageThrottler):
        """
        Initialize batch throttler.

        Args:
            throttler: The main message throttler
        """
        self.throttler = throttler

    async def filter_messages_for_client(
        self,
        session_id: str,
        messages: list[tuple[str, dict]]
    ) -> list[dict]:
        """
        Filter a batch of messages based on throttling rules.

        Args:
            session_id: Client session ID
            messages: List of (channel, message) tuples

        Returns:
            List of messages that should be sent
        """
        allowed_messages = []

        for channel, message in messages:
            if await self.throttler.should_allow_message(session_id, channel):
                allowed_messages.append(message)

        return allowed_messages


# Global throttler instance
throttler = MessageThrottler()
batch_throttler = BatchThrottler(throttler)