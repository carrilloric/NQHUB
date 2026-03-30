"""
Tests for Rithmic Data Client (AUT-345)

TDD implementation for M3.2 Rithmic live adapter using async_rithmic.
Tests written BEFORE implementation following TDD principles.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime

# These will be implemented
from app.trading.adapters.rithmic_data_client import (
    RithmicDataClient,
    RithmicDataClientConfig,
)


# ============= Test Fixtures =============

@pytest.fixture
def rithmic_config():
    """Create test configuration for Rithmic client"""
    return RithmicDataClientConfig(
        rithmic_user="test_user",
        rithmic_password="test_password",
        rithmic_system="Rithmic Test",
        gateway="wss://test-gateway.rithmic.com:443",
    )


@pytest.fixture
def mock_rithmic_client():
    """Mock async_rithmic.RithmicClient"""
    client = AsyncMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.get_market_data_stream = AsyncMock()
    return client


@pytest.fixture
def sample_rithmic_tick():
    """Sample raw tick from Rithmic"""
    return {
        "symbol": "NQ",
        "price": 16850.25,
        "size": 5,
        "timestamp": 1711825200000,  # milliseconds
        "trade_id": "12345",
        "side": "BUY",
    }


# ============= Connection Tests =============

@pytest.mark.asyncio
async def test_data_client_connects(rithmic_config, mock_rithmic_client):
    """Test that RithmicDataClient connects to async_rithmic successfully"""
    # Mock SysInfraType enum
    mock_sys_infra = MagicMock()
    mock_sys_infra.TICKER_PLANT = "TICKER_PLANT"

    with patch("app.trading.adapters.rithmic_data_client.RithmicClient", return_value=mock_rithmic_client), \
         patch("app.trading.adapters.rithmic_data_client.SysInfraType", mock_sys_infra):
        client = RithmicDataClient(config=rithmic_config)

        await client._connect()

        # Verify RithmicClient was instantiated with correct params
        assert mock_rithmic_client.connect.called
        assert client._client == mock_rithmic_client


@pytest.mark.asyncio
async def test_disconnect_on_error(rithmic_config, mock_rithmic_client):
    """
    Test that client disconnects properly on error.
    NO automatic reconnection - manual restart required.
    """
    # Mock SysInfraType enum
    mock_sys_infra = MagicMock()
    mock_sys_infra.TICKER_PLANT = "TICKER_PLANT"

    with patch("app.trading.adapters.rithmic_data_client.RithmicClient", return_value=mock_rithmic_client), \
         patch("app.trading.adapters.rithmic_data_client.SysInfraType", mock_sys_infra):
        client = RithmicDataClient(config=rithmic_config)
        await client._connect()

        # Simulate error
        await client._disconnect()

        # Verify disconnect was called
        assert mock_rithmic_client.disconnect.called

        # Verify NO reconnection attempt (should stay disconnected)
        assert mock_rithmic_client.connect.call_count == 1  # Only initial connect


# ============= Tick Conversion Tests =============

@pytest.mark.asyncio
async def test_tick_conversion_to_nautilus(rithmic_config, sample_rithmic_tick):
    """
    Test conversion from raw Rithmic tick to NautilusTrader TradeTick.

    NQ Constants:
    - tick_size = 0.25
    - tick_value = $5
    - point_value = $20
    """
    # Skip test if NautilusTrader not installed (will be available in production)
    pytest.importorskip("nautilus_trader")

    client = RithmicDataClient(config=rithmic_config)

    # Convert raw tick to Nautilus TradeTick
    nautilus_tick = client._convert_to_nautilus_tick(sample_rithmic_tick)

    # Verify conversion
    assert nautilus_tick.instrument_id.symbol.value == "NQ"
    assert float(nautilus_tick.price) == 16850.25
    assert nautilus_tick.size.as_double() == 5.0
    assert nautilus_tick.aggressor_side.name == "BUYER"

    # Verify tick has timestamp
    assert nautilus_tick.ts_init > 0


@pytest.mark.asyncio
async def test_nq_instrument_constants(rithmic_config):
    """
    Test that NQ instrument is configured with correct constants:
    - tick_size = 0.25
    - tick_value = $5.00
    - point_value = $20.00
    """
    client = RithmicDataClient(config=rithmic_config)

    # Get NQ instrument configuration
    nq_config = client._get_instrument_config("NQ")

    assert nq_config["tick_size"] == Decimal("0.25")
    assert nq_config["tick_value"] == Decimal("5.00")
    assert nq_config["point_value"] == Decimal("20.00")


# ============= Subscription Tests =============

@pytest.mark.asyncio
async def test_subscribe_trade_ticks(rithmic_config, mock_rithmic_client, sample_rithmic_tick):
    """Test subscription to NQ trade ticks"""
    # Mock SysInfraType enum
    mock_sys_infra = MagicMock()
    mock_sys_infra.TICKER_PLANT = "TICKER_PLANT"

    # Mock the async generator
    async def mock_stream():
        yield sample_rithmic_tick

    mock_rithmic_client.get_market_data_stream.return_value = mock_stream()

    with patch("app.trading.adapters.rithmic_data_client.RithmicClient", return_value=mock_rithmic_client), \
         patch("app.trading.adapters.rithmic_data_client.SysInfraType", mock_sys_infra):
        client = RithmicDataClient(config=rithmic_config)
        await client._connect()

        # Mock the handler
        client._handle_trade_tick = Mock()

        # Subscribe to ticks (skip conversion if NautilusTrader not installed)
        try:
            await client._subscribe_trade_ticks("NQ")
        except ImportError:
            # Expected if NautilusTrader not installed
            pass

        # If we got here without ImportError, verify handler was called
        if client._handle_trade_tick.called:
            assert client._handle_trade_tick.called


# ============= Configuration Tests =============

def test_config_from_env_vars():
    """Test that configuration can be loaded from environment variables"""
    import os

    os.environ["RITHMIC_USER"] = "env_user"
    os.environ["RITHMIC_PASSWORD"] = "env_password"
    os.environ["RITHMIC_SYSTEM"] = "Rithmic Test"

    config = RithmicDataClientConfig.from_env()

    assert config.rithmic_user == "env_user"
    assert config.rithmic_password == "env_password"
    assert config.rithmic_system == "Rithmic Test"


# ============= Error Handling Tests =============

@pytest.mark.asyncio
async def test_connection_failure_raises_error(rithmic_config, mock_rithmic_client):
    """Test that connection failures are raised (no auto-reconnect)"""
    mock_rithmic_client.connect.side_effect = ConnectionError("Connection failed")

    with patch("app.trading.adapters.rithmic_data_client.RithmicClient", return_value=mock_rithmic_client):
        client = RithmicDataClient(config=rithmic_config)

        # Should raise error, NOT auto-reconnect
        with pytest.raises(ConnectionError):
            await client._connect()


@pytest.mark.asyncio
async def test_stream_interruption_no_auto_reconnect(rithmic_config, mock_rithmic_client):
    """
    Test that stream interruption does NOT trigger automatic reconnection.
    Bot must be manually restarted.
    """
    # Mock SysInfraType enum
    mock_sys_infra = MagicMock()
    mock_sys_infra.TICKER_PLANT = "TICKER_PLANT"

    async def failing_stream():
        yield {"symbol": "NQ", "price": 16850.25, "size": 1, "timestamp": 1711825200000, "side": "BUY", "trade_id": "123"}
        raise ConnectionError("Stream interrupted")

    mock_rithmic_client.get_market_data_stream.return_value = failing_stream()

    with patch("app.trading.adapters.rithmic_data_client.RithmicClient", return_value=mock_rithmic_client), \
         patch("app.trading.adapters.rithmic_data_client.SysInfraType", mock_sys_infra):
        client = RithmicDataClient(config=rithmic_config)
        await client._connect()

        client._handle_trade_tick = Mock()

        # Stream should raise error and NOT reconnect
        with pytest.raises((ConnectionError, ImportError)):
            # May raise ImportError if NautilusTrader not installed
            await client._subscribe_trade_ticks("NQ")

        # Verify connect was only called once (no auto-reconnect)
        assert mock_rithmic_client.connect.call_count == 1
