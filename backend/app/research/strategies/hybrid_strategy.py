"""
HybridStrategy

Combines rule-based logic with ML/RL models.

Hybrid strategies leverage the best of both worlds:
- Rules: Fast, transparent, reliable for known patterns
- ML/RL: Adaptive, learn complex patterns from data

Common patterns:
- Rule-based filters + ML predictions
- Rules for entry, ML for exit
- RL for position sizing, rules for signal generation
- Ensemble of rules + ML models

Example:
    class MyHybridStrategy(HybridStrategy):
        def __init__(self, metadata, **kwargs):
            super().__init__(metadata, **kwargs)
            # Initialize both rule-based and ML components
            self.ml_model = RandomForestClassifier()
            self.rules = {
                "min_fvg_score": 0.7,
                "allowed_sessions": ["NY_AM"]
            }

        def generate_signals(self, market_state: MarketState, data=None) -> pd.Series:
            # Step 1: Apply rule-based filters
            if not self._check_rules(market_state):
                return pd.Series([0], index=[market_state.timestamp])

            # Step 2: Use ML model for prediction
            features = self._extract_features(market_state, data)
            ml_signal = self.ml_model.predict(features)[0]

            return pd.Series([ml_signal], index=[market_state.timestamp])
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from .base import NQHubStrategy, StrategyMetadata
from app.research.market_state import MarketState


class HybridStrategy(NQHubStrategy):
    """
    Base class for hybrid strategies combining rules + ML/RL.

    Hybrid strategies combine the strengths of different approaches:
    - Rules provide guardrails and domain knowledge
    - ML/RL models discover patterns and adapt to market conditions

    Common architectures:
    1. **Sequential**: Rules → ML → Signal
       - Rules filter out bad conditions
       - ML predicts on remaining candidates

    2. **Parallel**: Rules + ML → Ensemble
       - Both generate signals independently
       - Combine via voting, averaging, or weighted ensemble

    3. **Hierarchical**: Rules for regime, ML for signals
       - Rules detect market regime (trending, ranging, volatile)
       - Different ML models for different regimes

    4. **Contextual**: ML with rule-based features
       - Rules compute high-level features
       - ML uses these features for prediction

    Advantages:
    - More robust than pure ML (rules provide safety)
    - More adaptive than pure rules (ML handles complexity)
    - Easier to explain and debug than pure ML

    Disadvantages:
    - More complex to implement and maintain
    - Need to balance rule logic and ML predictions
    - Risk of conflicting signals
    """

    def __init__(self, metadata: StrategyMetadata, **kwargs):
        """
        Initialize hybrid strategy.

        Args:
            metadata: Strategy metadata
            **kwargs: Strategy-specific parameters

        Common parameters:
        - combination_method: How to combine rules and ML ("filter", "ensemble", "hierarchical")
        - ml_weight: Weight for ML predictions (0.0 - 1.0)
        - rule_weight: Weight for rule-based signals (0.0 - 1.0)
        - min_agreement: Minimum agreement between rules and ML to trade
        """
        metadata.strategy_type = "hybrid"
        super().__init__(metadata, **kwargs)

        # Hybrid strategies may need training (for ML component)
        self.is_fitted = False

        # Components
        self.rules: Dict[str, Any] = {}
        self.ml_model = None
        self.rl_agent = None

    def fit_ml_component(self, X: pd.DataFrame, y: pd.Series, **fit_params):
        """
        Train the ML component of the hybrid strategy.

        Args:
            X: Feature matrix
            y: Target labels
            **fit_params: Additional parameters for model.fit()

        Example:
            from sklearn.ensemble import RandomForestClassifier

            def fit_ml_component(self, X, y):
                self.ml_model = RandomForestClassifier(n_estimators=100)
                self.ml_model.fit(X, y)
                self.is_fitted = True
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement fit_ml_component() if using ML"
        )

    def train_rl_component(self, env, n_episodes: int = 1000, **train_params):
        """
        Train the RL component of the hybrid strategy.

        Args:
            env: Trading environment
            n_episodes: Number of training episodes
            **train_params: Additional training parameters

        Example:
            from stable_baselines3 import PPO

            def train_rl_component(self, env, n_episodes=1000):
                self.rl_agent = PPO("MlpPolicy", env)
                self.rl_agent.learn(total_timesteps=n_episodes * 1000)
                self.is_fitted = True
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement train_rl_component() if using RL"
        )

    # Subclasses must implement these abstract methods
    def required_features(self) -> List[str]:
        """
        Declare required features.

        For hybrid strategies, this includes features for both rules and ML/RL.

        Example:
            return [
                # Rule-based features
                "active_fvgs", "bias", "session",
                # ML features
                "rsi", "macd", "atr", "volume_profile"
            ]
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement required_features()"
        )

    def generate_signals(self, market_state: MarketState, data: Optional[pd.DataFrame] = None) -> pd.Series:
        """
        Generate signals using hybrid approach.

        Args:
            market_state: Current MarketState
            data: OHLCV data

        Returns:
            pd.Series with signals (1/0/-1)

        Example:
            # Sequential: Rules → ML
            if not self._check_rules(market_state):
                return pd.Series([0], index=[market_state.timestamp])

            features = self._extract_features(market_state, data)
            ml_signal = self.ml_model.predict(features)[0]
            return pd.Series([ml_signal], index=[market_state.timestamp])
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement generate_signals()"
        )

    def position_size(self, signal: int, market_state: MarketState, **kwargs) -> float:
        """
        Calculate position size.

        For hybrid strategies, position sizing can combine:
        - Rule-based risk management
        - ML confidence scores
        - RL value functions

        Default: Fixed size (1 contract)
        """
        if signal == 0:
            return 0.0

        # Get parameters
        risk_per_trade = self.params.get("risk_per_trade", 1.0)
        ml_weight = self.params.get("ml_weight", 0.5)

        # Get ML confidence if available
        confidence = kwargs.get("confidence", 1.0)

        # Combine rule-based sizing with ML confidence
        if signal == 1:  # Long
            return risk_per_trade * (1.0 - ml_weight + ml_weight * confidence)
        elif signal == -1:  # Short
            return -risk_per_trade * (1.0 - ml_weight + ml_weight * confidence)
        else:
            return 0.0

    # Helper methods for hybrid strategies

    def _check_rules(self, market_state: MarketState) -> bool:
        """
        Check if rule-based conditions are met.

        Override this to implement custom rule filters.

        Args:
            market_state: Current MarketState

        Returns:
            True if rules pass, False otherwise

        Example:
            # Only trade during NY_AM session
            if market_state.session != "NY_AM":
                return False

            # Require at least one active FVG
            if len(market_state.get_active_fvgs("5min")) == 0:
                return False

            return True
        """
        return True  # Default: all conditions pass

    def _combine_signals(
        self,
        rule_signal: int,
        ml_signal: int,
        method: str = "filter"
    ) -> int:
        """
        Combine rule-based and ML signals.

        Args:
            rule_signal: Signal from rules (1/0/-1)
            ml_signal: Signal from ML model (1/0/-1)
            method: Combination method

        Methods:
        - "filter": Use ML signal only if rules pass (rule_signal != 0)
        - "ensemble": Average the signals (requires agreement for action)
        - "vote": Take majority vote (at least 2 agree)
        - "ml_primary": Use ML signal, rules as veto

        Returns:
            Combined signal (1/0/-1)
        """
        if method == "filter":
            # Rules filter, ML predicts
            return ml_signal if rule_signal != 0 else 0

        elif method == "ensemble":
            # Average signals (requires strong agreement)
            avg = (rule_signal + ml_signal) / 2
            if avg >= 0.5:
                return 1
            elif avg <= -0.5:
                return -1
            else:
                return 0

        elif method == "vote":
            # Majority vote (both must agree for action)
            if rule_signal == ml_signal:
                return rule_signal
            else:
                return 0  # Disagreement → no trade

        elif method == "ml_primary":
            # ML primary, rules as veto
            if rule_signal == 0:
                return 0  # Rules veto
            else:
                return ml_signal  # ML decides direction

        else:
            raise ValueError(f"Unknown combination method: {method}")

    def get_ml_confidence(self, X: pd.DataFrame) -> float:
        """
        Get confidence score from ML model (if available).

        Args:
            X: Feature matrix

        Returns:
            Confidence score (0.0 - 1.0)

        Example:
            # For probabilistic models
            if hasattr(self.ml_model, 'predict_proba'):
                proba = self.ml_model.predict_proba(X)
                return np.max(proba)
        """
        if self.ml_model is None or not self.is_fitted:
            return 1.0  # Default confidence

        # For probabilistic models
        if hasattr(self.ml_model, 'predict_proba'):
            proba = self.ml_model.predict_proba(X)
            return float(np.max(proba))

        return 1.0  # Default for non-probabilistic models

    def __repr__(self) -> str:
        fitted_status = "fitted" if self.is_fitted else "not fitted"
        has_ml = "ML" if self.ml_model is not None else ""
        has_rl = "RL" if self.rl_agent is not None else ""
        components = "+".join(filter(None, [has_ml, has_rl]))

        return (
            f"HybridStrategy("
            f"name='{self.metadata.name}', "
            f"version='{self.metadata.version}', "
            f"components='{components}', "
            f"status='{fitted_status}')"
        )
