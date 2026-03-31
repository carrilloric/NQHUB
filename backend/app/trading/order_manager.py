"""
NQHubOrderManager - Order Management System (AUT-350)

Full order lifecycle management from signal to fill confirmation.
All communication with Rithmic via RithmicExecutionClient (AUT-346).

CRITICAL RULES:
- NEVER retry automatically on order submission failure
- If submit fails, log and notify - trader decides next action
- When TP fills → cancel SL immediately (and vice versa)
- All 3 bracket legs created in DB BEFORE sending to Rithmic
- broker_order_id comes from Rithmic ACK (handle the gap)

Order Lifecycle States:
  PENDING_SUBMIT → SUBMITTED → ACCEPTED → FILLED
                             → REJECTED
                             → CANCELLED
                FAILED (if submit raises exception)
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import uuid4, UUID
import logging

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.production import Order

logger = logging.getLogger(__name__)


class OrderStatus(str, Enum):
    """Order status constants"""
    PENDING_SUBMIT = "PENDING_SUBMIT"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


# NQ Futures constants (hardcoded as per requirements)
NQ_TICK_SIZE = Decimal('0.25')
NQ_TICK_VALUE = Decimal('5.00')  # $5 per tick
NQ_POINT_VALUE = Decimal('20.00')  # $20 per point (4 ticks = 1 point)
NQ_COMMISSION_PER_CONTRACT = Decimal('2.40')  # Round-trip commission


class NQHubOrderManager:
    """
    Order Management System for NQ Futures trading.

    Handles full order lifecycle including:
    - Bracket order creation (entry + TP + SL)
    - Order submission to Rithmic (NO automatic retries)
    - Fill event handling
    - Rejection handling
    - P&L calculation
    - Bracket management (cancel sibling on fill)
    """

    def __init__(self, db: AsyncSession, rithmic_client):
        """
        Initialize OrderManager

        Args:
            db: Async database session
            rithmic_client: RithmicExecutionClient instance (AUT-346)
        """
        self.db = db
        self.rithmic_client = rithmic_client

    async def submit_bracket_order(
        self,
        side: str,
        entry_price: Decimal,
        tp_ticks: int,
        sl_ticks: int,
        contracts: int,
        bot_id: str
    ) -> str:
        """
        Create and submit a bracket order (entry + TP + SL).

        Creates all 3 orders in DB BEFORE submitting to Rithmic.
        If Rithmic submit fails, orders are marked FAILED with no retry.

        Args:
            side: "BUY" or "SELL"
            entry_price: Entry price (LIMIT order)
            tp_ticks: Take profit offset in ticks (from entry)
            sl_ticks: Stop loss offset in ticks (from entry)
            contracts: Number of contracts
            bot_id: Bot instance ID

        Returns:
            Entry order ID (UUID string)

        Raises:
            Exception: If Rithmic submission fails (NO RETRY)
        """
        logger.info(
            f"Creating bracket order: {side} {contracts}x @ {entry_price}, "
            f"TP={tp_ticks} ticks, SL={sl_ticks} ticks, bot={bot_id}"
        )

        try:
            # Calculate TP and SL prices
            if side == "BUY":
                tp_price = self._ticks_to_price(entry_price, tp_ticks, direction="UP")
                sl_price = self._ticks_to_price(entry_price, sl_ticks, direction="DOWN")
                exit_side = "SELL"
            else:  # SELL
                tp_price = self._ticks_to_price(entry_price, tp_ticks, direction="DOWN")
                sl_price = self._ticks_to_price(entry_price, sl_ticks, direction="UP")
                exit_side = "BUY"

            # Generate client order IDs (unique identifiers)
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            entry_client_id = f"ORD-{bot_id[:8]}-{timestamp}-ENTRY"
            tp_client_id = f"ORD-{bot_id[:8]}-{timestamp}-TP"
            sl_client_id = f"ORD-{bot_id[:8]}-{timestamp}-SL"

            # Create ENTRY order
            entry_order = Order(
                id=uuid4(),
                bot_id=UUID(bot_id),
                client_order_id=entry_client_id,
                bracket_role='ENTRY',
                parent_order_id=None,
                symbol='NQ',
                side=side,
                order_type='LIMIT',
                type='LIMIT',  # Legacy field
                contracts=contracts,
                quantity=contracts,  # Legacy field
                price=entry_price,
                status=OrderStatus.PENDING_SUBMIT,
            )
            self.db.add(entry_order)

            # Create TP order (child of entry)
            tp_order = Order(
                id=uuid4(),
                bot_id=UUID(bot_id),
                client_order_id=tp_client_id,
                bracket_role='TP',
                parent_order_id=entry_order.id,
                symbol='NQ',
                side=exit_side,
                order_type='LIMIT',
                type='LIMIT',
                contracts=contracts,
                quantity=contracts,
                price=tp_price,
                status=OrderStatus.PENDING_SUBMIT,
            )
            self.db.add(tp_order)

            # Create SL order (child of entry)
            sl_order = Order(
                id=uuid4(),
                bot_id=UUID(bot_id),
                client_order_id=sl_client_id,
                bracket_role='SL',
                parent_order_id=entry_order.id,
                symbol='NQ',
                side=exit_side,
                order_type='STOP',
                type='STOP',
                contracts=contracts,
                quantity=contracts,
                price=sl_price,
                status=OrderStatus.PENDING_SUBMIT,
            )
            self.db.add(sl_order)

            # Commit to DB BEFORE sending to Rithmic
            await self.db.commit()
            logger.info(f"Created 3 bracket orders in DB: ENTRY={entry_order.id}, TP={tp_order.id}, SL={sl_order.id}")

            # Submit ONLY entry order to Rithmic (TP/SL submitted after entry fills)
            try:
                broker_order_id = await self.rithmic_client.submit_order(
                    client_order_id=entry_client_id,
                    side=side,
                    order_type='LIMIT',
                    price=entry_price,
                    contracts=contracts
                )

                # Update entry order with broker_order_id from Rithmic ACK
                entry_order.broker_order_id = broker_order_id
                entry_order.rithmic_order_id = broker_order_id  # Legacy field
                entry_order.status = OrderStatus.SUBMITTED
                await self.db.commit()

                logger.info(f"Submitted entry order to Rithmic: {broker_order_id}")
                return str(entry_order.id)

            except Exception as submit_error:
                # CRITICAL: NO RETRY - mark as FAILED and re-raise
                logger.error(f"Rithmic submit FAILED: {submit_error} - NO RETRY")

                entry_order.status = OrderStatus.FAILED
                entry_order.rejection_reason = str(submit_error)
                tp_order.status = OrderStatus.FAILED
                tp_order.rejection_reason = "Entry order failed"
                sl_order.status = OrderStatus.FAILED
                sl_order.rejection_reason = "Entry order failed"

                await self.db.commit()

                # Re-raise exception (NO RETRY)
                raise

        except Exception as e:
            logger.error(f"Bracket order creation failed: {e}")
            raise

    async def cancel_order(self, order_id: str, bot_id: str) -> bool:
        """
        Cancel a pending order.

        Args:
            order_id: Order UUID
            bot_id: Bot instance ID (for validation)

        Returns:
            True if cancelled, False if cannot cancel (already filled/cancelled)
        """
        # Fetch order from DB
        query = select(Order).where(
            and_(
                Order.id == UUID(order_id),
                Order.bot_id == UUID(bot_id)
            )
        )
        result = await self.db.execute(query)
        order = result.scalars().first()

        if not order:
            logger.warning(f"Order {order_id} not found")
            return False

        # Check if order can be cancelled
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.FAILED]:
            logger.warning(f"Cannot cancel order {order_id} with status {order.status}")
            return False

        # Cancel via Rithmic
        if order.broker_order_id:
            try:
                await self.rithmic_client.cancel_order(order.broker_order_id)
            except Exception as e:
                logger.error(f"Rithmic cancel failed for {order_id}: {e}")
                return False

        # Update status in DB
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.utcnow()
        await self.db.commit()

        logger.info(f"Cancelled order {order_id}")
        return True

    async def on_fill(self, fill_report: dict) -> None:
        """
        Handle fill event from Rithmic.

        Actions:
        - If ENTRY fills: activate (submit) TP and SL
        - If TP fills: cancel SL immediately
        - If SL fills: cancel TP immediately
        - Calculate P&L for exit orders

        Args:
            fill_report: Dict with fill details from Rithmic
                {
                    'client_order_id': str,
                    'broker_order_id': str,
                    'fill_price': Decimal,
                    'fill_time': datetime,
                    'contracts': int
                }
        """
        client_order_id = fill_report.get('client_order_id')
        logger.info(f"Processing fill for {client_order_id}")

        # Fetch order from DB
        query = select(Order).where(Order.client_order_id == client_order_id)
        result = await self.db.execute(query)
        order = result.scalars().first()

        if not order:
            logger.error(f"Order {client_order_id} not found for fill")
            return

        # Update order with fill details
        order.status = OrderStatus.FILLED
        order.fill_price = fill_report['fill_price']
        order.fill_time = fill_report['fill_time']
        order.filled_at = fill_report['fill_time']  # Legacy field
        order.broker_order_id = fill_report.get('broker_order_id', order.broker_order_id)

        # Handle based on bracket role
        if order.bracket_role == 'ENTRY':
            # Entry filled → activate TP and SL
            await self._activate_exit_orders(order)

        elif order.bracket_role == 'TP':
            # TP filled → cancel SL
            await self._cancel_sibling_order(order, target_role='SL')
            # Calculate P&L
            await self._calculate_pnl(order, fill_report)

        elif order.bracket_role == 'SL':
            # SL filled → cancel TP
            await self._cancel_sibling_order(order, target_role='TP')
            # Calculate P&L
            await self._calculate_pnl(order, fill_report)

        await self.db.commit()
        logger.info(f"Fill processed for {client_order_id}")

    async def on_order_rejected(self, rejection: dict) -> None:
        """
        Handle order rejection from Rithmic.

        Updates order status to REJECTED and logs reason.
        NO RETRY - trader must decide next action.

        Args:
            rejection: Dict with rejection details
                {
                    'client_order_id': str,
                    'reason': str,
                    'timestamp': datetime
                }
        """
        client_order_id = rejection.get('client_order_id')
        reason = rejection.get('reason', 'Unknown rejection reason')

        logger.warning(f"Order {client_order_id} REJECTED: {reason}")

        # Fetch order from DB
        query = select(Order).where(Order.client_order_id == client_order_id)
        result = await self.db.execute(query)
        order = result.scalars().first()

        if not order:
            logger.error(f"Order {client_order_id} not found for rejection")
            return

        # Update status - NO RETRY
        order.status = OrderStatus.REJECTED
        order.rejection_reason = reason
        await self.db.commit()

        logger.info(f"Order {client_order_id} marked as REJECTED (no retry)")

    def _ticks_to_price(self, base_price: Decimal, ticks: int, direction: str) -> Decimal:
        """
        Calculate price from tick offset.

        Args:
            base_price: Starting price
            ticks: Number of ticks offset
            direction: "UP" or "DOWN"

        Returns:
            Calculated price
        """
        tick_value = ticks * NQ_TICK_SIZE

        if direction == "UP":
            return base_price + tick_value
        else:  # DOWN
            return base_price - tick_value

    async def _activate_exit_orders(self, entry_order: Order) -> None:
        """
        Activate TP and SL orders after entry fills.

        Submits TP and SL to Rithmic and updates status to SUBMITTED.
        """
        logger.info(f"Activating exit orders for entry {entry_order.id}")

        # Fetch child orders (TP and SL)
        query = select(Order).where(Order.parent_order_id == entry_order.id)
        result = await self.db.execute(query)
        exit_orders = result.scalars().all()

        for exit_order in exit_orders:
            try:
                # Submit to Rithmic
                broker_order_id = await self.rithmic_client.submit_order(
                    client_order_id=exit_order.client_order_id,
                    side=exit_order.side,
                    order_type=exit_order.order_type,
                    price=exit_order.price,
                    contracts=exit_order.contracts
                )

                # Update order
                exit_order.broker_order_id = broker_order_id
                exit_order.rithmic_order_id = broker_order_id
                exit_order.status = OrderStatus.SUBMITTED

                logger.info(f"Activated {exit_order.bracket_role} order: {broker_order_id}")

            except Exception as e:
                logger.error(f"Failed to activate {exit_order.bracket_role}: {e}")
                exit_order.status = OrderStatus.FAILED
                exit_order.rejection_reason = str(e)

    async def _cancel_sibling_order(self, order: Order, target_role: str) -> None:
        """
        Cancel sibling order when TP or SL fills.

        Args:
            order: The filled order (TP or SL)
            target_role: Role of sibling to cancel ('TP' or 'SL')
        """
        logger.info(f"Cancelling sibling {target_role} for {order.bracket_role} fill")

        # Fetch sibling order
        query = select(Order).where(
            and_(
                Order.parent_order_id == order.parent_order_id,
                Order.bracket_role == target_role
            )
        )
        result = await self.db.execute(query)
        sibling = result.scalars().first()

        if not sibling:
            logger.warning(f"No {target_role} sibling found for {order.id}")
            return

        # Cancel if not already filled/cancelled
        if sibling.status in [OrderStatus.SUBMITTED, OrderStatus.ACCEPTED]:
            try:
                await self.rithmic_client.cancel_order(sibling.broker_order_id)
                sibling.status = OrderStatus.CANCELLED
                sibling.cancelled_at = datetime.utcnow()
                logger.info(f"Cancelled {target_role} order {sibling.id}")
            except Exception as e:
                logger.error(f"Failed to cancel {target_role}: {e}")

    async def _calculate_pnl(self, exit_order: Order, fill_report: dict) -> None:
        """
        Calculate P&L for filled exit order (TP or SL).

        gross_pnl = (exit_price - entry_price) * contracts * point_value
        net_pnl = gross_pnl - commission

        Args:
            exit_order: Filled TP or SL order
            fill_report: Fill details
        """
        # Fetch entry order (parent)
        query = select(Order).where(Order.id == exit_order.parent_order_id)
        result = await self.db.execute(query)
        entry_order = result.scalars().first()

        if not entry_order or not entry_order.fill_price:
            logger.warning(f"Cannot calculate P&L - entry order not filled: {exit_order.parent_order_id}")
            return

        entry_price = entry_order.fill_price
        exit_price = exit_order.fill_price
        contracts = exit_order.contracts

        # Calculate ticks difference
        price_diff = exit_price - entry_price

        # Adjust for SHORT positions (inverse P&L)
        if entry_order.side == "SELL":
            price_diff = -price_diff

        # Convert to ticks
        ticks_diff = price_diff / NQ_TICK_SIZE

        # Calculate gross P&L
        gross_pnl = ticks_diff * NQ_TICK_VALUE * contracts

        # Calculate commission (round-trip)
        commission = NQ_COMMISSION_PER_CONTRACT * contracts

        # Calculate net P&L
        net_pnl = gross_pnl - commission

        # Update order
        exit_order.gross_pnl = gross_pnl
        exit_order.commission = commission
        exit_order.net_pnl = net_pnl

        logger.info(
            f"P&L calculated for {exit_order.bracket_role}: "
            f"gross=${gross_pnl}, commission=${commission}, net=${net_pnl}"
        )
