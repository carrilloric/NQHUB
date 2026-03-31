"""
Event Bus Publisher for Redis pub/sub.

Handles event serialization and publication to Redis channels.
Provides special priority handling for kill switch events.
"""
import redis.asyncio as redis
import json
import logging
from typing import Optional
from app.trading.events.schemas import BaseEvent, KillSwitchEvent

logger = logging.getLogger(__name__)


class EventBusPublisher:
    """
    Publishes events to Redis pub/sub channels.

    Used by WsBridgeActor for normal events and directly by
    KillSwitchActor for priority events.

    Features:
    - JSON serialization of Pydantic events
    - Channel-based routing
    - Special priority handling for kill switch events
    """

    def __init__(self, redis_client: redis.Redis):
        """
        Initialize the publisher with a Redis client.

        Args:
            redis_client: Async Redis client instance
        """
        self._redis = redis_client
        self._published_count = 0

    async def publish(self, event: BaseEvent) -> None:
        """
        Serialize event to JSON and publish to its channel.

        Args:
            event: Event to publish (any subclass of BaseEvent)
        """
        try:
            # Serialize to JSON using Pydantic's model_dump_json
            payload = event.model_dump_json()

            # Publish to the event's channel
            subscribers = await self._redis.publish(event.channel, payload)

            self._published_count += 1
            logger.debug(
                f"Published event to channel '{event.channel}' "
                f"({subscribers} subscribers, total: {self._published_count})"
            )

        except Exception as e:
            logger.error(
                f"Failed to publish event to channel '{event.channel}': {e}",
                exc_info=True
            )
            raise

    async def publish_kill_switch(self, event: KillSwitchEvent) -> None:
        """
        Publish kill switch event with maximum priority.

        Kill switch events are published to:
        1. Their specific channel (nqhub.risk.kill_switch)
        2. A wildcard channel (nqhub.risk.*) for guaranteed delivery

        This ensures all risk management components receive the event
        even if they're not specifically subscribed to kill_switch.

        Args:
            event: Kill switch event to publish
        """
        try:
            # Serialize once
            payload = event.model_dump_json()

            # Publish to specific kill switch channel
            subscribers_specific = await self._redis.publish(
                "nqhub.risk.kill_switch",
                payload
            )

            # Also publish to wildcard risk channel for guaranteed delivery
            subscribers_wildcard = await self._redis.publish(
                "nqhub.risk.*",
                payload
            )

            self._published_count += 2

            logger.warning(
                f"KILL SWITCH ACTIVATED: Published to "
                f"'nqhub.risk.kill_switch' ({subscribers_specific} subscribers) and "
                f"'nqhub.risk.*' ({subscribers_wildcard} subscribers). "
                f"Reason: {event.reason}"
            )

        except Exception as e:
            logger.critical(
                f"CRITICAL: Failed to publish kill switch event: {e}",
                exc_info=True
            )
            # Re-raise - kill switch failures are critical
            raise

    @property
    def published_count(self) -> int:
        """Get total number of events published."""
        return self._published_count

    async def close(self) -> None:
        """
        Close the publisher and clean up resources.
        Note: Does not close the Redis client (owned by caller).
        """
        logger.info(f"EventBusPublisher closed. Total events published: {self._published_count}")