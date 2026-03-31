"""
Tests exhaustivos para Kill Switch y Circuit Breakers.

Safety-critical module - todos los tests deben pasar antes del PR.
Incluye tests de boundary (±1 tick), concurrencia e idempotencia.
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import List, Dict, Any
import threading
from concurrent.futures import ThreadPoolExecutor

# Import the classes we'll be testing
from app.trading.kill_switch import KillSwitchActor, KillSwitchEvent
from app.trading.circuit_breaker import CircuitBreaker, CircuitBreakerType
from app.models.bot_instance import BotInstance, BotStatus


# NQ Futures constants for boundary testing
NQ_TICK_SIZE = 0.25
NQ_TICK_VALUE = 5.0
NQ_POINT_VALUE = 20.0


class TestKillSwitchPerBot:
    """Tests for per-bot kill switch functionality."""

    @pytest.fixture
    def kill_switch(self):
        """Create a KillSwitchActor instance with mocked dependencies."""
        mock_logger = Mock()
        mock_msgbus = Mock()
        mock_execution_client = Mock()
        mock_db_session = Mock()

        kill_switch = KillSwitchActor(
            logger=mock_logger,
            msgbus=mock_msgbus,
            execution_client=mock_execution_client,
            db_session=mock_db_session
        )
        return kill_switch

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot instance."""
        bot = Mock(spec=BotInstance)
        bot.id = "bot_test_001"
        bot.status = BotStatus.RUNNING
        bot.positions = [
            {"symbol": "NQ", "quantity": 2, "side": "LONG"},
            {"symbol": "NQ", "quantity": -1, "side": "SHORT"}
        ]
        bot.pending_orders = [
            {"id": "order_001", "status": "PENDING"},
            {"id": "order_002", "status": "PENDING"}
        ]
        return bot

    @pytest.mark.asyncio
    async def test_per_bot_kill_flattens_positions(self, kill_switch, mock_bot):
        """Test that per-bot kill switch flattens all positions."""
        # Setup
        kill_switch._execution_client.flatten_position = AsyncMock(return_value=True)
        kill_switch._db_session.query.return_value.filter.return_value.first.return_value = mock_bot

        # Act
        await kill_switch.activate_bot_kill(
            bot_id=mock_bot.id,
            reason="Test kill - flatten positions"
        )

        # Assert
        # Should flatten each position
        assert kill_switch._execution_client.flatten_position.call_count == len(mock_bot.positions)

        # Verify correct positions were flattened
        for position in mock_bot.positions:
            kill_switch._execution_client.flatten_position.assert_any_call(
                symbol=position["symbol"],
                quantity=position["quantity"],
                order_type="MARKET",
                time_in_force="IOC"
            )

    @pytest.mark.asyncio
    async def test_per_bot_kill_cancels_pending_orders(self, kill_switch, mock_bot):
        """Test that per-bot kill switch cancels all pending orders."""
        # Setup
        kill_switch._execution_client.cancel_order = AsyncMock(return_value=True)
        kill_switch._db_session.query.return_value.filter.return_value.first.return_value = mock_bot

        # Act
        await kill_switch.activate_bot_kill(
            bot_id=mock_bot.id,
            reason="Test kill - cancel orders"
        )

        # Assert
        # Should cancel each pending order
        assert kill_switch.execution_client.cancel_order.call_count == len(mock_bot.pending_orders)

        # Verify correct orders were cancelled
        for order in mock_bot.pending_orders:
            kill_switch.execution_client.cancel_order.assert_any_call(
                order_id=order["id"]
            )

    @pytest.mark.asyncio
    async def test_per_bot_kill_sets_halted_status(self, kill_switch, mock_bot):
        """Test that per-bot kill switch sets bot status to HALTED."""
        # Setup
        kill_switch.db_session.query.return_value.filter.return_value.first.return_value = mock_bot
        kill_switch.execution_client.flatten_position = AsyncMock(return_value=True)
        kill_switch.execution_client.cancel_order = AsyncMock(return_value=True)

        # Act
        await kill_switch.activate_bot_kill(
            bot_id=mock_bot.id,
            reason="Test kill - set halted"
        )

        # Assert
        assert mock_bot.status == BotStatus.HALTED
        assert mock_bot.halted_at is not None
        assert mock_bot.halt_reason == "Test kill - set halted"
        assert mock_bot.kill_scope == "per_bot"
        kill_switch.db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_halted_bot_rejects_new_orders(self, kill_switch):
        """Test that a HALTED bot rejects any new orders."""
        # Setup
        mock_bot = Mock()
        mock_bot.id = "bot_halted_001"
        mock_bot.status = BotStatus.HALTED

        kill_switch.db_session.query.return_value.filter.return_value.first.return_value = mock_bot

        # Act & Assert
        with pytest.raises(Exception, match="Bot is HALTED"):
            await kill_switch.submit_order(
                bot_id=mock_bot.id,
                order={"symbol": "NQ", "quantity": 1, "side": "BUY"}
            )

    @pytest.mark.asyncio
    async def test_resume_requires_manual_action(self, kill_switch):
        """Test that resuming a HALTED bot requires explicit manual confirmation."""
        # Setup
        mock_bot = Mock()
        mock_bot.id = "bot_halted_002"
        mock_bot.status = BotStatus.HALTED
        mock_bot.halted_at = datetime.utcnow() - timedelta(minutes=5)

        kill_switch.db_session.query.return_value.filter.return_value.first.return_value = mock_bot

        # Act - Try to resume without confirmation
        with pytest.raises(Exception, match="Manual confirmation required"):
            await kill_switch.resume_bot(bot_id=mock_bot.id)

        # Act - Resume with confirmation
        await kill_switch.resume_bot(
            bot_id=mock_bot.id,
            manual_confirmation=True,
            confirmed_by="admin_user"
        )

        # Assert
        assert mock_bot.status == BotStatus.RUNNING
        assert mock_bot.halted_at is None
        assert mock_bot.halt_reason is None
        kill_switch.db_session.commit.assert_called()


class TestKillSwitchGlobal:
    """Tests for global kill switch functionality."""

    @pytest.fixture
    def kill_switch(self):
        """Create a KillSwitchActor instance."""
        mock_logger = Mock()
        mock_msgbus = Mock()
        mock_execution_client = Mock()
        mock_db_session = Mock()

        kill_switch = KillSwitchActor(
            logger=mock_logger,
            msgbus=mock_msgbus,
            execution_client=mock_execution_client,
            db_session=mock_db_session
        )
        return kill_switch

    @pytest.fixture
    def active_bots(self):
        """Create multiple active bot instances."""
        bots = []
        for i in range(3):
            bot = Mock(spec=BotInstance)
            bot.id = f"bot_active_{i:03d}"
            bot.status = BotStatus.RUNNING
            bot.positions = [{"symbol": "NQ", "quantity": 1, "side": "LONG"}]
            bot.pending_orders = [{"id": f"order_{i:03d}", "status": "PENDING"}]
            bots.append(bot)
        return bots

    @pytest.mark.asyncio
    async def test_global_kill_affects_all_active_bots(self, kill_switch, active_bots):
        """Test that global kill switch affects all active bots."""
        # Setup
        kill_switch.db_session.query.return_value.filter.return_value.all.return_value = active_bots
        kill_switch.execution_client.flatten_position = AsyncMock(return_value=True)
        kill_switch.execution_client.cancel_order = AsyncMock(return_value=True)

        # Act
        await kill_switch.activate_global_kill(reason="Emergency global kill")

        # Assert
        # All bots should be HALTED
        for bot in active_bots:
            assert bot.status == BotStatus.HALTED
            assert bot.halt_reason == "global_kill: Emergency global kill"
            assert bot.kill_scope == "global"

        # Verify positions flattened and orders cancelled for all bots
        expected_flatten_calls = sum(len(bot.positions) for bot in active_bots)
        expected_cancel_calls = sum(len(bot.pending_orders) for bot in active_bots)

        assert kill_switch.execution_client.flatten_position.call_count == expected_flatten_calls
        assert kill_switch.execution_client.cancel_order.call_count == expected_cancel_calls

    @pytest.mark.asyncio
    async def test_global_kill_ignores_already_stopped_bots(self, kill_switch):
        """Test that global kill ignores bots that are already stopped."""
        # Setup
        running_bot = Mock()
        running_bot.id = "bot_running"
        running_bot.status = BotStatus.RUNNING
        running_bot.positions = []
        running_bot.pending_orders = []

        stopped_bot = Mock()
        stopped_bot.id = "bot_stopped"
        stopped_bot.status = BotStatus.STOPPED
        stopped_bot.positions = []
        stopped_bot.pending_orders = []

        halted_bot = Mock()
        halted_bot.id = "bot_halted"
        halted_bot.status = BotStatus.HALTED
        halted_bot.positions = []
        halted_bot.pending_orders = []

        all_bots = [running_bot, stopped_bot, halted_bot]
        kill_switch.db_session.query.return_value.filter.return_value.all.return_value = [running_bot]
        kill_switch.execution_client.flatten_position = AsyncMock(return_value=True)

        # Act
        await kill_switch.activate_global_kill(reason="Global kill test")

        # Assert
        # Only running bot should be affected
        assert running_bot.status == BotStatus.HALTED
        assert stopped_bot.status == BotStatus.STOPPED  # Unchanged
        assert halted_bot.status == BotStatus.HALTED  # Unchanged


class TestCircuitBreakers:
    """Tests for circuit breaker functionality."""

    @pytest.fixture
    def circuit_breaker(self):
        """Create a CircuitBreaker instance."""
        import logging

        mock_logger = logging.getLogger(__name__)
        mock_kill_switch = Mock()
        mock_kill_switch.activate_bot_kill = AsyncMock()
        mock_kill_switch.get_bot_status = Mock(return_value=BotStatus.RUNNING)
        mock_db_session = Mock()

        return CircuitBreaker(
            logger=mock_logger,
            kill_switch_actor=mock_kill_switch,
            db_session=mock_db_session
        )

    @pytest.fixture
    def kill_switch(self):
        """Create a mock kill switch."""
        mock_kill_switch = Mock()
        mock_kill_switch.activate_bot_kill = AsyncMock()
        return mock_kill_switch

    @pytest.fixture
    def bot_config(self):
        """Create bot risk configuration."""
        return {
            "max_daily_loss": -1000.0,  # $1000 daily loss limit
            "max_consecutive_losses": 5,
            "trailing_threshold_buffer": 100.0,  # $100 buffer from trailing threshold
            "max_orders_per_minute": 10
        }

    @pytest.mark.asyncio
    async def test_circuit_breaker_daily_loss_triggers_kill(
        self, circuit_breaker, kill_switch, bot_config
    ):
        """Test that daily loss exceeding threshold triggers kill switch."""
        # Setup
        bot_id = "bot_loss_001"
        current_pnl = -1001.0  # Exceeds $1000 limit by $1

        circuit_breaker.kill_switch = kill_switch

        # Act
        should_kill = await circuit_breaker.check_daily_loss(
            bot_id=bot_id,
            current_pnl=current_pnl,
            config=bot_config
        )

        # Assert
        assert should_kill is True
        kill_switch.activate_bot_kill.assert_called_once_with(
            bot_id=bot_id,
            reason="Circuit breaker: max_daily_loss exceeded (-1001.00 < -1000.00)"
        )

    @pytest.mark.asyncio
    async def test_circuit_breaker_consecutive_losses(
        self, circuit_breaker, kill_switch, bot_config
    ):
        """Test that consecutive losses trigger kill switch."""
        # Setup
        bot_id = "bot_streak_001"
        loss_streak = 6  # Exceeds limit of 5

        circuit_breaker.kill_switch = kill_switch

        # Act
        should_kill = await circuit_breaker.check_consecutive_losses(
            bot_id=bot_id,
            loss_streak=loss_streak,
            config=bot_config
        )

        # Assert
        assert should_kill is True
        kill_switch.activate_bot_kill.assert_called_once_with(
            bot_id=bot_id,
            reason="Circuit breaker: max_consecutive_losses exceeded (6 > 5)"
        )

    @pytest.mark.asyncio
    async def test_circuit_breaker_trailing_threshold_proximity(
        self, circuit_breaker, kill_switch, bot_config
    ):
        """Test that proximity to trailing threshold triggers kill switch."""
        # Setup
        bot_id = "bot_trailing_001"
        current_balance = 25099.0  # $25,099
        trailing_threshold = 25000.0  # $25,000 trailing threshold
        # Within $100 buffer ($99 from threshold)

        circuit_breaker.kill_switch = kill_switch

        # Act
        should_kill = await circuit_breaker.check_trailing_threshold(
            bot_id=bot_id,
            balance=current_balance,
            trailing_threshold=trailing_threshold,
            config=bot_config
        )

        # Assert
        assert should_kill is True
        kill_switch.activate_bot_kill.assert_called_once_with(
            bot_id=bot_id,
            reason="Circuit breaker: within trailing_threshold buffer (99.00 < 100.00)"
        )

    @pytest.mark.asyncio
    async def test_circuit_breaker_runaway_orders(
        self, circuit_breaker, kill_switch, bot_config
    ):
        """Test that excessive order frequency triggers kill switch."""
        # Setup
        bot_id = "bot_runaway_001"
        orders_last_minute = 11  # Exceeds limit of 10

        circuit_breaker.kill_switch = kill_switch

        # Act
        should_kill = await circuit_breaker.check_order_frequency(
            bot_id=bot_id,
            orders_last_minute=orders_last_minute,
            config=bot_config
        )

        # Assert
        assert should_kill is True
        kill_switch.activate_bot_kill.assert_called_once_with(
            bot_id=bot_id,
            reason="Circuit breaker: runaway detected (11 orders/min > 10)"
        )

    @pytest.mark.asyncio
    async def test_circuit_breaker_boundary_exactly_at_threshold(
        self, circuit_breaker, kill_switch, bot_config
    ):
        """Test boundary conditions at exactly the threshold (±1 tick)."""
        circuit_breaker.kill_switch = kill_switch
        bot_id = "bot_boundary_001"

        # Test 1: Exactly at daily loss threshold
        current_pnl = -1000.0  # Exactly at limit
        should_kill = await circuit_breaker.check_daily_loss(
            bot_id=bot_id,
            current_pnl=current_pnl,
            config=bot_config
        )
        assert should_kill is False  # Should not trigger at exact threshold

        # Test 2: One tick beyond daily loss threshold
        current_pnl = -1000.0 - NQ_TICK_VALUE  # $1005 loss
        should_kill = await circuit_breaker.check_daily_loss(
            bot_id=bot_id,
            current_pnl=current_pnl,
            config=bot_config
        )
        assert should_kill is True  # Should trigger

        # Test 3: One tick before daily loss threshold
        current_pnl = -1000.0 + NQ_TICK_VALUE  # $995 loss
        should_kill = await circuit_breaker.check_daily_loss(
            bot_id=bot_id,
            current_pnl=current_pnl,
            config=bot_config
        )
        assert should_kill is False  # Should not trigger

        # Test 4: Exactly at consecutive losses threshold
        loss_streak = 5  # Exactly at limit
        should_kill = await circuit_breaker.check_consecutive_losses(
            bot_id=bot_id,
            loss_streak=loss_streak,
            config=bot_config
        )
        assert should_kill is False  # Should not trigger at exact threshold

        # Test 5: One beyond consecutive losses threshold
        loss_streak = 6
        should_kill = await circuit_breaker.check_consecutive_losses(
            bot_id=bot_id,
            loss_streak=loss_streak,
            config=bot_config
        )
        assert should_kill is True  # Should trigger

    @pytest.mark.asyncio
    async def test_no_duplicate_kill_if_already_halted(
        self, circuit_breaker, kill_switch
    ):
        """Test that circuit breaker is idempotent - no duplicate kill if already HALTED."""
        # Setup
        bot_id = "bot_halted_003"
        mock_bot = Mock()
        mock_bot.id = bot_id
        mock_bot.status = BotStatus.HALTED  # Already halted

        circuit_breaker.kill_switch = kill_switch
        circuit_breaker.get_bot_status = Mock(return_value=BotStatus.HALTED)

        bot_config = {
            "max_daily_loss": -1000.0,
            "max_consecutive_losses": 5
        }

        # Act - Try to trigger multiple circuit breakers
        await circuit_breaker.check_daily_loss(
            bot_id=bot_id,
            current_pnl=-2000.0,  # Way over limit
            config=bot_config
        )

        await circuit_breaker.check_consecutive_losses(
            bot_id=bot_id,
            loss_streak=10,  # Way over limit
            config=bot_config
        )

        # Assert - Kill switch should NOT be called since bot is already HALTED
        kill_switch.activate_bot_kill.assert_not_called()


class TestConcurrency:
    """Tests for concurrency and idempotency."""

    @pytest.fixture
    def kill_switch(self):
        """Create a thread-safe KillSwitchActor instance."""
        mock_logger = Mock()
        mock_msgbus = Mock()
        mock_execution_client = Mock()
        mock_db_session = Mock()

        kill_switch = KillSwitchActor(
            logger=mock_logger,
            msgbus=mock_msgbus,
            execution_client=mock_execution_client,
            db_session=mock_db_session
        )
        kill_switch._lock = threading.Lock()
        kill_switch._killed_bots = set()  # Track killed bots for idempotency
        return kill_switch

    @pytest.mark.asyncio
    async def test_concurrent_kill_signals_idempotent(self, kill_switch):
        """Test that multiple concurrent kill signals are idempotent."""
        # Setup
        bot_id = "bot_concurrent_001"
        mock_bot = Mock()
        mock_bot.id = bot_id
        mock_bot.status = BotStatus.RUNNING
        mock_bot.positions = [{"symbol": "NQ", "quantity": 1, "side": "LONG"}]
        mock_bot.pending_orders = []

        kill_switch.db_session.query.return_value.filter.return_value.first.return_value = mock_bot
        kill_switch.execution_client.flatten_position = AsyncMock(return_value=True)

        # Track actual kill executions
        kill_executions = []

        async def track_kill(*args, **kwargs):
            """Track kill executions."""
            kill_executions.append(datetime.utcnow())
            # Simulate some processing time
            await asyncio.sleep(0.01)
            return True

        kill_switch._execute_kill = track_kill

        # Act - Send multiple concurrent kill signals
        tasks = []
        for i in range(10):
            task = asyncio.create_task(
                kill_switch.activate_bot_kill(
                    bot_id=bot_id,
                    reason=f"Concurrent kill test {i}"
                )
            )
            tasks.append(task)

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

        # Assert - Only one kill should have been executed
        assert len(kill_executions) == 1
        assert bot_id in kill_switch._killed_bots

    def test_thread_safe_kill_switch(self, kill_switch):
        """Test that kill switch operations are thread-safe."""
        # Setup
        bot_id = "bot_threadsafe_001"
        execution_count = {"flatten": 0, "cancel": 0}

        def mock_flatten():
            """Mock flatten with counter."""
            execution_count["flatten"] += 1
            return True

        def mock_cancel():
            """Mock cancel with counter."""
            execution_count["cancel"] += 1
            return True

        kill_switch._flatten_positions_sync = mock_flatten
        kill_switch._cancel_orders_sync = mock_cancel

        # Act - Multiple threads trying to kill the same bot
        def attempt_kill(thread_id):
            """Thread function to attempt kill."""
            asyncio.run(kill_switch.activate_bot_kill(
                bot_id=bot_id,
                reason=f"Thread {thread_id} kill"
            ))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(attempt_kill, i) for i in range(10)]
            for future in futures:
                future.result()

        # Assert - Operations should only execute once despite multiple threads
        assert execution_count["flatten"] == 1
        assert execution_count["cancel"] == 1


class TestKillSwitchEvents:
    """Tests for kill switch event logging and publishing."""

    @pytest.fixture
    def kill_switch(self):
        """Create a KillSwitchActor with event tracking."""
        mock_logger = Mock()
        mock_msgbus = Mock()
        mock_execution_client = Mock()
        mock_db_session = Mock()

        kill_switch = KillSwitchActor(
            logger=mock_logger,
            msgbus=mock_msgbus,
            execution_client=mock_execution_client,
            db_session=mock_db_session
        )
        return kill_switch

    @pytest.mark.asyncio
    async def test_kill_event_published_to_message_bus(self, kill_switch):
        """Test that kill switch events are published to message bus with priority 0."""
        # Setup
        bot_id = "bot_event_001"
        reason = "Test event publishing"

        mock_bot = Mock()
        mock_bot.id = bot_id
        mock_bot.status = BotStatus.RUNNING
        mock_bot.positions = []
        mock_bot.pending_orders = []

        kill_switch.db_session.query.return_value.filter.return_value.first.return_value = mock_bot

        # Act
        await kill_switch.activate_bot_kill(bot_id=bot_id, reason=reason)

        # Assert
        kill_switch.msgbus.publish.assert_called()

        # Get the published event
        call_args = kill_switch.msgbus.publish.call_args
        event = call_args[0][0]  # First positional argument
        priority = call_args[1].get("priority", None)  # Keyword argument

        # Verify event properties
        assert isinstance(event, KillSwitchEvent)
        assert event.bot_id == bot_id
        assert event.reason == reason
        assert event.scope == "per_bot"
        assert priority == 0  # Maximum priority

    @pytest.mark.asyncio
    async def test_kill_event_logged_to_database(self, kill_switch):
        """Test that kill switch events are logged to database."""
        # Setup
        bot_id = "bot_log_001"
        reason = "Test database logging"

        mock_bot = Mock()
        mock_bot.id = bot_id
        mock_bot.status = BotStatus.RUNNING
        mock_bot.positions = [{"symbol": "NQ", "quantity": 2}]
        mock_bot.pending_orders = [{"id": "order_001"}]

        kill_switch.db_session.query.return_value.filter.return_value.first.return_value = mock_bot
        kill_switch.execution_client.flatten_position = AsyncMock(return_value=True)
        kill_switch.execution_client.cancel_order = AsyncMock(return_value=True)

        # Mock the event logging
        mock_event_record = Mock()
        kill_switch.db_session.add = Mock()

        # Act
        await kill_switch.activate_bot_kill(bot_id=bot_id, reason=reason)

        # Assert - Event should be logged to database
        # Check that an event record was created and added to session
        assert kill_switch.db_session.add.called
        assert kill_switch.db_session.commit.called

        # Verify the event record properties
        event_record = kill_switch.db_session.add.call_args[0][0]
        assert event_record.bot_id == bot_id
        assert event_record.reason == reason
        assert event_record.scope == "per_bot"
        assert event_record.triggered_by == "manual"
        assert event_record.positions_closed == 1  # Number of positions
        assert event_record.orders_cancelled == 1  # Number of orders


class TestNQSpecificScenarios:
    """Tests specific to NQ futures trading scenarios."""

    @pytest.fixture
    def kill_switch(self):
        """Create a KillSwitchActor for NQ testing."""
        mock_logger = Mock()
        mock_msgbus = Mock()
        mock_execution_client = Mock()
        mock_db_session = Mock()

        kill_switch = KillSwitchActor(
            logger=mock_logger,
            msgbus=mock_msgbus,
            execution_client=mock_execution_client,
            db_session=mock_db_session
        )
        return kill_switch

    @pytest.mark.asyncio
    async def test_nq_position_flatten_at_market(self, kill_switch):
        """Test that NQ positions are flattened with market orders (no limit orders)."""
        # Setup
        bot_id = "bot_nq_001"
        mock_bot = Mock()
        mock_bot.id = bot_id
        mock_bot.status = BotStatus.RUNNING

        # NQ position: 2 contracts long at 15000.00
        mock_bot.positions = [{
            "symbol": "NQ",
            "quantity": 2,
            "side": "LONG",
            "entry_price": 15000.00
        }]
        mock_bot.pending_orders = []

        kill_switch.db_session.query.return_value.filter.return_value.first.return_value = mock_bot
        kill_switch.execution_client.flatten_position = AsyncMock(return_value=True)

        # Act
        await kill_switch.activate_bot_kill(bot_id=bot_id, reason="NQ flatten test")

        # Assert - Should use market order, not limit order
        kill_switch.execution_client.flatten_position.assert_called_once()
        call_args = kill_switch.execution_client.flatten_position.call_args[1]

        assert call_args["order_type"] == "MARKET"
        assert "limit_price" not in call_args or call_args["limit_price"] is None
        assert call_args["time_in_force"] == "IOC"  # Immediate or cancel

    @pytest.mark.asyncio
    async def test_nq_tick_precision_in_pnl_calculation(self, circuit_breaker):
        """Test that P&L calculations respect NQ tick size (0.25)."""
        # Setup
        bot_id = "bot_nq_002"

        # P&L should be rounded to nearest tick value
        # 1 tick = $5, so P&L should be in $5 increments
        test_cases = [
            (-997.50, False),  # -199.5 ticks * $5 = -$997.50 (valid)
            (-1000.00, False),  # -200 ticks * $5 = -$1000.00 (at limit)
            (-1002.50, True),   # -200.5 ticks * $5 = -$1002.50 (exceeds)
            (-1001.25, None),   # Invalid - not a multiple of tick value
        ]

        bot_config = {"max_daily_loss": -1000.0}

        for pnl, should_trigger in test_cases:
            if should_trigger is None:
                # Invalid P&L value
                with pytest.raises(ValueError, match="Invalid P&L"):
                    await circuit_breaker.check_daily_loss(
                        bot_id=bot_id,
                        current_pnl=pnl,
                        config=bot_config
                    )
            else:
                result = await circuit_breaker.check_daily_loss(
                    bot_id=bot_id,
                    current_pnl=pnl,
                    config=bot_config
                )
                assert result == should_trigger