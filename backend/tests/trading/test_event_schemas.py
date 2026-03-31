"""
Tests for Event Bus schemas.
Verifies JSON serialization and channel configuration for all event types.
"""
import json
import pytest
from datetime import datetime, timezone
from decimal import Decimal


class TestEventSchemas:
    """Test suite for Event Bus schemas."""

    def test_candle_event_serializes_to_json(self):
        """Test that CandleEvent serializes correctly to JSON."""
        from app.trading.events.schemas import CandleEvent

        event = CandleEvent(
            channel="nqhub.candle.1min",
            ts=datetime(2026, 3, 31, 14, 30, 0, tzinfo=timezone.utc),
            bot_id="bot-001",
            timeframe="1min",
            open=19250.25,
            high=19255.00,
            low=19248.50,
            close=19252.75,
            volume=1234,
            delta=45,
            poc=19251.50
        )

        # Should serialize to JSON without errors
        json_str = event.model_dump_json()
        data = json.loads(json_str)

        assert data["channel"] == "nqhub.candle.1min"
        assert data["bot_id"] == "bot-001"
        assert data["timeframe"] == "1min"
        assert data["open"] == 19250.25
        assert data["high"] == 19255.00
        assert data["low"] == 19248.50
        assert data["close"] == 19252.75
        assert data["volume"] == 1234
        assert data["delta"] == 45
        assert data["poc"] == 19251.50
        assert "ts" in data

    def test_kill_switch_event_has_correct_channel(self):
        """Test that KillSwitchEvent has the correct high-priority channel."""
        from app.trading.events.schemas import KillSwitchEvent

        event = KillSwitchEvent(
            channel="nqhub.risk.kill_switch",
            ts=datetime(2026, 3, 31, 14, 30, 0, tzinfo=timezone.utc),
            bot_id="bot-001",
            scope="per_bot",
            reason="trailing_threshold_breach",
            triggered_by="circuit_breaker",
            positions_closed=2,
            orders_cancelled=3
        )

        # Kill switch events must use the high-priority channel
        assert event.channel == "nqhub.risk.kill_switch"
        assert event.scope in ["per_bot", "global"]
        assert event.triggered_by in ["manual", "circuit_breaker"]
        assert event.positions_closed == 2
        assert event.orders_cancelled == 3

    def test_order_event_filled_status(self):
        """Test OrderEvent with FILLED status."""
        from app.trading.events.schemas import OrderEvent

        event = OrderEvent(
            channel="exec.order.filled",
            ts=datetime(2026, 3, 31, 14, 30, 0, tzinfo=timezone.utc),
            bot_id="bot-001",
            order_id="uuid-here",
            client_order_id="nqhub-uuid",
            broker_order_id="rithmic-123",
            bracket_role="ENTRY",
            side="BUY",
            contracts=2,
            fill_price=19252.75,
            status="FILLED"
        )

        assert event.channel == "exec.order.filled"
        assert event.status == "FILLED"
        assert event.fill_price == 19252.75
        assert event.contracts == 2
        assert event.side == "BUY"
        assert event.bracket_role == "ENTRY"

        # Test that fill_price can be None for non-filled orders
        pending_event = OrderEvent(
            channel="exec.order.submitted",
            ts=datetime.utcnow(),
            bot_id="bot-001",
            order_id="uuid-2",
            client_order_id="nqhub-uuid-2",
            broker_order_id=None,  # No broker ID yet
            bracket_role=None,
            side="SELL",
            contracts=1,
            fill_price=None,  # No fill price for submitted order
            status="SUBMITTED"
        )

        assert pending_event.fill_price is None
        assert pending_event.broker_order_id is None

    def test_position_event_pnl_calculation(self):
        """Test PositionEvent PNL calculation with NQ constants."""
        from app.trading.events.schemas import PositionEvent

        # NQ constants
        tick_size = 0.25
        tick_value = 5.00

        entry_price = 19252.75
        current_price = 19255.00
        contracts = 2

        # Calculate PNL
        price_diff = current_price - entry_price  # 2.25
        ticks = price_diff / tick_size  # 9 ticks
        unrealized_pnl = ticks * tick_value * contracts  # 9 * 5 * 2 = 90.00

        event = PositionEvent(
            channel="exec.position.update",
            ts=datetime(2026, 3, 31, 14, 30, 0, tzinfo=timezone.utc),
            bot_id="bot-001",
            symbol="NQ",
            side="LONG",
            contracts=contracts,
            entry_price=entry_price,
            current_price=current_price,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_ticks=ticks
        )

        assert event.unrealized_pnl == 90.00
        assert event.unrealized_pnl_ticks == 9

        # Test SHORT position (PNL calculation reversed)
        short_event = PositionEvent(
            channel="exec.position.update",
            ts=datetime(2026, 3, 31, 14, 30, 0, tzinfo=timezone.utc),
            bot_id="bot-001",
            symbol="NQ",
            side="SHORT",
            contracts=1,
            entry_price=19255.00,
            current_price=19252.75,
            unrealized_pnl=45.00,  # (19255 - 19252.75) / 0.25 * 5 * 1 = 45.00
            unrealized_pnl_ticks=9
        )

        assert short_event.unrealized_pnl == 45.00
        assert short_event.unrealized_pnl_ticks == 9

    def test_all_events_have_ts_and_bot_id(self):
        """Test that all event types have timestamp and bot_id fields."""
        from app.trading.events.schemas import (
            CandleEvent, PatternEvent, RiskCheckEvent,
            KillSwitchEvent, OrderEvent, PositionEvent
        )

        ts = datetime(2026, 3, 31, 14, 30, 0, tzinfo=timezone.utc)
        bot_id = "bot-001"

        # Test CandleEvent
        candle = CandleEvent(
            channel="nqhub.candle.1min",
            ts=ts,
            bot_id=bot_id,
            timeframe="1min",
            open=19250.25,
            high=19255.00,
            low=19248.50,
            close=19252.75,
            volume=1234,
            delta=45,
            poc=19251.50
        )
        assert candle.ts == ts
        assert candle.bot_id == bot_id

        # Test PatternEvent
        pattern = PatternEvent(
            channel="nqhub.pattern.fvg",
            ts=ts,
            bot_id=bot_id,
            pattern_type="fvg",
            direction="bullish",
            top=19255.00,
            bottom=19248.50,
            timeframe="5min",
            status="active"
        )
        assert pattern.ts == ts
        assert pattern.bot_id == bot_id

        # Test RiskCheckEvent
        risk = RiskCheckEvent(
            channel="nqhub.risk.check",
            ts=ts,
            bot_id=bot_id,
            check_name="trailing_threshold_check",
            result="REJECTED",
            reason="Balance too close to trailing threshold",
            trigger_kill_switch=False,
            account_balance=24100.00,
            current_pnl=-850.00
        )
        assert risk.ts == ts
        assert risk.bot_id == bot_id

        # Test KillSwitchEvent
        kill_switch = KillSwitchEvent(
            channel="nqhub.risk.kill_switch",
            ts=ts,
            bot_id=bot_id,
            scope="per_bot",
            reason="trailing_threshold_breach",
            triggered_by="circuit_breaker",
            positions_closed=2,
            orders_cancelled=3
        )
        assert kill_switch.ts == ts
        assert kill_switch.bot_id == bot_id

        # Test OrderEvent
        order = OrderEvent(
            channel="exec.order.filled",
            ts=ts,
            bot_id=bot_id,
            order_id="uuid-here",
            client_order_id="nqhub-uuid",
            broker_order_id="rithmic-123",
            bracket_role="ENTRY",
            side="BUY",
            contracts=2,
            fill_price=19252.75,
            status="FILLED"
        )
        assert order.ts == ts
        assert order.bot_id == bot_id

        # Test PositionEvent
        position = PositionEvent(
            channel="exec.position.update",
            ts=ts,
            bot_id=bot_id,
            symbol="NQ",
            side="LONG",
            contracts=2,
            entry_price=19252.75,
            current_price=19255.00,
            unrealized_pnl=90.00,
            unrealized_pnl_ticks=9
        )
        assert position.ts == ts
        assert position.bot_id == bot_id

    def test_risk_check_event_trigger_kill_switch_false_by_default(self):
        """Test that RiskCheckEvent has trigger_kill_switch=False by default."""
        from app.trading.events.schemas import RiskCheckEvent

        # Create event without specifying trigger_kill_switch
        event = RiskCheckEvent(
            channel="nqhub.risk.check",
            ts=datetime(2026, 3, 31, 14, 30, 0, tzinfo=timezone.utc),
            bot_id="bot-001",
            check_name="max_position_check",
            result="PASSED",
            reason="",  # Empty reason for passed check
            # trigger_kill_switch not specified - should default to False
            account_balance=25000.00,
            current_pnl=150.00
        )

        # Default should be False
        assert event.trigger_kill_switch is False

        # Verify it can be set to True when needed
        critical_event = RiskCheckEvent(
            channel="nqhub.risk.check",
            ts=datetime(2026, 3, 31, 14, 30, 0, tzinfo=timezone.utc),
            bot_id="bot-001",
            check_name="critical_loss_check",
            result="REJECTED",
            reason="Critical loss threshold exceeded",
            trigger_kill_switch=True,  # Explicitly set to True
            account_balance=20000.00,
            current_pnl=-5000.00
        )

        assert critical_event.trigger_kill_switch is True
        assert critical_event.result == "REJECTED"

    def test_pattern_event_types(self):
        """Test PatternEvent with different pattern types."""
        from app.trading.events.schemas import PatternEvent

        # Test FVG pattern
        fvg = PatternEvent(
            channel="nqhub.pattern.fvg",
            ts=datetime.utcnow(),
            bot_id="bot-001",
            pattern_type="fvg",
            direction="bearish",
            top=19260.00,
            bottom=19255.00,
            timeframe="15min",
            status="active"
        )
        assert fvg.pattern_type == "fvg"
        assert fvg.direction == "bearish"

        # Test Order Block pattern
        ob = PatternEvent(
            channel="nqhub.pattern.ob",
            ts=datetime.utcnow(),
            bot_id="bot-001",
            pattern_type="ob",
            direction="bullish",
            top=19250.00,
            bottom=19245.00,
            timeframe="1h",
            status="mitigated"
        )
        assert ob.pattern_type == "ob"
        assert ob.status == "mitigated"

        # Test Liquidity Pool pattern
        lp = PatternEvent(
            channel="nqhub.pattern.lp",
            ts=datetime.utcnow(),
            bot_id="bot-001",
            pattern_type="lp",
            direction="bullish",
            top=19280.00,
            bottom=19275.00,
            timeframe="4h",
            status="broken"
        )
        assert lp.pattern_type == "lp"
        assert lp.status == "broken"

    def test_order_event_bracket_roles(self):
        """Test OrderEvent with different bracket roles."""
        from app.trading.events.schemas import OrderEvent

        ts = datetime.utcnow()

        # Entry order
        entry = OrderEvent(
            channel="exec.order.submitted",
            ts=ts,
            bot_id="bot-001",
            order_id="entry-001",
            client_order_id="nqhub-entry-001",
            broker_order_id=None,
            bracket_role="ENTRY",
            side="BUY",
            contracts=2,
            fill_price=None,
            status="SUBMITTED"
        )
        assert entry.bracket_role == "ENTRY"

        # Take Profit order
        tp = OrderEvent(
            channel="exec.order.submitted",
            ts=ts,
            bot_id="bot-001",
            order_id="tp-001",
            client_order_id="nqhub-tp-001",
            broker_order_id=None,
            bracket_role="TP",
            side="SELL",
            contracts=2,
            fill_price=None,
            status="SUBMITTED"
        )
        assert tp.bracket_role == "TP"

        # Stop Loss order
        sl = OrderEvent(
            channel="exec.order.submitted",
            ts=ts,
            bot_id="bot-001",
            order_id="sl-001",
            client_order_id="nqhub-sl-001",
            broker_order_id=None,
            bracket_role="SL",
            side="SELL",
            contracts=2,
            fill_price=None,
            status="SUBMITTED"
        )
        assert sl.bracket_role == "SL"