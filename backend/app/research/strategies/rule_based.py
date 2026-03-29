"""
RuleBasedStrategy

Pure algorithmic rule-based trading strategies.

These strategies use explicit rules based on:
- ICT patterns (FVGs, Order Blocks, Liquidity Pools)
- Market structure (bias, session, key levels)
- Technical indicators (moving averages, RSI, etc.)

No machine learning or AI - just deterministic logic.

Example:
    class MyFVGStrategy(RuleBasedStrategy):
        def required_features(self) -> List[str]:
            return ["active_fvgs", "bias", "session"]

        def generate_signals(self, market_state: MarketState, data=None) -> pd.Series:
            # If 5min bias is bullish and we have active bullish FVG → go long
            if market_state.get_bias("5min") == "bullish":
                fvgs = market_state.get_active_fvgs("5min", direction="bullish")
                if len(fvgs) > 0:
                    return pd.Series([1], index=[market_state.timestamp])
            return pd.Series([0], index=[market_state.timestamp])
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

from .base import NQHubStrategy, StrategyMetadata
from app.research.market_state import MarketState


class RuleBasedStrategy(NQHubStrategy):
    """
    Base class for rule-based strategies.

    Rule-based strategies use explicit, deterministic rules to generate signals.
    They don't require training or fitting - they're ready to use immediately.

    Common patterns:
    - Pattern-based: Trade FVG retests, OB bounces, etc.
    - Structure-based: Follow market bias, respect key levels
    - Session-based: Only trade during specific sessions (NY_AM, London)
    - Indicator-based: Moving average crossovers, RSI oversold/overbought

    Advantages:
    - Transparent and explainable
    - No training required
    - Fast execution
    - Easy to debug and optimize

    Disadvantages:
    - May not adapt to changing market conditions
    - Can be over-optimized (curve-fitted)
    - Limited by human intuition
    """

    def __init__(self, metadata: StrategyMetadata, **kwargs):
        """
        Initialize rule-based strategy.

        Args:
            metadata: Strategy metadata
            **kwargs: Strategy-specific parameters

        Common parameters:
        - min_fvg_score: Minimum FVG displacement score (0.0 - 1.0)
        - min_ob_quality: Minimum Order Block quality score (0.0 - 1.0)
        - allowed_sessions: List of trading sessions (e.g., ["NY_AM", "London"])
        - timeframes: List of timeframes to analyze (e.g., ["5min", "15min"])
        - risk_per_trade: Risk percentage per trade (e.g., 0.02 for 2%)
        """
        metadata.strategy_type = "rule_based"
        super().__init__(metadata, **kwargs)

        # Rule-based strategies are always "fitted" (no training needed)
        self.is_fitted = True

    # Subclasses must implement these abstract methods
    def required_features(self) -> List[str]:
        """
        Declare required features.

        Override this in your concrete strategy.

        Example:
            return ["active_fvgs", "bias", "session"]
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement required_features()"
        )

    def generate_signals(self, market_state: MarketState, data: Optional[pd.DataFrame] = None) -> pd.Series:
        """
        Generate trading signals based on rules.

        Override this in your concrete strategy.

        Example:
            if self._should_go_long(market_state):
                return pd.Series([1], index=[market_state.timestamp])
            elif self._should_go_short(market_state):
                return pd.Series([-1], index=[market_state.timestamp])
            else:
                return pd.Series([0], index=[market_state.timestamp])
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement generate_signals()"
        )

    def position_size(self, signal: int, market_state: MarketState, **kwargs) -> float:
        """
        Calculate position size.

        Default: Fixed size (1 contract per signal)

        Override for custom sizing:
        - Percentage of equity
        - ATR-based (volatility sizing)
        - Kelly criterion
        """
        if signal == 0:
            return 0.0

        # Get risk per trade from parameters (default 1.0 = full size)
        risk_per_trade = self.params.get("risk_per_trade", 1.0)

        # Get account equity if provided
        account_equity = kwargs.get("account_equity", 100000.0)

        # Fixed position sizing based on risk
        if signal == 1:  # Long
            return risk_per_trade
        elif signal == -1:  # Short
            return -risk_per_trade
        else:
            return 0.0

    # Helper methods for common rule-based patterns

    def _check_session_filter(self, market_state: MarketState) -> bool:
        """
        Check if current session is allowed for trading.

        Returns:
            True if session is allowed, False otherwise
        """
        allowed_sessions = self.params.get("allowed_sessions", None)

        if allowed_sessions is None:
            return True  # No filter, all sessions allowed

        return market_state.session in allowed_sessions

    def _check_bias_alignment(self, market_state: MarketState, direction: str, timeframe: str = "5min") -> bool:
        """
        Check if market bias aligns with desired direction.

        Args:
            market_state: Current MarketState
            direction: Desired direction ("bullish" or "bearish")
            timeframe: Timeframe to check (default "5min")

        Returns:
            True if bias aligns with direction
        """
        bias = market_state.get_bias(timeframe)
        return bias == direction

    def _get_pattern_quality_score(self, market_state: MarketState, pattern_type: str = "fvg") -> float:
        """
        Get average quality score of active patterns.

        Args:
            market_state: Current MarketState
            pattern_type: "fvg" or "ob"

        Returns:
            Average quality/displacement score (0.0 - 1.0)
        """
        if pattern_type == "fvg":
            # Get all FVGs across all timeframes
            all_fvgs = []
            for timeframe in market_state.active_fvgs.keys():
                all_fvgs.extend(market_state.active_fvgs[timeframe])

            if not all_fvgs:
                return 0.0

            # Calculate average displacement score
            return sum(fvg.displacement_score for fvg in all_fvgs) / len(all_fvgs)

        elif pattern_type == "ob":
            # Get all OBs across all timeframes
            all_obs = []
            for timeframe in market_state.active_obs.keys():
                all_obs.extend(market_state.active_obs[timeframe])

            if not all_obs:
                return 0.0

            # Calculate average quality score
            return sum(ob.quality_score for ob in all_obs) / len(all_obs)

        return 0.0

    def __repr__(self) -> str:
        return (
            f"RuleBasedStrategy("
            f"name='{self.metadata.name}', "
            f"version='{self.metadata.version}')"
        )
