"""
Simplified tests for RithmicExecutionClient.
Focus on critical behavior: NO automatic retry on order submission.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from datetime import datetime
from decimal import Decimal


class TestRithmicExecutionClientSimple:
    """Simplified test suite for RithmicExecutionClient."""

    @pytest.fixture
    def mock_rithmic_client(self):
        """Create a mock async_rithmic RithmicClient."""
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()
        mock_client.submit_order = AsyncMock()
        mock_client.cancel_order = AsyncMock()
        mock_client.list_accounts = AsyncMock(return_value=["APEX-12345-01"])

        # Mock events
        mock_client.on_exchange_order_notification = MagicMock()
        mock_client.on_rithmic_order_notification = MagicMock()

        return mock_client

    @pytest.mark.asyncio
    async def test_import_rithmic_exec_client(self):
        """Test that RithmicExecutionClient can be imported."""
        from app.trading.adapters.rithmic_exec_client import RithmicExecutionClient, RithmicExecClientConfig

        # Verify classes exist
        assert RithmicExecutionClient is not None
        assert RithmicExecClientConfig is not None

    @pytest.mark.asyncio
    async def test_config_creation(self):
        """Test RithmicExecClientConfig creation."""
        from app.trading.adapters.rithmic_exec_client import RithmicExecClientConfig

        config = RithmicExecClientConfig(
            venue="RITHMIC",
            rithmic_user="test_user",
            rithmic_password="test_password",
            rithmic_system="Apex",
            gateway="wss://rituz00100.rithmic.com:443",
            account_id="APEX-12345-01"
        )

        assert config.rithmic_user == "test_user"
        assert config.rithmic_password == "test_password"
        assert config.rithmic_system == "Apex"
        assert config.gateway == "wss://rituz00100.rithmic.com:443"
        assert config.account_id == "APEX-12345-01"
        assert config.app_name == "NQHUB"
        assert config.app_version == "2.0"

    @pytest.mark.asyncio
    async def test_nq_constants_defined(self):
        """Test that NQ futures constants are defined."""
        from app.trading.adapters.rithmic_exec_client import RithmicExecutionClient

        assert RithmicExecutionClient.NQ_TICK_SIZE == Decimal("0.25")
        assert RithmicExecutionClient.NQ_TICK_VALUE == Decimal("5.00")
        assert RithmicExecutionClient.NQ_POINT_VALUE == Decimal("20.00")

    @pytest.mark.asyncio
    async def test_no_retry_policy(self):
        """Test that retry policy prevents automatic retries."""
        from app.trading.adapters.rithmic_exec_client import RithmicExecutionClient, RithmicExecClientConfig

        config = RithmicExecClientConfig(
            venue="RITHMIC",
            rithmic_user="test_user",
            rithmic_password="test_password",
            rithmic_system="Apex",
            gateway="wss://test.rithmic.com",
            account_id="APEX-12345-01"
        )

        # Create minimal mocks for NautilusTrader components
        mock_msgbus = Mock()
        mock_cache = Mock()
        mock_clock = Mock()

        with patch("app.trading.adapters.rithmic_exec_client.RithmicClient") as MockRithmicClient:
            MockRithmicClient.return_value = AsyncMock()

            client = RithmicExecutionClient(
                config=config,
                msgbus=mock_msgbus,
                cache=mock_cache,
                clock=mock_clock,
            )

            # Verify NO retry policy
            assert client._no_retry_policy == True
            assert client._retry_settings["submit_order"]["max_retries"] == 0
            assert client._retry_settings["cancel_order"]["max_retries"] == 1

    @pytest.mark.asyncio
    async def test_submit_order_single_attempt(self, mock_rithmic_client):
        """Test that order submission makes exactly one attempt."""
        from app.trading.adapters.rithmic_exec_client import RithmicExecutionClient, RithmicExecClientConfig

        config = RithmicExecClientConfig(
            venue="RITHMIC",
            rithmic_user="test",
            rithmic_password="test",
            rithmic_system="Apex",
            gateway="wss://test.rithmic.com",
            account_id="APEX-12345-01"
        )

        mock_msgbus = Mock()
        mock_cache = Mock()
        mock_clock = Mock()
        mock_clock.timestamp_ns = Mock(return_value=0)

        with patch("app.trading.adapters.rithmic_exec_client.RithmicClient") as MockRithmicClient:
            MockRithmicClient.return_value = mock_rithmic_client

            client = RithmicExecutionClient(
                config=config,
                msgbus=mock_msgbus,
                cache=mock_cache,
                clock=mock_clock,
            )
            client._rithmic_client = mock_rithmic_client

            # Mock a simple order object
            mock_order = Mock()
            mock_order.client_order_id.value = "ORDER-001"
            mock_order.instrument_id.symbol.value = "NQ"
            mock_order.instrument_id.venue.value = "CME"
            mock_order.side.value = "BUY"
            mock_order.quantity.as_int.return_value = 2

            # Test successful submission
            await client._submit_market_order(mock_order)

            # Assert called exactly once
            assert mock_rithmic_client.submit_order.call_count == 1

            # Reset mock
            mock_rithmic_client.submit_order.reset_mock()

            # Test failed submission
            mock_rithmic_client.submit_order.side_effect = Exception("Connection lost")

            await client._submit_market_order(mock_order)

            # Assert still called exactly once (no retry)
            assert mock_rithmic_client.submit_order.call_count == 1

    @pytest.mark.asyncio
    async def test_bracket_order_tp_sl_calculation(self, mock_rithmic_client):
        """Test bracket order TP/SL calculation for NQ futures."""
        from app.trading.adapters.rithmic_exec_client import RithmicExecutionClient, RithmicExecClientConfig

        config = RithmicExecClientConfig(
            venue="RITHMIC",
            rithmic_user="test",
            rithmic_password="test",
            rithmic_system="Apex",
            gateway="wss://test.rithmic.com",
            account_id="APEX-12345-01"
        )

        mock_msgbus = Mock()
        mock_cache = Mock()
        mock_clock = Mock()

        with patch("app.trading.adapters.rithmic_exec_client.RithmicClient") as MockRithmicClient:
            MockRithmicClient.return_value = mock_rithmic_client

            client = RithmicExecutionClient(
                config=config,
                msgbus=mock_msgbus,
                cache=mock_cache,
                clock=mock_clock,
            )
            client._rithmic_client = mock_rithmic_client

            # Test BUY bracket order
            entry_price = Decimal("15000.00")
            tp_offset = 10  # ticks
            sl_offset = 5   # ticks

            await client._submit_bracket_order(
                order_id="BRACKET-001",
                symbol="NQ",
                exchange="CME",
                quantity=1,
                is_buy=True,
                entry_price=entry_price,
                tp_offset_ticks=tp_offset,
                sl_offset_ticks=sl_offset
            )

            call_args = mock_rithmic_client.submit_order.call_args.kwargs

            # For BUY order:
            # TP = entry + (tick_size * tp_offset) = 15000 + (0.25 * 10) = 15002.50
            # SL = entry - (tick_size * sl_offset) = 15000 - (0.25 * 5) = 14998.75
            assert call_args["take_profit_price"] == 15002.50
            assert call_args["stop_loss_price"] == 14998.75

            # Reset and test SELL bracket order
            mock_rithmic_client.submit_order.reset_mock()

            await client._submit_bracket_order(
                order_id="BRACKET-002",
                symbol="NQ",
                exchange="CME",
                quantity=1,
                is_buy=False,
                entry_price=entry_price,
                tp_offset_ticks=tp_offset,
                sl_offset_ticks=sl_offset
            )

            call_args = mock_rithmic_client.submit_order.call_args.kwargs

            # For SELL order (reversed):
            # TP = entry - (tick_size * tp_offset) = 15000 - (0.25 * 10) = 14997.50
            # SL = entry + (tick_size * sl_offset) = 15000 + (0.25 * 5) = 15001.25
            assert call_args["take_profit_price"] == 14997.50
            assert call_args["stop_loss_price"] == 15001.25

    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, mock_rithmic_client):
        """Test connection and disconnection."""
        from app.trading.adapters.rithmic_exec_client import RithmicExecutionClient, RithmicExecClientConfig

        config = RithmicExecClientConfig(
            venue="RITHMIC",
            rithmic_user="test",
            rithmic_password="test",
            rithmic_system="Rithmic Test",
            gateway="wss://test.rithmic.com",
            account_id="APEX-12345-01"
        )

        mock_msgbus = Mock()
        mock_cache = Mock()
        mock_clock = Mock()

        with patch("app.trading.adapters.rithmic_exec_client.RithmicClient") as MockRithmicClient:
            MockRithmicClient.return_value = mock_rithmic_client

            client = RithmicExecutionClient(
                config=config,
                msgbus=mock_msgbus,
                cache=mock_cache,
                clock=mock_clock,
            )

            # Connect
            await client._connect()
            assert MockRithmicClient.called
            assert mock_rithmic_client.connect.called

            # Disconnect
            client._rithmic_client = mock_rithmic_client
            await client._disconnect()
            assert mock_rithmic_client.disconnect.called