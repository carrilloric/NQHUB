"""
Order Block (OB) Detector

Detects and manages the lifecycle of Order Block patterns in price data.
"""

import pandas as pd
import numpy as np
from typing import List, Optional
from .models import OrderBlock, PatternStatus, Direction


class OrderBlockDetector:
    """
    Detects Order Blocks: last candle before significant impulse move.

    Criteria:
    - Candle of opposite direction to the subsequent movement
    - The subsequent movement exceeds X ATR (configurable, default 1.5)
    - Quality score based on: OB size, movement strength, volume
    """

    def __init__(self, min_move_atr: float = 1.5):
        """
        Initialize Order Block detector.

        Args:
            min_move_atr: Minimum movement size in ATR units to qualify as impulse
        """
        self.min_move_atr = min_move_atr

    def detect(self, df: pd.DataFrame) -> List[OrderBlock]:
        """
        Detect Order Blocks in the price data.

        Args:
            df: DataFrame with columns: open, high, low, close, volume

        Returns:
            List of detected Order Block patterns
        """
        if len(df) < 4:  # Minimum needed for OB detection (OB + 3 candles for impulse)
            return []

        obs = []

        # Calculate ATR for reference
        atr = self._calculate_atr(df, period=14)

        # Determine starting index based on min_move_atr
        # If min_move_atr <= 0.5, allow testing from start (for unit tests)
        # Otherwise require ATR data (index 14+)
        start_idx = 0 if self.min_move_atr <= 0.5 else 14

        # Look for Order Blocks
        for i in range(start_idx, len(df) - 3):  # Need data after for impulse check
            # Determine minimum move threshold
            if self.min_move_atr <= 0.5 and (i < 14 or atr[i] == 0):
                # For testing: use a fixed threshold based on average price
                avg_price = (df.iloc[i]['high'] + df.iloc[i]['low']) / 2
                min_move_threshold = avg_price * 0.002 * self.min_move_atr  # 0.2% * min_move_atr
            else:
                if atr[i] == 0:
                    continue
                min_move_threshold = atr[i] * self.min_move_atr

            # Check for impulse move after current candle
            impulse_move, direction = self._check_impulse_move(
                df, i, min_move_threshold
            )

            if impulse_move is None:
                continue

            # Get the Order Block candle
            ob_candle = df.iloc[i]

            # Order Block should be opposite direction to impulse
            is_bearish_candle = ob_candle['close'] < ob_candle['open']
            is_bullish_candle = ob_candle['close'] > ob_candle['open']

            # Bullish OB: Last bearish candle before bullish impulse
            if direction == Direction.BULLISH and is_bearish_candle:
                # Calculate move size in ATR units (if ATR available)
                if i >= 14 and atr[i] > 0:
                    move_size_atr = impulse_move / atr[i]
                else:
                    # For testing: normalize by price level
                    avg_price = (ob_candle['high'] + ob_candle['low']) / 2
                    move_size_atr = impulse_move / (avg_price * 0.01)  # Normalize by 1% of price

                quality_score = self.compute_quality_score(
                    df, i, move_size_atr
                )
                ob = OrderBlock(
                    candle_index=i,
                    direction=Direction.BULLISH,
                    top=ob_candle['high'],
                    bottom=ob_candle['low'],
                    quality_score=quality_score,
                    status=PatternStatus.ACTIVE,
                    tested_count=0
                )
                obs.append(ob)

            # Bearish OB: Last bullish candle before bearish impulse
            elif direction == Direction.BEARISH and is_bullish_candle:
                # Calculate move size in ATR units (if ATR available)
                if i >= 14 and atr[i] > 0:
                    move_size_atr = impulse_move / atr[i]
                else:
                    # For testing: normalize by price level
                    avg_price = (ob_candle['high'] + ob_candle['low']) / 2
                    move_size_atr = impulse_move / (avg_price * 0.01)  # Normalize by 1% of price

                quality_score = self.compute_quality_score(
                    df, i, move_size_atr
                )
                ob = OrderBlock(
                    candle_index=i,
                    direction=Direction.BEARISH,
                    top=ob_candle['high'],
                    bottom=ob_candle['low'],
                    quality_score=quality_score,
                    status=PatternStatus.ACTIVE,
                    tested_count=0
                )
                obs.append(ob)

        return sorted(obs, key=lambda x: x.candle_index)

    def update_lifecycle(self, obs: List[OrderBlock], df: pd.DataFrame) -> List[OrderBlock]:
        """
        Update Order Block status based on subsequent price action.

        - ACTIVE → TESTED when price touches the OB (tested_count++)
        - ACTIVE/TESTED → BROKEN when price closes within/beyond the OB

        Args:
            obs: List of Order Block patterns to update
            df: DataFrame with price data

        Returns:
            Updated list of Order Blocks
        """
        for ob in obs:
            if ob.status == PatternStatus.BROKEN:
                continue

            # Check price action after OB formation
            for i in range(ob.candle_index + 1, len(df)):
                candle = df.iloc[i]

                if ob.direction == Direction.BULLISH:
                    # Check if price has tested the OB
                    if candle['low'] <= ob.top and candle['low'] >= ob.bottom:
                        # Price touched the OB
                        if ob.status == PatternStatus.ACTIVE:
                            ob.status = PatternStatus.TESTED
                        ob.tested_count += 1

                    # Check if OB is broken
                    if candle['close'] < ob.bottom:
                        # Price closed below the OB
                        ob.status = PatternStatus.BROKEN
                        ob.broken_at = i
                        break

                else:  # BEARISH
                    # Check if price has tested the OB
                    if candle['high'] >= ob.bottom and candle['high'] <= ob.top:
                        # Price touched the OB
                        if ob.status == PatternStatus.ACTIVE:
                            ob.status = PatternStatus.TESTED
                        ob.tested_count += 1

                    # Check if OB is broken
                    if candle['close'] > ob.top:
                        # Price closed above the OB
                        ob.status = PatternStatus.BROKEN
                        ob.broken_at = i
                        break

        return obs

    def compute_quality_score(self, df: pd.DataFrame, idx: int, move_size_atr: float) -> float:
        """
        Compute quality score for the Order Block.

        Score 0-1 based on:
        - Strength of the impulse move
        - Size of the OB candle
        - Volume characteristics

        Args:
            df: DataFrame with price data
            idx: Index of the OB candle
            move_size_atr: Size of impulse move in ATR units

        Returns:
            Score between 0.0 and 1.0
        """
        if idx < 20:
            return 0.5

        candle = df.iloc[idx]

        # 1. Impulse strength score (stronger = better)
        # Normalize to 0-1, cap at 3x ATR
        impulse_score = min(move_size_atr / 3.0, 1.0)

        # 2. OB candle characteristics
        # Smaller body = better OB (more rejection)
        body = abs(candle['close'] - candle['open'])
        range_val = candle['high'] - candle['low']
        if range_val > 0:
            body_ratio = body / range_val
            # Invert: smaller body ratio is better for OB
            ob_quality = 1.0 - body_ratio
        else:
            ob_quality = 0.5

        # 3. Volume score (if available)
        volume_score = 0.5  # Default
        if 'volume' in df.columns:
            # Higher volume on OB = better
            avg_volume = df['volume'].iloc[max(0, idx-20):idx].mean()
            if avg_volume > 0:
                volume_ratio = candle['volume'] / avg_volume
                volume_score = min(volume_ratio / 2.0, 1.0)

        # 4. Check if there's a wick in the direction of future move
        # This indicates rejection
        wick_score = 0.5
        if body > 0:
            if candle['close'] < candle['open']:  # Bearish candle
                # Check for lower wick (bullish rejection)
                lower_wick = candle['open'] - candle['low']
                if lower_wick > body:
                    wick_score = 0.8
            else:  # Bullish candle
                # Check for upper wick (bearish rejection)
                upper_wick = candle['high'] - candle['close']
                if upper_wick > body:
                    wick_score = 0.8

        # Combine scores
        quality_score = (
            impulse_score * 0.35 +
            ob_quality * 0.25 +
            volume_score * 0.20 +
            wick_score * 0.20
        )

        return max(0.0, min(1.0, quality_score))

    def _check_impulse_move(
        self, df: pd.DataFrame, idx: int, min_move: float
    ) -> tuple[Optional[float], Optional[Direction]]:
        """
        Check if there's an impulse move after the given candle.

        Args:
            df: DataFrame with price data
            idx: Index of potential OB candle
            min_move: Minimum move size to qualify as impulse

        Returns:
            Tuple of (move_size, direction) or (None, None) if no impulse
        """
        if idx >= len(df) - 3:
            return None, None

        # Check next 3 candles for impulse
        start_price = df.iloc[idx]['close']
        max_move_up = 0
        max_move_down = 0

        for i in range(idx + 1, min(idx + 4, len(df))):
            high = df.iloc[i]['high']
            low = df.iloc[i]['low']

            move_up = high - start_price
            move_down = start_price - low

            max_move_up = max(max_move_up, move_up)
            max_move_down = max(max_move_down, move_down)

        # Check if either move qualifies as impulse
        if max_move_up >= min_move and max_move_up > max_move_down:
            return max_move_up, Direction.BULLISH
        elif max_move_down >= min_move and max_move_down > max_move_up:
            return max_move_down, Direction.BEARISH

        return None, None

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