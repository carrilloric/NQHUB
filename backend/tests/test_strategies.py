"""
Tests for Strategy Framework

Tests NQHubStrategy base class, strategy subclasses (RuleBasedStrategy,
MLStrategy, RLStrategy, HybridStrategy), and StrategyRegistry.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Optional
import pytz

from app.research.strategies import (
    NQHubStrategy,
    RuleBasedStrategy,
    MLStrategy,
    RLStrategy,
    HybridStrategy,
    StrategyRegistry,
)
from app.research.strategies.base import StrategyMetadata
from app.research.market_state import MarketState, Bias, Session
from app.research.ict.models import FVG, OrderBlock, Direction, PatternStatus


# ==================== FIXTURES ====================

@pytest.fixture
def strategy_metadata():
    """Create sample strategy metadata"""
    return StrategyMetadata(
        name="Test Strategy",
        description="A test strategy for unit tests",
        version="1.0.0",
        author="test@nqhub.com",
        strategy_type="rule_based",
    )


@pytest.fixture
def market_state():
    """Create sample MarketState for testing"""
    # Create sample FVGs
    fvg1 = FVG(
        candle_index=10,
        direction=Direction.BULLISH,
        top=18100.0,
        bottom=18050.0,
        displacement_score=0.8,
        status=PatternStatus.ACTIVE,
    )

    fvg2 = FVG(
        candle_index=15,
        direction=Direction.BEARISH,
        top=18200.0,
        bottom=18150.0,
        displacement_score=0.7,
        status=PatternStatus.ACTIVE,
    )

    # Create sample OBs
    ob1 = OrderBlock(
        candle_index=20,
        direction=Direction.BULLISH,
        top=18000.0,
        bottom=17950.0,
        quality_score=0.85,
        status=PatternStatus.ACTIVE,
    )

    # Create MarketState
    timestamp = datetime(2024, 1, 15, 10, 0, tzinfo=pytz.UTC)

    return MarketState(
        timestamp=timestamp,
        symbol="NQ",
        bias={"5min": Bias.BULLISH.value, "15min": Bias.NEUTRAL.value},
        active_fvgs={"5min": [fvg1, fvg2]},
        active_obs={"15min": [ob1]},
        key_levels=[18000.0, 18100.0, 18200.0],
        session=Session.NY_AM.value,
    )


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data"""
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-15 09:30", periods=100, freq="5min")

    data = {
        "open": 18000 + np.random.randn(100) * 10,
        "high": 18010 + np.random.randn(100) * 10,
        "low": 17990 + np.random.randn(100) * 10,
        "close": 18000 + np.random.randn(100) * 10,
        "volume": np.random.randint(100, 1000, 100),
    }

    return pd.DataFrame(data, index=dates)


# ==================== CONCRETE STRATEGY IMPLEMENTATIONS FOR TESTING ====================

class TestRuleBasedStrategy(RuleBasedStrategy):
    """Simple rule-based strategy for testing"""

    def required_features(self) -> List[str]:
        return ["active_fvgs", "bias", "session"]

    def generate_signals(
        self, market_state: MarketState, data: Optional[pd.DataFrame] = None
    ) -> pd.Series:
        # Simple rule: go long if bias is bullish and we have active FVGs
        if market_state.get_bias("5min") == Bias.BULLISH.value:
            fvgs = market_state.get_active_fvgs("5min")
            if len(fvgs) > 0:
                return pd.Series([1], index=[market_state.timestamp])

        return pd.Series([0], index=[market_state.timestamp])


class TestMLStrategy(MLStrategy):
    """Simple ML strategy for testing (mock ML model)"""

    def required_features(self) -> List[str]:
        return ["active_fvgs", "active_obs", "bias"]

    def fit(self, X: pd.DataFrame, y: pd.Series, **fit_params):
        # Mock fit - just set is_fitted flag
        self.model = "MockModel"
        self.feature_names = X.columns.tolist()
        self.is_fitted = True

    def generate_signals(
        self, market_state: MarketState, data: Optional[pd.DataFrame] = None
    ) -> pd.Series:
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        # Mock prediction: return 1 if we have active patterns
        has_patterns = (
            len(market_state.get_active_fvgs("5min")) > 0 or
            len(market_state.get_active_obs("15min")) > 0
        )

        signal = 1 if has_patterns else 0
        return pd.Series([signal], index=[market_state.timestamp])

    def _extract_features(
        self, market_state: MarketState, data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        features = {
            "num_fvgs": len(market_state.get_active_fvgs("5min")),
            "num_obs": len(market_state.get_active_obs("15min")),
            "bias_bullish": 1 if market_state.get_bias("5min") == "bullish" else 0,
        }
        return pd.DataFrame([features], index=[market_state.timestamp])

    def save_model(self, filepath: str):
        pass  # Mock implementation

    def load_model(self, filepath: str):
        pass  # Mock implementation


class TestRLStrategy(RLStrategy):
    """Simple RL strategy for testing (mock RL agent)"""

    def required_features(self) -> List[str]:
        return ["active_fvgs", "bias", "session"]

    def train(self, env, n_episodes: int = 1000, **train_params):
        # Mock training
        self.agent = "MockAgent"
        self.is_fitted = True

    def generate_signals(
        self, market_state: MarketState, data: Optional[pd.DataFrame] = None
    ) -> pd.Series:
        if not self.is_fitted:
            raise ValueError("Agent must be trained first")

        # Mock action selection
        observation = self._state_to_observation(market_state, data)
        action = 0  # Mock: always select action 0 (long)
        signal = self._action_to_signal(action)

        return pd.Series([signal], index=[market_state.timestamp])

    def _state_to_observation(
        self, market_state: MarketState, data: Optional[pd.DataFrame] = None
    ) -> np.ndarray:
        # Mock observation
        return np.array([
            len(market_state.get_active_fvgs("5min")),
            1 if market_state.get_bias("5min") == "bullish" else 0,
        ])

    def save_agent(self, filepath: str):
        pass  # Mock implementation

    def load_agent(self, filepath: str):
        pass  # Mock implementation


class TestHybridStrategy(HybridStrategy):
    """Simple hybrid strategy for testing"""

    def required_features(self) -> List[str]:
        return ["active_fvgs", "bias"]

    def generate_signals(
        self, market_state: MarketState, data: Optional[pd.DataFrame] = None
    ) -> pd.Series:
        # Rule: only trade during NY_AM
        if not self._check_rules(market_state):
            return pd.Series([0], index=[market_state.timestamp])

        # Mock ML prediction
        signal = 1 if len(market_state.get_active_fvgs("5min")) > 0 else 0
        return pd.Series([signal], index=[market_state.timestamp])

    def _check_rules(self, market_state: MarketState) -> bool:
        return market_state.session == Session.NY_AM.value


# ==================== TESTS ====================

def test_strategy_metadata_creation(strategy_metadata):
    """Test StrategyMetadata creation"""
    assert strategy_metadata.name == "Test Strategy"
    assert strategy_metadata.version == "1.0.0"
    assert strategy_metadata.author == "test@nqhub.com"
    assert strategy_metadata.strategy_type == "rule_based"


def test_rule_based_strategy_creation(strategy_metadata):
    """Test RuleBasedStrategy instantiation"""
    strategy = TestRuleBasedStrategy(strategy_metadata, min_fvg_score=0.7)

    assert strategy.metadata.name == "Test Strategy"
    assert strategy.is_fitted == True  # Rule-based strategies are always fitted
    assert strategy.params["min_fvg_score"] == 0.7
    assert strategy.metadata.strategy_type == "rule_based"


def test_rule_based_strategy_required_features():
    """Test required_features() returns correct features"""
    metadata = StrategyMetadata(
        name="Test", version="1.0.0", author="test@test.com", description="Test strategy"
    )
    strategy = TestRuleBasedStrategy(metadata)

    features = strategy.required_features()

    assert "active_fvgs" in features
    assert "bias" in features
    assert "session" in features


def test_rule_based_strategy_generate_signals(market_state):
    """Test signal generation with bullish bias and active FVGs"""
    metadata = StrategyMetadata(
        name="Test", version="1.0.0", author="test@test.com", description="Test strategy"
    )
    strategy = TestRuleBasedStrategy(metadata)

    signals = strategy.generate_signals(market_state)

    assert len(signals) == 1
    assert signals.iloc[0] == 1  # Should be long signal (bullish bias + FVGs)


def test_rule_based_strategy_position_sizing(market_state):
    """Test position sizing logic"""
    metadata = StrategyMetadata(
        name="Test", version="1.0.0", author="test@test.com", description="Test strategy"
    )
    strategy = TestRuleBasedStrategy(metadata, risk_per_trade=2.0)

    # Test long signal
    size_long = strategy.position_size(1, market_state)
    assert size_long == 2.0

    # Test short signal
    size_short = strategy.position_size(-1, market_state)
    assert size_short == -2.0

    # Test flat signal
    size_flat = strategy.position_size(0, market_state)
    assert size_flat == 0.0


def test_ml_strategy_requires_fitting():
    """Test ML strategy requires fitting before use"""
    metadata = StrategyMetadata(
        name="ML Test", version="1.0.0", author="test@test.com", description="ML test strategy"
    )
    strategy = TestMLStrategy(metadata)

    assert strategy.is_fitted == False

    # Should raise error if trying to generate signals before fitting
    with pytest.raises(ValueError, match="must be fitted"):
        signals = strategy.generate_signals(MarketState(timestamp=datetime.now(pytz.UTC)))


def test_ml_strategy_fit_and_predict(market_state):
    """Test ML strategy fit and prediction"""
    metadata = StrategyMetadata(
        name="ML Test", version="1.0.0", author="test@test.com", description="ML test strategy"
    )
    strategy = TestMLStrategy(metadata)

    # Create mock training data
    X = pd.DataFrame({
        "num_fvgs": [1, 0, 2],
        "num_obs": [1, 1, 0],
        "bias_bullish": [1, 0, 1],
    })
    y = pd.Series([1, 0, 1])

    # Fit the model
    strategy.fit(X, y)

    assert strategy.is_fitted == True
    assert strategy.model is not None

    # Generate signals
    signals = strategy.generate_signals(market_state)

    assert len(signals) == 1
    assert signals.iloc[0] in [0, 1, -1]  # Valid signal


def test_rl_strategy_requires_training():
    """Test RL strategy requires training before use"""
    metadata = StrategyMetadata(
        name="RL Test", version="1.0.0", author="test@test.com", description="RL test strategy"
    )
    strategy = TestRLStrategy(metadata)

    assert strategy.is_fitted == False

    # Should raise error if trying to generate signals before training
    with pytest.raises(ValueError, match="must be trained"):
        signals = strategy.generate_signals(MarketState(timestamp=datetime.now(pytz.UTC)))


def test_rl_strategy_train_and_predict(market_state):
    """Test RL strategy training and prediction"""
    metadata = StrategyMetadata(
        name="RL Test", version="1.0.0", author="test@test.com", description="RL test strategy"
    )
    strategy = TestRLStrategy(metadata)

    # Train (mock)
    strategy.train(env=None, n_episodes=100)

    assert strategy.is_fitted == True
    assert strategy.agent is not None

    # Generate signals
    signals = strategy.generate_signals(market_state)

    assert len(signals) == 1
    assert signals.iloc[0] in [0, 1, -1]


def test_hybrid_strategy_combines_rules_and_ml(market_state):
    """Test hybrid strategy combines rules and ML"""
    metadata = StrategyMetadata(
        name="Hybrid Test", version="1.0.0", author="test@test.com", description="Hybrid test strategy"
    )
    strategy = TestHybridStrategy(metadata)

    # Should generate signal (passes rule filter + has FVGs)
    signals = strategy.generate_signals(market_state)

    assert len(signals) == 1
    assert signals.iloc[0] == 1  # Long signal

    # Test with different session (should fail rule filter)
    market_state.session = Session.LONDON.value
    signals = strategy.generate_signals(market_state)

    assert signals.iloc[0] == 0  # Flat signal (rule filter failed)


def test_strategy_registry_initialization():
    """Test StrategyRegistry initialization"""
    registry = StrategyRegistry()

    assert len(registry) == 0
    assert isinstance(registry._strategies, dict)


def test_strategy_registry_register_and_get():
    """Test registering and retrieving strategies"""
    registry = StrategyRegistry()

    metadata = StrategyMetadata(
        name="Test Strategy", version="1.0.0", author="test@test.com", description="Test strategy"
    )
    strategy = TestRuleBasedStrategy(metadata)

    # Register strategy
    success = registry.register(strategy)

    assert success == True
    assert len(registry) == 1
    assert "Test Strategy" in registry

    # Retrieve strategy
    retrieved = registry.get("Test Strategy", version="1.0.0")

    assert retrieved is not None
    assert retrieved.metadata.name == "Test Strategy"
    assert retrieved.metadata.version == "1.0.0"


def test_strategy_registry_prevents_duplicate_registration():
    """Test registry prevents duplicate registration without overwrite"""
    registry = StrategyRegistry()

    metadata = StrategyMetadata(
        name="Test Strategy", version="1.0.0", author="test@test.com", description="Test strategy"
    )
    strategy1 = TestRuleBasedStrategy(metadata)
    strategy2 = TestRuleBasedStrategy(metadata)

    # First registration should succeed
    registry.register(strategy1)

    # Second registration should fail (same name/version)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(strategy2, overwrite=False)

    # But should succeed with overwrite=True
    success = registry.register(strategy2, overwrite=True)
    assert success == True


def test_strategy_registry_list_strategies():
    """Test listing all registered strategies"""
    registry = StrategyRegistry()

    # Register multiple strategies
    metadata1 = StrategyMetadata(
        name="Strategy 1", version="1.0.0", author="test@test.com", description="Strategy 1"
    )
    strategy1 = TestRuleBasedStrategy(metadata1)

    metadata2 = StrategyMetadata(
        name="Strategy 2", version="1.0.0", author="test@test.com", description="Strategy 2"
    )
    strategy2 = TestMLStrategy(metadata2)

    registry.register(strategy1)
    registry.register(strategy2)

    # List all strategies
    strategies = registry.list_strategies()

    assert len(strategies) == 2
    assert any(s["name"] == "Strategy 1" for s in strategies)
    assert any(s["name"] == "Strategy 2" for s in strategies)


def test_strategy_registry_filter_by_type():
    """Test filtering strategies by type"""
    registry = StrategyRegistry()

    # Register strategies of different types
    metadata1 = StrategyMetadata(
        name="Rule Strategy", version="1.0.0", author="test@test.com", description="Rule-based strategy"
    )
    strategy1 = TestRuleBasedStrategy(metadata1)

    metadata2 = StrategyMetadata(
        name="ML Strategy", version="1.0.0", author="test@test.com", description="ML strategy"
    )
    strategy2 = TestMLStrategy(metadata2)

    registry.register(strategy1)
    registry.register(strategy2)

    # Filter by rule_based
    rule_based_strategies = registry.list_strategies(strategy_type="rule_based")

    assert len(rule_based_strategies) == 1
    assert rule_based_strategies[0]["name"] == "Rule Strategy"

    # Filter by ml
    ml_strategies = registry.list_strategies(strategy_type="ml")

    assert len(ml_strategies) == 1
    assert ml_strategies[0]["name"] == "ML Strategy"


def test_strategy_registry_unregister():
    """Test unregistering strategies"""
    registry = StrategyRegistry()

    metadata = StrategyMetadata(
        name="Test Strategy", version="1.0.0", author="test@test.com", description="Test strategy"
    )
    strategy = TestRuleBasedStrategy(metadata)

    registry.register(strategy)
    assert len(registry) == 1

    # Unregister
    success = registry.unregister("Test Strategy", version="1.0.0")

    assert success == True
    assert len(registry) == 0
    assert "Test Strategy" not in registry


def test_strategy_registry_get_metadata():
    """Test getting strategy metadata without loading full strategy"""
    registry = StrategyRegistry()

    metadata = StrategyMetadata(
        name="Test Strategy",
        version="1.0.0",
        author="test@test.com",
        description="Test description"
    )
    strategy = TestRuleBasedStrategy(metadata)

    registry.register(strategy)

    # Get metadata
    retrieved_metadata = registry.get_metadata("Test Strategy", version="1.0.0")

    assert retrieved_metadata is not None
    assert retrieved_metadata.name == "Test Strategy"
    assert retrieved_metadata.description == "Test description"


def test_strategy_validate_features(market_state):
    """Test strategy feature validation"""
    metadata = StrategyMetadata(
        name="Test", version="1.0.0", author="test@test.com", description="Test strategy"
    )
    strategy = TestRuleBasedStrategy(metadata)

    # Should validate successfully (all required features present)
    is_valid = strategy.validate_features(market_state)
    assert is_valid == True


def test_strategy_to_dict():
    """Test strategy serialization to dict"""
    metadata = StrategyMetadata(
        name="Test Strategy", version="1.0.0", author="test@test.com", description="Test strategy"
    )
    strategy = TestRuleBasedStrategy(metadata, min_fvg_score=0.7)

    strategy_dict = strategy.to_dict()

    assert strategy_dict["name"] == "Test Strategy"
    assert strategy_dict["version"] == "1.0.0"
    assert strategy_dict["strategy_type"] == "rule_based"
    assert strategy_dict["parameters"]["min_fvg_score"] == 0.7
    assert "required_features" in strategy_dict
