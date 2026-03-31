"""
Circuit Breaker system for automatic bot shutdown based on risk thresholds.

Four circuit breaker types monitor bot performance and trigger kill switch when thresholds are breached:
1. max_daily_loss - Daily P&L threshold
2. max_consecutive_losses - Consecutive loss streak
3. trailing_threshold_proximity - Balance buffer from trailing threshold
4. max_orders_per_minute - Runaway order detection

All thresholds use NQ tick precision (0.25 points = $5).
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session


# NQ Futures specifications
NQ_TICK_SIZE = 0.25
NQ_TICK_VALUE = 5.0  # $5 per tick
NQ_POINT_VALUE = 20.0  # $20 per point


class CircuitBreakerType(str, Enum):
    """Circuit breaker types."""
    MAX_DAILY_LOSS = "max_daily_loss"
    MAX_CONSECUTIVE_LOSSES = "max_consecutive_losses"
    TRAILING_THRESHOLD_PROXIMITY = "trailing_threshold_proximity"
    MAX_ORDERS_PER_MINUTE = "max_orders_per_minute"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breakers."""
    max_daily_loss: float = -1000.0  # Default $1000 loss limit
    max_consecutive_losses: int = 5  # Default 5 consecutive losses
    trailing_threshold_buffer: float = 500.0  # Default $500 buffer
    max_orders_per_minute: int = 10  # Default 10 orders/min limit
    enabled: bool = True


@dataclass
class BotMetrics:
    """Current bot metrics for circuit breaker evaluation."""
    bot_id: str
    current_pnl: float
    consecutive_losses: int
    account_balance: float
    trailing_threshold: float
    recent_orders: List[datetime]
    positions: List[Dict[str, Any]]
    pending_orders: List[Dict[str, Any]]


class CircuitBreaker:
    """
    Circuit breaker system for automatic bot shutdown.

    Monitors bot performance and triggers kill switch when risk thresholds are breached.
    Uses NQ tick precision for all P&L calculations.
    """

    def __init__(
        self,
        logger: logging.Logger,
        kill_switch_actor,
        db_session: Session
    ):
        """Initialize the CircuitBreaker.

        Args:
            logger: Logger instance
            kill_switch_actor: KillSwitchActor instance for triggering kills
            db_session: Database session
        """
        self._log = logger
        self._kill_switch = kill_switch_actor
        self._db_session = db_session

        # Track triggered circuit breakers to prevent duplicates
        self._triggered_breakers = {}  # {bot_id: set of triggered types}

    async def check_all(self, bot_metrics: BotMetrics, config: CircuitBreakerConfig) -> Optional[str]:
        """
        Check all circuit breakers for a bot.

        Args:
            bot_metrics: Current bot metrics
            config: Circuit breaker configuration

        Returns:
            Trigger reason if any breaker triggered, None otherwise
        """
        if not config.enabled:
            return None

        # Check if bot already halted
        bot_status = self._kill_switch.get_bot_status(bot_metrics.bot_id)
        if bot_status == "HALTED":
            self._log.debug(f"Bot {bot_metrics.bot_id} already HALTED, skipping circuit breakers")
            return None

        # Check each circuit breaker
        breakers = [
            (self.check_daily_loss, CircuitBreakerType.MAX_DAILY_LOSS),
            (self.check_consecutive_losses, CircuitBreakerType.MAX_CONSECUTIVE_LOSSES),
            (self.check_trailing_threshold, CircuitBreakerType.TRAILING_THRESHOLD_PROXIMITY),
            (self.check_order_frequency, CircuitBreakerType.MAX_ORDERS_PER_MINUTE)
        ]

        for check_func, breaker_type in breakers:
            trigger_reason = await check_func(bot_metrics, config)
            if trigger_reason:
                # Check if this breaker already triggered
                if bot_metrics.bot_id in self._triggered_breakers:
                    if breaker_type in self._triggered_breakers[bot_metrics.bot_id]:
                        self._log.warning(
                            f"Circuit breaker {breaker_type} already triggered for bot {bot_metrics.bot_id}"
                        )
                        continue
                else:
                    self._triggered_breakers[bot_metrics.bot_id] = set()

                # Mark as triggered
                self._triggered_breakers[bot_metrics.bot_id].add(breaker_type)

                # Trigger kill switch
                await self._trigger_kill_switch(
                    bot_metrics.bot_id,
                    trigger_reason,
                    breaker_type
                )

                return trigger_reason

        return None

    async def check_daily_loss(
        self,
        bot_id: str = None,
        current_pnl: float = None,
        bot_metrics: BotMetrics = None,
        config: Any = None
    ) -> bool:
        """
        Check if daily P&L has breached loss threshold.

        Uses NQ tick precision for boundary testing:
        - At threshold: NO trigger
        - One tick beyond: TRIGGER

        Args:
            bot_id: Bot identifier (for test compatibility)
            current_pnl: Current P&L (for test compatibility)
            bot_metrics: Current bot metrics (production use)
            config: Circuit breaker configuration

        Returns:
            True if kill switch should trigger, False otherwise
        """
        # Handle both test and production interfaces
        if bot_metrics:
            pnl = self._round_to_tick_value(bot_metrics.current_pnl)
            bot_id = bot_metrics.bot_id
        else:
            pnl = self._round_to_tick_value(current_pnl)

        # Get threshold from config
        if isinstance(config, dict):
            threshold = config.get("max_daily_loss", -1000.0)
        else:
            threshold = config.max_daily_loss if config else -1000.0

        # Boundary condition: trigger only if STRICTLY less than threshold
        if pnl < threshold:
            loss_amount = abs(pnl)
            reason = f"Circuit breaker: max_daily_loss exceeded ({pnl:.2f} < {threshold:.2f})"

            if hasattr(self, '_kill_switch') and self._kill_switch:
                await self._kill_switch.activate_bot_kill(bot_id, reason)
            elif hasattr(self, 'kill_switch'):
                await self.kill_switch.activate_bot_kill(bot_id, reason)

            return True

        return False

    async def check_consecutive_losses(
        self,
        bot_id: str = None,
        loss_streak: int = None,
        bot_metrics: BotMetrics = None,
        config: Any = None
    ) -> bool:
        """
        Check if consecutive losses have reached limit.

        Args:
            bot_id: Bot identifier (for test compatibility)
            loss_streak: Number of consecutive losses (for test compatibility)
            bot_metrics: Current bot metrics (production use)
            config: Circuit breaker configuration

        Returns:
            True if kill switch should trigger, False otherwise
        """
        # Handle both test and production interfaces
        if bot_metrics:
            losses = bot_metrics.consecutive_losses
            bot_id = bot_metrics.bot_id
        else:
            losses = loss_streak

        # Get limit from config
        if isinstance(config, dict):
            limit = config.get("max_consecutive_losses", 5)
        else:
            limit = config.max_consecutive_losses if config else 5

        if losses >= limit:
            reason = f"Circuit breaker: consecutive losses ({losses}) reached limit ({limit})"

            if hasattr(self, '_kill_switch') and self._kill_switch:
                await self._kill_switch.activate_bot_kill(bot_id, reason)
            elif hasattr(self, 'kill_switch'):
                await self.kill_switch.activate_bot_kill(bot_id, reason)

            return True

        return False

    async def check_trailing_threshold(
        self,
        bot_metrics: BotMetrics,
        config: CircuitBreakerConfig
    ) -> Optional[str]:
        """
        Check if account balance is too close to trailing threshold.

        Uses NQ tick precision for buffer calculation.

        Args:
            bot_metrics: Current bot metrics
            config: Circuit breaker configuration

        Returns:
            Trigger reason if breached, None otherwise
        """
        balance = self._round_to_tick_value(bot_metrics.account_balance)
        threshold = self._round_to_tick_value(bot_metrics.trailing_threshold)
        buffer = config.trailing_threshold_buffer

        # Calculate distance from threshold
        distance = balance - threshold

        # Trigger if within buffer zone
        if distance <= buffer:
            return (
                f"Account balance ${balance:.2f} within ${buffer:.2f} "
                f"of trailing threshold ${threshold:.2f} (distance: ${distance:.2f})"
            )

        return None

    async def check_order_frequency(
        self,
        bot_metrics: BotMetrics,
        config: CircuitBreakerConfig
    ) -> Optional[str]:
        """
        Check if order submission rate indicates runaway bot.

        Args:
            bot_metrics: Current bot metrics
            config: Circuit breaker configuration

        Returns:
            Trigger reason if breached, None otherwise
        """
        # Filter orders from last minute
        now = datetime.utcnow()
        one_minute_ago = now - timedelta(minutes=1)

        recent_count = sum(
            1 for order_time in bot_metrics.recent_orders
            if order_time >= one_minute_ago
        )

        if recent_count > config.max_orders_per_minute:
            return (
                f"Order frequency ({recent_count} orders/min) exceeded "
                f"limit ({config.max_orders_per_minute} orders/min) - possible runaway bot"
            )

        return None

    async def _trigger_kill_switch(
        self,
        bot_id: str,
        reason: str,
        breaker_type: CircuitBreakerType
    ) -> None:
        """
        Trigger kill switch for a bot via circuit breaker.

        Args:
            bot_id: Bot identifier
            reason: Reason for triggering
            breaker_type: Which circuit breaker triggered
        """
        full_reason = f"Circuit breaker ({breaker_type.value}): {reason}"

        self._log.warning(
            f"Circuit breaker {breaker_type.value} triggered for bot {bot_id}: {reason}"
        )

        # Trigger kill switch
        await self._kill_switch.activate_bot_kill(bot_id, full_reason)

        # Log circuit breaker activation
        self._log_circuit_breaker_event(bot_id, breaker_type, reason)

    def _log_circuit_breaker_event(
        self,
        bot_id: str,
        breaker_type: CircuitBreakerType,
        reason: str
    ) -> None:
        """
        Log circuit breaker activation to database.

        Args:
            bot_id: Bot identifier
            breaker_type: Type of circuit breaker
            reason: Trigger reason
        """
        # Log to kill_switch_events with circuit_breaker details
        self._kill_switch._log_kill_event(
            bot_id=bot_id,
            reason=reason,
            scope="per_bot",
            triggered_by="circuit_breaker",
            circuit_breaker_type=breaker_type.value
        )

    def _round_to_tick_value(self, value: float) -> float:
        """
        Round value to nearest NQ tick value ($5 increments).

        Args:
            value: Value to round

        Returns:
            Value rounded to nearest $5
        """
        return round(value / NQ_TICK_VALUE) * NQ_TICK_VALUE

    def reset_triggered_breakers(self, bot_id: str) -> None:
        """
        Reset triggered breakers for a bot (used when resuming).

        Args:
            bot_id: Bot identifier
        """
        if bot_id in self._triggered_breakers:
            del self._triggered_breakers[bot_id]
            self._log.info(f"Reset triggered circuit breakers for bot {bot_id}")

    def get_config_from_bot(self, bot_id: str) -> CircuitBreakerConfig:
        """
        Get circuit breaker configuration from bot's risk_config.

        Args:
            bot_id: Bot identifier

        Returns:
            CircuitBreakerConfig with bot's settings or defaults
        """
        from app.models.bot_instance import BotInstance

        bot = self._db_session.query(BotInstance).filter(
            BotInstance.id == bot_id
        ).first()

        if not bot or not bot.risk_config:
            return CircuitBreakerConfig()

        risk_config = bot.risk_config  # JSONB field

        return CircuitBreakerConfig(
            max_daily_loss=risk_config.get("max_daily_loss", -1000.0),
            max_consecutive_losses=risk_config.get("max_consecutive_losses", 5),
            trailing_threshold_buffer=risk_config.get("trailing_threshold_buffer", 500.0),
            max_orders_per_minute=risk_config.get("max_orders_per_minute", 10),
            enabled=risk_config.get("circuit_breakers_enabled", True)
        )

    async def monitor_bot(
        self,
        bot_id: str,
        interval_seconds: int = 5
    ) -> None:
        """
        Continuously monitor a bot for circuit breaker conditions.

        Args:
            bot_id: Bot identifier
            interval_seconds: Check interval in seconds
        """
        self._log.info(f"Starting circuit breaker monitoring for bot {bot_id}")

        while True:
            try:
                # Get current bot metrics
                metrics = await self._get_bot_metrics(bot_id)
                if not metrics:
                    self._log.warning(f"No metrics available for bot {bot_id}")
                    await asyncio.sleep(interval_seconds)
                    continue

                # Get config from bot
                config = self.get_config_from_bot(bot_id)

                # Check all circuit breakers
                trigger_reason = await self.check_all(metrics, config)

                if trigger_reason:
                    self._log.info(f"Circuit breaker triggered for bot {bot_id}: {trigger_reason}")
                    break  # Stop monitoring after trigger

            except Exception as e:
                self._log.error(f"Error monitoring bot {bot_id}: {e}")

            await asyncio.sleep(interval_seconds)

    async def _get_bot_metrics(self, bot_id: str) -> Optional[BotMetrics]:
        """
        Get current metrics for a bot.

        Args:
            bot_id: Bot identifier

        Returns:
            BotMetrics or None if bot not found
        """
        from app.models.bot_instance import BotInstance

        bot = self._db_session.query(BotInstance).filter(
            BotInstance.id == bot_id
        ).first()

        if not bot:
            return None

        # In real implementation, these would come from:
        # - P&L from positions/trades
        # - Order history from execution_client
        # - Account data from broker API

        # Mock implementation for testing
        return BotMetrics(
            bot_id=bot_id,
            current_pnl=getattr(bot, 'current_pnl', 0.0),
            consecutive_losses=getattr(bot, 'consecutive_losses', 0),
            account_balance=getattr(bot, 'account_balance', 25000.0),
            trailing_threshold=getattr(bot, 'trailing_threshold', 23000.0),
            recent_orders=getattr(bot, 'recent_orders', []),
            positions=getattr(bot, 'positions', []),
            pending_orders=getattr(bot, 'pending_orders', [])
        )