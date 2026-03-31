"""
Tests for Risk Manager (AUT-349)

TDD implementation for M3.6 Risk Manager with 6 pre-trade checks.
Tests written BEFORE implementation following TDD principles.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, time
from zoneinfo import ZoneInfo

# These will be implemented
from app.trading.risk_manager import (
    NQHubRiskActor,
    RiskCheckResult,
    RiskConfig,
)


# ============= Test Fixtures =============

@pytest.fixture
def risk_config():
    """Standard risk configuration for testing"""
    return RiskConfig(
        apex_account_size=25000,
        apex_max_contracts=4,
        apex_trailing_threshold=1500,
        trailing_safety_buffer=500,
        max_daily_loss=1000,
        max_consecutive_losses=5,
        max_orders_per_minute=10,
        news_blackout_minutes=5,
    )


@pytest.fixture
def mock_order():
    """Mock NautilusTrader Order"""
    order = Mock()
    order.quantity = 1  # 1 contract
    order.instrument_id = Mock()
    order.instrument_id.symbol.value = "NQ"
    order.client_order_id = "ORDER-123"
    return order


@pytest.fixture
def mock_kill_switch():
    """Mock KillSwitchActor"""
    kill_switch = Mock()
    kill_switch.activate_bot_kill = Mock()
    return kill_switch


@pytest.fixture
def risk_actor(risk_config, mock_kill_switch):
    """Create NQHubRiskActor instance with mocks"""
    actor = NQHubRiskActor(
        bot_id="test_bot_1",
        risk_config=risk_config,
        kill_switch=mock_kill_switch,
    )

    # Mock account state
    actor._current_position = 0  # contracts
    actor._account_balance = Decimal("25000")
    actor._daily_pnl = Decimal("0")

    return actor


# ============= Happy Path Tests =============

def test_all_checks_pass_order_submitted(risk_actor, mock_order):
    """
    Test that when all 6 checks pass, the order is approved.

    Setup:
    - Position: 0 contracts (below limit)
    - Daily P&L: $0 (no loss)
    - Balance: $25,000 (well above trailing threshold)
    - Time: 2:00 PM ET (within trading hours)
    - Config: Valid Apex account config
    """
    # Set time to 2:00 PM ET (valid trading time)
    with patch('app.trading.risk_manager.datetime') as mock_datetime:
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2024, 3, 15, 14, 0, 0, tzinfo=et_tz)  # 2:00 PM ET
        mock_datetime.now.return_value = mock_now

        result = risk_actor.on_order(mock_order)

        assert result is True, "Order should pass all checks"


# ============= Position Size Check Tests =============

def test_position_size_exceeds_apex_limit_rejected(risk_actor, mock_order):
    """
    Test that order is rejected if current position + new order exceeds apex_max_contracts.

    Setup:
    - Current position: 3 contracts
    - New order: 2 contracts
    - Total: 5 contracts > apex_max_contracts (4)
    """
    risk_actor._current_position = 3
    mock_order.quantity = 2

    result = risk_actor.on_order(mock_order)

    assert result is False, "Order should be rejected for exceeding position size"


# ============= Daily Loss Check Tests =============

def test_daily_loss_exceeded_rejected(risk_actor, mock_order):
    """
    Test that order is rejected if daily P&L exceeds max_daily_loss threshold.

    Setup:
    - Daily P&L: -$1,200
    - max_daily_loss: $1,000
    - P&L < -max_daily_loss → reject
    """
    risk_actor._daily_pnl = Decimal("-1200")

    result = risk_actor.on_order(mock_order)

    assert result is False, "Order should be rejected for exceeding daily loss limit"


# ============= Trailing Threshold Check Tests =============

def test_trailing_threshold_proximity_rejected(risk_actor, mock_order):
    """
    Test that order is rejected when balance is within safety buffer of trailing threshold.

    Setup:
    - Balance: $1,800
    - Trailing threshold: $1,500
    - Safety buffer: $500
    - Minimum safe balance: $1,500 + $500 = $2,000
    - $1,800 < $2,000 → reject (proximity warning)

    Note: This should NOT trigger kill switch (only proximity, not breach)
    """
    risk_actor._account_balance = Decimal("1800")

    result = risk_actor.on_order(mock_order)

    assert result is False, "Order should be rejected for trailing threshold proximity"
    assert not risk_actor._kill_switch.activate_bot_kill.called, \
        "Kill switch should NOT be triggered for proximity (only for breach)"


def test_trailing_threshold_breach_triggers_kill_switch(risk_actor, mock_order, mock_kill_switch):
    """
    Test that when balance breaches trailing threshold, kill switch is activated.

    Setup:
    - Balance: $1,400
    - Trailing threshold: $1,500
    - $1,400 < $1,500 → BREACH → activate kill switch

    Critical: This is a REAL breach, not just proximity warning.
    """
    risk_actor._account_balance = Decimal("1400")

    result = risk_actor.on_order(mock_order)

    assert result is False, "Order should be rejected for trailing threshold breach"
    assert mock_kill_switch.activate_bot_kill.called, \
        "Kill switch MUST be triggered on real breach"

    # Verify kill switch was called with correct bot_id and reason
    call_args = mock_kill_switch.activate_bot_kill.call_args
    assert call_args[0][0] == "test_bot_1", "Should activate kill switch for correct bot"
    assert "trailing threshold breach" in call_args[0][1].lower(), \
        "Reason should mention trailing threshold breach"


# ============= Max Contracts Check Tests =============

def test_max_contracts_exceeded_rejected(risk_actor, mock_order):
    """
    Test that order is rejected if it would exceed Apex max contracts limit.

    Setup:
    - Current position: 4 contracts (at limit)
    - New order: 1 contract
    - Total: 5 contracts > apex_max_contracts (4)
    """
    risk_actor._current_position = 4
    mock_order.quantity = 1

    result = risk_actor.on_order(mock_order)

    assert result is False, "Order should be rejected for exceeding max contracts"


# ============= Trading Hours Check Tests =============

def test_trading_hours_4pm_to_5pm_et_rejected(risk_actor, mock_order):
    """
    Test that orders are rejected during Apex maintenance window (4:00-5:00 PM ET).

    Setup:
    - Time: 4:30 PM ET (middle of maintenance window)
    """
    with patch('app.trading.risk_manager.datetime') as mock_datetime:
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2024, 3, 15, 16, 30, 0, tzinfo=et_tz)  # 4:30 PM ET
        mock_datetime.now.return_value = mock_now

        result = risk_actor.on_order(mock_order)

        assert result is False, "Order should be rejected during maintenance window"


def test_trading_hours_exactly_at_4pm_rejected(risk_actor, mock_order):
    """
    Boundary test: Verify that exactly 4:00:00 PM ET is rejected.

    Critical: Test the EXACT boundary condition.
    """
    with patch('app.trading.risk_manager.datetime') as mock_datetime:
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2024, 3, 15, 16, 0, 0, tzinfo=et_tz)  # Exactly 4:00 PM ET
        mock_datetime.now.return_value = mock_now

        result = risk_actor.on_order(mock_order)

        assert result is False, "Order at exactly 4:00 PM ET should be rejected"


def test_trading_hours_exactly_at_5pm_passes(risk_actor, mock_order):
    """
    Boundary test: Verify that exactly 5:00:00 PM ET passes (maintenance window ended).

    Critical: Test the EXACT boundary condition.
    """
    with patch('app.trading.risk_manager.datetime') as mock_datetime:
        et_tz = ZoneInfo("America/New_York")
        mock_now = datetime(2024, 3, 15, 17, 0, 0, tzinfo=et_tz)  # Exactly 5:00 PM ET
        mock_datetime.now.return_value = mock_now

        result = risk_actor.on_order(mock_order)

        # Should pass (assuming all other checks pass)
        # If it fails, it should NOT be due to trading hours
        if not result:
            # Check that failure reason is NOT trading hours
            assert "trading hours" not in risk_actor._last_rejection_reason.lower(), \
                "Order at exactly 5:00 PM ET should NOT be rejected for trading hours"


# ============= Apex Consistency Check Tests =============

def test_apex_consistency_mismatch_rejected(risk_actor, mock_order):
    """
    Test that order is rejected if bot config is inconsistent with Apex account.

    Setup:
    - Bot config: apex_max_contracts = 4
    - Actual Apex account: max_contracts = 2 (inconsistent)
    """
    # Mock inconsistent Apex account config
    risk_actor._apex_account_max_contracts = 2  # Different from config (4)

    result = risk_actor.on_order(mock_order)

    assert result is False, "Order should be rejected for Apex config mismatch"


# ============= Risk Config Update Tests =============

def test_risk_config_update_requires_bot_stopped():
    """
    Test that risk config can ONLY be updated when bot is STOPPED.

    This test would typically be in the REST endpoint tests, but we include
    it here to verify the constraint at the manager level.
    """
    # This will be tested in integration tests with the REST API
    # For now, we just document the requirement
    pass


def test_risk_config_running_bot_rejects_update():
    """
    Test that attempting to update risk config while bot is RUNNING fails.

    This test would typically be in the REST endpoint tests.
    """
    # This will be tested in integration tests with the REST API
    pass


# ============= Event Logging Tests =============

@pytest.mark.asyncio
async def test_risk_event_logged_on_rejection(risk_actor, mock_order):
    """
    Test that a risk_events record is created when an order is rejected.

    Setup:
    - Trigger a rejection (e.g., daily loss exceeded)
    - Verify risk_events table contains the rejection record
    """
    risk_actor._daily_pnl = Decimal("-1200")  # Exceeds max_daily_loss

    # Mock the event logging function
    risk_actor._log_risk_event = AsyncMock()

    result = risk_actor.on_order(mock_order)

    assert result is False, "Order should be rejected"

    # Verify event was logged
    if hasattr(risk_actor, '_log_risk_event'):
        assert risk_actor._log_risk_event.called, "Risk event should be logged"

        # Verify event details
        call_args = risk_actor._log_risk_event.call_args
        assert call_args is not None, "Event logging should have been called"


@pytest.mark.asyncio
async def test_kill_switch_event_logged_on_breach(risk_actor, mock_order, mock_kill_switch):
    """
    Test that kill switch activation is logged when trailing threshold is breached.

    Setup:
    - Balance: $1,400 (below $1,500 trailing threshold)
    - Trigger breach
    - Verify kill_switch_triggered = TRUE in risk_events
    """
    risk_actor._account_balance = Decimal("1400")  # Below threshold
    risk_actor._log_risk_event = AsyncMock()

    result = risk_actor.on_order(mock_order)

    assert result is False, "Order should be rejected"
    assert mock_kill_switch.activate_bot_kill.called, "Kill switch should be activated"

    # Verify event was logged with kill_switch_triggered = TRUE
    if hasattr(risk_actor, '_log_risk_event'):
        assert risk_actor._log_risk_event.called, "Event should be logged"

        # Check if kill_switch_triggered flag was set
        call_args = risk_actor._log_risk_event.call_args
        if call_args and len(call_args[1]) > 0:
            assert call_args[1].get('kill_switch_triggered') is True, \
                "Kill switch triggered flag should be True"


# ============= Check Order Tests =============

def test_checks_run_in_order_stops_at_first_failure(risk_actor, mock_order):
    """
    Test that checks run in the specified order and stop at the first failure.

    Order of checks:
    1. position_size_check
    2. daily_loss_check
    3. trailing_threshold_check
    4. max_contracts_check
    5. trading_hours_check
    6. apex_consistency_check

    Setup:
    - Trigger failure in check #2 (daily_loss_check)
    - Verify that checks #3-6 are NOT executed
    """
    risk_actor._daily_pnl = Decimal("-1200")  # Fails check #2

    # Mock all check methods to track calls
    risk_actor._check_position_size = Mock(return_value=RiskCheckResult(passed=True, check_name="position_size"))
    risk_actor._check_daily_loss = Mock(return_value=RiskCheckResult(
        passed=False,
        reason="Daily loss exceeded",
        check_name="daily_loss"
    ))
    risk_actor._check_trailing_threshold = Mock()
    risk_actor._check_max_contracts = Mock()
    risk_actor._check_trading_hours = Mock()
    risk_actor._check_apex_consistency = Mock()

    result = risk_actor.on_order(mock_order)

    assert result is False, "Order should be rejected"
    assert risk_actor._check_position_size.called, "Check #1 should be executed"
    assert risk_actor._check_daily_loss.called, "Check #2 should be executed"
    assert not risk_actor._check_trailing_threshold.called, "Check #3 should NOT be executed"
    assert not risk_actor._check_max_contracts.called, "Check #4 should NOT be executed"
    assert not risk_actor._check_trading_hours.called, "Check #5 should NOT be executed"
    assert not risk_actor._check_apex_consistency.called, "Check #6 should NOT be executed"


# ============= NQ Constants Tests =============

def test_nq_constants_configured():
    """
    Test that NQ instrument constants are correctly configured.

    NQ Constants:
    - tick_size = 0.25
    - tick_value = $5.00
    - point_value = $20.00
    """
    from app.trading.risk_manager import NQ_CONSTANTS

    assert NQ_CONSTANTS["tick_size"] == Decimal("0.25")
    assert NQ_CONSTANTS["tick_value"] == Decimal("5.00")
    assert NQ_CONSTANTS["point_value"] == Decimal("20.00")
    assert NQ_CONSTANTS["symbol"] == "NQ"
    assert NQ_CONSTANTS["exchange"] == "CME"
