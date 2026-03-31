"""
Base Strategy class for NQHUB trading system.
"""
from decimal import Decimal
from typing import Optional
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.trading.strategy import StrategyConfig
from nautilus_trader.model.data import Bar, TradeTick


<<<<<<< HEAD
class NQHubStrategyConfig(StrategyConfig, kw_only=True):
=======
class NQHubStrategyConfig(StrategyConfig):
>>>>>>> 1ee3282 (feat(AUT-336): Implement VectorBT Pro backtesting engine with Celery workers)
    """Configuration for NQHubStrategy."""
    strategy_id: str  # FK to strategies table
    bot_id: str
    risk_config: dict


class NQHubStrategy(Strategy):
    """
    Base class for all NQHUB Strategies.

    This class extends the NautilusTrader Strategy to provide
    common functionality for all NQHUB trading strategies.
    Subclasses: RuleBasedStrategy, MLStrategy, RLStrategy.

    NQ Futures Constants:
    - Tick Size: 0.25 points
    - Tick Value: $5.00 per tick
    - Point Value: $20.00 per point (4 ticks per point)
    """

    # NQ Futures contract specifications
    TICK_SIZE = Decimal("0.25")
    TICK_VALUE = Decimal("5.00")
    POINT_VALUE = Decimal("20.00")

    def __init__(self, config: NQHubStrategyConfig):
        """
        Initialize NQHubStrategy.

        Args:
            config: Strategy configuration including bot_id and risk_config
        """
        super().__init__(config)
        self.bot_id = config.bot_id
        self.strategy_id = config.strategy_id
        self.risk_config = config.risk_config
<<<<<<< HEAD

    def on_start(self) -> None:
        """Called when the strategy starts."""
=======
        self.is_running = False

    def on_start(self) -> None:
        """Called when the strategy starts."""
        self.is_running = True
>>>>>>> 1ee3282 (feat(AUT-336): Implement VectorBT Pro backtesting engine with Celery workers)
        self.log.info(f"Starting strategy {self.strategy_id} for bot {self.bot_id}")

    def on_stop(self) -> None:
        """Called when the strategy stops."""
<<<<<<< HEAD
=======
        self.is_running = False
>>>>>>> 1ee3282 (feat(AUT-336): Implement VectorBT Pro backtesting engine with Celery workers)
        self.log.info(f"Stopping strategy {self.strategy_id} for bot {self.bot_id}")

    def on_bar(self, bar: Bar) -> None:
        """
        Handle bar data.

        Args:
            bar: Bar data from the market
        """
        # Base implementation - subclasses should override
        pass

    def on_trade_tick(self, tick: TradeTick) -> None:
        """
        Handle trade tick data.

        Args:
            tick: Trade tick data from the market
        """
        # Base implementation - subclasses should override
        pass