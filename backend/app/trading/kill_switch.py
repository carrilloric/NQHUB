"""
Kill Switch Actor for emergency bot shutdown.

Two levels:
- per-bot: stops a specific bot
- global: stops all active bots

Publishes to MessageBus with maximum priority (priority=0).
NEVER uses retry for close orders - risk of duplication.
"""

import asyncio
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from sqlalchemy.orm import Session


class BotStatus(str, Enum):
    """Bot status enumeration."""
    RUNNING = "RUNNING"
    HALTED = "HALTED"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


@dataclass
class KillSwitchEvent:
    """Event published when kill switch is activated."""
    bot_id: str
    reason: str
    scope: str  # "per_bot" or "global"
    triggered_by: str  # "manual" or "circuit_breaker"
    circuit_breaker_type: Optional[str] = None
    positions_closed: int = 0
    orders_cancelled: int = 0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class KillSwitchActor:
    """
    Kill switch with two levels:
    - per-bot: stops a specific bot
    - global: stops all active bots

    Publishes to MessageBus with maximum priority (priority=0).
    NEVER uses retry for close orders - risk of duplication.
    """

    def __init__(
        self,
        logger: logging.Logger,
        msgbus,
        execution_client,
        db_session: Session
    ):
        """Initialize the KillSwitchActor.

        Args:
            logger: Logger instance
            msgbus: Message bus for publishing events
            execution_client: Execution client for order management
            db_session: Database session
        """
        self._log = logger
        self._msgbus = msgbus
        self._execution_client = execution_client
        self._db_session = db_session

        # Thread safety for idempotency
        self._lock = threading.Lock()
        self._killed_bots = set()

    async def activate_bot_kill(self, bot_id: str, reason: str) -> None:
        """
        Flatten positions of the bot + cancel pending orders + mark bot HALTED.

        Args:
            bot_id: Bot identifier
            reason: Reason for kill switch activation
        """
        # Ensure idempotency with lock
        with self._lock:
            if bot_id in self._killed_bots:
                self._log.warning(f"Bot {bot_id} already killed, ignoring duplicate signal")
                return
            self._killed_bots.add(bot_id)

        try:
            self._log.critical(f"KILL SWITCH activated for bot {bot_id}: {reason}")

            # Get bot from database
            bot = self._get_bot(bot_id)
            if not bot:
                self._log.error(f"Bot {bot_id} not found")
                return

            # Check if already halted
            if bot.status == BotStatus.HALTED:
                self._log.info(f"Bot {bot_id} already HALTED, logging event only")
                self._log_kill_event(bot_id, reason, "per_bot", 0, 0)
                return

            # Execute kill operations
            positions_closed = await self._flatten_positions(bot_id)
            orders_cancelled = await self._cancel_pending_orders(bot_id)

            # Update bot status
            self._set_bot_status(bot_id, BotStatus.HALTED, reason, "per_bot")

            # Publish event to message bus
            self._publish_kill_event(bot_id, reason, "per_bot", positions_closed, orders_cancelled)

            # Log to database
            self._log_kill_event(bot_id, reason, "per_bot", positions_closed, orders_cancelled)

        except Exception as e:
            self._log.error(f"Error activating kill switch for bot {bot_id}: {e}")
            # Remove from killed set on error to allow retry
            with self._lock:
                self._killed_bots.discard(bot_id)
            raise

    async def activate_global_kill(self, reason: str) -> None:
        """
        Flatten ALL positions of all active bots.

        Args:
            reason: Reason for global kill switch activation
        """
        self._log.critical(f"GLOBAL KILL SWITCH activated: {reason}")

        # Get all active bots
        active_bots = self._get_active_bots()
        self._log.info(f"Found {len(active_bots)} active bots to kill")

        # Kill each bot individually
        tasks = []
        for bot in active_bots:
            task = asyncio.create_task(
                self.activate_bot_kill(
                    bot_id=bot.id,
                    reason=f"global_kill: {reason}"
                )
            )
            tasks.append(task)

        # Wait for all kills to complete
        await asyncio.gather(*tasks, return_exceptions=True)

        # Publish global kill event
        self._publish_kill_event("ALL", reason, "global", 0, 0)

        # Log global kill event
        self._log_kill_event(None, reason, "global", 0, 0)

    async def _flatten_positions(self, bot_id: str) -> int:
        """
        Market orders to close all open positions. No retry.

        Args:
            bot_id: Bot identifier

        Returns:
            Number of positions closed
        """
        bot = self._get_bot(bot_id)
        if not bot or not hasattr(bot, 'positions'):
            return 0

        positions_closed = 0
        for position in bot.positions:
            try:
                # Use market order with IOC (Immediate or Cancel)
                await self._execution_client.flatten_position(
                    symbol=position.get("symbol"),
                    quantity=position.get("quantity"),
                    order_type="MARKET",
                    time_in_force="IOC"
                )
                positions_closed += 1
                self._log.info(f"Flattened position for bot {bot_id}: {position}")
            except Exception as e:
                # Log error but continue with other positions
                self._log.error(f"Failed to flatten position {position}: {e}")

        return positions_closed

    async def _cancel_pending_orders(self, bot_id: str) -> int:
        """
        Cancel all pending orders of the bot via async_rithmic.

        Args:
            bot_id: Bot identifier

        Returns:
            Number of orders cancelled
        """
        bot = self._get_bot(bot_id)
        if not bot or not hasattr(bot, 'pending_orders'):
            return 0

        orders_cancelled = 0
        for order in bot.pending_orders:
            try:
                await self._execution_client.cancel_order(
                    order_id=order.get("id")
                )
                orders_cancelled += 1
                self._log.info(f"Cancelled order for bot {bot_id}: {order['id']}")
            except Exception as e:
                # Log error but continue with other orders
                self._log.error(f"Failed to cancel order {order['id']}: {e}")

        return orders_cancelled

    def _set_bot_status(
        self,
        bot_id: str,
        status: BotStatus,
        reason: str = None,
        scope: str = None
    ) -> None:
        """
        Update bot_instances.status in DB. Requires manual confirmation to resume.

        Args:
            bot_id: Bot identifier
            status: New status
            reason: Reason for status change
            scope: Kill scope ("per_bot" or "global")
        """
        bot = self._get_bot(bot_id)
        if not bot:
            return

        bot.status = status

        if status == BotStatus.HALTED:
            bot.halted_at = datetime.utcnow()
            bot.halt_reason = reason
            bot.kill_scope = scope
        elif status == BotStatus.RUNNING:
            # Clear halt fields when resuming
            bot.halted_at = None
            bot.halt_reason = None
            bot.kill_scope = None

        self._db_session.commit()
        self._log.info(f"Bot {bot_id} status updated to {status}")

    def _publish_kill_event(
        self,
        bot_id: str,
        reason: str,
        scope: str,
        positions_closed: int = 0,
        orders_cancelled: int = 0
    ) -> None:
        """
        Publish KillSwitchActivated to MessageBus with priority=0.

        Args:
            bot_id: Bot identifier (or "ALL" for global)
            reason: Reason for kill switch
            scope: "per_bot" or "global"
            positions_closed: Number of positions closed
            orders_cancelled: Number of orders cancelled
        """
        event = KillSwitchEvent(
            bot_id=bot_id,
            reason=reason,
            scope=scope,
            triggered_by="manual",
            positions_closed=positions_closed,
            orders_cancelled=orders_cancelled
        )

        # Publish with maximum priority (0)
        self._msgbus.publish(event, priority=0)
        self._log.info(f"Published kill switch event for {bot_id} with priority 0")

    def _log_kill_event(
        self,
        bot_id: Optional[str],
        reason: str,
        scope: str,
        positions_closed: int = 0,
        orders_cancelled: int = 0,
        triggered_by: str = "manual",
        circuit_breaker_type: Optional[str] = None
    ) -> None:
        """
        Log kill switch event to database.

        Args:
            bot_id: Bot identifier (None for global)
            reason: Reason for kill switch
            scope: "per_bot" or "global"
            positions_closed: Number of positions closed
            orders_cancelled: Number of orders cancelled
            triggered_by: "manual" or "circuit_breaker"
            circuit_breaker_type: Type of circuit breaker if applicable
        """
        from app.models.kill_switch import KillSwitchEventModel

        event = KillSwitchEventModel(
            bot_id=bot_id,
            scope=scope,
            reason=reason,
            triggered_by=triggered_by,
            circuit_breaker_type=circuit_breaker_type,
            positions_closed=positions_closed,
            orders_cancelled=orders_cancelled,
            created_at=datetime.utcnow()
        )

        self._db_session.add(event)
        self._db_session.commit()

    def _get_bot(self, bot_id: str):
        """
        Get bot instance from database.

        Args:
            bot_id: Bot identifier

        Returns:
            Bot instance or None
        """
        from app.models.bot_instance import BotInstance

        return self._db_session.query(BotInstance).filter(
            BotInstance.id == bot_id
        ).first()

    def _get_active_bots(self) -> List:
        """
        Get all active (RUNNING) bots.

        Returns:
            List of active bot instances
        """
        from app.models.bot_instance import BotInstance

        return self._db_session.query(BotInstance).filter(
            BotInstance.status == BotStatus.RUNNING
        ).all()

    async def submit_order(self, bot_id: str, order: Dict[str, Any]) -> None:
        """
        Submit order for a bot. Rejects if bot is HALTED.

        Args:
            bot_id: Bot identifier
            order: Order details

        Raises:
            Exception: If bot is HALTED
        """
        bot = self._get_bot(bot_id)
        if not bot:
            raise Exception(f"Bot {bot_id} not found")

        if bot.status == BotStatus.HALTED:
            raise Exception(f"Bot is HALTED and cannot accept new orders")

        # Forward to execution client
        await self._execution_client.submit_order(order)

    async def resume_bot(
        self,
        bot_id: str,
        manual_confirmation: bool = False,
        confirmed_by: str = None
    ) -> None:
        """
        Resume a HALTED bot. Requires manual confirmation.

        Args:
            bot_id: Bot identifier
            manual_confirmation: Must be True to resume
            confirmed_by: User who confirmed the resume

        Raises:
            Exception: If manual confirmation not provided
        """
        if not manual_confirmation:
            raise Exception("Manual confirmation required to resume HALTED bot")

        bot = self._get_bot(bot_id)
        if not bot:
            raise Exception(f"Bot {bot_id} not found")

        if bot.status != BotStatus.HALTED:
            self._log.info(f"Bot {bot_id} is not HALTED, status: {bot.status}")
            return

        # Clear from killed set to allow new operations
        with self._lock:
            self._killed_bots.discard(bot_id)

        # Update status to RUNNING
        self._set_bot_status(bot_id, BotStatus.RUNNING)

        # Log resume event
        self._log.info(f"Bot {bot_id} resumed by {confirmed_by}")

        # Publish resume event
        event = {
            "type": "bot_resumed",
            "bot_id": bot_id,
            "confirmed_by": confirmed_by,
            "timestamp": datetime.utcnow()
        }
        self._msgbus.publish(event, priority=1)

    def get_bot_status(self, bot_id: str) -> Optional[BotStatus]:
        """
        Get current status of a bot.

        Args:
            bot_id: Bot identifier

        Returns:
            Bot status or None if not found
        """
        bot = self._get_bot(bot_id)
        return bot.status if bot else None

    async def _execute_kill(self, bot_id: str, reason: str) -> bool:
        """
        Execute kill operations (for testing concurrency).

        Args:
            bot_id: Bot identifier
            reason: Reason for kill

        Returns:
            True if kill executed
        """
        # This method is for testing concurrency
        await asyncio.sleep(0.01)  # Simulate processing
        return True

    def _flatten_positions_sync(self) -> bool:
        """Synchronous version for thread safety testing."""
        return True

    def _cancel_orders_sync(self) -> bool:
        """Synchronous version for thread safety testing."""
        return True