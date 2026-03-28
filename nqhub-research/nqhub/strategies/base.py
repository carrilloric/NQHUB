"""
Base Strategy Abstract Class for NQHUB

All trading strategies must inherit from this base class.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


class NQHubStrategy(ABC):
    """
    Abstract base class for all NQHUB trading strategies.

    NQ Futures constants are hardcoded and NEVER configurable (ADR-001).
    These values are intrinsic to the NQ futures contract specification.
    """

    # NQ Futures Contract Specifications - HARDCODED (ADR-001)
    TICK_SIZE = 0.25      # Minimum price increment
    TICK_VALUE = 5.0      # USD value per tick
    POINT_VALUE = 20.0    # USD value per full point (4 ticks)

    def __init__(self, name: str = "NQHubStrategy"):
        """
        Initialize the strategy.

        Args:
            name: Strategy name for identification
        """
        self.name = name
        self._validate_constants()

    def _validate_constants(self) -> None:
        """
        Validate that NQ constants haven't been modified.

        Raises:
            RuntimeError: If constants have been tampered with
        """
        if self.TICK_SIZE != 0.25:
            raise RuntimeError(f"TICK_SIZE must be 0.25, got {self.TICK_SIZE}")
        if self.TICK_VALUE != 5.0:
            raise RuntimeError(f"TICK_VALUE must be 5.0, got {self.TICK_VALUE}")
        if self.POINT_VALUE != 20.0:
            raise RuntimeError(f"POINT_VALUE must be 20.0, got {self.POINT_VALUE}")

    @abstractmethod
    def required_features(self) -> List[str]:
        """
        List of features/indicators required by the strategy.

        Returns:
            List of feature names that must be present in the data.

        Example:
            return ["rsi", "macd", "volume", "atr", "vwap"]
        """
        ...

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on the provided data.

        Args:
            data: DataFrame with OHLCV and required features

        Returns:
            Series with signal values:
                1 = Long signal
                0 = No position (flat)
               -1 = Short signal

        The returned Series should have the same index as the input DataFrame.
        """
        ...

    @abstractmethod
    def position_size(self, equity: float, risk_pct: float) -> int:
        """
        Calculate the number of contracts to trade.

        Args:
            equity: Current account equity in USD
            risk_pct: Percentage of equity to risk per trade (e.g., 1.0 for 1%)

        Returns:
            Number of NQ contracts (positive integer)

        Example:
            If equity = $100,000 and risk_pct = 1.0:
            Risk amount = $1,000
            With 20 tick stop loss = 20 * $5 = $100 per contract
            Position size = $1,000 / $100 = 10 contracts
        """
        ...

    def calculate_pnl_points(self, entry_price: float, exit_price: float,
                            side: int) -> float:
        """
        Calculate P&L in points.

        Args:
            entry_price: Entry price
            exit_price: Exit price
            side: 1 for long, -1 for short

        Returns:
            P&L in points
        """
        if side == 1:  # Long
            return exit_price - entry_price
        elif side == -1:  # Short
            return entry_price - exit_price
        else:
            return 0.0

    def calculate_pnl_ticks(self, entry_price: float, exit_price: float,
                           side: int) -> int:
        """
        Calculate P&L in ticks.

        Args:
            entry_price: Entry price
            exit_price: Exit price
            side: 1 for long, -1 for short

        Returns:
            P&L in ticks (integer)
        """
        pnl_points = self.calculate_pnl_points(entry_price, exit_price, side)
        return int(pnl_points / self.TICK_SIZE)

    def calculate_pnl_dollars(self, entry_price: float, exit_price: float,
                             side: int, contracts: int = 1) -> float:
        """
        Calculate P&L in dollars.

        Args:
            entry_price: Entry price
            exit_price: Exit price
            side: 1 for long, -1 for short
            contracts: Number of contracts traded

        Returns:
            P&L in USD (before commissions)
        """
        pnl_ticks = self.calculate_pnl_ticks(entry_price, exit_price, side)
        return pnl_ticks * self.TICK_VALUE * contracts

    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate that the data contains all required features.

        Args:
            data: DataFrame to validate

        Returns:
            True if valid, False otherwise
        """
        required = set(self.required_features())
        available = set(data.columns)
        missing = required - available

        if missing:
            print(f"Missing required features: {missing}")
            return False

        return True

    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get strategy information and metadata.

        Returns:
            Dictionary with strategy details
        """
        return {
            "name": self.name,
            "class": self.__class__.__name__,
            "required_features": self.required_features(),
            "nq_constants": {
                "tick_size": self.TICK_SIZE,
                "tick_value": self.TICK_VALUE,
                "point_value": self.POINT_VALUE
            }
        }