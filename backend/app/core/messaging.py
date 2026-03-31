"""
Message bus for event-driven architecture.

Provides pub/sub messaging with priority support.
"""

import asyncio
from typing import Any, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Message wrapper with priority."""
    event: Any
    priority: int = 5  # Default medium priority (0=highest, 10=lowest)


class MessageBus:
    """
    Message bus for event publishing with priority support.

    Priority levels:
    - 0: Maximum (kill switch events)
    - 1-2: High (critical alerts)
    - 3-5: Medium (normal operations)
    - 6-8: Low (informational)
    - 9-10: Minimum (debug)
    """

    def __init__(self):
        """Initialize message bus."""
        self._subscribers = {}
        self._queue = asyncio.PriorityQueue()
        self._running = False

    def subscribe(self, event_type: str, handler):
        """Subscribe to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event: Any, priority: int = 5):
        """
        Publish an event with priority.

        Args:
            event: Event to publish
            priority: Priority level (0=highest, 10=lowest)
        """
        event_type = type(event).__name__
        logger.debug(f"Publishing {event_type} with priority {priority}")

        # Store in priority queue
        message = Message(event=event, priority=priority)
        asyncio.create_task(self._queue.put((priority, message)))

        # Notify subscribers
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        asyncio.create_task(handler(event))
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")

    async def process_queue(self):
        """Process message queue in priority order."""
        self._running = True
        while self._running:
            try:
                priority, message = await self._queue.get()
                # Process message
                logger.debug(f"Processing message with priority {priority}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    def stop(self):
        """Stop message bus processing."""
        self._running = False


# Global message bus instance
_message_bus: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    """Get global message bus instance."""
    global _message_bus
    if _message_bus is None:
        _message_bus = MessageBus()
    return _message_bus