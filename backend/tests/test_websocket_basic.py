"""
Basic WebSocket tests to verify implementation
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import timedelta
from fastapi import WebSocket

from app.api.websocket.connection_manager import ConnectionManager, Connection
from app.api.websocket.throttle import MessageThrottler
from app.core.security import create_access_token, verify_token


def test_imports():
    """Test that all WebSocket modules can be imported."""
    from app.api.websocket import websocket_router
    from app.api.websocket.ws_server import WebSocketHandler
    from app.api.websocket.connection_manager import manager
    from app.api.websocket.throttle import throttler

    assert websocket_router is not None
    assert WebSocketHandler is not None
    assert manager is not None
    assert throttler is not None


def test_jwt_token_creation():
    """Test JWT token creation and validation."""
    # Create a token
    token = create_access_token("test_user", expires_delta=timedelta(minutes=5))
    assert token is not None

    # Verify the token
    user_id = verify_token(token)
    assert user_id == "test_user"

    # Test invalid token
    invalid_user = verify_token("invalid.token.here")
    assert invalid_user is None


@pytest.mark.asyncio
async def test_connection_manager():
    """Test ConnectionManager basic functionality."""
    manager = ConnectionManager()

    # Create mock WebSocket
    mock_ws = AsyncMock(spec=WebSocket)
    mock_ws.send_json = AsyncMock()

    # Test connection
    session_id = await manager.connect(mock_ws, "test_user")
    assert session_id is not None
    assert manager.connection_count == 1

    # Test get connection
    connection = manager.get_connection(session_id)
    assert connection is not None
    assert connection.user_id == "test_user"
    assert connection.session_id == session_id

    # Test subscription
    channels = await manager.subscribe(session_id, ["price", "risk"])
    assert set(channels) == {"price", "risk"}
    assert "price" in connection.subscribed_channels
    assert "risk" in connection.subscribed_channels

    # Test unsubscription
    unsubscribed = await manager.unsubscribe(session_id, ["price"])
    assert unsubscribed == ["price"]
    assert "price" not in connection.subscribed_channels
    assert "risk" in connection.subscribed_channels

    # Test disconnection
    await manager.disconnect(session_id)
    assert manager.connection_count == 0
    assert manager.get_connection(session_id) is None


@pytest.mark.asyncio
async def test_throttler():
    """Test MessageThrottler basic functionality."""
    throttler = MessageThrottler()

    # Test risk channel is never throttled
    for _ in range(100):
        allowed = await throttler.should_allow_message("test_session", "risk")
        assert allowed is True

    # Test price channel throttling (10/s limit)
    allowed_count = 0
    for _ in range(20):
        if await throttler.should_allow_message("test_session", "price"):
            allowed_count += 1
    assert allowed_count == 10  # Should be limited to 10

    # Test positions channel throttling (1/s limit)
    allowed_count = 0
    for _ in range(5):
        if await throttler.should_allow_message("test_session", "positions"):
            allowed_count += 1
    assert allowed_count == 1  # Should be limited to 1

    # Test cleanup
    await throttler.cleanup_session("test_session")
    stats = await throttler.get_session_stats("test_session")
    assert len(stats) == 0


@pytest.mark.asyncio
async def test_channel_validation():
    """Test channel name validation."""
    manager = ConnectionManager()

    # Create mock WebSocket
    mock_ws = AsyncMock(spec=WebSocket)
    session_id = await manager.connect(mock_ws, "test_user")

    # Valid channels
    valid_channels = ["price", "orderflow", "patterns", "orders",
                     "positions", "portfolio", "risk", "bot"]
    subscribed = await manager.subscribe(session_id, valid_channels)
    assert len(subscribed) == len(valid_channels)

    # Invalid channels
    invalid_channels = ["invalid", "unknown", "test"]
    subscribed = await manager.subscribe(session_id, invalid_channels)
    assert len(subscribed) == 0

    # Mixed valid and invalid
    mixed_channels = ["price", "invalid", "risk"]
    subscribed = await manager.subscribe(session_id, mixed_channels)
    assert set(subscribed) == {"price", "risk"}  # Only valid ones

    await manager.disconnect(session_id)


@pytest.mark.asyncio
async def test_broadcast():
    """Test message broadcasting."""
    manager = ConnectionManager()

    # Create two mock WebSockets
    mock_ws1 = AsyncMock(spec=WebSocket)
    mock_ws1.send_json = AsyncMock()
    mock_ws2 = AsyncMock(spec=WebSocket)
    mock_ws2.send_json = AsyncMock()

    # Connect both
    session1 = await manager.connect(mock_ws1, "user1")
    session2 = await manager.connect(mock_ws2, "user2")

    # Subscribe only session1 to price
    await manager.subscribe(session1, ["price"])

    # Broadcast to price channel
    test_message = {
        "channel": "price",
        "event": "test",
        "data": {"value": 123}
    }
    await manager.broadcast_to_channel("price", test_message)

    # Only session1 should receive the broadcast
    # Check last call to send_json (skip connection established message)
    assert mock_ws1.send_json.call_count >= 2  # Connection + broadcast
    last_call = mock_ws1.send_json.call_args_list[-1]
    assert last_call[0][0] == test_message

    # Session2 should only have connection message
    assert mock_ws2.send_json.call_count == 1

    await manager.disconnect(session1)
    await manager.disconnect(session2)


@pytest.mark.asyncio
async def test_heartbeat_mechanism():
    """Test heartbeat tracking."""
    manager = ConnectionManager()

    mock_ws = AsyncMock(spec=WebSocket)
    session_id = await manager.connect(mock_ws, "test_user")
    connection = manager.get_connection(session_id)

    # Initially no heartbeat
    assert connection.last_heartbeat is None
    assert connection.heartbeat_sequence == 0
    assert not connection.is_stale  # Grace period for first heartbeat

    # Update heartbeat
    connection.update_heartbeat()
    assert connection.last_heartbeat is not None
    assert connection.heartbeat_sequence == 1
    assert not connection.is_stale

    # Update again
    connection.update_heartbeat()
    assert connection.heartbeat_sequence == 2

    await manager.disconnect(session_id)


@pytest.mark.asyncio
async def test_throttler_window_reset():
    """Test that throttling window resets after time."""
    throttler = MessageThrottler()
    session_id = "test_session"

    # Use up the price channel limit (10 messages)
    for _ in range(10):
        allowed = await throttler.should_allow_message(session_id, "price")
        assert allowed is True

    # 11th message should be throttled
    allowed = await throttler.should_allow_message(session_id, "price")
    assert allowed is False

    # Wait for window to expire
    await asyncio.sleep(1.1)

    # Should be allowed again
    allowed = await throttler.should_allow_message(session_id, "price")
    assert allowed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])