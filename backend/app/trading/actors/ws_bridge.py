"""
WebSocket Bridge Actor for NautilusTrader.
Bridges MessageBus events to Redis pub/sub for WebSocket server consumption.
"""
import json
import redis
from typing import Optional, List, Dict, Any
from app.trading.actors.base import NQHubActor, NQHubActorConfig


class WsBridgeActorConfig(NQHubActorConfig, kw_only=True):
    """Configuration for WsBridgeActor."""
    redis_client: Optional[redis.Redis] = None
    channels: List[str] = []


class WsBridgeActor(NQHubActor):
    """
    Actor that bridges MessageBus events to Redis pub/sub.

    This actor subscribes to MessageBus events and publishes them
    to Redis channels for WebSocket server consumption.
    """

    def __init__(self, config: WsBridgeActorConfig):
        """
        Initialize WsBridgeActor.

        Args:
            config: Actor configuration including Redis client and channels
        """
        super().__init__(config)
        self.redis_client = config.redis_client
        self.channels = config.channels or []

    def on_start(self) -> None:
        """Start the actor and subscribe to MessageBus events."""
        super().on_start()
        # Subscribe to relevant MessageBus events
        # self.subscribe_data(DataType.TRADE_TICK)
        # self.subscribe_data(DataType.ORDER_BOOK)
        self.log.info(f"WsBridgeActor started, publishing to channels: {self.channels}")

    def on_stop(self) -> None:
        """Stop the actor and clean up connections."""
        super().on_stop()
        if self.redis_client:
            try:
                self.redis_client.close()
            except Exception as e:
                self.log.error(f"Error closing Redis connection: {e}")

    async def publish_event(self, channel: str, event: Dict[str, Any]) -> None:
        """
        Publish an event to Redis pub/sub.

        Args:
            channel: Redis channel to publish to
            event: Event data to publish
        """
        if self.redis_client and channel in self.channels:
            try:
                event_json = json.dumps(event)
                await self.redis_client.publish(channel, event_json)
                self.log.debug(f"Published event to channel {channel}: {event.get('type', 'unknown')}")
            except Exception as e:
                self.log.error(f"Error publishing to Redis channel {channel}: {e}")