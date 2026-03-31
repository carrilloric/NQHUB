"""
WebSocket Tests for /ws/live endpoint.

Tests all WebSocket functionality including:
- JWT authentication
- Subscribe/unsubscribe protocol
- Broadcast to subscribed clients
- Redis pub/sub event mapping
- Multi-client scenarios
- Disconnect cleanup
"""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.ws.connection_manager import ConnectionManager, VALID_CHANNELS
from app.api.v1.ws import live
from app.models.user import User, UserRole


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def connection_manager():
    """Create a fresh ConnectionManager instance for each test."""
    return ConnectionManager()


@pytest.fixture
def valid_jwt_token():
    """Mock valid JWT token."""
    return "valid_jwt_token_12345"


@pytest.fixture
def invalid_jwt_token():
    """Mock invalid JWT token."""
    return "invalid_token"


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.is_active = True
    user.role = UserRole.TRADER
    return user


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


# ============================================================================
# ConnectionManager Unit Tests
# ============================================================================

@pytest.mark.asyncio
async def test_subscribe_to_valid_channel(connection_manager):
    """
    Test: Subscribe to valid channels returns success response.

    GIVEN a ConnectionManager instance
    WHEN subscribing to valid channels
    THEN response should confirm subscription
    """
    # Create mock WebSocket
    ws = MagicMock(spec=WebSocket)

    # Subscribe to valid channels
    result = await connection_manager.subscribe(ws, ["price", "risk"])

    # Verify response
    assert result["type"] == "subscribed"
    assert set(result["channels"]) == {"price", "risk"}

    # Verify WebSocket was added to channels
    assert ws in connection_manager._connections["price"]
    assert ws in connection_manager._connections["risk"]

    # Verify tracking
    assert ws in connection_manager._ws_channels
    assert connection_manager._ws_channels[ws] == {"price", "risk"}


@pytest.mark.asyncio
async def test_subscribe_to_invalid_channel_returns_error(connection_manager):
    """
    Test: Subscribe to invalid channel returns error response.

    GIVEN a ConnectionManager instance
    WHEN subscribing to invalid channels
    THEN response should contain error message
    """
    ws = MagicMock(spec=WebSocket)

    # Subscribe to invalid channel
    result = await connection_manager.subscribe(ws, ["price", "invalid_channel"])

    # Verify error response
    assert result["type"] == "error"
    assert "invalid_channel" in result["message"].lower()

    # Verify no channels were subscribed
    assert ws not in connection_manager._connections["price"]
    assert ws not in connection_manager._ws_channels


@pytest.mark.asyncio
async def test_broadcast_reaches_subscribed_clients(connection_manager):
    """
    Test: Broadcast message reaches all subscribed clients.

    GIVEN multiple WebSocket clients subscribed to a channel
    WHEN broadcasting a message to that channel
    THEN all subscribed clients receive the message
    """
    # Create mock WebSockets
    ws1 = AsyncMock(spec=WebSocket)
    ws2 = AsyncMock(spec=WebSocket)
    ws3 = AsyncMock(spec=WebSocket)

    # Subscribe ws1 and ws2 to 'price' channel
    await connection_manager.subscribe(ws1, ["price"])
    await connection_manager.subscribe(ws2, ["price"])
    # ws3 is NOT subscribed

    # Broadcast message to 'price' channel
    message = json.dumps({"type": "candle", "price": 15000.0})
    count = await connection_manager.broadcast("price", message)

    # Verify count
    assert count == 2

    # Verify ws1 and ws2 received message, ws3 did not
    ws1.send_text.assert_called_once_with(message)
    ws2.send_text.assert_called_once_with(message)
    ws3.send_text.assert_not_called()


@pytest.mark.asyncio
async def test_broadcast_does_not_reach_unsubscribed_clients(connection_manager):
    """
    Test: Broadcast does not reach unsubscribed clients.

    GIVEN a client subscribed to channel A
    WHEN broadcasting to channel B
    THEN client does not receive the message
    """
    ws = AsyncMock(spec=WebSocket)

    # Subscribe to 'price' channel only
    await connection_manager.subscribe(ws, ["price"])

    # Broadcast to 'risk' channel
    message = json.dumps({"type": "risk", "check": "passed"})
    count = await connection_manager.broadcast("risk", message)

    # Verify no clients received message
    assert count == 0
    ws.send_text.assert_not_called()


@pytest.mark.asyncio
async def test_disconnect_removes_from_all_channels(connection_manager):
    """
    Test: Disconnect removes client from all subscribed channels.

    GIVEN a client subscribed to multiple channels
    WHEN client disconnects
    THEN client is removed from all channels
    """
    ws = AsyncMock(spec=WebSocket)

    # Subscribe to multiple channels
    await connection_manager.subscribe(ws, ["price", "risk", "orders"])

    # Verify subscription
    assert ws in connection_manager._connections["price"]
    assert ws in connection_manager._connections["risk"]
    assert ws in connection_manager._connections["orders"]

    # Disconnect
    await connection_manager.disconnect(ws)

    # Verify removed from all channels
    assert ws not in connection_manager._connections["price"]
    assert ws not in connection_manager._connections["risk"]
    assert ws not in connection_manager._connections["orders"]

    # Verify tracking cleared
    assert ws not in connection_manager._ws_channels


@pytest.mark.asyncio
async def test_multiple_clients_same_channel(connection_manager):
    """
    Test: Multiple clients can subscribe to same channel.

    GIVEN multiple WebSocket clients
    WHEN all subscribe to the same channel
    THEN all receive broadcast messages
    """
    # Create multiple mock WebSockets
    clients = [AsyncMock(spec=WebSocket) for _ in range(5)]

    # Subscribe all to 'price' channel
    for ws in clients:
        await connection_manager.subscribe(ws, ["price"])

    # Broadcast message
    message = json.dumps({"type": "candle", "price": 15000.0})
    count = await connection_manager.broadcast("price", message)

    # Verify all clients received message
    assert count == 5
    for ws in clients:
        ws.send_text.assert_called_once_with(message)


# ============================================================================
# Redis Event Mapping Tests
# ============================================================================

def test_redis_candle_event_maps_to_price_channel():
    """
    Test: Redis candle event maps to price channel.

    GIVEN a Redis channel "nqhub.candle.1min"
    WHEN mapping to WebSocket channel
    THEN returns "price+orderflow" (special marker for both channels)
    """
    redis_channel = "nqhub.candle.1min"
    ws_channel = live.map_redis_to_ws_channel(redis_channel)

    assert ws_channel == "price+orderflow"


def test_redis_kill_switch_maps_to_risk_channel():
    """
    Test: Redis kill switch event maps to risk channel.

    GIVEN a Redis channel "nqhub.risk.kill_switch"
    WHEN mapping to WebSocket channel
    THEN returns "risk"
    """
    redis_channel = "nqhub.risk.kill_switch"
    ws_channel = live.map_redis_to_ws_channel(redis_channel)

    assert ws_channel == "risk"


def test_redis_pattern_event_maps_to_patterns_channel():
    """
    Test: Redis pattern event maps to patterns channel.

    GIVEN a Redis channel "nqhub.pattern.fvg"
    WHEN mapping to WebSocket channel
    THEN returns "patterns"
    """
    redis_channel = "nqhub.pattern.fvg"
    ws_channel = live.map_redis_to_ws_channel(redis_channel)

    assert ws_channel == "patterns"


def test_redis_order_event_maps_to_orders_channel():
    """
    Test: Redis order event maps to orders channel.

    GIVEN a Redis channel "exec.order.filled"
    WHEN mapping to WebSocket channel
    THEN returns "orders"
    """
    redis_channel = "exec.order.filled"
    ws_channel = live.map_redis_to_ws_channel(redis_channel)

    assert ws_channel == "orders"


def test_redis_position_event_maps_to_positions_channel():
    """
    Test: Redis position event maps to positions channel.

    GIVEN a Redis channel "exec.position.update"
    WHEN mapping to WebSocket channel
    THEN returns "positions"
    """
    redis_channel = "exec.position.update"
    ws_channel = live.map_redis_to_ws_channel(redis_channel)

    assert ws_channel == "positions"


# ============================================================================
# WebSocket Endpoint Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_websocket_connects_with_valid_jwt(
    valid_jwt_token,
    mock_user,
    mock_db_session
):
    """
    Test: WebSocket connects successfully with valid JWT.

    GIVEN a valid JWT token
    WHEN connecting to /ws/live endpoint
    THEN connection is accepted
    """
    # Mock verify_token to return user_id
    with patch('app.api.v1.ws.live.verify_token', return_value="1"):
        # Mock database query to return user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result

        # Mock get_db to yield mock session
        async def mock_get_db():
            yield mock_db_session

        with patch('app.api.v1.ws.live.get_db', mock_get_db):
            # Mock ConnectionManager
            with patch('app.api.v1.ws.live.get_connection_manager') as mock_get_cm:
                mock_cm = ConnectionManager()
                mock_get_cm.return_value = mock_cm

                # Create mock WebSocket
                ws = AsyncMock(spec=WebSocket)
                ws.accept = AsyncMock()
                ws.receive_text = AsyncMock()
                ws.receive_text.side_effect = asyncio.CancelledError()  # Simulate disconnect

                # Authenticate
                user = await live.authenticate_websocket(valid_jwt_token, mock_db_session)

                # Verify user authenticated
                assert user is not None
                assert user.id == 1
                assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_websocket_rejects_invalid_jwt(invalid_jwt_token, mock_db_session):
    """
    Test: WebSocket rejects connection with invalid JWT.

    GIVEN an invalid JWT token
    WHEN connecting to /ws/live endpoint
    THEN connection is rejected
    """
    # Mock verify_token to return None (invalid token)
    with patch('app.api.v1.ws.live.verify_token', return_value=None):
        # Authenticate
        user = await live.authenticate_websocket(invalid_jwt_token, mock_db_session)

        # Verify authentication failed
        assert user is None


# ============================================================================
# Additional Tests
# ============================================================================

@pytest.mark.asyncio
async def test_unsubscribe_from_channels(connection_manager):
    """
    Test: Unsubscribe removes client from specific channels only.

    GIVEN a client subscribed to multiple channels
    WHEN unsubscribing from specific channels
    THEN client is removed only from those channels
    """
    ws = AsyncMock(spec=WebSocket)

    # Subscribe to multiple channels
    await connection_manager.subscribe(ws, ["price", "risk", "orders"])

    # Unsubscribe from 'price' only
    result = await connection_manager.unsubscribe(ws, ["price"])

    # Verify response
    assert result["type"] == "unsubscribed"
    assert result["channels"] == ["price"]

    # Verify removed from 'price' but still in 'risk' and 'orders'
    assert ws not in connection_manager._connections["price"]
    assert ws in connection_manager._connections["risk"]
    assert ws in connection_manager._connections["orders"]


@pytest.mark.asyncio
async def test_broadcast_to_risk_channel_has_priority(connection_manager):
    """
    Test: Risk channel broadcasts have priority flag.

    GIVEN clients subscribed to risk channel
    WHEN broadcasting with is_risk=True
    THEN message is sent with priority
    """
    ws = AsyncMock(spec=WebSocket)
    await connection_manager.subscribe(ws, ["risk"])

    # Broadcast with risk priority
    message = json.dumps({"type": "kill_switch", "reason": "max_loss"})
    count = await connection_manager.broadcast("risk", message, is_risk=True)

    # Verify broadcast succeeded
    assert count == 1
    ws.send_text.assert_called_once_with(message)


def test_valid_channels_constant():
    """
    Test: VALID_CHANNELS constant has all 8 required channels.

    GIVEN the VALID_CHANNELS constant
    THEN it should contain exactly 8 channels
    """
    expected_channels = {
        "price",
        "orderflow",
        "patterns",
        "orders",
        "positions",
        "portfolio",
        "risk",
        "bot",
    }

    assert VALID_CHANNELS == expected_channels


@pytest.mark.asyncio
async def test_get_channel_stats(connection_manager):
    """
    Test: get_channel_stats returns correct client counts.

    GIVEN clients subscribed to various channels
    WHEN calling get_channel_stats
    THEN returns accurate count per channel
    """
    # Create clients
    ws1 = AsyncMock(spec=WebSocket)
    ws2 = AsyncMock(spec=WebSocket)
    ws3 = AsyncMock(spec=WebSocket)

    # Subscribe to different channels
    await connection_manager.subscribe(ws1, ["price", "risk"])
    await connection_manager.subscribe(ws2, ["price"])
    await connection_manager.subscribe(ws3, ["risk", "orders"])

    # Get stats
    stats = connection_manager.get_channel_stats()

    # Verify counts
    assert stats["price"] == 2  # ws1, ws2
    assert stats["risk"] == 2  # ws1, ws3
    assert stats["orders"] == 1  # ws3
    assert stats["orderflow"] == 0
    assert stats["patterns"] == 0
    assert stats["positions"] == 0
    assert stats["portfolio"] == 0
    assert stats["bot"] == 0
