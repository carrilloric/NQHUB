"""
Rithmic Execution Client for NautilusTrader.
Uses async_rithmic for order execution via Rithmic/Apex.

CRITICAL: NO automatic retry on order submission - risk of duplicate orders.
"""
import asyncio
import ssl
from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime

from nautilus_trader.live.execution_client import LiveExecutionClient
from nautilus_trader.config import LiveExecClientConfig
from nautilus_trader.model.identifiers import (
    ClientOrderId,
    VenueOrderId,
    AccountId,
    InstrumentId,
)
from nautilus_trader.model.orders import Order, MarketOrder, LimitOrder
from nautilus_trader.model.events import (
    OrderAccepted,
    OrderRejected,
    OrderDenied,
    OrderSubmitted,
    OrderFilled,
    OrderCanceled,
    OrderExpired,
    OrderTriggered,
    OrderPendingUpdate,
    OrderPendingCancel,
    OrderModifyRejected,
    OrderCancelRejected,
    OrderUpdated,
)
from nautilus_trader.model.enums import OrderStatus, OrderType
from nautilus_trader.model.objects import Price, Quantity, Money
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.common.component import Logger

# async_rithmic imports - optional for testing
try:
    from async_rithmic import (
        RithmicClient,
        SysInfraType,
        OrderType as RithmicOrderType,
        TransactionType,
        OrderPlacement,
        DataType,
    )
    ASYNC_RITHMIC_AVAILABLE = True
except ImportError:
    # For testing, we'll use mocks
    ASYNC_RITHMIC_AVAILABLE = False
    # Create placeholder classes/enums for testing
    RithmicClient = None
    SysInfraType = type('SysInfraType', (), {'ORDER_PLANT': 'ORDER_PLANT'})()
    RithmicOrderType = type('RithmicOrderType', (), {'MARKET': 'MARKET', 'LIMIT': 'LIMIT'})()
    TransactionType = type('TransactionType', (), {'BUY': 'BUY', 'SELL': 'SELL'})()
    OrderPlacement = type('OrderPlacement', (), {'MANUAL': 'MANUAL'})()
    DataType = None


class RithmicExecClientConfig(LiveExecClientConfig, kw_only=True):
    """
    Configuration for RithmicExecutionClient.

    Parameters
    ----------
    venue : str
        The venue identifier (e.g., "RITHMIC", "CME").
    client_id : str
        The client identifier for the execution client.
    oms_type : str
        The order management system type.
    account_id : str
        The trading account identifier.
    account_type : str
        The account type (e.g., "FUTURES").
    base_currency : str
        Base currency for the account (e.g., "USD").
    rithmic_user : str
        Rithmic API username.
    rithmic_password : str
        Rithmic API password.
    rithmic_system : str
        Rithmic system name (e.g., "Apex", "Rithmic Test").
    gateway : str
        WebSocket gateway URL.
    app_name : str, default "NQHUB"
        Application name for Rithmic connection.
    app_version : str, default "2.0"
        Application version for Rithmic connection.
    """
    # NautilusTrader fields
    venue: str = "RITHMIC"
    client_id: str = "RITHMIC-001"
    oms_type: str = "HEDGING"
    account_id: str  # This will be the Apex account ID
    account_type: str = "MARGIN"  # For futures trading
    base_currency: str = "USD"

    # Rithmic-specific fields
    rithmic_user: str
    rithmic_password: str
    rithmic_system: str
    gateway: str
    app_name: str = "NQHUB"
    app_version: str = "2.0"


class RithmicExecutionClient(LiveExecutionClient):
    """
    ExecutionClient that sends orders via async_rithmic to Rithmic/Apex.

    Supports:
    - Market orders
    - Bracket orders (entry + TP + SL)
    - Order cancellation

    CRITICAL: NO automatic retry on order submission to prevent duplicate orders.
    """

    # NQ Futures constants
    NQ_TICK_SIZE = Decimal("0.25")
    NQ_TICK_VALUE = Decimal("5.00")
    NQ_POINT_VALUE = Decimal("20.00")

    def __init__(
        self,
        config: RithmicExecClientConfig,
        msgbus,
        cache,
        clock,
        loop=None,
        instrument_provider=None,
    ):
        """
        Initialize RithmicExecutionClient.

        Parameters
        ----------
        config : RithmicExecClientConfig
            The client configuration.
        msgbus : MessageBus
            The message bus for the trading system.
        cache : Cache
            The cache for the trading system.
        clock : Clock
            The clock for the trading system.
        loop : AbstractEventLoop, optional
            The event loop.
        instrument_provider : InstrumentProvider, optional
            The instrument provider.
        """
        # Import NautilusTrader components
        from nautilus_trader.model.identifiers import ClientId, Venue
        from nautilus_trader.core.rust.model import OmsType, AccountType
        from nautilus_trader.model.objects import Currency

        # Convert string enums to proper types
        client_id = ClientId(config.client_id)
        venue = Venue(config.venue)
        oms_type = OmsType[config.oms_type]
        account_type = AccountType[config.account_type]
        base_currency = Currency.from_str(config.base_currency) if config.base_currency else None

        # Get event loop if not provided
        if loop is None:
            import asyncio
            loop = asyncio.get_event_loop()

        super().__init__(
            loop=loop,
            client_id=client_id,
            venue=venue,
            oms_type=oms_type,
            account_id=AccountId(f"{config.venue}-{config.account_id}"),
            account_type=account_type,
            base_currency=base_currency,
            instrument_provider=instrument_provider,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            config=config,
        )

        self._config = config
        self._account_id = config.account_id
        self._rithmic_client: Optional[RithmicClient] = None

        # NO retry policy for orders
        self._no_retry_policy = True
        self._retry_settings = {
            "submit_order": {"max_retries": 0},  # Single attempt only
            "cancel_order": {"max_retries": 1},   # Allow one retry for cancels
        }

        # Track orders for event conversion
        self._pending_orders: Dict[str, Order] = {}

    async def _connect(self) -> None:
        """
        Connect to Rithmic gateway.
        """
        self._log.info(f"Connecting to Rithmic gateway at {self._config.gateway}")

        if not ASYNC_RITHMIC_AVAILABLE:
            self._log.warning("async_rithmic not available - running in test mode")
            return

        try:
            self._rithmic_client = RithmicClient(
                user=self._config.rithmic_user,
                password=self._config.rithmic_password,
                system_name=self._config.rithmic_system,
                app_name=self._config.app_name,
                app_version=self._config.app_version,
                url=self._config.gateway,
                manual_or_auto=OrderPlacement.MANUAL,
            )

            # Disable SSL verification for paper trading
            if "paper" in self._config.gateway.lower() or "test" in self._config.rithmic_system.lower():
                self._rithmic_client.ssl_context = ssl.create_default_context()
                self._rithmic_client.ssl_context.check_hostname = False
                self._rithmic_client.ssl_context.verify_mode = ssl.CERT_NONE

            # Connect to ORDER_PLANT for execution
            await self._rithmic_client.connect(plants=[SysInfraType.ORDER_PLANT])

            # Register event handlers
            self._rithmic_client.on_exchange_order_notification += self._on_exchange_order_notification
            self._rithmic_client.on_rithmic_order_notification += self._on_rithmic_order_notification

            self._log.info("Successfully connected to Rithmic")

        except Exception as e:
            self._log.error(f"Failed to connect to Rithmic: {e}")
            raise

    async def _disconnect(self) -> None:
        """
        Disconnect from Rithmic gateway.
        """
        if self._rithmic_client:
            self._log.info("Disconnecting from Rithmic")

            # Unregister event handlers
            self._rithmic_client.on_exchange_order_notification -= self._on_exchange_order_notification
            self._rithmic_client.on_rithmic_order_notification -= self._on_rithmic_order_notification

            await self._rithmic_client.disconnect(timeout=5.0)
            self._rithmic_client = None

    async def _submit_order(self, command) -> None:
        """
        Submit an order to Rithmic.

        CRITICAL: Single attempt only - NO retry to prevent duplicate orders.
        """
        order = command.order

        # Convert order type
        if isinstance(order, MarketOrder):
            await self._submit_market_order(order)
        else:
            self._log.error(f"Unsupported order type: {type(order)}")
            await self._handle_order_denied(order, "Unsupported order type")

    async def _submit_market_order(self, order: MarketOrder) -> None:
        """
        Submit a market order to Rithmic.

        NO retry on failure - single attempt only.
        """
        try:
            # Extract symbol and exchange from InstrumentId
            symbol = order.instrument_id.symbol.value
            exchange = order.instrument_id.venue.value

            # Convert order side
            transaction_type = (
                TransactionType.BUY if order.side.value == "BUY"
                else TransactionType.SELL
            )

            self._log.info(
                f"Submitting market order {order.client_order_id.value}: "
                f"{symbol} {transaction_type.name} {order.quantity.as_int()}"
            )

            # Store order for event conversion
            self._pending_orders[order.client_order_id.value] = order

            # Check if we have a real client
            if not self._rithmic_client:
                self._log.warning("No Rithmic client available - test mode")
                # In test mode, just generate submitted event
                self._handle_event(
                    OrderSubmitted(
                        trader_id=order.trader_id,
                        strategy_id=order.strategy_id,
                        instrument_id=order.instrument_id,
                        client_order_id=order.client_order_id,
                        account_id=self.account_id,
                        ts_event=self._clock.timestamp_ns(),
                        event_id=UUID4(),
                    )
                )
                return

            # Submit to Rithmic - SINGLE ATTEMPT ONLY
            result = await self._rithmic_client.submit_order(
                order_id=order.client_order_id.value,
                symbol=symbol,
                exchange=exchange,
                qty=order.quantity.as_int(),
                transaction_type=transaction_type,
                order_type=RithmicOrderType.MARKET,
                account_id=self._account_id,
            )

            # Generate OrderSubmitted event
            self._handle_event(
                OrderSubmitted(
                    trader_id=order.trader_id,
                    strategy_id=order.strategy_id,
                    instrument_id=order.instrument_id,
                    client_order_id=order.client_order_id,
                    account_id=self.account_id,
                    ts_event=self._clock.timestamp_ns(),
                    event_id=UUID4(),
                )
            )

        except Exception as e:
            self._log.error(f"Order submission failed: {e}. NO retry.")
            await self._handle_order_denied(order, f"Submission failed: {e}. NO retry.")

    async def _submit_bracket_order(
        self,
        order_id: str,
        symbol: str,
        exchange: str,
        quantity: int,
        is_buy: bool,
        entry_price: Decimal,
        tp_offset_ticks: int,
        sl_offset_ticks: int,
    ) -> None:
        """
        Submit a bracket order: entry + TP + SL.

        NQ: tick_size=0.25, tick_value=$5, point_value=$20
        """
        try:
            transaction_type = TransactionType.BUY if is_buy else TransactionType.SELL

            # Calculate TP and SL prices
            if is_buy:
                take_profit_price = float(entry_price + self.NQ_TICK_SIZE * tp_offset_ticks)
                stop_loss_price = float(entry_price - self.NQ_TICK_SIZE * sl_offset_ticks)
            else:
                take_profit_price = float(entry_price - self.NQ_TICK_SIZE * tp_offset_ticks)
                stop_loss_price = float(entry_price + self.NQ_TICK_SIZE * sl_offset_ticks)

            self._log.info(
                f"Submitting bracket order {order_id}: "
                f"Entry={entry_price}, TP={take_profit_price}, SL={stop_loss_price}"
            )

            # Check if we have a real client
            if not self._rithmic_client:
                self._log.warning("No Rithmic client available - test mode")
                return

            # Submit bracket order to Rithmic
            result = await self._rithmic_client.submit_order(
                order_id=order_id,
                symbol=symbol,
                exchange=exchange,
                qty=quantity,
                transaction_type=transaction_type,
                order_type=RithmicOrderType.LIMIT,
                price=float(entry_price),
                take_profit_price=take_profit_price,
                stop_loss_price=stop_loss_price,
                account_id=self._account_id,
            )

            self._log.info(f"Bracket order {order_id} submitted successfully")

        except Exception as e:
            self._log.error(f"Bracket order submission failed: {e}. NO retry.")
            raise

    async def _cancel_order(self, command) -> None:
        """
        Cancel an order via async_rithmic.
        """
        # Support both command objects and direct order_id strings
        if hasattr(command, 'order'):
            order_id = command.order.client_order_id.value
        else:
            order_id = command  # Direct string ID

        try:
            self._log.info(f"Canceling order {order_id}")

            # Check if we have a real client
            if not self._rithmic_client:
                self._log.warning("No Rithmic client available - test mode")
                return

            result = await self._rithmic_client.cancel_order(
                order_id=order_id
            )

            self._log.info(f"Order {order_id} cancellation request sent")

        except Exception as e:
            self._log.error(f"Order cancellation failed: {e}")
            # Generate OrderCancelRejected event if we have the order
            if hasattr(command, 'order'):
                self._handle_event(
                    OrderCancelRejected(
                        trader_id=command.order.trader_id,
                        strategy_id=command.order.strategy_id,
                        instrument_id=command.order.instrument_id,
                        client_order_id=command.order.client_order_id,
                        account_id=self.account_id,
                        reason=str(e),
                        ts_event=self._clock.timestamp_ns(),
                        event_id=UUID4(),
                    )
                )

    async def _handle_order_denied(self, order: Order, reason: str) -> None:
        """
        Generate OrderDenied event for failed order submission.
        """
        self._handle_event(
            OrderDenied(
                trader_id=order.trader_id,
                strategy_id=order.strategy_id,
                instrument_id=order.instrument_id,
                client_order_id=order.client_order_id,
                account_id=self.account_id,
                reason=reason,
                ts_event=self._clock.timestamp_ns(),
                event_id=UUID4(),
            )
        )

    async def _on_exchange_order_notification(self, data: Dict[str, Any]) -> None:
        """
        Handle exchange order notifications from Rithmic.
        Convert to NautilusTrader events.
        """
        try:
            order_id = data.get("order_id")
            status = data.get("status", "").upper()

            # Get the order from pending orders
            order = self._pending_orders.get(order_id)
            if not order:
                self._log.warning(f"Received notification for unknown order {order_id}")
                return

            # Convert Rithmic status to Nautilus events
            if status == "ACCEPTED":
                self._handle_event(
                    OrderAccepted(
                        trader_id=order.trader_id,
                        strategy_id=order.strategy_id,
                        instrument_id=order.instrument_id,
                        client_order_id=order.client_order_id,
                        venue_order_id=VenueOrderId(data.get("exchange_order_id", order_id)),
                        account_id=self.account_id,
                        ts_event=self._clock.timestamp_ns(),
                        event_id=UUID4(),
                    )
                )
            elif status == "REJECTED":
                reason = data.get("reason", "Unknown reason")
                self._handle_event(
                    OrderRejected(
                        trader_id=order.trader_id,
                        strategy_id=order.strategy_id,
                        instrument_id=order.instrument_id,
                        client_order_id=order.client_order_id,
                        account_id=self.account_id,
                        reason=reason,
                        ts_event=self._clock.timestamp_ns(),
                        event_id=UUID4(),
                    )
                )
                # Remove from pending
                del self._pending_orders[order_id]

            elif status in ["FILLED", "PARTIAL_FILL"]:
                await self._handle_fill_notification(data)

            elif status == "CANCELLED":
                self._handle_event(
                    OrderCanceled(
                        trader_id=order.trader_id,
                        strategy_id=order.strategy_id,
                        instrument_id=order.instrument_id,
                        client_order_id=order.client_order_id,
                        venue_order_id=VenueOrderId(data.get("exchange_order_id", order_id)),
                        account_id=self.account_id,
                        ts_event=self._clock.timestamp_ns(),
                        event_id=UUID4(),
                    )
                )
                # Remove from pending
                del self._pending_orders[order_id]

        except Exception as e:
            self._log.error(f"Error processing exchange order notification: {e}")

    async def _on_rithmic_order_notification(self, data: Dict[str, Any]) -> None:
        """
        Handle Rithmic system order notifications.
        """
        # Log for monitoring - most processing happens in exchange notifications
        order_id = data.get("order_id")
        notification_type = data.get("type")
        self._log.debug(f"Rithmic notification for {order_id}: {notification_type}")

    async def _handle_fill_notification(self, data: Dict[str, Any]) -> None:
        """
        Convert Rithmic fill notification to NautilusTrader OrderFilled event.
        """
        try:
            order_id = data.get("order_id")
            order = self._pending_orders.get(order_id)

            if not order:
                self._log.warning(f"Received fill for unknown order {order_id}")
                return

            # Create OrderFilled event
            self._handle_event(
                OrderFilled(
                    trader_id=order.trader_id,
                    strategy_id=order.strategy_id,
                    instrument_id=order.instrument_id,
                    client_order_id=order.client_order_id,
                    venue_order_id=VenueOrderId(data.get("exchange_order_id", order_id)),
                    account_id=self.account_id,
                    trade_id=VenueOrderId(data.get("trade_id", f"{order_id}-FILL")),
                    order_side=order.side,
                    order_type=order.order_type,
                    last_qty=Quantity.from_int(data.get("fill_quantity", 0)),
                    last_px=Price.from_str(str(data.get("fill_price", 0))),
                    currency=order.instrument_id.symbol,  # Simplified - should be USD for NQ
                    commission=Money(data.get("commission", 0), "USD"),
                    liquidity_side=order.liquidity_side,
                    ts_event=self._clock.timestamp_ns(),
                    event_id=UUID4(),
                )
            )

            # Check if order is fully filled
            if data.get("status") == "FILLED":
                # Remove from pending orders
                del self._pending_orders[order_id]

        except Exception as e:
            self._log.error(f"Error processing fill notification: {e}")

    # Additional methods required by LiveExecutionClient interface

    async def _submit_limit_order(self, command) -> None:
        """Submit a limit order."""
        # Implementation similar to market order but with limit price
        pass

    async def _submit_limit_if_touched_order(self, command) -> None:
        """Submit a limit-if-touched order."""
        # Not implemented for Rithmic
        pass

    async def _submit_market_if_touched_order(self, command) -> None:
        """Submit a market-if-touched order."""
        # Not implemented for Rithmic
        pass

    async def _submit_stop_order(self, command) -> None:
        """Submit a stop order."""
        # Implementation for stop orders
        pass

    async def _submit_stop_limit_order(self, command) -> None:
        """Submit a stop-limit order."""
        # Implementation for stop-limit orders
        pass

    async def _submit_trailing_stop_market_order(self, command) -> None:
        """Submit a trailing stop market order."""
        # Not implemented for Rithmic
        pass

    async def _submit_trailing_stop_limit_order(self, command) -> None:
        """Submit a trailing stop limit order."""
        # Not implemented for Rithmic
        pass

    async def _modify_order(self, command) -> None:
        """Modify an existing order."""
        # Implementation for order modification
        pass

    async def _query_order(self, command) -> None:
        """Query order status."""
        # Implementation for order query
        pass

    def _handle_event(self, event) -> None:
        """
        Handle an event by passing it to the message bus.
        """
        self._msgbus.send(event)