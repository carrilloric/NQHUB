"""
Performance Metrics Calculator for NQ Futures Trading

Calcula métricas de performance para backtests y live trading.
Lógica pura Python/NumPy — sin librerías de backtesting.
Incluye el Deflated Sharpe Ratio de López de Prado para detectar overfitting.

Author: Ricardo Carrillo
Date: 2026-03-29
Reference: López de Prado, "Advances in Financial Machine Learning", Cap. 8
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class PerformanceReport:
    """Report completo de métricas de performance"""
    # Retornos
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    deflated_sharpe_ratio: float   # López de Prado

    # Drawdown
    max_drawdown_pct: float        # ej: -0.15 (-15%)
    max_drawdown_usd: float        # ej: -3750.0

    # Trades
    total_trades: int
    win_rate: float                # 0.0 a 1.0
    profit_factor: float
    avg_win_usd: float
    avg_loss_usd: float
    expectancy_usd: float          # (win_rate * avg_win) - (loss_rate * avg_loss)

    # NQ específico
    total_pnl_usd: float
    total_pnl_ticks: float         # pnl / tick_value


class PerformanceMetrics:
    """
    Calcula métricas de performance estándar sobre una serie de retornos o trades.
    Input: pd.Series de retornos diarios o pd.DataFrame de trades.
    Output: PerformanceReport dataclass.
    """

    # Constantes NQ Futures
    TICK_SIZE = 0.25
    TICK_VALUE = 5.0      # USD por tick
    POINT_VALUE = 20.0    # USD por punto

    def sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252
    ) -> float:
        """
        Sharpe = (mean(returns) - risk_free_rate) / std(returns) * sqrt(periods_per_year)
        Retorna 0.0 si std=0.

        Args:
            returns: Serie de retornos periódicos
            risk_free_rate: Tasa libre de riesgo (default 0)
            periods_per_year: Períodos de trading por año (252 para diario)

        Returns:
            Sharpe ratio anualizado
        """
        if len(returns) == 0:
            return 0.0

        returns_std = returns.std()
        # Manejar casos especiales
        if returns_std == 0 or np.isnan(returns_std) or returns_std < 1e-10:
            return 0.0

        excess_returns = returns.mean() - risk_free_rate
        sharpe = (excess_returns / returns_std) * np.sqrt(periods_per_year)

        return float(sharpe)

    def sortino_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252
    ) -> float:
        """
        Como Sharpe pero solo penaliza downside volatility.
        Sortino = (mean(returns) - risk_free_rate) / downside_std * sqrt(periods)
        downside_std = std de retornos negativos únicamente.

        Args:
            returns: Serie de retornos periódicos
            risk_free_rate: Tasa libre de riesgo (default 0)
            periods_per_year: Períodos de trading por año

        Returns:
            Sortino ratio anualizado
        """
        if len(returns) == 0:
            return 0.0

        # Solo considerar retornos negativos para downside deviation
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0:
            # No hay retornos negativos, retornar un valor alto
            return float('inf') if returns.mean() > risk_free_rate else 0.0

        downside_std = np.sqrt(np.mean(downside_returns ** 2))

        if downside_std == 0 or np.isnan(downside_std):
            return 0.0

        excess_returns = returns.mean() - risk_free_rate
        sortino = (excess_returns / downside_std) * np.sqrt(periods_per_year)

        return float(sortino)

    def calmar_ratio(
        self,
        returns: pd.Series,
        periods_per_year: int = 252
    ) -> float:
        """
        Calmar = annualized_return / abs(max_drawdown)
        Mide retorno ajustado por el peor drawdown histórico.

        Args:
            returns: Serie de retornos periódicos
            periods_per_year: Períodos de trading por año

        Returns:
            Calmar ratio
        """
        if len(returns) == 0:
            return 0.0

        # Calcular retorno anualizado
        total_return = (1 + returns).prod() - 1
        n_periods = len(returns)
        annualized_return = (1 + total_return) ** (periods_per_year / n_periods) - 1

        # Calcular equity curve para max drawdown
        equity_curve = (1 + returns).cumprod()
        max_dd = self.max_drawdown(equity_curve)

        if max_dd == 0:
            return float('inf') if annualized_return > 0 else 0.0

        calmar = annualized_return / abs(max_dd)

        return float(calmar)

    def max_drawdown(self, equity_curve: pd.Series) -> float:
        """
        Drawdown máximo pico a valle de la equity curve.
        MDD = min((equity - cummax(equity)) / cummax(equity))
        Retorna valor negativo (ej: -0.15 = -15%).

        Args:
            equity_curve: Serie temporal de equity/capital

        Returns:
            Max drawdown como valor negativo (ej: -0.15)
        """
        if len(equity_curve) == 0:
            return 0.0

        # Calcular running maximum
        running_max = equity_curve.expanding().max()

        # Calcular drawdown en cada punto
        drawdown = (equity_curve - running_max) / running_max

        # Retornar el peor drawdown (más negativo)
        max_dd = drawdown.min()

        return float(max_dd) if not np.isnan(max_dd) else 0.0

    def max_drawdown_usd(self, equity_curve: pd.Series) -> float:
        """
        MDD en USD absoluto — más relevante para Apex compliance.

        Args:
            equity_curve: Serie temporal de equity en USD

        Returns:
            Max drawdown en USD (valor negativo)
        """
        if len(equity_curve) == 0:
            return 0.0

        # Calcular running maximum
        running_max = equity_curve.expanding().max()

        # Calcular drawdown en USD
        drawdown_usd = equity_curve - running_max

        # Retornar el peor drawdown en USD
        max_dd_usd = drawdown_usd.min()

        return float(max_dd_usd) if not np.isnan(max_dd_usd) else 0.0

    def profit_factor(self, trades: pd.DataFrame) -> float:
        """
        Profit Factor = gross_profit / abs(gross_loss)
        trades debe tener columna 'pnl'.
        Retorna inf si no hay trades perdedores.

        Args:
            trades: DataFrame con columna 'pnl'

        Returns:
            Profit factor
        """
        if len(trades) == 0 or 'pnl' not in trades.columns:
            return 0.0

        winning_trades = trades[trades['pnl'] > 0]
        losing_trades = trades[trades['pnl'] < 0]

        gross_profit = winning_trades['pnl'].sum() if len(winning_trades) > 0 else 0.0
        gross_loss = abs(losing_trades['pnl'].sum()) if len(losing_trades) > 0 else 0.0

        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0

        return float(gross_profit / gross_loss)

    def win_rate(self, trades: pd.DataFrame) -> float:
        """
        Win Rate = winning_trades / total_trades
        Retorna valor entre 0.0 y 1.0.

        Args:
            trades: DataFrame con columna 'pnl'

        Returns:
            Win rate como fracción (0.0 a 1.0)
        """
        if len(trades) == 0 or 'pnl' not in trades.columns:
            return 0.0

        winning_trades = (trades['pnl'] > 0).sum()
        total_trades = len(trades)

        if total_trades == 0:
            return 0.0

        return float(winning_trades / total_trades)

    def deflated_sharpe_ratio(
        self,
        sharpe_ratio: float,
        n_trials: int,
        n_observations: int,
        skewness: float = 0.0,
        kurtosis: float = 3.0
    ) -> float:
        """
        Deflated Sharpe Ratio (López de Prado, 2018).
        Ajusta el Sharpe por múltiples trials de backtest — detecta overfitting.

        DSR = Probabilidad de que el Sharpe sea genuino dado múltiples backtests.

        La fórmula considera el efecto de múltiples pruebas (multiple testing)
        y ajusta por los momentos de orden superior de la distribución.

        Args:
            sharpe_ratio: Sharpe ratio observado
            n_trials: Número de estrategias/backtests probados
            n_observations: Número de observaciones (días de trading)
            skewness: Asimetría de los retornos (default 0)
            kurtosis: Curtosis de los retornos (default 3 para normal)

        Returns:
            Probabilidad de que el Sharpe sea genuino (0.0 a 1.0)
            DSR > 0.95 = Sharpe probablemente genuino
            DSR < 0.95 = Posible overfitting

        Reference:
            López de Prado, "Advances in Financial Machine Learning", Cap. 8
        """
        if n_trials <= 0 or n_observations <= 1:
            return 0.0

        # Función auxiliar para calcular la función de distribución normal inversa (ppf)
        def norm_ppf(p):
            """Aproximación de la función cuantil normal usando la aproximación de Abramowitz y Stegun"""
            if p <= 0:
                return -np.inf
            if p >= 1:
                return np.inf

            # Aproximación racional para la función cuantil normal
            c0 = 2.515517
            c1 = 0.802853
            c2 = 0.010328
            d1 = 1.432788
            d2 = 0.189269
            d3 = 0.001308

            if p < 0.5:
                t = np.sqrt(-2 * np.log(p))
                return -(t - ((c2*t + c1)*t + c0) / (((d3*t + d2)*t + d1)*t + 1))
            else:
                t = np.sqrt(-2 * np.log(1 - p))
                return t - ((c2*t + c1)*t + c0) / (((d3*t + d2)*t + d1)*t + 1)

        # Función auxiliar para calcular la CDF normal
        def norm_cdf(x):
            """Función de distribución acumulada normal usando error function"""
            return 0.5 * (1 + math.erf(x / np.sqrt(2)))

        # Deflated Sharpe Ratio (Simplified Implementation)
        # Adjusts Sharpe ratio confidence for multiple testing bias

        # Note: This is a simplified implementation that penalizes for multiple trials.
        # The exact López de Prado formula requires more complex calculations
        # involving the distribution of order statistics.

        # Step 1: Calculate statistical significance of observed Sharpe
        # Adjust variance for non-normal returns
        var_factor = 1 - skewness * sharpe_ratio + ((kurtosis - 3) / 4) * sharpe_ratio**2
        if var_factor <= 0:
            var_factor = 1.0

        # Standard error and z-score
        sr_se = np.sqrt(var_factor / n_observations)
        z_observed = sharpe_ratio / sr_se

        # Step 2: Adjust for multiple testing
        # With n_trials, we need a higher z-score to maintain the same confidence
        # Using Bonferroni-inspired adjustment

        # Expected maximum z-score from n_trials random strategies
        if n_trials > 1:
            # Approximate expected maximum of n standard normals
            z_expected_max = np.sqrt(2 * np.log(n_trials))
        else:
            z_expected_max = 0.0

        # Step 3: Calculate adjusted z-score
        # Penalize based on how much selection bias we have
        # The more trials, the higher the penalty

        # Simple linear interpolation between observed z and adjusted z
        # Weight depends on number of trials
        selection_bias_factor = min(1.0, np.log(n_trials + 1) / 10)  # Caps at ~1.0 for n=22000

        # Adjusted z-score accounts for selection bias
        z_adjusted = z_observed - selection_bias_factor * z_expected_max

        # Step 4: Convert to probability
        # Use normal CDF of adjusted z-score
        dsr = norm_cdf(z_adjusted)

        # Additional penalty for extreme multiple testing
        # This ensures DSR decreases with more trials even for very high Sharpe ratios
        if n_trials > 1:
            # Penalty increases with log of trials
            multiple_testing_penalty = (np.log(n_trials) / np.log(100)) * 0.1  # 0.1 penalty at n=100
            dsr = dsr * (1 - multiple_testing_penalty)

        # Ensure DSR is properly bounded
        dsr = max(0.0, min(1.0, dsr))

        return float(np.clip(dsr, 0.0, 1.0))

    def calculate_all(
        self,
        equity_curve: pd.Series,
        trades: pd.DataFrame,
        n_trials: int = 1,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252
    ) -> PerformanceReport:
        """
        Calcula todas las métricas y retorna PerformanceReport.

        Args:
            equity_curve: Serie temporal de equity en USD
            trades: DataFrame con columna 'pnl'
            n_trials: Número de backtests/estrategias probadas
            risk_free_rate: Tasa libre de riesgo
            periods_per_year: Períodos de trading por año

        Returns:
            PerformanceReport con todas las métricas calculadas
        """
        # Calcular retornos a partir de equity curve
        returns = equity_curve.pct_change().dropna()

        # Métricas de retorno
        sharpe = self.sharpe_ratio(returns, risk_free_rate, periods_per_year)
        sortino = self.sortino_ratio(returns, risk_free_rate, periods_per_year)
        calmar = self.calmar_ratio(returns, periods_per_year)

        # Calcular skewness y kurtosis para Deflated Sharpe
        skewness = float(returns.skew()) if len(returns) > 0 else 0.0
        kurtosis = float(returns.kurtosis() + 3) if len(returns) > 0 else 3.0  # Convertir a no-excess

        deflated_sharpe = self.deflated_sharpe_ratio(
            sharpe, n_trials, len(returns),
            skewness, kurtosis
        )

        # Métricas de drawdown
        max_dd_pct = self.max_drawdown(equity_curve)
        max_dd_usd = self.max_drawdown_usd(equity_curve)

        # Métricas de trades
        if len(trades) > 0 and 'pnl' in trades.columns:
            total_trades = len(trades)
            win_rate_val = self.win_rate(trades)
            profit_factor_val = self.profit_factor(trades)

            winning_trades = trades[trades['pnl'] > 0]
            losing_trades = trades[trades['pnl'] < 0]

            avg_win_usd = float(winning_trades['pnl'].mean()) if len(winning_trades) > 0 else 0.0
            avg_loss_usd = float(losing_trades['pnl'].mean()) if len(losing_trades) > 0 else 0.0

            # Expectancy = (win_rate * avg_win) + (loss_rate * avg_loss)
            # Nota: avg_loss ya es negativo
            loss_rate = 1 - win_rate_val
            expectancy_usd = (win_rate_val * avg_win_usd) + (loss_rate * avg_loss_usd)

            total_pnl_usd = float(trades['pnl'].sum())
            total_pnl_ticks = total_pnl_usd / self.TICK_VALUE
        else:
            # Valores por defecto si no hay trades
            total_trades = 0
            win_rate_val = 0.0
            profit_factor_val = 0.0
            avg_win_usd = 0.0
            avg_loss_usd = 0.0
            expectancy_usd = 0.0
            total_pnl_usd = 0.0
            total_pnl_ticks = 0.0

        return PerformanceReport(
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            deflated_sharpe_ratio=deflated_sharpe,
            max_drawdown_pct=max_dd_pct,
            max_drawdown_usd=max_dd_usd,
            total_trades=total_trades,
            win_rate=win_rate_val,
            profit_factor=profit_factor_val,
            avg_win_usd=avg_win_usd,
            avg_loss_usd=avg_loss_usd,
            expectancy_usd=expectancy_usd,
            total_pnl_usd=total_pnl_usd,
            total_pnl_ticks=total_pnl_ticks
        )