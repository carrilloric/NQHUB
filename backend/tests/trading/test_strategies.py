"""
Tests for NQHubStrategy base class.
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from decimal import Decimal
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import TradeTick
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.core.datetime import millis_to_nanos


class TestNQHubStrategy:
    """Tests for NQHubStrategy base class."""

    def test_nqhub_strategy_lifecycle(self):
        """Test strategy lifecycle: on_start / on_stop / on_bar."""
        from app.trading.strategies.base import NQHubStrategy, NQHubStrategyConfig

        # Create config
        config = NQHubStrategyConfig(
            strategy_id="test-strategy-001",
            bot_id="test-bot-001",
            risk_config={
                "max_position_size": 5,
                "max_daily_loss": 1000,
                "trailing_drawdown_pct": 0.8
            }
        )

        # Create strategy
        strategy = NQHubStrategy(config)

        # Test initialization
        assert strategy.bot_id == "test-bot-001"
        assert strategy.strategy_id == "test-strategy-001"
        assert strategy.risk_config["max_position_size"] == 5

        # Test lifecycle methods exist
        assert hasattr(strategy, "on_start")
        assert hasattr(strategy, "on_stop")
        assert hasattr(strategy, "on_bar")
        assert hasattr(strategy, "on_trade_tick")

        # Test on_start
        strategy.on_start()
        assert strategy.is_running

        # Test on_stop
        strategy.on_stop()
        assert not strategy.is_running

    def test_nqhub_strategy_handles_bar_data(self):
        """Test strategy handles bar data correctly."""
        from app.trading.strategies.base import NQHubStrategy, NQHubStrategyConfig

        config = NQHubStrategyConfig(
            strategy_id="test-strategy-002",
            bot_id="test-bot-002",
            risk_config={}
        )

        strategy = NQHubStrategy(config)

        # Create mock bar data for NQ futures
        instrument_id = InstrumentId(Symbol("NQ"), Venue("CME"))
        bar = Bar(
            bar_type="NQ.CME-1-MINUTE-BID",
            open=Price(15000.25, precision=2),
            high=Price(15005.50, precision=2),
            low=Price(14995.75, precision=2),
            close=Price(15002.00, precision=2),
            volume=Quantity(1000, precision=0),
            ts_event=millis_to_nanos(int(datetime.now().timestamp() * 1000)),
            ts_init=millis_to_nanos(int(datetime.now().timestamp() * 1000))
        )

        # Process bar
        strategy.on_bar(bar)

        # Verify NQ constants
        assert strategy.TICK_SIZE == Decimal("0.25")
        assert strategy.TICK_VALUE == Decimal("5.00")
        assert strategy.POINT_VALUE == Decimal("20.00")

    def test_nqhub_strategy_handles_trade_tick(self):
        """Test strategy handles trade tick data correctly."""
        from app.trading.strategies.base import NQHubStrategy, NQHubStrategyConfig

        config = NQHubStrategyConfig(
            strategy_id="test-strategy-003",
            bot_id="test-bot-003",
            risk_config={}
        )

        strategy = NQHubStrategy(config)

        # Create mock trade tick
        instrument_id = InstrumentId(Symbol("NQ"), Venue("CME"))
        tick = TradeTick(
            instrument_id=instrument_id,
            price=Price(15000.50, precision=2),
            size=Quantity(10, precision=0),
            aggressor_side=1,  # BUY
            trade_id="123456",
            ts_event=millis_to_nanos(int(datetime.now().timestamp() * 1000)),
            ts_init=millis_to_nanos(int(datetime.now().timestamp() * 1000))
        )

        # Process tick
        strategy.on_trade_tick(tick)

    def test_nqhub_strategy_inheritance(self):
        """Test that NQHubStrategy can be properly inherited."""
        from app.trading.strategies.base import NQHubStrategy, NQHubStrategyConfig

        class TestStrategy(NQHubStrategy):
            def __init__(self, config):
                super().__init__(config)
                self.bar_count = 0

            def on_bar(self, bar):
                super().on_bar(bar)
                self.bar_count += 1

        config = NQHubStrategyConfig(
            strategy_id="test-strategy-004",
            bot_id="test-bot-004",
            risk_config={}
        )

        strategy = TestStrategy(config)

        # Test inherited properties
        assert strategy.bot_id == "test-bot-004"
        assert strategy.strategy_id == "test-strategy-004"
        assert strategy.bar_count == 0

        # Create mock bar
        instrument_id = InstrumentId(Symbol("NQ"), Venue("CME"))
        bar = Bar(
            bar_type="NQ.CME-1-MINUTE-BID",
            open=Price(15000.25, precision=2),
            high=Price(15005.50, precision=2),
            low=Price(14995.75, precision=2),
            close=Price(15002.00, precision=2),
            volume=Quantity(1000, precision=0),
            ts_event=millis_to_nanos(int(datetime.now().timestamp() * 1000)),
            ts_init=millis_to_nanos(int(datetime.now().timestamp() * 1000))
        )

        strategy.on_bar(bar)
        assert strategy.bar_count == 1