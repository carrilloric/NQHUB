"""
<<<<<<< HEAD
Tests for NQHUB Actor components.
"""
import pytest
import redis
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from app.trading.actors.base import NQHubActor, NQHubActorConfig
from app.trading.actors.ws_bridge import WsBridgeActor, WsBridgeActorConfig
from app.trading.actors.db_writer import DbWriterActor, DbWriterActorConfig


class TestNQHubActor:
    """Test suite for NQHubActor base class."""

    def test_create_base_actor(self):
        """Test creation of base NQHubActor."""
        config = NQHubActorConfig(
            bot_id="test-bot-1",
            component_id="test-component"
        )
        actor = NQHubActor(config)

        assert actor.bot_id == "test-bot-1"
        assert actor.component_id == "test-component"

    def test_actor_default_component_id(self):
        """Test that actor generates default component_id if not provided."""
        config = NQHubActorConfig(bot_id="test-bot-2")
        actor = NQHubActor(config)

        assert actor.bot_id == "test-bot-2"
        assert actor.component_id == "test-bot-2-NQHubActor"

    def test_actor_lifecycle_methods(self):
        """Test actor lifecycle methods."""
        config = NQHubActorConfig(bot_id="test-bot-3")
        actor = NQHubActor(config)

        # These should not raise exceptions
        actor.on_start()
        actor.on_stop()


class TestWsBridgeActor:
    """Test suite for WsBridgeActor."""

    def test_create_ws_bridge_actor(self):
        """Test creation of WsBridgeActor."""
        mock_redis = Mock(spec=redis.Redis)
        config = WsBridgeActorConfig(
            bot_id="test-bot-ws",
            redis_client=mock_redis,
            channels=["test-channel"]
        )
        actor = WsBridgeActor(config)

        assert actor.bot_id == "test-bot-ws"
        assert actor.redis_client == mock_redis
        assert actor.channels == ["test-channel"]

    @pytest.mark.asyncio
    async def test_ws_bridge_publish_event(self):
        """Test publishing event to Redis."""
        mock_redis = AsyncMock(spec=redis.Redis)
        config = WsBridgeActorConfig(
            bot_id="test-bot-ws-2",
            redis_client=mock_redis,
            channels=["test-channel"]
        )
        actor = WsBridgeActor(config)

        event = {"type": "test", "data": "test-data"}
        await actor.publish_event("test-channel", event)

        mock_redis.publish.assert_called_once()


class TestDbWriterActor:
    """Test suite for DbWriterActor."""

    def test_create_db_writer_actor(self):
        """Test creation of DbWriterActor."""
        mock_session = Mock()
        config = DbWriterActorConfig(
            bot_id="test-bot-db",
            db_session=mock_session,
            batch_size=50,
            flush_interval_ms=3000
        )
        actor = DbWriterActor(config)

        assert actor.bot_id == "test-bot-db"
        assert actor.db_session == mock_session
        assert actor.batch_size == 50
        assert actor.flush_interval_ms == 3000

    @pytest.mark.asyncio
    async def test_db_writer_persist_event(self):
        """Test persisting event to batch."""
        config = DbWriterActorConfig(
            bot_id="test-bot-db-2",
            batch_size=2
        )
        actor = DbWriterActor(config)

        await actor.persist_event("test-type", {"key": "value"})
        assert len(actor._event_batch) == 1

        await actor.persist_event("test-type-2", {"key2": "value2"})
        assert len(actor._event_batch) == 2

    def test_db_writer_flush_on_stop(self):
        """Test that DbWriterActor flushes batch on stop."""
        mock_session = Mock()
        config = DbWriterActorConfig(
            bot_id="test-bot-db-3",
            db_session=mock_session
        )
        actor = DbWriterActor(config)

        # Add some events to batch
        actor._event_batch = [{"test": "event"}]

        # Stop should flush the batch
        actor.on_stop()
        # Batch should be cleared after flush
        assert len(actor._event_batch) == 0
=======
Tests for NQHub Actors: base, WsBridge, and DbWriter.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import json
from datetime import datetime


class TestNQHubActor:
    """Tests for NQHubActor base class."""

    def test_nqhub_actor_initialization(self):
        """Test NQHubActor base initialization."""
        from app.trading.actors.base import NQHubActor, NQHubActorConfig

        config = NQHubActorConfig(
            bot_id="test-bot-001"
        )

        actor = NQHubActor(config)

        assert actor.bot_id == "test-bot-001"
        assert hasattr(actor, "on_start")
        assert hasattr(actor, "on_stop")


class TestWsBridgeActor:
    """Tests for WsBridgeActor."""

    @pytest.mark.asyncio
    async def test_ws_bridge_actor_publishes_to_redis(self):
        """Test WsBridgeActor publishes MessageBus events to Redis pub/sub."""
        from app.trading.actors.ws_bridge import WsBridgeActor, WsBridgeActorConfig

        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock(return_value=1)

        config = WsBridgeActorConfig(
            bot_id="test-bot-001",
            redis_client=mock_redis,
            channels=[
                "nqhub.candle.*",
                "nqhub.pattern.*",
                "nqhub.risk.*",
                "exec.order.*",
                "exec.position.*"
            ]
        )

        with patch("app.trading.actors.ws_bridge.redis_client", mock_redis):
            actor = WsBridgeActor(config)

            # Test publishing candle event
            candle_event = {
                "type": "candle",
                "symbol": "NQ",
                "timestamp": datetime.now().isoformat(),
                "open": 15000.25,
                "high": 15005.50,
                "low": 14995.75,
                "close": 15002.00,
                "volume": 1000
            }

            await actor.publish_event("nqhub.candle.1m", candle_event)

            # Verify Redis publish was called
            mock_redis.publish.assert_called_once()
            args = mock_redis.publish.call_args[0]
            assert args[0] == "nqhub.candle.1m"
            assert json.loads(args[1]) == candle_event

    @pytest.mark.asyncio
    async def test_ws_bridge_handles_pattern_events(self):
        """Test WsBridgeActor handles pattern detection events."""
        from app.trading.actors.ws_bridge import WsBridgeActor, WsBridgeActorConfig

        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock(return_value=1)

        config = WsBridgeActorConfig(
            bot_id="test-bot-002",
            redis_client=mock_redis,
            channels=["nqhub.pattern.*"]
        )

        actor = WsBridgeActor(config)

        # Test publishing FVG pattern event
        fvg_event = {
            "type": "pattern",
            "pattern_type": "FVG",
            "symbol": "NQ",
            "timestamp": datetime.now().isoformat(),
            "gap_high": 15005.50,
            "gap_low": 15000.25,
            "significance": "MEDIUM"
        }

        await actor.publish_event("nqhub.pattern.fvg", fvg_event)

        # Verify event was published to Redis
        assert mock_redis.publish.call_count == 1

    @pytest.mark.asyncio
    async def test_ws_bridge_handles_execution_events(self):
        """Test WsBridgeActor handles order and position events."""
        from app.trading.actors.ws_bridge import WsBridgeActor, WsBridgeActorConfig

        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock(return_value=1)

        config = WsBridgeActorConfig(
            bot_id="test-bot-003",
            redis_client=mock_redis,
            channels=["exec.order.*", "exec.position.*"]
        )

        actor = WsBridgeActor(config)

        # Test publishing order event
        order_event = {
            "type": "order",
            "order_id": "ORDER-123",
            "symbol": "NQ",
            "side": "BUY",
            "quantity": 2,
            "price": 15000.50,
            "status": "FILLED"
        }

        await actor.publish_event("exec.order.filled", order_event)

        # Test publishing position event
        position_event = {
            "type": "position",
            "symbol": "NQ",
            "side": "LONG",
            "quantity": 2,
            "entry_price": 15000.50,
            "current_price": 15002.00,
            "unrealized_pnl": 60.00
        }

        await actor.publish_event("exec.position.update", position_event)

        # Verify both events were published
        assert mock_redis.publish.call_count == 2


class TestDbWriterActor:
    """Tests for DbWriterActor."""

    @pytest.mark.asyncio
    async def test_db_writer_actor_persists_events(self):
        """Test DbWriterActor persists MessageBus events to PostgreSQL."""
        from app.trading.actors.db_writer import DbWriterActor, DbWriterActorConfig

        # Mock database session
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.flush = AsyncMock()

        config = DbWriterActorConfig(
            bot_id="test-bot-001",
            db_session=mock_db,
            batch_size=10,
            flush_interval_ms=1000
        )

        actor = DbWriterActor(config)

        # Test persisting trade event
        trade_event = {
            "type": "trade",
            "symbol": "NQ",
            "side": "BUY",
            "quantity": 2,
            "price": 15000.50,
            "timestamp": datetime.now()
        }

        await actor.persist_event("trade", trade_event)

        # Verify event was added to batch
        assert len(actor._event_batch) == 1

        # Test batch processing
        for i in range(9):
            await actor.persist_event("trade", trade_event)

        # Batch should be full and flushed
        assert len(actor._event_batch) == 0
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_db_writer_batch_processing(self):
        """Test DbWriterActor batch processing for performance."""
        from app.trading.actors.db_writer import DbWriterActor, DbWriterActorConfig

        mock_db = AsyncMock()
        mock_db.add_all = MagicMock()
        mock_db.commit = AsyncMock()

        config = DbWriterActorConfig(
            bot_id="test-bot-002",
            db_session=mock_db,
            batch_size=5,
            flush_interval_ms=500
        )

        actor = DbWriterActor(config)

        # Add events below batch size
        events = []
        for i in range(3):
            event = {
                "type": "candle",
                "symbol": "NQ",
                "timestamp": datetime.now(),
                "close": 15000.00 + i
            }
            events.append(event)
            await actor.persist_event("candle", event)

        # Verify events are batched
        assert len(actor._event_batch) == 3

        # Add more events to trigger batch flush
        for i in range(2):
            event = {
                "type": "candle",
                "symbol": "NQ",
                "timestamp": datetime.now(),
                "close": 15003.00 + i
            }
            await actor.persist_event("candle", event)

        # Batch should be flushed
        assert len(actor._event_batch) == 0
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_db_writer_handles_errors(self):
        """Test DbWriterActor handles database errors gracefully."""
        from app.trading.actors.db_writer import DbWriterActor, DbWriterActorConfig

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock(side_effect=Exception("DB Error"))
        mock_db.rollback = AsyncMock()

        config = DbWriterActorConfig(
            bot_id="test-bot-003",
            db_session=mock_db,
            batch_size=5,
            flush_interval_ms=500
        )

        actor = DbWriterActor(config)

        # Add events to trigger batch
        for i in range(5):
            event = {"type": "test", "value": i}
            await actor.persist_event("test", event)

        # Verify rollback was called on error
        mock_db.rollback.assert_called()
>>>>>>> 1ee3282 (feat(AUT-336): Implement VectorBT Pro backtesting engine with Celery workers)
