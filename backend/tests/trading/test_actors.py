"""
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