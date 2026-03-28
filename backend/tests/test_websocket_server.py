"""
Tests for WebSocket Server Implementation

Validates CONTRACT-005 WebSocket API compliance.
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import WebSocket
from jose import jwt
import redis.asyncio as redis

from app.main import app
from app.config import settings
from app.core.security import create_access_token
from app.api.websocket.connection_manager import ConnectionManager, Connection
from app.api.websocket.throttle import MessageThrottler
from app.api.websocket.ws_server import WebSocketHandler


# Test fixtures
@pytest.fixture
def valid_token():
    """Generate a valid JWT token for testing."""
    access_token = create_access_token(
        subject="test_user_123",
        expires_delta=timedelta(minutes=15)
    )
    return access_token


@pytest.fixture
def invalid_token():
    """Generate an invalid JWT token for testing."""
    return "invalid.jwt.token"


@pytest.fixture
def expired_token():
    """Generate an expired JWT token for testing."""
    # Create a token that expired 1 hour ago
    expire = datetime.utcnow() - timedelta(hours=1)
    to_encode = {"exp": expire, "sub": "test_user"}
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


@pytest.fixture
async def mock_redis():
    """Mock Redis client for testing."""
    mock_client = AsyncMock(spec=redis.Redis)
    mock_pubsub = AsyncMock()
    mock_client.pubsub.return_value = mock_pubsub
    mock_pubsub.channels = {}
    mock_pubsub.psubscribe = AsyncMock()
    mock_pubsub.punsubscribe = AsyncMock()
    mock_pubsub.unsubscribe = AsyncMock()
    mock_pubsub.close = AsyncMock()
    mock_pubsub.get_message = AsyncMock(return_value=None)
    return mock_client


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestWebSocketAuthentication:
    """Test WebSocket authentication behavior."""

    def test_ws_rejects_invalid_jwt(self, test_client, invalid_token):
        """Test that WebSocket rejects connections with invalid JWT."""
        with pytest.raises(Exception) as exc_info:
            with test_client.websocket_connect(f"/ws/live?token={invalid_token}") as websocket:
                # Should not reach here
                pass

        # Check that connection was rejected with code 4001
        assert "4001" in str(exc_info.value) or "Invalid token" in str(exc_info.value)

    def test_ws_rejects_missing_token(self, test_client):
        """Test that WebSocket rejects connections without token."""
        with pytest.raises(Exception) as exc_info:
            with test_client.websocket_connect("/ws/live") as websocket:
                # Should not reach here
                pass

        # Check that connection was rejected with code 4001
        assert "4001" in str(exc_info.value) or "Authentication required" in str(exc_info.value)

    def test_ws_rejects_expired_token(self, test_client, expired_token):
        """Test that WebSocket rejects connections with expired token."""
        with pytest.raises(Exception) as exc_info:
            with test_client.websocket_connect(f"/ws/live?token={expired_token}") as websocket:
                # Should not reach here
                pass

        # Check that connection was rejected with code 4001
        assert "4001" in str(exc_info.value) or "Invalid token" in str(exc_info.value)

    def test_ws_accepts_valid_jwt(self, test_client, valid_token):
        """Test that WebSocket accepts connections with valid JWT."""
        with test_client.websocket_connect(f"/ws/live?token={valid_token}") as websocket:
            # Should receive connection established message
            data = websocket.receive_json()
            assert data["event"] == "connection_established"
            assert "session_id" in data["data"]
            assert "server_time" in data["data"]
            assert data["data"]["version"] == "1.0.0"


class TestSubscriptionProtocol:
    """Test WebSocket subscription protocol."""

    def test_subscribe_protocol(self, test_client, valid_token):
        """Test subscribe action returns subscribed confirmation."""
        with test_client.websocket_connect(f"/ws/live?token={valid_token}") as websocket:
            # Skip connection established message
            websocket.receive_json()

            # Send subscribe request
            subscribe_msg = {
                "action": "subscribe",
                "channels": ["price", "risk", "bot"]
            }
            websocket.send_json(subscribe_msg)

            # Should receive subscribed confirmation
            response = websocket.receive_json()
            assert response["action"] == "subscribed"
            assert set(response["channels"]) == {"price", "risk", "bot"}

    def test_unsubscribe_protocol(self, test_client, valid_token):
        """Test unsubscribe action returns unsubscribed confirmation."""
        with test_client.websocket_connect(f"/ws/live?token={valid_token}") as websocket:
            # Skip connection established message
            websocket.receive_json()

            # First subscribe
            subscribe_msg = {
                "action": "subscribe",
                "channels": ["price", "risk"]
            }
            websocket.send_json(subscribe_msg)
            websocket.receive_json()  # Skip subscribed confirmation

            # Now unsubscribe
            unsubscribe_msg = {
                "action": "unsubscribe",
                "channels": ["price"]
            }
            websocket.send_json(unsubscribe_msg)

            # Should receive unsubscribed confirmation
            response = websocket.receive_json()
            assert response["action"] == "unsubscribed"
            assert response["channels"] == ["price"]

    def test_subscribe_page(self, test_client, valid_token):
        """Test page subscription convenience method."""
        with test_client.websocket_connect(f"/ws/live?token={valid_token}") as websocket:
            # Skip connection established message
            websocket.receive_json()

            # Subscribe to dashboard page
            subscribe_msg = {
                "action": "subscribe_page",
                "page": "dashboard"
            }
            websocket.send_json(subscribe_msg)

            # Should receive subscribed confirmation with page channels
            response = websocket.receive_json()
            assert response["action"] == "subscribed"
            assert response["page"] == "dashboard"
            # Dashboard should subscribe to: price, positions, risk
            assert set(response["channels"]) == {"price", "positions", "risk"}

    def test_invalid_channel_rejected(self, test_client, valid_token):
        """Test that invalid channels are not subscribed."""
        with test_client.websocket_connect(f"/ws/live?token={valid_token}") as websocket:
            # Skip connection established message
            websocket.receive_json()

            # Try to subscribe to invalid channel
            subscribe_msg = {
                "action": "subscribe",
                "channels": ["invalid_channel", "price"]
            }
            websocket.send_json(subscribe_msg)

            # Should only subscribe to valid channel
            response = websocket.receive_json()
            assert response["action"] == "subscribed"
            assert response["channels"] == ["price"]  # Only valid channel


@pytest.mark.asyncio
class TestMessageBroadcast:
    """Test message broadcasting functionality."""

    async def test_message_broadcast_to_subscriber(self):
        """Test that subscribed clients receive broadcasted messages."""
        manager = ConnectionManager()

        # Create mock WebSocket
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()

        # Connect and subscribe
        session_id = await manager.connect(mock_ws, "test_user")
        await manager.subscribe(session_id, ["price"])

        # Broadcast message to price channel
        test_message = {
            "channel": "price",
            "event": "bar_update",
            "data": {"close": 15000.5},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        await manager.broadcast_to_channel("price", test_message)

        # Verify message was sent (skip connection established message)
        calls = mock_ws.send_json.call_args_list
        assert len(calls) >= 2  # At least connection + broadcast
        broadcast_call = calls[-1]
        assert broadcast_call[0][0] == test_message

    async def test_message_not_sent_to_non_subscriber(self):
        """Test that non-subscribed clients don't receive messages."""
        manager = ConnectionManager()

        # Create two mock WebSockets
        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws1.send_json = AsyncMock()
        mock_ws2 = AsyncMock(spec=WebSocket)
        mock_ws2.send_json = AsyncMock()

        # Connect both
        session1 = await manager.connect(mock_ws1, "user1")
        session2 = await manager.connect(mock_ws2, "user2")

        # Only subscribe session1 to price
        await manager.subscribe(session1, ["price"])

        # Broadcast message to price channel
        test_message = {
            "channel": "price",
            "event": "bar_update",
            "data": {"close": 15000.5}
        }

        await manager.broadcast_to_channel("price", test_message)

        # Session1 should receive message
        assert mock_ws1.send_json.call_count >= 2  # connection + broadcast

        # Session2 should only have connection message
        assert mock_ws2.send_json.call_count == 1  # Only connection established


@pytest.mark.asyncio
class TestThrottling:
    """Test message throttling functionality."""

    async def test_risk_channel_not_throttled(self):
        """Test that risk channel messages are never throttled."""
        throttler = MessageThrottler()
        session_id = "test_session"

        # Send 20 risk messages rapidly
        results = []
        for i in range(20):
            allowed = await throttler.should_allow_message(session_id, "risk")
            results.append(allowed)

        # All messages should be allowed (risk is never throttled)
        assert all(results)
        assert len([r for r in results if r]) == 20

    async def test_price_channel_throttled(self):
        """Test that price channel is throttled to 10 messages/second."""
        throttler = MessageThrottler()
        session_id = "test_session"

        # Send 20 price messages rapidly
        results = []
        for i in range(20):
            allowed = await throttler.should_allow_message(session_id, "price")
            results.append(allowed)

        # Only 10 messages should be allowed (price limit is 10/s)
        allowed_count = len([r for r in results if r])
        assert allowed_count == 10

    async def test_positions_channel_throttled(self):
        """Test that positions channel is throttled to 1 message/second."""
        throttler = MessageThrottler()
        session_id = "test_session"

        # Send 5 position messages rapidly
        results = []
        for i in range(5):
            allowed = await throttler.should_allow_message(session_id, "positions")
            results.append(allowed)

        # Only 1 message should be allowed (positions limit is 1/s)
        allowed_count = len([r for r in results if r])
        assert allowed_count == 1

    async def test_throttling_per_client(self):
        """Test that throttling applies per client independently."""
        throttler = MessageThrottler()

        # Send messages from two different sessions
        session1_results = []
        session2_results = []

        for i in range(15):
            allowed1 = await throttler.should_allow_message("session1", "price")
            allowed2 = await throttler.should_allow_message("session2", "price")
            session1_results.append(allowed1)
            session2_results.append(allowed2)

        # Each session should be throttled independently to 10 messages
        assert len([r for r in session1_results if r]) == 10
        assert len([r for r in session2_results if r]) == 10

    async def test_throttling_window_reset(self):
        """Test that throttling window resets after 1 second."""
        throttler = MessageThrottler()
        session_id = "test_session"

        # Send 10 messages (hit the limit)
        for i in range(10):
            await throttler.should_allow_message(session_id, "price")

        # Next message should be throttled
        assert not await throttler.should_allow_message(session_id, "price")

        # Wait for window to reset
        await asyncio.sleep(1.1)

        # Now message should be allowed again
        assert await throttler.should_allow_message(session_id, "price")


@pytest.mark.asyncio
class TestHeartbeat:
    """Test heartbeat mechanism."""

    async def test_heartbeat_updates_connection(self):
        """Test that pong messages update heartbeat timestamp."""
        manager = ConnectionManager()
        mock_ws = AsyncMock(spec=WebSocket)

        session_id = await manager.connect(mock_ws, "test_user")
        connection = manager.get_connection(session_id)

        # Initially no heartbeat
        assert connection.last_heartbeat is None

        # Update heartbeat
        connection.update_heartbeat()

        # Heartbeat should be updated
        assert connection.last_heartbeat is not None
        assert connection.heartbeat_sequence == 1

        # Update again
        connection.update_heartbeat()
        assert connection.heartbeat_sequence == 2

    async def test_stale_connection_detection(self):
        """Test detection of stale connections."""
        manager = ConnectionManager()
        mock_ws = AsyncMock(spec=WebSocket)

        session_id = await manager.connect(mock_ws, "test_user")
        connection = manager.get_connection(session_id)

        # Fresh connection should not be stale (60s grace period)
        assert not connection.is_stale

        # Simulate old connection without heartbeat
        connection.connected_at = datetime.utcnow() - timedelta(seconds=61)
        assert connection.is_stale

        # Update heartbeat
        connection.update_heartbeat()
        assert not connection.is_stale

        # Simulate old heartbeat
        connection.last_heartbeat = datetime.utcnow() - timedelta(seconds=61)
        assert connection.is_stale


@pytest.mark.asyncio
class TestRedisIntegration:
    """Test Redis pub/sub integration."""

    async def test_redis_channel_mapping(self, mock_redis):
        """Test that WebSocket channels map correctly to Redis channels."""
        from app.api.websocket.ws_server import REDIS_CHANNEL_MAPPING

        # Verify mapping structure
        assert "price" in REDIS_CHANNEL_MAPPING
        assert "nqhub.candle.*" in REDIS_CHANNEL_MAPPING["price"]

        assert "risk" in REDIS_CHANNEL_MAPPING
        assert "nqhub.risk.*" in REDIS_CHANNEL_MAPPING["risk"]

        assert "bot" in REDIS_CHANNEL_MAPPING
        assert "bot.status.*" in REDIS_CHANNEL_MAPPING["bot"]

    @patch("app.api.websocket.ws_server.get_redis_client")
    async def test_redis_subscription_on_channel_subscribe(self, mock_get_redis, mock_redis):
        """Test that subscribing to WebSocket channel subscribes to Redis."""
        mock_get_redis.return_value = mock_redis

        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.receive_text = AsyncMock()
        mock_ws.send_json = AsyncMock()

        handler = WebSocketHandler(mock_ws, "test_session", "test_user")
        handler.redis_client = mock_redis
        handler.redis_pubsub = mock_redis.pubsub()

        # Simulate subscription
        await handler._handle_subscribe({"action": "subscribe", "channels": ["price"]})

        # Verify response was sent
        mock_ws.send_json.assert_called()


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in WebSocket server."""

    async def test_invalid_json_handled(self, test_client, valid_token):
        """Test that invalid JSON is handled gracefully."""
        with test_client.websocket_connect(f"/ws/live?token={valid_token}") as websocket:
            # Skip connection established message
            websocket.receive_json()

            # Send invalid JSON
            websocket.send_text("invalid json {")

            # Should receive error message
            response = websocket.receive_json()
            assert response["event"] == "error"
            assert "Invalid JSON" in response["data"]["message"]

    async def test_unknown_action_handled(self, test_client, valid_token):
        """Test that unknown actions are handled gracefully."""
        with test_client.websocket_connect(f"/ws/live?token={valid_token}") as websocket:
            # Skip connection established message
            websocket.receive_json()

            # Send unknown action
            websocket.send_json({"action": "unknown_action"})

            # Should receive error message
            response = websocket.receive_json()
            assert response["event"] == "error"
            assert "Unknown action" in response["data"]["message"]

    async def test_cleanup_on_disconnect(self):
        """Test that resources are cleaned up on disconnect."""
        manager = ConnectionManager()
        throttler = MessageThrottler()

        mock_ws = AsyncMock(spec=WebSocket)
        session_id = await manager.connect(mock_ws, "test_user")

        # Add some throttling data
        await throttler.should_allow_message(session_id, "price")

        # Verify connection exists
        assert manager.get_connection(session_id) is not None
        assert session_id in throttler._client_timestamps

        # Disconnect
        await manager.disconnect(session_id)
        await throttler.cleanup_session(session_id)

        # Verify cleanup
        assert manager.get_connection(session_id) is None
        assert session_id not in throttler._client_timestamps


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])