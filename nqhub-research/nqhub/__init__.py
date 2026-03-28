"""
NQHUB Research Package

A comprehensive library for NQ futures trading research, backtesting, and strategy development.
"""

__version__ = "0.1.0"
__author__ = "NQHUB Team"

# NQ Futures Constants (ADR-001: These are NEVER configurable)
TICK_SIZE = 0.25
TICK_VALUE = 5.0    # USD per tick
POINT_VALUE = 20.0  # USD per point (4 ticks per point)

# Import key classes for convenience
from nqhub.strategies.base import NQHubStrategy

__all__ = [
    "NQHubStrategy",
    "TICK_SIZE",
    "TICK_VALUE",
    "POINT_VALUE"
]