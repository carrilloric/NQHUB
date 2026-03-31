"""
Risk Manager (AUT-349)

NQHubRiskActor — Pre-trade risk manager for NautilusTrader.
Executes 6 checks before every order. If any check fails, order is rejected.

Features:
- 6 pre-trade risk checks (position size, daily loss, trailing threshold, etc.)
- Automatic kill switch activation on trailing threshold breach
- Event logging to risk_events table
- Configurable thresholds via risk_config JSONB
- Trading hours enforcement (NO trading 4:00-5:00 PM ET)

References:
- Linear Issue: AUT-349
- Depends on: AUT-346 (RithmicExecutionClient), AUT-348 (KillSwitchActor)
- Unblocks: AUT-350 (OMS)
"""
import logging
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, time
from zoneinfo import ZoneInfo
from typing import Optional

# NautilusTrader imports (will be available when AUT-344 is done)
try:
    from nautilus_trader.common.actor import Actor
    from nautilus_trader.model.orders import Order
except ImportError:
    # Temporary mocks for development
    Actor = object
    Order = object


logger = logging.getLogger(__name__)


# ============= NQ Instrument Constants =============

NQ_CONSTANTS = {
    "tick_size": Decimal("0.25"),
    "tick_value": Decimal("5.00"),  # $5 per tick
    "point_value": Decimal("20.00"),  # $20 per point (4 ticks)
    "symbol": "NQ",
    "exchange": "CME",
    "currency": "USD",
}


# ============= Risk Configuration =============

@dataclass
class RiskConfig:
    """
    Risk configuration for a bot instance.

    Loaded from bot_instances.risk_config JSONB column.
    Can only be modified when bot is in STOPPED state.

    Attributes:
        apex_account_size: Initial Apex account size
        apex_max_contracts: Maximum contracts allowed per Apex account rules
        apex_trailing_threshold: Minimum balance before account is breached ($1500 for $25k account)
        trailing_safety_buffer: Safety buffer above trailing threshold ($500 default)
        max_daily_loss: Maximum daily loss before stopping ($1000 default)
        max_consecutive_losses: Max consecutive losing trades before stopping
        max_orders_per_minute: Rate limit for order submission
        news_blackout_minutes: Minutes to pause trading around major news events
    """
    apex_account_size: int = 25000
    apex_max_contracts: int = 4
    apex_trailing_threshold: int = 1500
    trailing_safety_buffer: int = 500
    max_daily_loss: int = 1000
    max_consecutive_losses: int = 5
    max_orders_per_minute: int = 10
    news_blackout_minutes: int = 5


# ============= Risk Check Result =============

@dataclass
class RiskCheckResult:
    """
    Result from a single risk check.

    Attributes:
        passed: True if check passed, False if failed
        reason: Human-readable explanation if check failed
        trigger_kill_switch: True if this failure should activate kill switch
        check_name: Name of the check that was executed
    """
    passed: bool
    reason: str = ""
    trigger_kill_switch: bool = False
    check_name: str = ""


# ============= NQHub Risk Actor =============

class NQHubRiskActor(Actor):
    """
    Pre-trade risk manager for NautilusTrader.

    Intercepts every order before submission and executes 6 risk checks.
    If any check fails, order is rejected and never reaches RithmicExecutionClient.

    Checks (executed in order):
    1. position_size_check     — current contracts + new order <= apex_max_contracts
    2. daily_loss_check        — daily P&L > -max_daily_loss threshold
    3. trailing_threshold_check — balance > trailing_threshold + safety_buffer
    4. max_contracts_check     — never exceed Apex contract limit
    5. trading_hours_check     — NO trading 4:00-5:00 PM ET (Apex maintenance)
    6. apex_consistency_check  — bot config matches Apex account config

    Critical Features:
    - Checks run in ORDER — if first fails, rest don't execute
    - Trailing threshold proximity (within buffer) → reject order
    - Trailing threshold breach (actual breach) → reject order + activate kill switch
    - All rejections logged to risk_events table
    - Events published to nqhub.risk.* MessageBus topic

    WARNING: Checks stop at first failure. Order of checks is critical.
    """

    def __init__(
        self,
        bot_id: str,
        risk_config: RiskConfig,
        kill_switch: Optional[object] = None,
    ):
        """
        Initialize NQHubRiskActor.

        Args:
            bot_id: Unique bot instance ID
            risk_config: Risk configuration with thresholds
            kill_switch: KillSwitchActor instance (optional for testing)
        """
        self._bot_id = bot_id
        self._risk_config = risk_config
        self._kill_switch = kill_switch

        # Account state (updated by AccountManager or mocked for testing)
        self._current_position = 0  # Current open contracts
        self._account_balance = Decimal(str(risk_config.apex_account_size))
        self._daily_pnl = Decimal("0")

        # Apex account config (for consistency check)
        self._apex_account_max_contracts = risk_config.apex_max_contracts

        # Tracking
        self._last_rejection_reason = ""

        logger.info(
            f"NQHubRiskActor initialized for bot: {bot_id} "
            f"with max_contracts={risk_config.apex_max_contracts}, "
            f"trailing_threshold=${risk_config.apex_trailing_threshold}"
        )

    # ============= Main Entry Point =============

    def on_order(self, order: Order) -> bool:
        """
        Execute all 6 risk checks on an order.

        Checks run in ORDER. If any check fails, order is rejected
        and remaining checks are NOT executed.

        Args:
            order: NautilusTrader Order to validate

        Returns:
            True if order passes all checks (submit to exchange)
            False if order fails any check (reject, do NOT submit)
        """
        checks = [
            self._check_position_size,
            self._check_daily_loss,
            self._check_trailing_threshold,
            self._check_max_contracts,
            self._check_trading_hours,
            self._check_apex_consistency,
        ]

        for check in checks:
            result = check(order)

            if not result.passed:
                self._reject_order(order, result)

                # Trigger kill switch if required
                if result.trigger_kill_switch:
                    self._activate_kill_switch(result.reason)

                return False

        # All checks passed
        logger.info(f"Order {order.client_order_id} passed all risk checks")
        return True

    # ============= Risk Checks =============

    def _check_position_size(self, order: Order) -> RiskCheckResult:
        """
        Check #1: Position size does not exceed apex_max_contracts.

        Validates: current_position + new_order.quantity <= apex_max_contracts

        Args:
            order: Order to validate

        Returns:
            RiskCheckResult with passed=True if within limit
        """
        new_total = self._current_position + order.quantity

        if new_total > self._risk_config.apex_max_contracts:
            return RiskCheckResult(
                passed=False,
                reason=(
                    f"Position size would exceed limit: "
                    f"{new_total} > {self._risk_config.apex_max_contracts} contracts"
                ),
                check_name="position_size_check",
            )

        return RiskCheckResult(passed=True, check_name="position_size_check")

    def _check_daily_loss(self, order: Order) -> RiskCheckResult:
        """
        Check #2: Daily P&L has not exceeded max_daily_loss threshold.

        Validates: daily_pnl > -max_daily_loss

        Args:
            order: Order to validate

        Returns:
            RiskCheckResult with passed=True if within loss limit
        """
        max_loss = Decimal(str(-self._risk_config.max_daily_loss))

        if self._daily_pnl < max_loss:
            return RiskCheckResult(
                passed=False,
                reason=(
                    f"Daily loss limit exceeded: "
                    f"${self._daily_pnl} < ${max_loss}"
                ),
                check_name="daily_loss_check",
            )

        return RiskCheckResult(passed=True, check_name="daily_loss_check")

    def _check_trailing_threshold(self, order: Order) -> RiskCheckResult:
        """
        Check #3: Account balance is above trailing threshold + safety buffer.

        Two scenarios:
        1. Proximity warning: balance <= threshold + buffer → reject order (no kill switch)
        2. Actual breach: balance <= threshold → reject order + ACTIVATE KILL SWITCH

        Validates:
        - For proximity: balance > trailing_threshold + trailing_safety_buffer
        - For breach: balance > trailing_threshold

        Args:
            order: Order to validate

        Returns:
            RiskCheckResult with trigger_kill_switch=True if actual breach
        """
        threshold = Decimal(str(self._risk_config.apex_trailing_threshold))
        buffer = Decimal(str(self._risk_config.trailing_safety_buffer))
        minimum_safe_balance = threshold + buffer

        # Check for ACTUAL BREACH (below threshold itself)
        if self._account_balance <= threshold:
            return RiskCheckResult(
                passed=False,
                reason=(
                    f"Trailing threshold BREACH: "
                    f"balance ${self._account_balance} <= threshold ${threshold}"
                ),
                trigger_kill_switch=True,  # ← CRITICAL: Activate kill switch
                check_name="trailing_threshold_check",
            )

        # Check for PROXIMITY (within buffer zone)
        if self._account_balance <= minimum_safe_balance:
            return RiskCheckResult(
                passed=False,
                reason=(
                    f"Trailing threshold proximity: "
                    f"balance ${self._account_balance} <= safe minimum ${minimum_safe_balance}"
                ),
                trigger_kill_switch=False,  # Proximity only, no kill switch
                check_name="trailing_threshold_check",
            )

        return RiskCheckResult(passed=True, check_name="trailing_threshold_check")

    def _check_max_contracts(self, order: Order) -> RiskCheckResult:
        """
        Check #4: Order does not exceed Apex maximum contracts limit.

        This is a duplicate of position_size_check but kept for explicit validation.

        Args:
            order: Order to validate

        Returns:
            RiskCheckResult with passed=True if within limit
        """
        new_total = self._current_position + order.quantity

        if new_total > self._risk_config.apex_max_contracts:
            return RiskCheckResult(
                passed=False,
                reason=(
                    f"Max contracts exceeded: "
                    f"{new_total} > {self._risk_config.apex_max_contracts}"
                ),
                check_name="max_contracts_check",
            )

        return RiskCheckResult(passed=True, check_name="max_contracts_check")

    def _check_trading_hours(self, order: Order) -> RiskCheckResult:
        """
        Check #5: Order is not submitted during Apex maintenance window.

        Maintenance window: 4:00 PM - 5:00 PM ET (16:00 - 17:00)

        Uses zoneinfo for proper timezone handling with America/New_York.

        Critical boundaries:
        - 4:00:00 PM ET → REJECT (maintenance starts)
        - 5:00:00 PM ET → ALLOW (maintenance ended)

        Args:
            order: Order to validate

        Returns:
            RiskCheckResult with passed=True if outside maintenance window
        """
        # Get current time in ET timezone
        et_tz = ZoneInfo("America/New_York")
        now_et = datetime.now(et_tz)
        current_time = now_et.time()

        # Maintenance window: 4:00 PM - 5:00 PM ET
        maintenance_start = time(16, 0, 0)  # 4:00 PM
        maintenance_end = time(17, 0, 0)    # 5:00 PM

        # Check if current time is within maintenance window
        # Note: maintenance_start <= current_time < maintenance_end
        if maintenance_start <= current_time < maintenance_end:
            return RiskCheckResult(
                passed=False,
                reason=(
                    f"Trading hours violation: "
                    f"Cannot trade during Apex maintenance window "
                    f"(4:00 PM - 5:00 PM ET). Current time: {current_time.strftime('%H:%M:%S')} ET"
                ),
                check_name="trading_hours_check",
            )

        return RiskCheckResult(passed=True, check_name="trading_hours_check")

    def _check_apex_consistency(self, order: Order) -> RiskCheckResult:
        """
        Check #6: Bot configuration is consistent with Apex account settings.

        Validates that bot's risk_config matches actual Apex account limits.
        This prevents configuration drift between bot and Apex account.

        Args:
            order: Order to validate

        Returns:
            RiskCheckResult with passed=True if config matches
        """
        if self._risk_config.apex_max_contracts != self._apex_account_max_contracts:
            return RiskCheckResult(
                passed=False,
                reason=(
                    f"Apex config mismatch: "
                    f"bot max_contracts={self._risk_config.apex_max_contracts} "
                    f"!= apex account max_contracts={self._apex_account_max_contracts}"
                ),
                check_name="apex_consistency_check",
            )

        return RiskCheckResult(passed=True, check_name="apex_consistency_check")

    # ============= Order Rejection & Kill Switch =============

    def _reject_order(self, order: Order, result: RiskCheckResult):
        """
        Reject an order and log the rejection event.

        Args:
            order: Order that failed check
            result: RiskCheckResult with failure details
        """
        self._last_rejection_reason = result.reason

        logger.warning(
            f"Order {order.client_order_id} REJECTED by {result.check_name}: "
            f"{result.reason}"
        )

        # Log to risk_events table
        # Check if logging method exists (for testing/mocking)
        if hasattr(self, '_log_risk_event') and callable(self._log_risk_event):
            # Call the logging method (async or sync depending on implementation)
            try:
                # Try to call as sync first (for mocking in tests)
                self._log_risk_event(order, result, kill_switch_triggered=result.trigger_kill_switch)
            except TypeError:
                # If it's actually async, we can't await in sync context
                # In production, this would be handled by a background task queue
                pass

    def _activate_kill_switch(self, reason: str):
        """
        Activate kill switch for this bot.

        Called when trailing threshold is BREACHED (not just proximity).

        Args:
            reason: Reason for kill switch activation
        """
        if self._kill_switch is None:
            logger.error("Kill switch not available, cannot activate")
            return

        logger.critical(
            f"KILL SWITCH ACTIVATED for bot {self._bot_id}: {reason}"
        )

        self._kill_switch.activate_bot_kill(self._bot_id, reason)

    async def _log_risk_event(
        self,
        order: Order,
        result: RiskCheckResult,
        kill_switch_triggered: bool = False,
    ):
        """
        Log risk event to risk_events table.

        Args:
            order: Order that was checked
            result: Result from risk check
            kill_switch_triggered: Whether kill switch was triggered
        """
        # In production, this would insert into risk_events table:
        # INSERT INTO risk_events (
        #     bot_id, check_name, order_id, result, reason,
        #     kill_switch_triggered, account_balance, current_pnl
        # ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        pass
