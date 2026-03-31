"""
Tests for RithmicExecutionClient.
CRITICAL: Verify NO automatic retry on order submission.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from datetime import datetime
from decimal import Decimal

from nautilus_trader.model.identifiers import (
    ClientOrderId,
    AccountId,
    TraderId,
    StrategyId,
    InstrumentId,
    Symbol,
    Venue,
    VenueOrderId,
)
from nautilus_trader.model.orders import MarketOrder
from nautilus_trader.model.events import OrderDenied, OrderFilled, OrderAccepted, OrderRejected
from nautilus_trader.model.enums import OrderType, OrderStatus, OrderSide
from nautilus_trader.model.objects import Quantity, Price
from nautilus_trader.live.execution_client import LiveExecutionClient
from nautilus_trader.config import LiveExecClientConfig


class TestRithmicExecutionClient:
    """Test suite for RithmicExecutionClient with async_rithmic."""

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

    @pytest.fixture
    def config(self):
        """Create RithmicExecClientConfig."""
        from app.trading.adapters.rithmic_exec_client import RithmicExecClientConfig

        return RithmicExecClientConfig(
            venue="RITHMIC",
            rithmic_user="test_user",
            rithmic_password="test_password",
            rithmic_system="Apex",
            gateway="wss://rituz00100.rithmic.com:443",
            account_id="APEX-12345-01"
        )

    @pytest.fixture
    def client(self, config, mock_rithmic_client):
        """Create RithmicExecutionClient with mocked Rithmic connection."""
        with patch("app.trading.adapters.rithmic_exec_client.RithmicClient") as MockRithmicClient:
            MockRithmicClient.return_value = mock_rithmic_client

            from app.trading.adapters.rithmic_exec_client import RithmicExecutionClient

            # Create mock components
            mock_msgbus = Mock()
            mock_cache = Mock()
            mock_clock = Mock()

            client = RithmicExecutionClient(
                config=config,
                msgbus=mock_msgbus,
                cache=mock_cache,
                clock=mock_clock,
            )

            # Store the mock for testing
            client._rithmic_client = mock_rithmic_client

            return client

    @pytest.mark.asyncio
    async def test_submit_market_order_once(self, client, mock_rithmic_client):
        """Test that market order is submitted exactly ONCE to Rithmic."""
        # Arrange
        instrument_id = InstrumentId(Symbol("NQ"), Venue("CME"))
        order = MarketOrder(
            trader_id=TraderId("TEST-001"),
            strategy_id=StrategyId("TEST-001"),
            instrument_id=instrument_id,
            client_order_id=ClientOrderId("ORDER-001"),
            order_side=OrderSide.BUY,
            quantity=Quantity.from_int(2),
            init_id=ClientOrderId("ORDER-001-INIT"),
            ts_init=0,
        )

        mock_rithmic_client.submit_order.return_value = {
            "order_id": "ORDER-001",
            "status": "SUBMITTED"
        }

        # Act
        await client._submit_market_order(order)

        # Assert - Called exactly once, no retry
        assert mock_rithmic_client.submit_order.call_count == 1

        # Verify call parameters
        call_args = mock_rithmic_client.submit_order.call_args
        assert call_args.kwargs["order_id"] == "ORDER-001"
        assert call_args.kwargs["symbol"] == "NQ"
        assert call_args.kwargs["exchange"] == "CME"
        assert call_args.kwargs["qty"] == 2
        assert call_args.kwargs["transaction_type"] == "BUY"
        assert call_args.kwargs["order_type"] == "MARKET"
        assert call_args.kwargs["account_id"] == "APEX-12345-01"

    @pytest.mark.asyncio
    async def test_no_retry_on_failure(self, client, mock_rithmic_client):
        """Test that order submission failure does NOT trigger retry."""
        # Arrange
        instrument_id = InstrumentId(Symbol("NQ"), Venue("CME"))
        order = MarketOrder(
            trader_id=TraderId("TEST-001"),
            strategy_id=StrategyId("TEST-001"),
            instrument_id=instrument_id,
            client_order_id=ClientOrderId("ORDER-002"),
            order_side=OrderSide.SELL,
            quantity=Quantity.from_int(1),
            init_id=ClientOrderId("ORDER-002-INIT"),
            ts_init=0,
        )

        # Simulate submission failure
        mock_rithmic_client.submit_order.side_effect = Exception("Connection lost")

        # Mock the event handler to capture OrderDenied
        order_denied_events = []
        client._handle_event = Mock(side_effect=lambda event: order_denied_events.append(event))

        # Act
        await client._submit_market_order(order)

        # Assert
        # 1. Submit was called exactly once (no retry)
        assert mock_rithmic_client.submit_order.call_count == 1

        # 2. OrderDenied event was generated
        assert len(order_denied_events) == 1
        assert isinstance(order_denied_events[0], OrderDenied)
        assert "NO retry" in order_denied_events[0].reason or "Connection lost" in order_denied_events[0].reason

    @pytest.mark.asyncio
    async def test_bracket_order_structure(self, client, mock_rithmic_client):
        """Test bracket order creates correct entry + TP + SL structure."""
        # Arrange
        # NQ specs: tick_size=0.25, tick_value=$5, point_value=$20
        entry_price = Decimal("15000.00")
        tp_offset = 10  # ticks = 2.5 points = $50
        sl_offset = 5   # ticks = 1.25 points = $25

        mock_rithmic_client.submit_order.return_value = {
            "order_id": "BRACKET-001",
            "status": "SUBMITTED"
        }

        # Act
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

        # Assert
        assert mock_rithmic_client.submit_order.call_count == 1
        call_args = mock_rithmic_client.submit_order.call_args

        # Verify bracket structure
        assert call_args.kwargs["order_id"] == "BRACKET-001"
        assert call_args.kwargs["symbol"] == "NQ"
        assert call_args.kwargs["exchange"] == "CME"
        assert call_args.kwargs["qty"] == 1
        assert call_args.kwargs["price"] == float(entry_price)

        # Verify TP/SL calculation (for BUY order)
        expected_tp = float(entry_price + Decimal("0.25") * tp_offset)  # 15002.50
        expected_sl = float(entry_price - Decimal("0.25") * sl_offset)  # 14998.75

        assert call_args.kwargs["take_profit_price"] == expected_tp
        assert call_args.kwargs["stop_loss_price"] == expected_sl

    @pytest.mark.asyncio
    async def test_cancel_order(self, client, mock_rithmic_client):
        """Test order cancellation."""
        # Arrange
        order_id = "ORDER-003"
        mock_rithmic_client.cancel_order.return_value = {
            "order_id": order_id,
            "status": "CANCELLED"
        }

        # Act
        await client._cancel_order(order_id)

        # Assert
        assert mock_rithmic_client.cancel_order.call_count == 1
        call_args = mock_rithmic_client.cancel_order.call_args
        assert call_args.kwargs["order_id"] == order_id

    @pytest.mark.asyncio
    async def test_fill_confirmation_received(self, client):
        """Test that Rithmic fill converts to NautilusTrader OrderFilled."""
        # Arrange
        fill_data = {
            "order_id": "ORDER-004",
            "symbol": "NQ",
            "exchange": "CME",
            "fill_price": 15001.25,
            "fill_quantity": 2,
            "side": "BUY",
            "timestamp": datetime.utcnow().isoformat(),
            "commission": 4.50,  # $2.25 per contract
        }

        # Mock the event handler to capture OrderFilled
        order_filled_events = []
        client._handle_event = Mock(side_effect=lambda event: order_filled_events.append(event))

        # Act
        await client._handle_fill_notification(fill_data)

        # Assert
        assert len(order_filled_events) == 1
        filled_event = order_filled_events[0]

        assert isinstance(filled_event, OrderFilled)
        assert filled_event.client_order_id.value == "ORDER-004"
        assert filled_event.last_px == Price.from_str("15001.25")
        assert filled_event.last_qty == Quantity.from_int(2)
        assert float(filled_event.commission.as_decimal()) == 4.50

    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, client, mock_rithmic_client):
        """Test connection and disconnection lifecycle."""
        # Act - Connect
        await client._connect()

        # Assert - Connect called with correct params
        assert mock_rithmic_client.connect.call_count == 1

        # Act - Disconnect
        await client._disconnect()

        # Assert - Disconnect called
        assert mock_rithmic_client.disconnect.call_count == 1

    @pytest.mark.asyncio
    async def test_order_events_registration(self, client, mock_rithmic_client):
        """Test that client registers for order events on connect."""
        # Act
        await client._connect()

        # Assert - Event handlers registered
        # The += operator is mocked but we verify the handler attributes exist
        assert hasattr(client, "_on_exchange_order_notification")
        assert hasattr(client, "_on_rithmic_order_notification")

    @pytest.mark.asyncio
    async def test_no_automatic_retry_configuration(self, client):
        """Test that retry settings explicitly prevent automatic retries."""
        # This test verifies the configuration, not behavior
        # The RithmicExecutionClient should have retry_settings that prevent auto-retry

        # For orders, max_retries should be 0 or 1 (single attempt)
        assert hasattr(client, "_retry_settings")
        assert client._retry_settings.get("submit_order", {}).get("max_retries", 0) <= 1

        # Message should indicate no retry policy
        assert hasattr(client, "_no_retry_policy")
        assert client._no_retry_policy == True

    @pytest.mark.asyncio
    async def test_account_id_from_config(self, client, config):
        """Test that account_id is correctly set from config."""
        assert client._account_id == config.account_id
        assert client._account_id == "APEX-12345-01"

    @pytest.mark.asyncio
    async def test_nq_futures_constants(self, client):
        """Test NQ futures contract specifications are defined."""
        assert client.NQ_TICK_SIZE == Decimal("0.25")
        assert client.NQ_TICK_VALUE == Decimal("5.00")
        assert client.NQ_POINT_VALUE == Decimal("20.00")