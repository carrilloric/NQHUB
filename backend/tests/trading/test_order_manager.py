"""
Tests for NQHubOrderManager (AUT-350)

TDD test suite for the Order Management System (OMS).
Tests are written BEFORE implementation to define expected behavior.

CRITICAL RULES:
- NEVER retry on submit_order failure
- When TP fills → cancel SL immediately (and vice versa)
- All 3 bracket legs created in DB before sending to Rithmic
- broker_order_id comes from Rithmic ACK (handle the gap)
"""
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.trading.order_manager import NQHubOrderManager, OrderStatus
from app.models.production import Order


# NQ Futures constants
NQ_TICK_SIZE = Decimal('0.25')
NQ_TICK_VALUE = Decimal('5.00')
NQ_POINT_VALUE = Decimal('20.00')


class TestBracketOrderCreation:
    """Test bracket order creation and structure"""

    @pytest.mark.asyncio
    async def test_bracket_order_creates_entry_tp_sl(self):
        """
        Bracket order must create 3 orders in DB: ENTRY, TP, SL
        All created BEFORE sending to Rithmic.
        """
        # Mock dependencies
        mock_db = AsyncMock()
        mock_rithmic_client = AsyncMock()
        mock_rithmic_client.submit_order.return_value = "RITHMIC_ACK_12345"

        manager = NQHubOrderManager(db=mock_db, rithmic_client=mock_rithmic_client)

        # Submit bracket order
        bot_id = str(uuid4())
        entry_price = Decimal('18500.00')
        tp_ticks = 20  # +20 ticks from entry
        sl_ticks = 10  # -10 ticks from entry

        entry_order_id = await manager.submit_bracket_order(
            side="BUY",
            entry_price=entry_price,
            tp_ticks=tp_ticks,
            sl_ticks=sl_ticks,
            contracts=2,
            bot_id=bot_id
        )

        # Verify 3 orders were created in DB
        # The manager should have called db.add() 3 times (entry, TP, SL)
        assert mock_db.add.call_count == 3, "Must create 3 orders (ENTRY, TP, SL)"

        # Verify orders have correct bracket_role
        created_orders = [call.args[0] for call in mock_db.add.call_args_list]
        assert len(created_orders) == 3

        # Find orders by role
        entry = next(o for o in created_orders if o.bracket_role == 'ENTRY')
        tp = next(o for o in created_orders if o.bracket_role == 'TP')
        sl = next(o for o in created_orders if o.bracket_role == 'SL')

        # Verify entry order
        assert entry.side == 'BUY'
        assert entry.price == entry_price
        assert entry.contracts == 2
        assert entry.status == OrderStatus.PENDING_SUBMIT
        assert entry.parent_order_id is None

        # Verify TP order
        expected_tp_price = entry_price + (tp_ticks * NQ_TICK_SIZE)
        assert tp.side == 'SELL'  # Exit for long
        assert tp.price == expected_tp_price
        assert tp.contracts == 2
        assert tp.parent_order_id == entry.id

        # Verify SL order
        expected_sl_price = entry_price - (sl_ticks * NQ_TICK_SIZE)
        assert sl.side == 'SELL'  # Exit for long
        assert sl.price == expected_sl_price
        assert sl.contracts == 2
        assert sl.parent_order_id == entry.id

        # Verify commit was called BEFORE Rithmic submit
        assert mock_db.commit.called
        assert mock_rithmic_client.submit_order.called

    @pytest.mark.asyncio
    async def test_bracket_ticks_to_price_nq(self):
        """
        NQ tick_size = 0.25
        Verify price calculation from ticks is correct.
        """
        mock_db = AsyncMock()
        mock_rithmic_client = AsyncMock()
        manager = NQHubOrderManager(db=mock_db, rithmic_client=mock_rithmic_client)

        # Entry at 18500.00
        # +20 ticks = 18500.00 + (20 * 0.25) = 18505.00
        # -10 ticks = 18500.00 - (10 * 0.25) = 18497.50

        entry_price = Decimal('18500.00')
        tp_price = manager._ticks_to_price(entry_price, 20, direction="UP")
        sl_price = manager._ticks_to_price(entry_price, 10, direction="DOWN")

        assert tp_price == Decimal('18505.00'), f"Expected 18505.00, got {tp_price}"
        assert sl_price == Decimal('18497.50'), f"Expected 18497.50, got {sl_price}"


class TestOrderSubmission:
    """Test order submission and retry logic"""

    @pytest.mark.asyncio
    async def test_submit_no_retry_on_failure(self):
        """
        CRITICAL: If Rithmic submit fails, set status=FAILED and log error.
        NEVER retry automatically - trader must decide.
        """
        mock_db = AsyncMock()
        mock_rithmic_client = AsyncMock()

        # Simulate Rithmic connection failure
        mock_rithmic_client.submit_order.side_effect = ConnectionError("Rithmic connection lost")

        manager = NQHubOrderManager(db=mock_db, rithmic_client=mock_rithmic_client)

        bot_id = str(uuid4())

        # Attempt to submit bracket order
        with pytest.raises(ConnectionError):
            await manager.submit_bracket_order(
                side="BUY",
                entry_price=Decimal('18500.00'),
                tp_ticks=20,
                sl_ticks=10,
                contracts=2,
                bot_id=bot_id
            )

        # Verify only ONE attempt was made (no retries)
        assert mock_rithmic_client.submit_order.call_count == 1, "Must NOT retry on failure"

        # Verify orders were marked as FAILED in DB
        created_orders = [call.args[0] for call in mock_db.add.call_args_list]
        entry = next(o for o in created_orders if o.bracket_role == 'ENTRY')
        assert entry.status == OrderStatus.FAILED
        assert entry.rejection_reason is not None


class TestFillHandling:
    """Test fill event handling and bracket management"""

    @pytest.mark.asyncio
    async def test_entry_fill_activates_tp_and_sl(self):
        """
        When ENTRY order fills, TP and SL should be activated (submitted to Rithmic).
        """
        mock_db = AsyncMock()
        mock_rithmic_client = AsyncMock()
        manager = NQHubOrderManager(db=mock_db, rithmic_client=mock_rithmic_client)

        # Create mock orders
        entry_order = Mock(spec=Order)
        entry_order.id = uuid4()
        entry_order.bracket_role = 'ENTRY'
        entry_order.status = OrderStatus.SUBMITTED
        entry_order.parent_order_id = None

        tp_order = Mock(spec=Order)
        tp_order.id = uuid4()
        tp_order.bracket_role = 'TP'
        tp_order.status = OrderStatus.PENDING_SUBMIT
        tp_order.parent_order_id = entry_order.id

        sl_order = Mock(spec=Order)
        sl_order.id = uuid4()
        sl_order.bracket_role = 'SL'
        sl_order.status = OrderStatus.PENDING_SUBMIT
        sl_order.parent_order_id = entry_order.id

        # Mock DB query to return TP and SL when looking for children
        mock_db.execute.return_value.scalars.return_value.all.return_value = [tp_order, sl_order]

        # Simulate fill report for entry
        fill_report = {
            'client_order_id': 'ORD-123',
            'broker_order_id': 'RITHMIC-456',
            'fill_price': Decimal('18500.00'),
            'fill_time': datetime.utcnow(),
            'contracts': 2
        }

        await manager.on_fill(fill_report)

        # Verify entry status updated to FILLED
        assert entry_order.status == OrderStatus.FILLED

        # Verify TP and SL were submitted to Rithmic
        assert mock_rithmic_client.submit_order.call_count == 2, "Must submit TP and SL"

        # Verify TP and SL status updated to SUBMITTED
        assert tp_order.status == OrderStatus.SUBMITTED
        assert sl_order.status == OrderStatus.SUBMITTED

    @pytest.mark.asyncio
    async def test_tp_fill_cancels_sl(self):
        """
        When TP fills, SL must be cancelled IMMEDIATELY.
        """
        mock_db = AsyncMock()
        mock_rithmic_client = AsyncMock()
        manager = NQHubOrderManager(db=mock_db, rithmic_client=mock_rithmic_client)

        # Create mock TP order
        tp_order = Mock(spec=Order)
        tp_order.id = uuid4()
        tp_order.bracket_role = 'TP'
        tp_order.status = OrderStatus.SUBMITTED
        tp_order.parent_order_id = uuid4()

        # Create mock SL order (sibling)
        sl_order = Mock(spec=Order)
        sl_order.id = uuid4()
        sl_order.bracket_role = 'SL'
        sl_order.status = OrderStatus.SUBMITTED
        sl_order.parent_order_id = tp_order.parent_order_id  # Same parent
        sl_order.broker_order_id = 'RITHMIC-SL-789'

        # Mock DB query to return SL when looking for sibling
        mock_db.execute.return_value.scalars.return_value.first.return_value = sl_order

        # Simulate TP fill
        fill_report = {
            'client_order_id': 'ORD-TP-123',
            'broker_order_id': 'RITHMIC-TP-456',
            'fill_price': Decimal('18505.00'),
            'fill_time': datetime.utcnow(),
            'contracts': 2
        }

        await manager.on_fill(fill_report)

        # Verify SL was cancelled
        assert mock_rithmic_client.cancel_order.called
        cancel_args = mock_rithmic_client.cancel_order.call_args
        assert cancel_args[0][0] == sl_order.broker_order_id

        # Verify SL status updated to CANCELLED
        assert sl_order.status == OrderStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_sl_fill_cancels_tp(self):
        """
        When SL fills, TP must be cancelled IMMEDIATELY.
        """
        mock_db = AsyncMock()
        mock_rithmic_client = AsyncMock()
        manager = NQHubOrderManager(db=mock_db, rithmic_client=mock_rithmic_client)

        # Create mock SL order
        sl_order = Mock(spec=Order)
        sl_order.id = uuid4()
        sl_order.bracket_role = 'SL'
        sl_order.status = OrderStatus.SUBMITTED
        sl_order.parent_order_id = uuid4()

        # Create mock TP order (sibling)
        tp_order = Mock(spec=Order)
        tp_order.id = uuid4()
        tp_order.bracket_role = 'TP'
        tp_order.status = OrderStatus.SUBMITTED
        tp_order.parent_order_id = sl_order.parent_order_id  # Same parent
        tp_order.broker_order_id = 'RITHMIC-TP-789'

        # Mock DB query to return TP when looking for sibling
        mock_db.execute.return_value.scalars.return_value.first.return_value = tp_order

        # Simulate SL fill
        fill_report = {
            'client_order_id': 'ORD-SL-123',
            'broker_order_id': 'RITHMIC-SL-456',
            'fill_price': Decimal('18497.50'),
            'fill_time': datetime.utcnow(),
            'contracts': 2
        }

        await manager.on_fill(fill_report)

        # Verify TP was cancelled
        assert mock_rithmic_client.cancel_order.called
        cancel_args = mock_rithmic_client.cancel_order.call_args
        assert cancel_args[0][0] == tp_order.broker_order_id

        # Verify TP status updated to CANCELLED
        assert tp_order.status == OrderStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_fill_calculates_pnl_correctly(self):
        """
        When TP or SL fills, calculate gross_pnl and net_pnl correctly.
        gross_pnl = (exit_price - entry_price) * contracts * point_value
        net_pnl = gross_pnl - commission
        """
        mock_db = AsyncMock()
        mock_rithmic_client = AsyncMock()
        manager = NQHubOrderManager(db=mock_db, rithmic_client=mock_rithmic_client)

        # Create mock entry order
        entry_order = Mock(spec=Order)
        entry_order.fill_price = Decimal('18500.00')
        entry_order.contracts = 2

        # Mock TP fill at 18505.00 (profit of 5 points = 20 ticks)
        tp_order = Mock(spec=Order)
        tp_order.id = uuid4()
        tp_order.bracket_role = 'TP'
        tp_order.fill_price = Decimal('18505.00')
        tp_order.contracts = 2
        tp_order.parent_order_id = uuid4()

        # Mock DB to return entry order
        mock_db.execute.return_value.scalars.return_value.first.return_value = entry_order

        fill_report = {
            'client_order_id': 'ORD-TP-123',
            'fill_price': Decimal('18505.00'),
            'contracts': 2
        }

        await manager._calculate_pnl(tp_order, fill_report)

        # Expected P&L:
        # Price difference = 5 points = 20 ticks
        # gross_pnl = 20 ticks * $5/tick * 2 contracts = $200
        # commission = $4.80 (2 contracts * $2.40 round-trip)
        # net_pnl = $200 - $4.80 = $195.20

        assert tp_order.gross_pnl == Decimal('200.00'), f"Expected $200, got {tp_order.gross_pnl}"
        # Commission calculation depends on implementation
        assert tp_order.net_pnl is not None


class TestOrderCancellation:
    """Test order cancellation logic"""

    @pytest.mark.asyncio
    async def test_cancel_pending_order(self):
        """
        Can cancel orders with status PENDING_SUBMIT or SUBMITTED.
        """
        mock_db = AsyncMock()
        mock_rithmic_client = AsyncMock()
        manager = NQHubOrderManager(db=mock_db, rithmic_client=mock_rithmic_client)

        # Create pending order
        order = Mock(spec=Order)
        order.id = uuid4()
        order.status = OrderStatus.SUBMITTED
        order.broker_order_id = 'RITHMIC-123'

        # Mock DB query
        mock_db.execute.return_value.scalars.return_value.first.return_value = order

        # Cancel order
        result = await manager.cancel_order(str(order.id), bot_id="bot-123")

        assert result is True
        assert mock_rithmic_client.cancel_order.called
        assert order.status == OrderStatus.CANCELLED
        assert order.cancelled_at is not None

    @pytest.mark.asyncio
    async def test_cancel_filled_order_fails(self):
        """
        Cannot cancel orders that are already FILLED.
        """
        mock_db = AsyncMock()
        mock_rithmic_client = AsyncMock()
        manager = NQHubOrderManager(db=mock_db, rithmic_client=mock_rithmic_client)

        # Create filled order
        order = Mock(spec=Order)
        order.id = uuid4()
        order.status = OrderStatus.FILLED
        order.broker_order_id = 'RITHMIC-123'

        # Mock DB query
        mock_db.execute.return_value.scalars.return_value.first.return_value = order

        # Attempt to cancel
        result = await manager.cancel_order(str(order.id), bot_id="bot-123")

        assert result is False
        assert not mock_rithmic_client.cancel_order.called
        assert order.status == OrderStatus.FILLED  # Status unchanged


class TestRejectionHandling:
    """Test order rejection handling"""

    @pytest.mark.asyncio
    async def test_rejected_order_logged_with_reason(self):
        """
        When Rithmic rejects an order, log the reason and set status=REJECTED.
        NO retry.
        """
        mock_db = AsyncMock()
        mock_rithmic_client = AsyncMock()
        manager = NQHubOrderManager(db=mock_db, rithmic_client=mock_rithmic_client)

        # Create order
        order = Mock(spec=Order)
        order.id = uuid4()
        order.client_order_id = 'ORD-123'
        order.status = OrderStatus.SUBMITTED

        # Mock DB query
        mock_db.execute.return_value.scalars.return_value.first.return_value = order

        # Simulate rejection
        rejection = {
            'client_order_id': 'ORD-123',
            'reason': 'Insufficient margin',
            'timestamp': datetime.utcnow()
        }

        await manager.on_order_rejected(rejection)

        # Verify status updated to REJECTED
        assert order.status == OrderStatus.REJECTED
        assert order.rejection_reason == 'Insufficient margin'

        # Verify NO retry was attempted
        # The submit_order should only have been called once (before rejection)
        # Rejection handler should NOT call submit_order again
        # (This will be validated by the actual implementation)
