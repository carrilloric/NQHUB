"""
MLStrategy

Machine Learning-based trading strategies.

These strategies use supervised or unsupervised learning models to predict:
- Price direction (classification: long/short/flat)
- Price targets (regression: expected price movement)
- Pattern recognition (clustering, anomaly detection)

Common ML models:
- Random Forest, XGBoost, LightGBM
- Neural Networks (MLP, LSTM, Transformer)
- Support Vector Machines (SVM)

Example:
    class MyMLStrategy(MLStrategy):
        def fit(self, X: pd.DataFrame, y: pd.Series):
            self.model = RandomForestClassifier()
            self.model.fit(X, y)
            self.is_fitted = True

        def generate_signals(self, market_state: MarketState, data=None) -> pd.Series:
            features = self._extract_features(market_state, data)
            predictions = self.model.predict(features)
            return pd.Series(predictions, index=[market_state.timestamp])
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from .base import NQHubStrategy, StrategyMetadata
from app.research.market_state import MarketState


class MLStrategy(NQHubStrategy):
    """
    Base class for machine learning strategies.

    ML strategies require training on historical data before they can generate signals.
    They learn patterns from data and can adapt to changing market conditions.

    Workflow:
    1. fit() - Train the model on historical data
    2. generate_signals() - Use trained model to predict signals
    3. evaluate() - Backtest and measure performance

    Advantages:
    - Can discover non-obvious patterns
    - Adapt to market regime changes (if retrained)
    - Handle high-dimensional feature spaces

    Disadvantages:
    - Require training data
    - Risk of overfitting
    - Less transparent (black box)
    - Computationally expensive
    """

    def __init__(self, metadata: StrategyMetadata, **kwargs):
        """
        Initialize ML strategy.

        Args:
            metadata: Strategy metadata
            **kwargs: Strategy-specific parameters

        Common parameters:
        - model_type: Type of ML model ("random_forest", "xgboost", "neural_net")
        - n_estimators: Number of trees (for ensemble methods)
        - max_depth: Maximum tree depth
        - learning_rate: Learning rate (for gradient boosting)
        - features: List of feature names to use
        - lookback_periods: Number of historical periods for features
        """
        metadata.strategy_type = "ml"
        super().__init__(metadata, **kwargs)

        # ML strategies need training
        self.is_fitted = False
        self.model = None
        self.feature_names: List[str] = []
        self.training_history: Dict[str, Any] = {}

    def fit(self, X: pd.DataFrame, y: pd.Series, **fit_params):
        """
        Train the ML model on historical data.

        Args:
            X: Feature matrix (rows=timestamps, cols=features)
            y: Target labels (1=long, 0=flat, -1=short)
            **fit_params: Additional parameters for model.fit()

        Example:
            from sklearn.ensemble import RandomForestClassifier

            class MyMLStrategy(MLStrategy):
                def fit(self, X, y):
                    self.model = RandomForestClassifier(n_estimators=100)
                    self.model.fit(X, y)
                    self.feature_names = X.columns.tolist()
                    self.is_fitted = True
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement fit()"
        )

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using the trained model.

        Args:
            X: Feature matrix

        Returns:
            Array of predictions (1, 0, -1)

        Raises:
            ValueError: If model is not fitted
        """
        if not self.is_fitted:
            raise ValueError(
                f"Strategy '{self.metadata.name}' must be fitted before prediction. "
                f"Call fit() first."
            )

        if self.model is None:
            raise ValueError(
                f"Strategy '{self.metadata.name}' has no model. "
                f"Implement fit() and set self.model."
            )

        return self.model.predict(X)

    # Subclasses must implement these abstract methods
    def required_features(self) -> List[str]:
        """
        Declare required features.

        For ML strategies, this typically includes:
        - Raw market data features
        - Derived technical indicators
        - Pattern-based features

        Example:
            return [
                "active_fvgs", "active_obs", "bias", "session",
                "rsi", "macd", "atr", "volume_profile"
            ]
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement required_features()"
        )

    def generate_signals(self, market_state: MarketState, data: Optional[pd.DataFrame] = None) -> pd.Series:
        """
        Generate signals using trained ML model.

        Args:
            market_state: Current MarketState
            data: OHLCV data for feature extraction

        Returns:
            pd.Series with signals (1/0/-1)

        Example:
            features = self._extract_features(market_state, data)
            prediction = self.predict(features)
            return pd.Series([prediction[0]], index=[market_state.timestamp])
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement generate_signals()"
        )

    def position_size(self, signal: int, market_state: MarketState, **kwargs) -> float:
        """
        Calculate position size.

        For ML strategies, position sizing can be based on:
        - Prediction confidence (if model outputs probabilities)
        - Model uncertainty (ensemble variance)
        - Kelly criterion with estimated win rate

        Default: Fixed size (1 contract)
        """
        if signal == 0:
            return 0.0

        # Get confidence from kwargs if available (for probabilistic models)
        confidence = kwargs.get("confidence", 1.0)

        # Get risk per trade from parameters
        risk_per_trade = self.params.get("risk_per_trade", 1.0)

        # Scale position size by confidence
        if signal == 1:  # Long
            return risk_per_trade * confidence
        elif signal == -1:  # Short
            return -risk_per_trade * confidence
        else:
            return 0.0

    # Helper methods for ML strategies

    def _extract_features(self, market_state: MarketState, data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Extract features from MarketState and OHLCV data.

        Override this to create custom feature engineering.

        Args:
            market_state: Current MarketState
            data: Optional OHLCV data

        Returns:
            DataFrame with one row (current timestamp) and feature columns

        Example:
            features = {
                "bias_5min": 1 if market_state.get_bias("5min") == "bullish" else 0,
                "num_active_fvgs": len(market_state.get_active_fvgs("5min")),
                "session_ny_am": 1 if market_state.session == "NY_AM" else 0,
            }
            return pd.DataFrame([features], index=[market_state.timestamp])
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _extract_features()"
        )

    def get_feature_importance(self) -> Optional[pd.Series]:
        """
        Get feature importance from trained model (if available).

        Returns:
            pd.Series with feature names as index and importance values

        Example:
            # For tree-based models
            if hasattr(self.model, 'feature_importances_'):
                return pd.Series(
                    self.model.feature_importances_,
                    index=self.feature_names
                ).sort_values(ascending=False)
        """
        if not self.is_fitted or self.model is None:
            return None

        # For tree-based models (RF, XGBoost, LightGBM)
        if hasattr(self.model, 'feature_importances_'):
            return pd.Series(
                self.model.feature_importances_,
                index=self.feature_names
            ).sort_values(ascending=False)

        return None

    def save_model(self, filepath: str):
        """
        Save trained model to disk.

        Args:
            filepath: Path to save the model

        Example:
            import joblib
            joblib.dump(self.model, filepath)
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement save_model()"
        )

    def load_model(self, filepath: str):
        """
        Load trained model from disk.

        Args:
            filepath: Path to load the model from

        Example:
            import joblib
            self.model = joblib.load(filepath)
            self.is_fitted = True
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement load_model()"
        )

    def __repr__(self) -> str:
        fitted_status = "fitted" if self.is_fitted else "not fitted"
        return (
            f"MLStrategy("
            f"name='{self.metadata.name}', "
            f"version='{self.metadata.version}', "
            f"status='{fitted_status}')"
        )
