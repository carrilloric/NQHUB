"""
NQHubStrategy Abstract Base Class

Core contract for all trading strategies in NQHUB.

Every strategy must implement:
- required_features() → List of feature names needed from MarketState
- generate_signals() → pd.Series with 1 (long), 0 (flat), -1 (short)
- position_size() → Position sizing logic

Reference: ADR-021 Strategy Framework
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import pandas as pd
import numpy as np

from app.research.market_state import MarketState


@dataclass
class StrategyMetadata:
    """
    Metadata about a strategy.

    Used for registration, discovery, and documentation.
    """
    name: str
    description: str
    version: str
    author: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    strategy_type: str = "unknown"  # rule_based, ml, rl, hybrid

    # Performance targets (optional)
    target_sharpe: Optional[float] = None
    target_win_rate: Optional[float] = None
    max_drawdown_tolerance: Optional[float] = None

    # Resource requirements (optional)
    requires_gpu: bool = False
    min_memory_gb: Optional[float] = None

    # Additional metadata
    tags: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)


class NQHubStrategy(ABC):
    """
    Abstract base class for all NQHUB trading strategies.

    This class defines the contract that all strategies must implement.
    Strategies can be:
    - Rule-based: Pure algorithmic rules (RuleBasedStrategy)
    - ML-based: Machine learning models (MLStrategy)
    - RL-based: Reinforcement learning agents (RLStrategy)
    - Hybrid: Combination of rules + ML/RL (HybridStrategy)

    Contract:
    1. required_features() - Declare what features the strategy needs
    2. generate_signals() - Generate trading signals (1/0/-1)
    3. position_size() - Calculate position size for each signal

    Usage:
        class MyStrategy(RuleBasedStrategy):
            def required_features(self) -> List[str]:
                return ["active_fvgs", "bias", "session"]

            def generate_signals(self, market_state: MarketState) -> pd.Series:
                # Your signal generation logic
                return pd.Series([1, 0, -1, ...])

            def position_size(self, signal: int, market_state: MarketState) -> float:
                # Your position sizing logic
                return 1.0 if signal != 0 else 0.0
    """

    def __init__(self, metadata: StrategyMetadata, **kwargs):
        """
        Initialize strategy with metadata.

        Args:
            metadata: Strategy metadata (name, description, version, etc.)
            **kwargs: Additional strategy-specific parameters
        """
        self.metadata = metadata
        self.params = kwargs
        self.is_fitted = False  # For ML/RL strategies
        self.performance_history: List[Dict[str, Any]] = []

    @abstractmethod
    def required_features(self) -> List[str]:
        """
        Declare which features from MarketState this strategy needs.

        Feature names can be:
        - "active_fvgs" - FVG patterns by timeframe
        - "active_obs" - Order Block patterns by timeframe
        - "bias" - Market bias by timeframe
        - "key_levels" - Support/resistance levels
        - "session" - Current trading session
        - Custom features from indicators or ML models

        Returns:
            List of feature names required by the strategy

        Example:
            return ["active_fvgs", "bias", "session"]
        """
        pass

    @abstractmethod
    def generate_signals(self, market_state: MarketState, data: Optional[pd.DataFrame] = None) -> pd.Series:
        """
        Generate trading signals based on current market state.

        Signal values:
        - 1: Long (buy)
        - 0: Flat (no position)
        - -1: Short (sell)

        Args:
            market_state: Current MarketState snapshot with patterns and bias
            data: Optional OHLCV data for technical analysis
                  Index should be datetime, columns: open, high, low, close, volume

        Returns:
            pd.Series with datetime index and values in {1, 0, -1}

        Example:
            timestamps = [datetime(2024, 1, 1, 9, 30), datetime(2024, 1, 1, 9, 31)]
            signals = pd.Series([1, 0], index=timestamps)
            return signals
        """
        pass

    @abstractmethod
    def position_size(self, signal: int, market_state: MarketState, **kwargs) -> float:
        """
        Calculate position size for a given signal.

        Position sizing strategies:
        - Fixed: Always use same size (e.g., 1 contract)
        - Percentage: Use % of account equity
        - Kelly Criterion: Based on win rate and profit factor
        - Volatility-based: Based on ATR or recent volatility

        Args:
            signal: Signal value (1, 0, or -1)
            market_state: Current MarketState snapshot
            **kwargs: Additional context (account_equity, risk_per_trade, etc.)

        Returns:
            Position size as float (0 = no position, 1 = full size)
            Negative values are allowed for short positions

        Example:
            if signal == 0:
                return 0.0
            elif signal == 1:
                return 1.0  # 1 contract long
            else:
                return -1.0  # 1 contract short
        """
        pass

    # Optional methods that strategies can override

    def validate_features(self, market_state: MarketState) -> bool:
        """
        Validate that required features are available in MarketState.

        Args:
            market_state: MarketState to validate

        Returns:
            True if all required features are available

        Raises:
            ValueError: If required features are missing
        """
        required = self.required_features()
        available = self._extract_available_features(market_state)

        missing = set(required) - set(available)
        if missing:
            raise ValueError(
                f"Strategy '{self.metadata.name}' requires features {missing} "
                f"which are not available in MarketState. "
                f"Available features: {available}"
            )

        return True

    def _extract_available_features(self, market_state: MarketState) -> List[str]:
        """Extract list of available features from MarketState"""
        features = []

        if market_state.active_fvgs:
            features.append("active_fvgs")

        if market_state.active_obs:
            features.append("active_obs")

        if market_state.bias:
            features.append("bias")

        if market_state.key_levels:
            features.append("key_levels")

        if market_state.session:
            features.append("session")

        return features

    def on_signal_generated(self, signal: int, market_state: MarketState):
        """
        Hook called after signal generation.

        Override this for logging, notifications, or side effects.

        Args:
            signal: Generated signal value
            market_state: Current MarketState
        """
        pass

    def on_position_opened(self, signal: int, size: float, market_state: MarketState):
        """
        Hook called when a position is opened.

        Args:
            signal: Signal that triggered the position (1 or -1)
            size: Position size
            market_state: Current MarketState
        """
        pass

    def on_position_closed(self, pnl: float, market_state: MarketState):
        """
        Hook called when a position is closed.

        Args:
            pnl: Profit/loss from the closed position
            market_state: Current MarketState
        """
        # Track performance
        self.performance_history.append({
            "timestamp": market_state.timestamp,
            "pnl": pnl,
        })

    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters"""
        return self.params

    def set_parameters(self, **kwargs):
        """Update strategy parameters"""
        self.params.update(kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize strategy to dictionary.

        Returns:
            Dictionary with strategy metadata and parameters
        """
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "version": self.metadata.version,
            "author": self.metadata.author,
            "strategy_type": self.metadata.strategy_type,
            "parameters": self.params,
            "is_fitted": self.is_fitted,
            "required_features": self.required_features(),
        }

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name='{self.metadata.name}', "
            f"version='{self.metadata.version}', "
            f"type='{self.metadata.strategy_type}')"
        )
