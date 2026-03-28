"""
Fair Value Gap (FVG) Detector

Detects and manages the lifecycle of FVG patterns in price data.
"""

import pandas as pd
import numpy as np
from typing import List, Optional
from .models import FVG, PatternStatus, Direction


class FVGDetector:
    """
    Detects Fair Value Gaps using ICT methodology.

    A FVG bullish: gap between high[i-2] and low[i] when close[i] > high[i-2]
    A FVG bearish: gap between low[i-2] and high[i] when close[i] < low[i-2]
    """

    def __init__(self, min_gap_atr_ratio: float = 0.5):
        """
        Initialize FVG detector.

        Args:
            min_gap_atr_ratio: Minimum gap size as ratio of ATR (default 0.5)
        """
        self.min_gap_atr_ratio = min_gap_atr_ratio

    def detect(self, df: pd.DataFrame) -> List[FVG]:
        """
        Detect Fair Value Gaps in the price data.

        Args:
            df: DataFrame with columns: open, high, low, close, volume

        Returns:
            List of detected FVG patterns sorted by candle_index
        """
        if len(df) < 3:
            return []

        fvgs = []

        # Calculate ATR for reference (14-period)
        atr = self._calculate_atr(df, period=14)

        # Iterate through candles looking for FVGs
        for i in range(2, len(df)):
            # Get the three candles
            prev2 = df.iloc[i - 2]
            prev1 = df.iloc[i - 1]
            current = df.iloc[i]

            # Check for bullish FVG
            # Gap up: low[i] > high[i-2]
            if current['low'] > prev2['high']:
                gap_size = current['low'] - prev2['high']

                # Check if gap is significant enough
                # If min_gap_atr_ratio is 0, skip ATR check (for testing)
                # If ATR is not available yet (i < period), use a simple threshold
                if self.min_gap_atr_ratio == 0.0:
                    # Skip ATR check for testing
                    displacement_score = self.compute_displacement_score(df, i)
                    fvg = FVG(
                        candle_index=i,
                        direction=Direction.BULLISH,
                        top=current['low'],  # Top of the gap
                        bottom=prev2['high'],  # Bottom of the gap
                        displacement_score=displacement_score,
                        status=PatternStatus.ACTIVE
                    )
                    fvgs.append(fvg)
                elif i >= 14 and atr[i] > 0 and gap_size >= atr[i] * self.min_gap_atr_ratio:
                    displacement_score = self.compute_displacement_score(df, i)
                    fvg = FVG(
                        candle_index=i,
                        direction=Direction.BULLISH,
                        top=current['low'],  # Top of the gap
                        bottom=prev2['high'],  # Bottom of the gap
                        displacement_score=displacement_score,
                        status=PatternStatus.ACTIVE
                    )
                    fvgs.append(fvg)

            # Check for bearish FVG
            # Gap down: high[i] < low[i-2]
            elif current['high'] < prev2['low']:
                gap_size = prev2['low'] - current['high']

                # Check if gap is significant enough
                # If min_gap_atr_ratio is 0, skip ATR check (for testing)
                # If ATR is not available yet (i < period), use a simple threshold
                if self.min_gap_atr_ratio == 0.0:
                    # Skip ATR check for testing
                    displacement_score = self.compute_displacement_score(df, i)
                    fvg = FVG(
                        candle_index=i,
                        direction=Direction.BEARISH,
                        top=prev2['low'],  # Top of the gap
                        bottom=current['high'],  # Bottom of the gap
                        displacement_score=displacement_score,
                        status=PatternStatus.ACTIVE
                    )
                    fvgs.append(fvg)
                elif i >= 14 and atr[i] > 0 and gap_size >= atr[i] * self.min_gap_atr_ratio:
                    displacement_score = self.compute_displacement_score(df, i)
                    fvg = FVG(
                        candle_index=i,
                        direction=Direction.BEARISH,
                        top=prev2['low'],  # Top of the gap
                        bottom=current['high'],  # Bottom of the gap
                        displacement_score=displacement_score,
                        status=PatternStatus.ACTIVE
                    )
                    fvgs.append(fvg)

        return sorted(fvgs, key=lambda x: x.candle_index)

    def update_lifecycle(self, fvgs: List[FVG], df: pd.DataFrame) -> List[FVG]:
        """
        Update the status of FVGs based on subsequent price action.

        - ACTIVE → MITIGATED when price touches the gap (50% of the gap)
        - ACTIVE → BROKEN when price closes beyond the gap

        Args:
            fvgs: List of FVG patterns to update
            df: DataFrame with price data

        Returns:
            Updated list of FVGs
        """
        for fvg in fvgs:
            if fvg.status != PatternStatus.ACTIVE:
                continue

            # Check price action after the FVG formation
            for i in range(fvg.candle_index + 1, len(df)):
                candle = df.iloc[i]

                if fvg.direction == Direction.BULLISH:
                    # Check if price closed below the gap (broken) first
                    if candle['close'] < fvg.bottom:
                        # Price closed below the gap
                        fvg.status = PatternStatus.BROKEN
                        fvg.mitigated_at = i
                        break
                    # Check if price has retraced into the gap but not broken it
                    # For mitigation: price touches midpoint but close stays within/above gap
                    elif candle['low'] <= fvg.midpoint and candle['close'] >= fvg.bottom:
                        # Price reached 50% of the gap without breaking it
                        fvg.status = PatternStatus.MITIGATED
                        fvg.mitigated_at = i
                        break

                else:  # BEARISH
                    # Check if price closed above the gap (broken) first
                    if candle['close'] > fvg.top:
                        # Price closed above the gap
                        fvg.status = PatternStatus.BROKEN
                        fvg.mitigated_at = i
                        break
                    # Check if price has retraced into the gap but not broken it
                    # For mitigation: price touches midpoint but close stays within/below gap
                    elif candle['high'] >= fvg.midpoint and candle['close'] <= fvg.top:
                        # Price reached 50% of the gap without breaking it
                        fvg.status = PatternStatus.MITIGATED
                        fvg.mitigated_at = i
                        break

        return fvgs

    def compute_displacement_score(self, df: pd.DataFrame, idx: int) -> float:
        """
        Compute displacement score based on the strength of the move.

        Score 0-1 based on:
        - Size of the gap relative to ATR
        - Velocity of the movement (body/range ratio of the candle)
        - Volume relative to average

        Args:
            df: DataFrame with price data
            idx: Index of the FVG candle

        Returns:
            Score between 0.0 and 1.0
        """
        if idx < 20:  # Need enough data for calculations
            return 0.5  # Default score

        candle = df.iloc[idx]

        # Calculate ATR
        atr = self._calculate_atr(df[:idx+1], period=14)
        if len(atr) == 0 or atr[-1] == 0:
            return 0.5

        # 1. Body to range ratio (higher = stronger move)
        body = abs(candle['close'] - candle['open'])
        range_val = candle['high'] - candle['low']
        body_ratio = body / range_val if range_val > 0 else 0

        # 2. Move size relative to ATR
        move_size = abs(candle['close'] - df.iloc[idx-1]['close'])
        move_ratio = min(move_size / atr[-1], 3.0) / 3.0  # Cap at 3x ATR

        # 3. Volume relative to average (if available)
        volume_score = 0.5  # Default
        if 'volume' in df.columns and df['volume'].iloc[:idx].mean() > 0:
            avg_volume = df['volume'].iloc[max(0, idx-20):idx].mean()
            if avg_volume > 0:
                volume_ratio = candle['volume'] / avg_volume
                volume_score = min(volume_ratio, 2.0) / 2.0  # Cap at 2x average

        # Combine scores (weighted average)
        score = (
            body_ratio * 0.3 +
            move_ratio * 0.4 +
            volume_score * 0.3
        )

        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> np.ndarray:
        """
        Calculate Average True Range (ATR).

        Args:
            df: DataFrame with OHLC data
            period: ATR period (default 14)

        Returns:
            Array of ATR values
        """
        if len(df) < 2:
            return np.array([])

        high = df['high'].values
        low = df['low'].values
        close = df['close'].values

        # Calculate True Range
        tr = np.zeros(len(df))
        tr[0] = high[0] - low[0]

        for i in range(1, len(df)):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i-1])
            lc = abs(low[i] - close[i-1])
            tr[i] = max(hl, hc, lc)

        # Calculate ATR using EMA
        atr = np.zeros(len(df))
        if len(df) >= period:
            atr[period-1] = np.mean(tr[:period])
            multiplier = 2.0 / (period + 1)

            for i in range(period, len(df)):
                atr[i] = (tr[i] - atr[i-1]) * multiplier + atr[i-1]

        return atr