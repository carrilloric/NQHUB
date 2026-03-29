"""
Strategy Framework

Base classes and implementations for trading strategies in NQHUB.

This module provides:
- NQHubStrategy: Abstract base class for all strategies
- StrategyMetadata: Metadata container for strategies
- RuleBasedStrategy: Pure rule-based strategies
- MLStrategy: Machine learning strategies
- RLStrategy: Reinforcement learning strategies
- HybridStrategy: Combined rule-based + ML/RL strategies
- StrategyRegistry: Central registry for strategy management
"""

from .base import NQHubStrategy, StrategyMetadata
from .rule_based import RuleBasedStrategy
from .ml_strategy import MLStrategy
from .rl_strategy import RLStrategy
from .hybrid_strategy import HybridStrategy
from .registry import StrategyRegistry

__all__ = [
    "NQHubStrategy",
    "StrategyMetadata",
    "RuleBasedStrategy",
    "MLStrategy",
    "RLStrategy",
    "HybridStrategy",
    "StrategyRegistry",
]
