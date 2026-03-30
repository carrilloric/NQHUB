"""
Breaker Block Detector

Detects Order Blocks that have been broken and inverted their function.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from enum import Enum

from app.research.ict.models import Direction, PatternStatus
from app.research.ict.ob_detector import OrderBlockDetector, OrderBlock


class BreakerBlockStatus(str, Enum):
    """Status of a Breaker Block"""
    ACTIVE = "active"
    TESTED = "tested"
    BROKEN = "broken"


@dataclass
class BreakerBlock:
    """
    Breaker Block pattern

    An Order Block that was broken inverts its function:
    - Bearish OB broken → becomes support (bullish BB)
    - Bullish OB broken → becomes resistance (bearish BB)
    """
    id: str
    timeframe: str
    direction: Direction  # Direction of the BB (opposite of original OB)
    original_ob_id: str  # ID of the Order Block that was broken
    top: float
    bottom: float
    break_candle_time: datetime
    break_candle_index: int
    quality_score: float  # Inherited from OB + break factor
    status: BreakerBlockStatus = BreakerBlockStatus.ACTIVE
    tested_count: int = 0
    broken_at: Optional[int] = None

    @property
    def size(self) -> float:
        """Size of the Breaker Block in price units"""
        return self.top - self.bottom

    @property
    def midpoint(self) -> float:
        """Midpoint of the Breaker Block"""
        return (self.top + self.bottom) / 2

    def __repr__(self) -> str:
        return (f"BreakerBlock(id={self.id}, {self.direction.value}, "
                f"[{self.bottom:.2f}-{self.top:.2f}], "
                f"quality={self.quality_score:.2f}, "
                f"tested={self.tested_count}, "
                f"status={self.status.value})")


class BreakerBlockDetector:
    """
    Detects Breaker Blocks from broken Order Blocks.

    When an Order Block is broken (price closes beyond it), it inverts its function
    and becomes a Breaker Block with opposite directional bias.
    """

    def __init__(self, ob_detector: Optional[OrderBlockDetector] = None):
        """
        Initialize Breaker Block detector.

        Args:
            ob_detector: OrderBlockDetector instance (will create one if not provided)
        """
        self.ob_detector = ob_detector if ob_detector else OrderBlockDetector()

    def detect(self, df: pd.DataFrame, timeframe: str) -> List[BreakerBlock]:
        """
        Detect Breaker Blocks from broken Order Blocks.

        Args:
            df: DataFrame with columns: open, high, low, close, volume, datetime
            timeframe: Timeframe string (e.g., "5m", "15m", "1h")

        Returns:
            List of detected BreakerBlock patterns
        """
        if len(df) < 10:
            return []

        breaker_blocks = []

        # First, get all Order Blocks
        order_blocks = self.ob_detector.detect(df)

        # Check each Order Block to see if it's been broken
        for ob in order_blocks:
            # Only process OBs that are at least 3 candles old
            if ob.candle_index >= len(df) - 3:
                continue

            # Check if OB has been broken
            break_info = self._check_ob_broken(ob, df)

            if break_info is not None:
                break_candle_idx, break_candle = break_info

                # Create Breaker Block with inverted direction
                bb_direction = Direction.BULLISH if ob.direction == Direction.BEARISH else Direction.BEARISH

                # Calculate quality score with break displacement factor
                break_factor = self._calculate_break_displacement_factor(ob, break_candle)
                quality_score = ob.quality_score * break_factor

                # Create BreakerBlock
                bb = BreakerBlock(
                    id=f"BB_{timeframe}_{ob.candle_index}_{bb_direction.value}",
                    timeframe=timeframe,
                    direction=bb_direction,
                    original_ob_id=f"OB_{timeframe}_{ob.candle_index}",
                    top=ob.top,
                    bottom=ob.bottom,
                    break_candle_time=break_candle['datetime'] if 'datetime' in break_candle else df.index[break_candle_idx],
                    break_candle_index=break_candle_idx,
                    quality_score=quality_score,
                    status=BreakerBlockStatus.ACTIVE,
                    tested_count=0
                )

                # Check if BB has been tested after formation
                bb.tested_count = self._count_tests(bb, df, break_candle_idx)

                # Check current status
                self._update_status(bb, df, break_candle_idx)

                breaker_blocks.append(bb)

        return breaker_blocks

    def _check_ob_broken(self, ob: OrderBlock, df: pd.DataFrame) -> Optional[tuple]:
        """
        Check if an Order Block has been broken.

        Args:
            ob: OrderBlock to check
            df: Price data

        Returns:
            Tuple of (break_candle_index, break_candle) if broken, None otherwise
        """
        # Look for candles after the OB
        for i in range(ob.candle_index + 1, len(df)):
            candle = df.iloc[i]

            # Check for break based on OB direction
            if ob.direction == Direction.BEARISH:
                # Bearish OB is broken if price closes above its top
                if candle['close'] > ob.top:
                    return (i, candle)
            else:  # BULLISH
                # Bullish OB is broken if price closes below its bottom
                if candle['close'] < ob.bottom:
                    return (i, candle)

        return None

    def _calculate_break_displacement_factor(self, ob: OrderBlock, break_candle: pd.Series) -> float:
        """
        Calculate break displacement factor (0.0-1.0).

        Larger displacement when breaking = stronger Breaker Block.

        Args:
            ob: Original Order Block
            break_candle: Candle that broke the OB

        Returns:
            Displacement factor between 0.0 and 1.0
        """
        # Calculate how far price moved beyond the OB
        if ob.direction == Direction.BEARISH:
            # For bearish OB, measure upward break
            displacement = break_candle['close'] - ob.top
            reference = break_candle['high'] - break_candle['low']  # Candle range
        else:
            # For bullish OB, measure downward break
            displacement = ob.bottom - break_candle['close']
            reference = break_candle['high'] - break_candle['low']

        if reference == 0:
            return 0.5  # Default factor

        # Normalize displacement (0-1)
        # Strong break = displacement > 2x candle range
        factor = min(abs(displacement) / (2 * reference), 1.0)

        # Scale to 0.5-1.0 range (never less than 0.5)
        return 0.5 + (factor * 0.5)

    def _count_tests(self, bb: BreakerBlock, df: pd.DataFrame, start_idx: int) -> int:
        """
        Count how many times the Breaker Block has been tested.

        Args:
            bb: BreakerBlock to check
            df: Price data
            start_idx: Index to start checking from (after BB formation)

        Returns:
            Number of tests
        """
        tests = 0

        for i in range(start_idx + 1, len(df)):
            candle = df.iloc[i]

            # Check if candle tested the BB zone
            if bb.direction == Direction.BULLISH:
                # Bullish BB (support) - test from above
                if candle['low'] <= bb.top and candle['close'] >= bb.bottom:
                    tests += 1
            else:  # BEARISH
                # Bearish BB (resistance) - test from below
                if candle['high'] >= bb.bottom and candle['close'] <= bb.top:
                    tests += 1

        return tests

    def _update_status(self, bb: BreakerBlock, df: pd.DataFrame, start_idx: int) -> None:
        """
        Update Breaker Block status based on price action.

        Args:
            bb: BreakerBlock to update
            df: Price data
            start_idx: Index where BB was formed
        """
        # Check if BB has been tested
        if bb.tested_count > 0:
            bb.status = BreakerBlockStatus.TESTED

        # Check if BB has been broken
        for i in range(start_idx + 1, len(df)):
            candle = df.iloc[i]

            if bb.direction == Direction.BULLISH:
                # Bullish BB broken if price closes below bottom
                if candle['close'] < bb.bottom:
                    bb.status = BreakerBlockStatus.BROKEN
                    bb.broken_at = i
                    break
            else:  # BEARISH
                # Bearish BB broken if price closes above top
                if candle['close'] > bb.top:
                    bb.status = BreakerBlockStatus.BROKEN
                    bb.broken_at = i
                    break

    def get_active_breaker_blocks(self, breaker_blocks: List[BreakerBlock]) -> List[BreakerBlock]:
        """
        Filter for active (unbroken) Breaker Blocks.

        Args:
            breaker_blocks: List of all BreakerBlocks

        Returns:
            List of active BreakerBlocks
        """
        return [bb for bb in breaker_blocks if bb.status != BreakerBlockStatus.BROKEN]

    def get_quality_breaker_blocks(self, breaker_blocks: List[BreakerBlock],
                                  min_quality: float = 0.7) -> List[BreakerBlock]:
        """
        Filter for high-quality Breaker Blocks.

        Args:
            breaker_blocks: List of all BreakerBlocks
            min_quality: Minimum quality score (default 0.7)

        Returns:
            List of high-quality BreakerBlocks
        """
        return [bb for bb in breaker_blocks if bb.quality_score >= min_quality]