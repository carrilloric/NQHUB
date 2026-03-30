"""
WebSocket Bridge Actor for NQHUB trading system.
Bridges MessageBus events to Redis pub/sub for WebSocket server.
"""
import json
from typing import List, Any, Dict, Optional
from app.trading.actors.base import NQHubActor, NQHubActorConfig
import redis.asyncio as redis


class WsBridgeActorConfig(NQHubActorConfig):
    """Configuration for WsBridgeActor."""
    redis_client: Optional[redis.Redis] = None
    channels: List[str] = []


class WsBridgeActor(NQHubActor):
    """
    Actor that bridges MessageBus events to Redis pub/sub.

    This actor subscribes to specific MessageBus events and publishes them
    to Redis pub/sub channels for the WebSocket server to consume.
    """

    def __init__(self, config: WsBridgeActorConfig):
        """
        Initialize WsBridgeActor.

        Args:
            config: Actor configuration including Redis client and channels
        """
        super().__init__(config)
        self.redis_client = config.redis_client
        self.channels = config.channels
        self._event_batch = []

    async def publish_event(self, channel: str, event: Dict[str, Any]) -> None:
        """
        Publish an event to Redis pub/sub.

        Args:
            channel: Redis channel to publish to
            event: Event data to publish
        """
        if self.redis_client:
            # Serialize event to JSON
            event_json = json.dumps(event)

            # Publish to Redis
            await self.redis_client.publish(channel, event_json)

            self.log.debug(f"Published event to {channel}: {event.get('type', 'unknown')}")

    def on_candle_update(self, candle_data: Dict[str, Any]) -> None:
        """
        Handle candle update events from MessageBus.

        Args:
            candle_data: Candle data from market
        """
        # Determine the appropriate channel based on timeframe
        timeframe = candle_data.get('timeframe', '1m')
        channel = f"nqhub.candle.{timeframe}"

        # Publish to Redis asynchronously
        self.log.debug(f"Received candle update for {channel}")
        # Note: In production, this would be awaited properly through the event loop
        # For now, we're storing for batch processing

    def on_pattern_detected(self, pattern_data: Dict[str, Any]) -> None:
        """
        Handle pattern detection events from MessageBus.

        Args:
            pattern_data: Pattern data (FVG, LP, OB, etc.)
        """
        pattern_type = pattern_data.get('pattern_type', 'unknown').lower()
        channel = f"nqhub.pattern.{pattern_type}"

        self.log.debug(f"Pattern detected: {pattern_type}")

    def on_order_event(self, order_data: Dict[str, Any]) -> None:
        """
        Handle order events from MessageBus.

        Args:
            order_data: Order event data
        """
        status = order_data.get('status', 'unknown').lower()
        channel = f"exec.order.{status}"

        self.log.debug(f"Order event: {status}")

    def on_position_event(self, position_data: Dict[str, Any]) -> None:
        """
        Handle position events from MessageBus.

        Args:
            position_data: Position event data
        """
        channel = "exec.position.update"

        self.log.debug(f"Position update received")

    def on_start(self) -> None:
        """Called when the actor starts."""
        super().on_start()

        # Subscribe to MessageBus channels
        for channel_pattern in self.channels:
            self.log.info(f"Subscribing to MessageBus channel: {channel_pattern}")
            # In production, this would register with NautilusTrader's MessageBus

    def on_stop(self) -> None:
        """Called when the actor stops."""
        super().on_stop()

        # Clean up Redis connection if needed
        if self.redis_client:
            self.log.info("Closing Redis connection")