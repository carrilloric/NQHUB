"""
Liquidity Pool Detector

Detects and manages the lifecycle of Liquidity Pool patterns using smartmoneyconcepts.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from enum import Enum

try:
    from smartmoneyconcepts import smc
except ImportError:
    import warnings
    warnings.warn("smartmoneyconcepts not installed. Some features will be limited.")
    smc = None


class LiquidityPoolType(str, Enum):
    """Type of Liquidity Pool"""
    EQH = "EQH"  # Equal Highs (bearish liquidity)
    EQL = "EQL"  # Equal Lows (bullish liquidity)


class LiquidityPoolStatus(str, Enum):
    """Status of a Liquidity Pool"""
    ACTIVE = "active"
    SWEPT = "swept"
    BROKEN = "broken"


@dataclass
class LiquidityPool:
    """
    Liquidity Pool pattern

    Represents areas where stop-losses accumulate, creating liquidity for institutional traders.
    """
    id: str
    timeframe: str
    type: LiquidityPoolType
    price_level: float  # Central price level of the zone
    zone_top: float    # Top of the liquidity zone
    zone_bottom: float  # Bottom of the liquidity zone
    tolerance_ticks: int = 4  # Ticks of tolerance for "equal" levels
    touches: int = 2  # Number of times price touched this level
    formation_time: datetime = None
    status: LiquidityPoolStatus = LiquidityPoolStatus.ACTIVE
    swept_at: Optional[datetime] = None
    sweep_candle_id: Optional[str] = None
    sweep_score: float = 0.0  # Probability of sweep (0.0-1.0)

    @property
    def zone_size(self) -> float:
        """Size of the liquidity zone in price units"""
        return self.zone_top - self.zone_bottom

    def __repr__(self) -> str:
        return (f"LiquidityPool(id={self.id}, {self.type.value}, "
                f"level={self.price_level:.2f}, touches={self.touches}, "
                f"status={self.status.value})")


class LiquidityPoolDetector:
    """
    Detects Liquidity Pools using smartmoneyconcepts library.

    Wraps smc.liquidity() to detect EQH/EQL zones and manages their lifecycle.
    """

    def __init__(self, range_percent: float = 0.01, min_touches: int = 2):
        """
        Initialize Liquidity Pool detector.

        Args:
            range_percent: Range tolerance for equal levels (default 1%)
            min_touches: Minimum touches to form valid pool (default 2)
        """
        self.range_percent = range_percent
        self.min_touches = min_touches

    def detect(self, df: pd.DataFrame, timeframe: str) -> List[LiquidityPool]:
        """
        Detect Liquidity Pools in the price data.

        Args:
            df: DataFrame with columns: open, high, low, close, volume, datetime
            timeframe: Timeframe string (e.g., "5m", "15m", "1h")

        Returns:
            List of detected LiquidityPool patterns
        """
        if smc is None:
            raise ImportError("smartmoneyconcepts is required for liquidity pool detection")

        if len(df) < 20:  # Need minimum data for swing analysis
            return []

        pools = []

        # Detect swing highs and lows first
        swing_highs_lows = smc.swing_highs_lows(df)

        # Detect liquidity pools using SMC
        liquidity_result = smc.liquidity(
            df,
            swing_highs_lows,
            range_percent=self.range_percent
        )

        # Process results
        for i in range(len(liquidity_result)):
            if liquidity_result['Liquidity'][i] != 0:
                # Get pool information
                pool_type = LiquidityPoolType.EQL if liquidity_result['Liquidity'][i] == 1 else LiquidityPoolType.EQH
                price_level = liquidity_result['Level'][i]

                # Calculate zone boundaries (tolerance based on tick size)
                tick_size = self._estimate_tick_size(df)
                tolerance = tick_size * 4  # Default 4 ticks tolerance

                zone_top = price_level + tolerance
                zone_bottom = price_level - tolerance

                # Count touches
                touches = self._count_touches(df, price_level, tolerance, i)

                # Skip if not enough touches
                if touches < self.min_touches:
                    continue

                # Check if swept
                status = LiquidityPoolStatus.ACTIVE
                swept_at = None
                sweep_candle_id = None

                if liquidity_result['Swept'][i] == 1:
                    status = LiquidityPoolStatus.SWEPT
                    swept_at = df.iloc[liquidity_result['End'][i]]['datetime']
                    sweep_candle_id = str(liquidity_result['End'][i])

                # Create LiquidityPool object
                pool = LiquidityPool(
                    id=f"LP_{timeframe}_{i}_{pool_type.value}",
                    timeframe=timeframe,
                    type=pool_type,
                    price_level=price_level,
                    zone_top=zone_top,
                    zone_bottom=zone_bottom,
                    tolerance_ticks=4,
                    touches=touches,
                    formation_time=df.iloc[i]['datetime'],
                    status=status,
                    swept_at=swept_at,
                    sweep_candle_id=sweep_candle_id,
                    sweep_score=self.calculate_sweep_score(pool_type, touches, df, i)
                )

                pools.append(pool)

        return pools

    def calculate_sweep_score(self, pool_type: LiquidityPoolType, touches: int,
                            df: pd.DataFrame, current_idx: int) -> float:
        """
        Calculate sweep probability score (0.0-1.0).

        Factors:
        - Number of touches (more touches = higher score)
        - Time since formation (older = higher score)
        - Volume at level (higher volume = higher score)

        Args:
            pool_type: Type of liquidity pool
            touches: Number of times price touched the level
            df: Price data
            current_idx: Current candle index

        Returns:
            Sweep score between 0.0 and 1.0
        """
        score = 0.0

        # Factor 1: Touch count (max 0.4)
        touch_score = min(touches / 5.0, 1.0) * 0.4
        score += touch_score

        # Factor 2: Age of pool (max 0.3)
        if current_idx > 20:
            age = min((current_idx - 20) / 100.0, 1.0) * 0.3
            score += age

        # Factor 3: Volume concentration (max 0.3)
        if 'volume' in df.columns:
            avg_volume = df['volume'].rolling(20).mean().iloc[current_idx]
            recent_volume = df['volume'].iloc[max(0, current_idx-5):current_idx].mean()
            if avg_volume > 0:
                volume_ratio = min(recent_volume / avg_volume, 2.0) / 2.0
                score += volume_ratio * 0.3

        return min(score, 1.0)

    def update_status(self, pool: LiquidityPool, df: pd.DataFrame) -> None:
        """
        Update the status of a liquidity pool based on recent price action.

        Args:
            pool: LiquidityPool to update
            df: Recent price data
        """
        if pool.status != LiquidityPoolStatus.ACTIVE:
            return  # Already swept or broken

        last_candle = df.iloc[-1]

        # Check for sweep (wick touches but body doesn't close beyond)
        if pool.type == LiquidityPoolType.EQH:
            # Bearish liquidity - check if high swept but close below
            if last_candle['high'] > pool.zone_top and last_candle['close'] <= pool.zone_top:
                pool.status = LiquidityPoolStatus.SWEPT
                pool.swept_at = last_candle['datetime']
                pool.sweep_candle_id = str(len(df) - 1)
        else:  # EQL
            # Bullish liquidity - check if low swept but close above
            if last_candle['low'] < pool.zone_bottom and last_candle['close'] >= pool.zone_bottom:
                pool.status = LiquidityPoolStatus.SWEPT
                pool.swept_at = last_candle['datetime']
                pool.sweep_candle_id = str(len(df) - 1)

        # Check for break (body closes beyond)
        if pool.type == LiquidityPoolType.EQH:
            if last_candle['close'] > pool.zone_top:
                pool.status = LiquidityPoolStatus.BROKEN
        else:  # EQL
            if last_candle['close'] < pool.zone_bottom:
                pool.status = LiquidityPoolStatus.BROKEN

    def _count_touches(self, df: pd.DataFrame, level: float, tolerance: float,
                      end_idx: int) -> int:
        """
        Count how many times price touched a level within tolerance.

        Args:
            df: Price data
            level: Price level to check
            tolerance: Tolerance for considering a touch
            end_idx: Index to stop counting

        Returns:
            Number of touches
        """
        touches = 0
        for i in range(min(end_idx, len(df))):
            high = df.iloc[i]['high']
            low = df.iloc[i]['low']

            # Check if candle touched the zone
            if (abs(high - level) <= tolerance or
                abs(low - level) <= tolerance):
                touches += 1

        return touches

    def _estimate_tick_size(self, df: pd.DataFrame) -> float:
        """
        Estimate tick size from price data.

        For NQ futures, typically 0.25

        Args:
            df: Price data

        Returns:
            Estimated tick size
        """
        # For NQ futures
        return 0.25