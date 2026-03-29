"""
Order Flow Indicators

Calcula indicadores de segundo nivel a partir de los campos de order flow
que ya existen en cada candle (delta, poc, oflow_detail, etc.).

Los campos de order flow son pre-calculados durante la ingesta de datos y
almacenados en las tablas candlestick_{tf} de TimescaleDB. Este módulo
consume esos campos para producir indicadores de series de tiempo.

Author: NQHUB Research Team
"""

import json
import pandas as pd
import numpy as np
from typing import Optional


class OrderFlowIndicators:
    """
    Calcula indicadores de segundo nivel a partir de los campos
    de order flow que ya existen en cada candle.
    Trabaja sobre DataFrames de candles de TimescaleDB.

    Los campos esperados en el DataFrame de entrada:
    - delta: sum(bids) - sum(asks) de todos los niveles
    - poc: Point of Control a 1pt resolution
    - real_poc: POC a 0.25pt resolution
    - oflow_detail: JSONB con {"price": {"asks": N, "bids": M}, ...}
    - oflow_unit: JSONB con {"price": {"asks": N, "bids": M}, ...}
    - asellers_uwick: asks en upper wick
    - asellers_lwick: asks en lower wick
    - abuyers_uwick: bids en upper wick
    - abuyers_lwick: bids en lower wick
    - upper_wick_volume: volumen en upper wick
    - lower_wick_volume: volumen en lower wick
    - body_volume: volumen en el cuerpo
    - volume: volumen total
    - close: precio de cierre
    - open: precio de apertura
    - high: precio máximo
    - low: precio mínimo
    """

    def cvd(self, candles: pd.DataFrame) -> pd.Series:
        """
        Cumulative Volume Delta — suma acumulada del campo delta.

        CVD[i] = sum(delta[0..i])

        Muestra dominancia compradora/vendedora acumulada en la sesión.
        Un CVD creciente indica dominancia compradora sostenida.
        Un CVD decreciente indica dominancia vendedora sostenida.

        Args:
            candles: DataFrame con columna 'delta'

        Returns:
            pd.Series con el CVD acumulado

        Example:
            >>> candles = pd.DataFrame({'delta': [10, -5, 8]})
            >>> indicators = OrderFlowIndicators()
            >>> indicators.cvd(candles)
            0    10
            1     5
            2    13
            dtype: int64
        """
        if 'delta' not in candles.columns:
            raise ValueError("DataFrame must contain 'delta' column")

        return candles['delta'].cumsum()

    def poc_migration(self, candles: pd.DataFrame) -> pd.Series:
        """
        Cambio del POC de vela a vela.

        migration[i] = poc[i] - poc[i-1]

        Positivo = POC subió (mercado acepta precios más altos)
        Negativo = POC bajó (mercado rechaza precios altos)

        Args:
            candles: DataFrame con columna 'poc'

        Returns:
            pd.Series con el cambio del POC (primer valor es NaN)

        Example:
            >>> candles = pd.DataFrame({'poc': [18250, 18260, 18255]})
            >>> indicators = OrderFlowIndicators()
            >>> indicators.poc_migration(candles)
            0     NaN
            1    10.0
            2    -5.0
            dtype: float64
        """
        if 'poc' not in candles.columns:
            raise ValueError("DataFrame must contain 'poc' column")

        return candles['poc'].diff()

    def absorption_score(self, candles: pd.DataFrame) -> pd.Series:
        """
        Detecta absorción institucional: volumen alto sin movimiento de precio.

        score[i] = abs(delta[i]) / volume[i]

        Un ratio cercano a 0 indica absorción: mucho volumen pero delta balanceado.
        Un ratio cercano a 1 indica flujo direccional fuerte.

        Complementa con body_volume/volume para ver qué % del volumen
        fue en el rango del cuerpo vs las mechas.

        Args:
            candles: DataFrame con columnas 'delta' y 'volume'

        Returns:
            pd.Series con score entre 0.0 (absorción) y 1.0 (direccional)

        Example:
            >>> candles = pd.DataFrame({
            ...     'delta': [5, -2, 0],
            ...     'volume': [100, 100, 100]
            ... })
            >>> indicators = OrderFlowIndicators()
            >>> indicators.absorption_score(candles)
            0    0.05
            1    0.02
            2    0.00
            dtype: float64
        """
        if 'delta' not in candles.columns or 'volume' not in candles.columns:
            raise ValueError("DataFrame must contain 'delta' and 'volume' columns")

        # Evitar división por cero
        volume_safe = candles['volume'].replace(0, np.nan)
        score = candles['delta'].abs() / volume_safe

        # Clip to [0, 1] range (shouldn't exceed 1 but ensure it)
        return score.clip(0, 1).fillna(0)

    def footprint_imbalance(self, candles: pd.DataFrame) -> pd.Series:
        """
        Imbalance dominante en oflow_detail.

        Para cada candle, calcula el nivel de precio con mayor desbalance bid/ask.
        Retorna el desbalance normalizado: max(|bids-asks|/total) por nivel.

        Args:
            candles: DataFrame con columna 'oflow_detail' (JSONB o dict)

        Returns:
            pd.Series con imbalance score entre 0.0 (balanceado) y 1.0 (total imbalance)

        Example:
            >>> candles = pd.DataFrame({
            ...     'oflow_detail': [
            ...         '{"18250.25": {"asks": 10, "bids": 90}}',
            ...         '{"18250.50": {"asks": 50, "bids": 50}}'
            ...     ]
            ... })
            >>> indicators = OrderFlowIndicators()
            >>> indicators.footprint_imbalance(candles)
            0    0.80
            1    0.00
            dtype: float64
        """
        if 'oflow_detail' not in candles.columns:
            raise ValueError("DataFrame must contain 'oflow_detail' column")

        def calc_imbalance(oflow_detail):
            """Calculate max imbalance across all price levels in footprint"""
            if pd.isna(oflow_detail) or not oflow_detail:
                return 0.0

            # Parse JSON if string
            if isinstance(oflow_detail, str):
                try:
                    oflow_detail = json.loads(oflow_detail)
                except (json.JSONDecodeError, TypeError):
                    return 0.0

            if not isinstance(oflow_detail, dict):
                return 0.0

            max_imbalance = 0.0

            for price_level, flow_data in oflow_detail.items():
                if not isinstance(flow_data, dict):
                    continue

                asks = flow_data.get('asks', 0)
                bids = flow_data.get('bids', 0)
                total = asks + bids

                if total == 0:
                    continue

                imbalance = abs(bids - asks) / total
                max_imbalance = max(max_imbalance, imbalance)

            return max_imbalance

        return candles['oflow_detail'].apply(calc_imbalance)

    def delta_divergence(self, candles: pd.DataFrame) -> pd.Series:
        """
        Delta divergence: delta y precio se mueven en direcciones opuestas.

        divergence[i] = 1 si (delta[i] > 0 y close[i] < close[i-1])
                           o (delta[i] < 0 y close[i] > close[i-1])
                      = 0 en caso contrario

        Señal de posible reversión: el delta muestra una cosa pero el precio hace otra.

        Args:
            candles: DataFrame con columnas 'delta' y 'close'

        Returns:
            pd.Series con 1 para divergencia, 0 para no divergencia

        Example:
            >>> candles = pd.DataFrame({
            ...     'delta': [10, -5, 8],
            ...     'close': [18250, 18260, 18255]
            ... })
            >>> indicators = OrderFlowIndicators()
            >>> indicators.delta_divergence(candles)
            0    0
            1    0
            2    1
            dtype: int64
        """
        if 'delta' not in candles.columns or 'close' not in candles.columns:
            raise ValueError("DataFrame must contain 'delta' and 'close' columns")

        # Calculate price change
        price_change = candles['close'].diff()

        # Bearish divergence: positive delta but price falls
        bearish_div = (candles['delta'] > 0) & (price_change < 0)

        # Bullish divergence: negative delta but price rises
        bullish_div = (candles['delta'] < 0) & (price_change > 0)

        # Return 1 for divergence, 0 otherwise
        divergence = (bearish_div | bullish_div).astype(int)

        # First value is always 0 (no previous candle to compare)
        divergence.iloc[0] = 0

        return divergence

    def wick_absorption_ratio(self, candles: pd.DataFrame, wick: str = 'upper') -> pd.Series:
        """
        Ratio de absorción en wicks.

        Para upper wick: abuyers_uwick / (asellers_uwick + abuyers_uwick)
        Para lower wick: abuyers_lwick / (asellers_lwick + abuyers_lwick)

        Alto (>0.7) = compradores absorbiendo presión vendedora en la mecha
        Bajo (<0.3) = vendedores dominando en la mecha

        Args:
            candles: DataFrame con columnas de wick absorption
            wick: 'upper' o 'lower' para seleccionar la mecha a analizar

        Returns:
            pd.Series con ratio entre 0.0 (vendedores) y 1.0 (compradores)

        Example:
            >>> candles = pd.DataFrame({
            ...     'abuyers_uwick': [80, 20],
            ...     'asellers_uwick': [20, 80]
            ... })
            >>> indicators = OrderFlowIndicators()
            >>> indicators.wick_absorption_ratio(candles, wick='upper')
            0    0.80
            1    0.20
            dtype: float64
        """
        if wick == 'upper':
            buyers_col = 'abuyers_uwick'
            sellers_col = 'asellers_uwick'
        elif wick == 'lower':
            buyers_col = 'abuyers_lwick'
            sellers_col = 'asellers_lwick'
        else:
            raise ValueError("wick must be 'upper' or 'lower'")

        if buyers_col not in candles.columns or sellers_col not in candles.columns:
            raise ValueError(f"DataFrame must contain '{buyers_col}' and '{sellers_col}' columns")

        buyers = candles[buyers_col]
        sellers = candles[sellers_col]
        total = buyers + sellers

        # Evitar división por cero
        total_safe = total.replace(0, np.nan)
        ratio = buyers / total_safe

        # Fill NaN with 0.5 (neutral when no wick activity)
        return ratio.fillna(0.5).clip(0, 1)
