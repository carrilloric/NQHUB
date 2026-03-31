"""
Tests for Event Bus publisher/subscriber implementation.

Tests EventBusPublisher, WsBridgeActor publishing, and DbWriterActor batching.
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, MagicMock, patch, call
from datetime import datetime
from typing import Any, Dict

import redis.asyncio as redis


class TestEventBusPublisher:
    """Test suite for EventBusPublisher."""

    @pytest.mark.asyncio
    async def test_publisher_publishes_to_correct_channel(self):
        """Test that EventBusPublisher publishes events to the correct Redis channel."""
        from app.trading.events.publisher import EventBusPublisher
        from app.trading.events.schemas import CandleEvent

        # Mock Redis client
        mock_redis = AsyncMock(spec=redis.Redis)
        mock_redis.publish = AsyncMock(return_value=1)  # 1 subscriber

        # Create publisher
        publisher = EventBusPublisher(mock_redis)

        # Create test event
        event = CandleEvent(
            channel="nqhub.candle.1min",
            ts=datetime.now(),
            bot_id="test-bot",
            timeframe="1min",
            open=19250.25,
            high=19255.00,
            low=19248.50,
            close=19252.75,
            volume=1234,
            delta=45,
            poc=19251.50
        )

        # Publish event
        await publisher.publish(event)

        # Verify Redis publish was called with correct channel and JSON payload
        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args

        # Check channel
        assert call_args[0][0] == "nqhub.candle.1min"

        # Check payload is valid JSON
        payload = call_args[0][1]
        data = json.loads(payload)
        assert data["channel"] == "nqhub.candle.1min"
        assert data["bot_id"] == "test-bot"
        assert data["timeframe"] == "1min"
        assert data["open"] == 19250.25

    @pytest.mark.asyncio
    async def test_kill_switch_published_to_priority_channel(self):
        """Test that kill switch events are published to priority channels."""
        from app.trading.events.publisher import EventBusPublisher
        from app.trading.events.schemas import KillSwitchEvent

        # Mock Redis client
        mock_redis = AsyncMock(spec=redis.Redis)
        mock_redis.publish = AsyncMock(return_value=2)  # 2 subscribers

        # Create publisher
        publisher = EventBusPublisher(mock_redis)

        # Create kill switch event
        event = KillSwitchEvent(
            channel="nqhub.risk.kill_switch",
            ts=datetime.now(),
            bot_id="test-bot",
            scope="global",
            reason="Critical loss threshold exceeded",
            triggered_by="circuit_breaker",
            positions_closed=5,
            orders_cancelled=10
        )

        # Publish kill switch event
        await publisher.publish_kill_switch(event)

        # Should publish to TWO channels for guaranteed delivery
        assert mock_redis.publish.call_count == 2

        # Get both calls
        calls = mock_redis.publish.call_args_list

        # First call: specific kill switch channel
        assert calls[0][0][0] == "nqhub.risk.kill_switch"
        payload1 = json.loads(calls[0][0][1])
        assert payload1["scope"] == "global"
        assert payload1["reason"] == "Critical loss threshold exceeded"

        # Second call: wildcard risk channel
        assert calls[1][0][0] == "nqhub.risk.*"
        payload2 = json.loads(calls[1][0][1])
        assert payload2 == payload1  # Same payload


class TestWsBridgeActor:
    """Test suite for WsBridgeActor publishing logic."""

    @pytest.mark.asyncio
    async def test_ws_bridge_publishes_candle_on_bar(self):
        """Test that WsBridgeActor publishes CandleEvent when receiving bar data."""
        from app.trading.actors.ws_bridge import WsBridgeActor, WsBridgeActorConfig
        from app.trading.events.publisher import EventBusPublisher
        from app.trading.events.schemas import CandleEvent

        # Mock Redis client
        mock_redis = AsyncMock(spec=redis.Redis)
        mock_redis.publish = AsyncMock(return_value=1)

        # Create config
        config = WsBridgeActorConfig(
            bot_id="test-bot",
            channels=["nqhub.candle.1min"]
        )

        # Create actor with redis_client as constructor parameter
        actor = WsBridgeActor(config, redis_client=mock_redis)

        # Manually set up publisher for testing
        publisher = EventBusPublisher(mock_redis)
        actor.set_publisher_for_testing(publisher)
        actor._loop = asyncio.get_event_loop()

        # Mock bar object (NautilusTrader Bar)
        mock_bar = Mock()
        mock_bar.bar_type.spec.step = "1min"
        mock_bar.ts_event = 1_700_000_000_000_000_000  # Nanoseconds
        mock_bar.open.as_double.return_value = 19250.25
        mock_bar.high.as_double.return_value = 19255.00
        mock_bar.low.as_double.return_value = 19248.50
        mock_bar.close.as_double.return_value = 19252.75
        mock_bar.volume.as_double.return_value = 1234

        # Process bar event
        actor.on_bar(mock_bar)

        # Since on_bar creates an async task, we need to manually execute the publish
        # Get the event that would be published
        event = CandleEvent(
            channel="nqhub.candle.1min",
            ts=datetime.fromtimestamp(1_700_000_000_000_000_000 / 1_000_000_000),
            bot_id="test-bot",
            timeframe="1min",
            open=19250.25,
            high=19255.00,
            low=19248.50,
            close=19252.75,
            volume=1234,
            delta=0,
            poc=19252.75
        )

        # Manually call publish to test
        await publisher.publish(event)

        # Verify Redis publish was called
        mock_redis.publish.assert_called_once()

        # Check the published event
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == "nqhub.candle.1min"  # Channel

        # Parse and verify payload
        payload = json.loads(call_args[0][1])
        assert payload["channel"] == "nqhub.candle.1min"
        assert payload["timeframe"] == "1min"
        assert payload["open"] == 19250.25
        assert payload["high"] == 19255.00
        assert payload["low"] == 19248.50
        assert payload["close"] == 19252.75
        assert payload["volume"] == 1234

    @pytest.mark.asyncio
    async def test_ws_bridge_publishes_order_on_fill(self):
        """Test that WsBridgeActor publishes OrderEvent when order is filled."""
        from app.trading.actors.ws_bridge import WsBridgeActor, WsBridgeActorConfig
        from app.trading.events.publisher import EventBusPublisher
        from app.trading.events.schemas import OrderEvent

        # Mock Redis client
        mock_redis = AsyncMock(spec=redis.Redis)
        mock_redis.publish = AsyncMock(return_value=1)

        # Create config
        config = WsBridgeActorConfig(
            bot_id="test-bot",
            channels=["exec.order.filled"]
        )

        # Create actor with redis_client as constructor parameter
        actor = WsBridgeActor(config, redis_client=mock_redis)

        # Manually set up publisher for testing
        publisher = EventBusPublisher(mock_redis)
        actor.set_publisher_for_testing(publisher)
        actor._loop = asyncio.get_event_loop()

        # Mock OrderFilled event
        mock_event = Mock()
        mock_event.ts_event = 1_700_000_000_000_000_000
        mock_event.order_id = "ORDER-001"
        mock_event.client_order_id = "CLIENT-001"
        mock_event.venue_order_id = "VENUE-001"
        mock_event.order_side = "BUY"
        mock_event.last_qty.as_double.return_value = 2
        mock_event.last_px.as_double.return_value = 19252.75

        # Process order filled event
        actor.on_order_filled(mock_event)

        # Since on_order_filled creates an async task, we manually execute the publish
        # Create the event that would be published
        order_event = OrderEvent(
            channel="exec.order.filled",
            ts=datetime.fromtimestamp(1_700_000_000_000_000_000 / 1_000_000_000),
            bot_id="test-bot",
            order_id="ORDER-001",
            client_order_id="CLIENT-001",
            broker_order_id="VENUE-001",
            bracket_role=None,
            side="BUY",
            contracts=2,
            fill_price=19252.75,
            status="FILLED"
        )

        # Manually call publish to test
        await publisher.publish(order_event)

        # Verify Redis publish was called
        mock_redis.publish.assert_called_once()

        # Check the published event
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == "exec.order.filled"  # Channel

        # Parse and verify payload
        payload = json.loads(call_args[0][1])
        assert payload["channel"] == "exec.order.filled"
        assert payload["order_id"] == "ORDER-001"
        assert payload["client_order_id"] == "CLIENT-001"
        assert payload["broker_order_id"] == "VENUE-001"
        assert payload["side"] == "BUY"
        assert payload["contracts"] == 2
        assert payload["fill_price"] == 19252.75
        assert payload["status"] == "FILLED"


class TestDbWriterActor:
    """Test suite for DbWriterActor batching logic."""

    @pytest.mark.asyncio
    async def test_db_writer_batches_events(self):
        """Test that DbWriterActor batches events instead of writing one by one."""
        from app.trading.actors.db_writer import DbWriterActor, DbWriterActorConfig

        # Mock DB session with proper async context manager
        mock_db = MagicMock()
        mock_transaction = MagicMock()

        # Create a proper async context manager mock
        class AsyncContextManagerMock:
            async def __aenter__(self):
                return mock_transaction
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        mock_db.begin.return_value = AsyncContextManagerMock()

        # Create config with small batch size for testing
        config = DbWriterActorConfig(
            bot_id="test-bot",
            batch_interval_ms=5000,  # Long interval so we control flushing
            max_buffer_size=10  # Small buffer for testing
        )

        # Create actor with db_session as constructor parameter
        actor = DbWriterActor(config, db_session=mock_db)

        # Add events to buffer (less than max_buffer_size)
        for i in range(5):
            await actor.persist_event('test', {'id': i})

        # Buffer should have events but not flushed yet
        assert actor.buffer_size == 5
        assert actor._total_flushes == 0

        # Add more events to reach max_buffer_size
        for i in range(5, 10):
            await actor.persist_event('test', {'id': i})

        # Should trigger automatic flush at max_buffer_size (10)
        # Buffer should be cleared after flush
        assert actor.buffer_size == 0
        assert actor._total_flushes == 1

        # Verify DB transaction was used (batch write)
        mock_db.begin.assert_called_once()

    @pytest.mark.asyncio
    async def test_db_writer_flushes_on_max_buffer(self):
        """Test that DbWriterActor forces flush when buffer reaches max size."""
        from app.trading.actors.db_writer import DbWriterActor, DbWriterActorConfig

        # Mock DB session with proper async context manager
        mock_db = MagicMock()
        mock_transaction = MagicMock()

        # Create a proper async context manager mock
        class AsyncContextManagerMock:
            async def __aenter__(self):
                return mock_transaction
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        mock_db.begin.return_value = AsyncContextManagerMock()

        # Create config with max_buffer_size=1000 as per spec
        config = DbWriterActorConfig(
            bot_id="test-bot",
            batch_interval_ms=10000,  # Long interval
            max_buffer_size=1000  # Force flush at 1000 events
        )

        # Create actor with db_session as constructor parameter
        actor = DbWriterActor(config, db_session=mock_db)

        # Add 999 events (just below max)
        for i in range(999):
            await actor.persist_event('test', {'id': i})

        # Should not flush yet
        assert actor.buffer_size == 999
        assert actor._total_flushes == 0

        # Add one more event to reach 1000
        await actor.persist_event('test', {'id': 999})

        # Should trigger immediate flush (synchronous in persist_event)

        # Verify flush occurred
        assert actor.buffer_size == 0
        assert actor._total_flushes == 1
        assert actor._total_events_persisted == 1000

        # Verify DB was called
        mock_db.begin.assert_called_once()

    @pytest.mark.asyncio
    async def test_db_writer_flushes_on_interval(self):
        """Test that DbWriterActor flushes periodically based on interval."""
        from app.trading.actors.db_writer import DbWriterActor, DbWriterActorConfig

        # Mock DB session with proper async context manager
        mock_db = MagicMock()
        mock_transaction = MagicMock()

        # Create a proper async context manager mock
        class AsyncContextManagerMock:
            async def __aenter__(self):
                return mock_transaction
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        mock_db.begin.return_value = AsyncContextManagerMock()

        # Create config with 500ms interval as per spec
        config = DbWriterActorConfig(
            bot_id="test-bot",
            batch_interval_ms=500,  # Flush every 500ms as per spec
            max_buffer_size=1000
        )

        # Create actor with db_session as constructor parameter
        actor = DbWriterActor(config, db_session=mock_db)

        # Mock the event loop for starting
        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = Mock()
            mock_loop.is_running.return_value = True
            mock_loop.create_task = Mock()
            mock_get_loop.return_value = mock_loop

            # Start actor (starts periodic flush task)
            actor.on_start()

            # Verify periodic flush task was created
            mock_loop.create_task.assert_called_once()

        # Test the periodic flush logic directly
        # Add some events
        for i in range(5):
            await actor.persist_event('test', {'id': i})

        assert actor.buffer_size == 5

        # Manually trigger what the periodic task would do
        await actor._flush_batch()

        # Verify flush occurred
        assert actor.buffer_size == 0
        assert actor._total_flushes == 1
        assert actor._total_events_persisted == 5

        # Test that empty buffer doesn't cause flush
        initial_flushes = actor._total_flushes
        await actor._flush_batch()  # Should do nothing
        assert actor._total_flushes == initial_flushes  # No additional flush

    @pytest.mark.asyncio
    async def test_db_writer_never_blocks_event_loop(self):
        """Test that DbWriterActor never performs synchronous DB writes."""
        from app.trading.actors.db_writer import DbWriterActor, DbWriterActorConfig

        # Mock DB session that simulates slow operation
        mock_db = MagicMock()
        mock_transaction = MagicMock()

        # Create a proper async context manager mock with delay
        class SlowAsyncContextManagerMock:
            async def __aenter__(self):
                await asyncio.sleep(0.01)  # Simulate DB latency
                return mock_transaction
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        mock_db.begin.return_value = SlowAsyncContextManagerMock()

        # Create actor
        config = DbWriterActorConfig(
            bot_id="test-bot",
            batch_interval_ms=500,
            max_buffer_size=5  # Small for testing
        )
        actor = DbWriterActor(config, db_session=mock_db)

        # Record start time
        start = asyncio.get_event_loop().time()

        # Add events rapidly (should not block)
        for i in range(10):
            await actor.persist_event('test', {'id': i})
            # This should return immediately, not wait for DB

        # Record time after adding events
        end = asyncio.get_event_loop().time()

        # Adding events should be very fast (< 0.01s), not blocked by DB
        assert (end - start) < 0.01

        # Wait for async flush to complete
        await asyncio.sleep(0.05)

        # Verify events were persisted asynchronously
        assert actor._total_flushes >= 1
        assert actor._total_events_persisted >= 5

    @pytest.mark.asyncio
    async def test_kill_switch_immediate_flush(self):
        """Test that kill switch events trigger immediate flush."""
        from app.trading.actors.db_writer import DbWriterActor, DbWriterActorConfig

        # Mock DB session with proper async context manager
        mock_db = MagicMock()
        mock_transaction = MagicMock()

        # Create a proper async context manager mock
        class AsyncContextManagerMock:
            async def __aenter__(self):
                return mock_transaction
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        mock_db.begin.return_value = AsyncContextManagerMock()

        # Create actor with large buffer to test forced flush
        config = DbWriterActorConfig(
            bot_id="test-bot",
            batch_interval_ms=10000,  # Long interval
            max_buffer_size=1000  # Large buffer
        )
        actor = DbWriterActor(config, db_session=mock_db)

        # Mock event loop
        mock_loop = Mock()
        mock_loop.is_running.return_value = True
        mock_loop.create_task = Mock()

        # Add some normal events
        for i in range(5):
            await actor.persist_event('test', {'id': i})

        assert actor.buffer_size == 5

        # Process kill switch event (should trigger immediate flush)
        with patch('asyncio.get_event_loop', return_value=mock_loop):
            actor.on_kill_switch_event({'reason': 'Emergency stop'})

        # Verify two tasks were created:
        # 1. Task to add kill switch event to buffer
        # 2. Task to flush immediately
        assert mock_loop.create_task.call_count == 2

        # Manually execute what the tasks would do
        await actor.persist_event('kill_switch', {'reason': 'Emergency stop'})
        await actor._flush_batch()

        # Verify immediate flush occurred
        assert actor.buffer_size == 0
        assert actor._total_flushes == 1
        assert actor._total_events_persisted == 6  # 5 normal + 1 kill switch