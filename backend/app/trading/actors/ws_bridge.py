"""
WebSocket Bridge Actor for NQHUB trading system.

Bridges MessageBus events to Redis pub/sub for WebSocket server consumption.
Converts NautilusTrader events to Event Bus schemas (AUT-366) and publishes
them via EventBusPublisher.
"""
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from app.trading.actors.base import NQHubActor, NQHubActorConfig
from app.trading.events.publisher import EventBusPublisher
from app.trading.events.schemas import (
    CandleEvent,
    PatternEvent,
    RiskCheckEvent,
    KillSwitchEvent,
    OrderEvent,
    PositionEvent,
)

import redis.asyncio as redis


class WsBridgeActorConfig(NQHubActorConfig):
    """Configuration for WsBridgeActor."""
    channels: List[str] = []
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0


class WsBridgeActor(NQHubActor):
    """
    Actor that bridges MessageBus events to Redis pub/sub.

    Subscribes to events from the NautilusTrader MessageBus,
    converts them to Event Bus schemas (from AUT-366), and
    publishes them to Redis via EventBusPublisher.

    The WebSocket server (AUT-352) reads from Redis and
    retransmits to frontend clients.
    """

    def __init__(
        self,
        config: WsBridgeActorConfig,
        redis_client: Optional[redis.Redis] = None
    ):
        """
        Initialize WsBridgeActor.

        Args:
            config: Actor configuration
            redis_client: Optional Redis client (for testing)
        """
        super().__init__(config)
        self.channels = config.channels or []
        self._redis_client = redis_client
        self._publisher: Optional[EventBusPublisher] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Store Redis config for creating connection
        self._redis_host = config.redis_host
        self._redis_port = config.redis_port
        self._redis_db = config.redis_db

    async def _init_redis(self) -> None:
        """Initialize Redis connection if not provided."""
        if not self._redis_client:
            self._redis_client = await redis.Redis.from_url(
                f"redis://{self._redis_host}:{self._redis_port}/{self._redis_db}",
                decode_responses=True
            )

    def on_start(self) -> None:
        """Start the actor and subscribe to MessageBus events."""
        super().on_start()

        # Initialize EventBusPublisher
        self._loop = asyncio.get_event_loop()

        # Create task to initialize Redis and publisher
        if self._loop and self._loop.is_running():
            self._loop.create_task(self._async_start())

    async def _async_start(self) -> None:
        """Async initialization."""
        await self._init_redis()
        if self._redis_client:
            self._publisher = EventBusPublisher(self._redis_client)
            self.log.info(f"WsBridgeActor started, publishing to channels: {self.channels}")

    def set_publisher_for_testing(self, publisher: EventBusPublisher) -> None:
        """Set publisher directly for testing."""
        self._publisher = publisher

    def on_stop(self) -> None:
        """Stop the actor and clean up connections."""
        super().on_stop()

        # Close publisher
        if self._publisher:
            if self._loop and self._loop.is_running():
                self._loop.create_task(self._publisher.close())

        # Close Redis connection if we created it
        if self._redis_client:
            if self._loop and self._loop.is_running():
                self._loop.create_task(self._redis_client.close())

    def on_bar(self, bar: Any) -> None:
        """
        Handle bar/candle events from NautilusTrader.

        Args:
            bar: NautilusTrader Bar object
        """
        if not self._publisher or not self._loop:
            return

        try:
            # Extract timeframe from bar type
            timeframe = str(bar.bar_type.spec.step)

            # Convert NautilusTrader Bar to CandleEvent
            event = CandleEvent(
                channel=f"nqhub.candle.{timeframe}",
                ts=datetime.fromtimestamp(bar.ts_event / 1_000_000_000),  # Convert from nanos
                bot_id=self.bot_id,
                timeframe=timeframe,
                open=float(bar.open.as_double()),
                high=float(bar.high.as_double()),
                low=float(bar.low.as_double()),
                close=float(bar.close.as_double()),
                volume=int(bar.volume.as_double()),
                delta=0,  # Will be calculated by candle enrichment service
                poc=float(bar.close.as_double()),  # Placeholder, real POC from footprint
            )

            # Publish asynchronously
            self._loop.create_task(self._publisher.publish(event))

            self.log.debug(f"Published candle event for {timeframe}")

        except Exception as e:
            self.log.error(f"Error processing bar event: {e}")

    def on_order_filled(self, event: Any) -> None:
        """
        Handle order filled events from NautilusTrader.

        Args:
            event: NautilusTrader OrderFilled event
        """
        if not self._publisher or not self._loop:
            return

        try:
            # Convert NautilusTrader OrderFilled to OrderEvent
            order_event = OrderEvent(
                channel="exec.order.filled",
                ts=datetime.fromtimestamp(event.ts_event / 1_000_000_000),
                bot_id=self.bot_id,
                order_id=str(event.order_id),
                client_order_id=str(event.client_order_id),
                broker_order_id=str(event.venue_order_id) if event.venue_order_id else None,
                bracket_role=self._determine_bracket_role(event),
                side=str(event.order_side),
                contracts=int(event.last_qty.as_double()),
                fill_price=float(event.last_px.as_double()),
                status="FILLED"
            )

            # Publish asynchronously
            self._loop.create_task(self._publisher.publish(order_event))

            self.log.debug(f"Published order filled event: {order_event.order_id}")

        except Exception as e:
            self.log.error(f"Error processing order filled event: {e}")

    def on_order_submitted(self, event: Any) -> None:
        """
        Handle order submitted events from NautilusTrader.

        Args:
            event: NautilusTrader OrderSubmitted event
        """
        if not self._publisher or not self._loop:
            return

        try:
            order_event = OrderEvent(
                channel="exec.order.submitted",
                ts=datetime.fromtimestamp(event.ts_event / 1_000_000_000),
                bot_id=self.bot_id,
                order_id=str(event.order_id),
                client_order_id=str(event.client_order_id),
                broker_order_id=None,  # Not yet assigned
                bracket_role=self._determine_bracket_role(event),
                side=str(event.order.side),
                contracts=int(event.order.quantity.as_double()),
                fill_price=None,  # Not filled yet
                status="SUBMITTED"
            )

            self._loop.create_task(self._publisher.publish(order_event))
            self.log.debug(f"Published order submitted event: {order_event.order_id}")

        except Exception as e:
            self.log.error(f"Error processing order submitted event: {e}")

    def on_order_rejected(self, event: Any) -> None:
        """
        Handle order rejected events from NautilusTrader.

        Args:
            event: NautilusTrader OrderRejected event
        """
        if not self._publisher or not self._loop:
            return

        try:
            order_event = OrderEvent(
                channel="exec.order.rejected",
                ts=datetime.fromtimestamp(event.ts_event / 1_000_000_000),
                bot_id=self.bot_id,
                order_id=str(event.order_id),
                client_order_id=str(event.client_order_id),
                broker_order_id=str(event.venue_order_id) if event.venue_order_id else None,
                bracket_role=self._determine_bracket_role(event),
                side=str(event.order.side) if hasattr(event, 'order') else "UNKNOWN",
                contracts=0,
                fill_price=None,
                status="REJECTED"
            )

            self._loop.create_task(self._publisher.publish(order_event))
            self.log.warning(f"Published order rejected event: {order_event.order_id}")

        except Exception as e:
            self.log.error(f"Error processing order rejected event: {e}")

    def on_position_changed(self, event: Any) -> None:
        """
        Handle position changed events from NautilusTrader.

        Args:
            event: NautilusTrader PositionChanged event
        """
        if not self._publisher or not self._loop:
            return

        try:
            # Calculate unrealized PNL
            entry_price = float(event.position.avg_px_open.as_double())
            current_price = float(event.last_px.as_double()) if hasattr(event, 'last_px') else entry_price
            contracts = int(event.position.quantity.as_double())

            # NQ constants
            tick_size = 0.25
            tick_value = 5.00

            # Calculate PNL based on side
            if str(event.position.side) == "LONG":
                price_diff = current_price - entry_price
            else:  # SHORT
                price_diff = entry_price - current_price

            ticks = price_diff / tick_size
            unrealized_pnl = ticks * tick_value * contracts

            position_event = PositionEvent(
                channel="exec.position.update",
                ts=datetime.fromtimestamp(event.ts_event / 1_000_000_000),
                bot_id=self.bot_id,
                symbol="NQ",
                side=str(event.position.side),
                contracts=contracts,
                entry_price=entry_price,
                current_price=current_price,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_ticks=ticks
            )

            self._loop.create_task(self._publisher.publish(position_event))
            self.log.debug(f"Published position update: {position_event.symbol} {position_event.side}")

        except Exception as e:
            self.log.error(f"Error processing position changed event: {e}")

    def on_pattern_detected(self, pattern_data: Dict[str, Any]) -> None:
        """
        Handle custom pattern detection events.

        Args:
            pattern_data: Pattern data dict with type, direction, levels, etc.
        """
        if not self._publisher or not self._loop:
            return

        try:
            pattern_type = pattern_data.get('pattern_type', 'unknown')

            pattern_event = PatternEvent(
                channel=f"nqhub.pattern.{pattern_type}",
                ts=datetime.now(),
                bot_id=self.bot_id,
                pattern_type=pattern_type,
                direction=pattern_data.get('direction', 'neutral'),
                top=pattern_data.get('top', 0.0),
                bottom=pattern_data.get('bottom', 0.0),
                timeframe=pattern_data.get('timeframe', '5min'),
                status=pattern_data.get('status', 'active')
            )

            self._loop.create_task(self._publisher.publish(pattern_event))
            self.log.debug(f"Published pattern event: {pattern_type}")

        except Exception as e:
            self.log.error(f"Error processing pattern event: {e}")

    def on_risk_check(self, risk_data: Dict[str, Any]) -> None:
        """
        Handle risk check events from RiskManager.

        Args:
            risk_data: Risk check data with result, reason, etc.
        """
        if not self._publisher or not self._loop:
            return

        try:
            risk_event = RiskCheckEvent(
                channel="nqhub.risk.check",
                ts=datetime.now(),
                bot_id=self.bot_id,
                check_name=risk_data.get('check_name', 'unknown'),
                result=risk_data.get('result', 'PASSED'),
                reason=risk_data.get('reason', ''),
                trigger_kill_switch=risk_data.get('trigger_kill_switch', False),
                account_balance=risk_data.get('account_balance', 0.0),
                current_pnl=risk_data.get('current_pnl', 0.0)
            )

            self._loop.create_task(self._publisher.publish(risk_event))

            if risk_event.trigger_kill_switch:
                self.log.warning(f"Risk check failed with kill switch trigger: {risk_event.check_name}")
            else:
                self.log.debug(f"Published risk check event: {risk_event.check_name}")

        except Exception as e:
            self.log.error(f"Error processing risk check event: {e}")

    def on_kill_switch(self, kill_data: Dict[str, Any]) -> None:
        """
        Handle kill switch activation events.

        Args:
            kill_data: Kill switch data with scope, reason, etc.
        """
        if not self._publisher or not self._loop:
            return

        try:
            kill_event = KillSwitchEvent(
                channel="nqhub.risk.kill_switch",
                ts=datetime.now(),
                bot_id=self.bot_id,
                scope=kill_data.get('scope', 'per_bot'),
                reason=kill_data.get('reason', 'unknown'),
                triggered_by=kill_data.get('triggered_by', 'manual'),
                positions_closed=kill_data.get('positions_closed', 0),
                orders_cancelled=kill_data.get('orders_cancelled', 0)
            )

            # Use special priority publishing for kill switch
            self._loop.create_task(self._publisher.publish_kill_switch(kill_event))
            self.log.critical(f"KILL SWITCH ACTIVATED: {kill_event.reason}")

        except Exception as e:
            self.log.critical(f"CRITICAL: Error processing kill switch event: {e}")

    def _determine_bracket_role(self, event: Any) -> Optional[str]:
        """
        Determine if order is part of a bracket (ENTRY, TP, SL).

        Args:
            event: Order event from NautilusTrader

        Returns:
            Bracket role string or None
        """
        # Check order tags or metadata to determine bracket role
        # This is implementation-specific based on how brackets are tagged
        if hasattr(event, 'order') and hasattr(event.order, 'tags'):
            tags = event.order.tags
            if 'ENTRY' in tags:
                return 'ENTRY'
            elif 'TP' in tags or 'TAKE_PROFIT' in tags:
                return 'TP'
            elif 'SL' in tags or 'STOP_LOSS' in tags:
                return 'SL'
        return None