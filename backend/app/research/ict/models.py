"""
ICT (Inner Circle Trader) Pattern Models

Dataclasses for FVG, Order Block, and related pattern detection models.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PatternStatus(str, Enum):
    """Status of a detected pattern in its lifecycle"""
    ACTIVE = "active"
    MITIGATED = "mitigated"
    BROKEN = "broken"
    TESTED = "tested"  # For Order Blocks


class Direction(str, Enum):
    """Direction of the pattern movement"""
    BULLISH = "bullish"
    BEARISH = "bearish"


@dataclass
class FVG:
    """
    Fair Value Gap pattern

    A FVG represents an imbalance between buyers and sellers,
    creating a gap in price that often acts as a magnet for future price action.
    """
    candle_index: int           # Index in the dataframe where FVG was detected
    direction: Direction        # Bullish or bearish
    top: float                 # Upper boundary of the gap
    bottom: float              # Lower boundary of the gap
    displacement_score: float  # 0.0 - 1.0 (strength of the movement)
    status: PatternStatus = PatternStatus.ACTIVE
    mitigated_at: Optional[int] = None  # candle_index where it was mitigated

    @property
    def size(self) -> float:
        """Size of the FVG in price units"""
        return self.top - self.bottom

    @property
    def midpoint(self) -> float:
        """Midpoint of the FVG (50% level)"""
        return (self.top + self.bottom) / 2

    def __repr__(self) -> str:
        return (f"FVG(idx={self.candle_index}, {self.direction.value}, "
                f"[{self.bottom:.2f}-{self.top:.2f}], "
                f"score={self.displacement_score:.2f}, "
                f"status={self.status.value})")


@dataclass
class OrderBlock:
    """
    Order Block pattern

    An Order Block represents the last candle before a significant impulse move,
    often indicating institutional order placement.
    """
    candle_index: int           # Index in the dataframe where OB was detected
    direction: Direction        # Bullish or bearish
    top: float                 # Upper boundary of the OB candle
    bottom: float              # Lower boundary of the OB candle
    quality_score: float       # 0.0 - 1.0 (quality of the OB)
    status: PatternStatus = PatternStatus.ACTIVE
    tested_count: int = 0      # Number of times price has tested the OB
    broken_at: Optional[int] = None  # candle_index where it was broken

    @property
    def size(self) -> float:
        """Size of the Order Block in price units"""
        return self.top - self.bottom

    @property
    def midpoint(self) -> float:
        """Midpoint of the Order Block"""
        return (self.top + self.bottom) / 2

    def __repr__(self) -> str:
        return (f"OB(idx={self.candle_index}, {self.direction.value}, "
                f"[{self.bottom:.2f}-{self.top:.2f}], "
                f"quality={self.quality_score:.2f}, "
                f"tested={self.tested_count}, "
                f"status={self.status.value})")