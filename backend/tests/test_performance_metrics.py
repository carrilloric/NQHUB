"""
Tests para Performance Metrics Calculator

Tests usando datos sintéticos — no necesita DB.
Verifica todas las métricas de performance incluyendo Deflated Sharpe Ratio.

Author: Ricardo Carrillo
Date: 2026-03-29
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from app.research.metrics.performance import PerformanceMetrics, PerformanceReport


class TestPerformanceMetrics:
    """Test suite para PerformanceMetrics"""

    @pytest.fixture
    def metrics(self):
        """Fixture para instancia de PerformanceMetrics"""
        return PerformanceMetrics()

    @pytest.fixture
    def positive_returns(self):
        """Serie de retornos positivos consistentes"""
        # Simular 252 días de retornos positivos (1 año)
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.01, 252))
        returns = returns.abs()  # Hacer todos positivos
        return returns

    @pytest.fixture
    def mixed_returns(self):
        """Serie de retornos mixtos realistas"""
        np.random.seed(42)
        # 60% días ganadores, 40% perdedores
        returns = pd.Series(np.random.normal(0.0005, 0.02, 252))
        return returns

    @pytest.fixture
    def equity_curve_positive(self):
        """Equity curve con crecimiento consistente"""
        initial_capital = 50000
        returns = pd.Series(np.random.normal(0.001, 0.005, 252))
        returns = returns.abs()  # Todos positivos
        equity = initial_capital * (1 + returns).cumprod()
        return equity

    @pytest.fixture
    def equity_curve_with_drawdown(self):
        """Equity curve con drawdown significativo"""
        initial_capital = 50000
        # Crear equity con crecimiento y luego una caída
        dates = pd.date_range(start='2024-01-01', periods=252, freq='D')
        equity_values = []

        capital = initial_capital
        for i in range(252):
            if i < 100:
                # Crecimiento inicial
                capital *= 1.002
            elif i < 150:
                # Drawdown del 15%
                capital *= 0.997
            else:
                # Recuperación
                capital *= 1.001
            equity_values.append(capital)

        return pd.Series(equity_values, index=dates)

    @pytest.fixture
    def sample_trades(self):
        """DataFrame de trades sintéticos"""
        np.random.seed(42)
        n_trades = 100

        # 60% ganadores, 40% perdedores
        pnls = []
        for _ in range(n_trades):
            if np.random.random() < 0.6:
                # Trade ganador
                pnl = np.random.uniform(100, 500)
            else:
                # Trade perdedor
                pnl = -np.random.uniform(50, 300)
            pnls.append(pnl)

        return pd.DataFrame({'pnl': pnls})

    def test_sharpe_ratio_positive(self, metrics, positive_returns):
        """Test: retornos positivos consistentes → sharpe > 0"""
        sharpe = metrics.sharpe_ratio(positive_returns)
        assert sharpe > 0, "Sharpe ratio debe ser positivo para retornos positivos"
        # Con retornos todos positivos, el Sharpe debe ser alto
        assert sharpe > 1.0, f"Sharpe ratio esperado > 1.0, obtenido: {sharpe}"

    def test_sharpe_ratio_zero_std(self, metrics):
        """Test: retornos constantes → retorna 0.0, no crash"""
        # Serie con retornos constantes (std = 0)
        constant_returns = pd.Series([0.001] * 100)
        sharpe = metrics.sharpe_ratio(constant_returns)
        assert sharpe == 0.0, "Sharpe ratio debe ser 0 cuando std = 0"

    def test_sortino_higher_than_sharpe(self, metrics):
        """Test: retornos con solo upside volatility → sortino > sharpe"""
        # Crear retornos con alta volatilidad positiva, poca negativa
        np.random.seed(42)
        returns = []
        for _ in range(252):
            if np.random.random() < 0.8:
                # 80% retornos positivos con alta variabilidad
                ret = np.random.uniform(0, 0.05)
            else:
                # 20% retornos negativos pequeños
                ret = -np.random.uniform(0, 0.01)
            returns.append(ret)

        returns_series = pd.Series(returns)
        sharpe = metrics.sharpe_ratio(returns_series)
        sortino = metrics.sortino_ratio(returns_series)

        assert sortino > sharpe, f"Sortino ({sortino:.2f}) debe ser mayor que Sharpe ({sharpe:.2f}) cuando downside volatility es baja"

    def test_max_drawdown_negative(self, metrics, equity_curve_with_drawdown):
        """Test: equity que baja → mdd < 0"""
        max_dd = metrics.max_drawdown(equity_curve_with_drawdown)
        assert max_dd < 0, f"Max drawdown debe ser negativo, obtenido: {max_dd}"
        # Verificar que está en rango razonable
        assert -0.20 < max_dd < -0.05, f"Max drawdown esperado entre -20% y -5%, obtenido: {max_dd:.2%}"

    def test_max_drawdown_no_loss(self, metrics):
        """Test: equity monotónica creciente → mdd = 0"""
        # Equity perfectamente creciente
        equity = pd.Series([50000 * (1.001 ** i) for i in range(100)])
        max_dd = metrics.max_drawdown(equity)
        assert max_dd == 0.0, f"Max drawdown debe ser 0 para equity monotónica creciente, obtenido: {max_dd}"

    def test_max_drawdown_usd_scale(self, metrics):
        """Test: mdd_usd = mdd_pct * peak_equity"""
        initial = 50000
        # Crear equity con un drawdown conocido
        equity_values = [initial]
        for i in range(1, 100):
            if i < 50:
                equity_values.append(equity_values[-1] * 1.01)  # Crecimiento
            elif i == 50:
                peak = equity_values[-1]
                equity_values.append(peak * 0.85)  # Caída del 15%
            else:
                equity_values.append(equity_values[-1] * 1.001)  # Recuperación lenta

        equity = pd.Series(equity_values)

        max_dd_pct = metrics.max_drawdown(equity)
        max_dd_usd = metrics.max_drawdown_usd(equity)

        # El drawdown en USD debe ser aproximadamente el 15% del pico
        peak_value = max(equity_values[:51])
        expected_dd_usd = peak_value * max_dd_pct

        assert abs(max_dd_usd - expected_dd_usd) < 1.0, \
            f"Max DD USD ({max_dd_usd:.2f}) debe ser aproximadamente {expected_dd_usd:.2f}"

    def test_profit_factor_above_one(self, metrics, sample_trades):
        """Test: más ganadores que perdedores → pf > 1"""
        pf = metrics.profit_factor(sample_trades)
        assert pf > 1.0, f"Profit factor debe ser > 1 con 60% win rate, obtenido: {pf:.2f}"
        assert pf < 10.0, f"Profit factor debe ser razonable (< 10), obtenido: {pf:.2f}"

    def test_profit_factor_no_losers(self, metrics):
        """Test: sin trades perdedores → inf"""
        # Solo trades ganadores
        winning_trades = pd.DataFrame({'pnl': [100, 200, 150, 300, 250]})
        pf = metrics.profit_factor(winning_trades)
        assert pf == float('inf'), "Profit factor debe ser inf cuando no hay perdedores"

    def test_win_rate_range(self, metrics):
        """Test: siempre entre 0.0 y 1.0"""
        # Test con diferentes proporciones
        test_cases = [
            (pd.DataFrame({'pnl': [100, -50, 200, -100]}), 0.5),  # 50% win rate
            (pd.DataFrame({'pnl': [100, 200, 150]}), 1.0),  # 100% win rate
            (pd.DataFrame({'pnl': [-100, -200, -150]}), 0.0),  # 0% win rate
        ]

        for trades, expected_wr in test_cases:
            win_rate = metrics.win_rate(trades)
            assert 0.0 <= win_rate <= 1.0, f"Win rate debe estar entre 0 y 1, obtenido: {win_rate}"
            assert abs(win_rate - expected_wr) < 0.01, \
                f"Win rate esperado: {expected_wr}, obtenido: {win_rate}"

    def test_calmar_ratio_positive(self, metrics, mixed_returns):
        """Test: retornos positivos con drawdown → calmar > 0"""
        # Asegurar que tenemos retorno neto positivo
        mixed_returns = mixed_returns + 0.0005  # Sesgo positivo
        calmar = metrics.calmar_ratio(mixed_returns)

        # Con retornos netos positivos y algún drawdown, Calmar debe ser positivo
        if mixed_returns.mean() > 0:
            assert calmar > 0, f"Calmar ratio debe ser positivo, obtenido: {calmar:.2f}"

    def test_deflated_sharpe_low_trials(self, metrics):
        """Test: n_trials=1 → DSR ≈ sharpe_ratio (sin penalización)"""
        sharpe = 1.5
        n_trials = 1
        n_observations = 252

        dsr = metrics.deflated_sharpe_ratio(
            sharpe_ratio=sharpe,
            n_trials=n_trials,
            n_observations=n_observations
        )

        # Con solo 1 trial, DSR debe ser alto (poca penalización)
        assert dsr > 0.8, f"DSR con 1 trial debe ser alto, obtenido: {dsr:.2f}"
        assert dsr <= 1.0, f"DSR debe estar entre 0 y 1, obtenido: {dsr:.2f}"

    def test_deflated_sharpe_many_trials(self, metrics):
        """Test: n_trials=100 → DSR < sharpe_ratio (penalizado)"""
        sharpe = 1.5
        n_observations = 252

        # Comparar DSR con 1 trial vs 100 trials
        dsr_1_trial = metrics.deflated_sharpe_ratio(
            sharpe_ratio=sharpe,
            n_trials=1,
            n_observations=n_observations
        )

        dsr_100_trials = metrics.deflated_sharpe_ratio(
            sharpe_ratio=sharpe,
            n_trials=100,
            n_observations=n_observations
        )

        assert dsr_100_trials < dsr_1_trial, \
            f"DSR con 100 trials ({dsr_100_trials:.2f}) debe ser menor que con 1 trial ({dsr_1_trial:.2f})"

        # Con muchos trials, DSR debe ser significativamente menor
        assert dsr_100_trials < 0.95, \
            f"DSR con 100 trials debe indicar posible overfitting (<0.95), obtenido: {dsr_100_trials:.2f}"

    def test_calculate_all_returns_report(self, metrics):
        """Test: equity + trades sintéticos → PerformanceReport completo"""
        # Crear datos sintéticos
        initial_capital = 50000
        returns = pd.Series(np.random.normal(0.0005, 0.02, 252))
        equity = initial_capital * (1 + returns).cumprod()

        trades = pd.DataFrame({
            'pnl': [200, -100, 300, -50, 150, -80, 250, 100, -120, 180]
        })

        # Calcular reporte completo
        report = metrics.calculate_all(
            equity_curve=equity,
            trades=trades,
            n_trials=5,
            risk_free_rate=0.0
        )

        # Verificar que el reporte tiene todos los campos
        assert isinstance(report, PerformanceReport)
        assert hasattr(report, 'sharpe_ratio')
        assert hasattr(report, 'sortino_ratio')
        assert hasattr(report, 'calmar_ratio')
        assert hasattr(report, 'deflated_sharpe_ratio')
        assert hasattr(report, 'max_drawdown_pct')
        assert hasattr(report, 'max_drawdown_usd')
        assert hasattr(report, 'total_trades')
        assert hasattr(report, 'win_rate')
        assert hasattr(report, 'profit_factor')
        assert hasattr(report, 'avg_win_usd')
        assert hasattr(report, 'avg_loss_usd')
        assert hasattr(report, 'expectancy_usd')
        assert hasattr(report, 'total_pnl_usd')
        assert hasattr(report, 'total_pnl_ticks')

        # Verificar valores razonables
        assert report.total_trades == len(trades)
        assert 0.0 <= report.win_rate <= 1.0
        assert report.max_drawdown_pct <= 0  # Debe ser negativo o cero
        assert report.deflated_sharpe_ratio >= 0.0
        assert report.deflated_sharpe_ratio <= 1.0

    def test_pnl_in_ticks_nq(self, metrics):
        """Test: pnl_usd / 5.0 = pnl_ticks (tick_value NQ = $5)"""
        trades = pd.DataFrame({
            'pnl': [500, -250, 750, -100]  # USD
        })

        equity = pd.Series([50000, 50500, 50250, 51000, 50900])

        report = metrics.calculate_all(equity, trades)

        expected_pnl_usd = sum(trades['pnl'])
        expected_pnl_ticks = expected_pnl_usd / metrics.TICK_VALUE

        assert abs(report.total_pnl_usd - expected_pnl_usd) < 0.01, \
            f"PnL USD esperado: {expected_pnl_usd}, obtenido: {report.total_pnl_usd}"

        assert abs(report.total_pnl_ticks - expected_pnl_ticks) < 0.01, \
            f"PnL en ticks esperado: {expected_pnl_ticks}, obtenido: {report.total_pnl_ticks}"

        # Verificar la constante TICK_VALUE
        assert metrics.TICK_VALUE == 5.0, "TICK_VALUE para NQ debe ser $5"
        assert metrics.TICK_SIZE == 0.25, "TICK_SIZE para NQ debe ser 0.25"
        assert metrics.POINT_VALUE == 20.0, "POINT_VALUE para NQ debe ser $20"


class TestEdgeCases:
    """Tests para casos límite y manejo de errores"""

    @pytest.fixture
    def metrics(self):
        return PerformanceMetrics()

    def test_empty_data_handling(self, metrics):
        """Test: manejo correcto de datos vacíos"""
        empty_series = pd.Series([])
        empty_df = pd.DataFrame()

        # No debe crashear con datos vacíos
        sharpe = metrics.sharpe_ratio(empty_series)
        assert sharpe == 0.0

        sortino = metrics.sortino_ratio(empty_series)
        assert sortino == 0.0

        max_dd = metrics.max_drawdown(empty_series)
        assert max_dd == 0.0

        pf = metrics.profit_factor(empty_df)
        assert pf == 0.0

        wr = metrics.win_rate(empty_df)
        assert wr == 0.0

    def test_single_value_handling(self, metrics):
        """Test: manejo de series con un solo valor"""
        single_return = pd.Series([0.01])
        single_equity = pd.Series([50000])

        sharpe = metrics.sharpe_ratio(single_return)
        # Con un solo punto, no hay volatilidad
        assert sharpe == 0.0 or np.isnan(sharpe) or sharpe == 0.0

        max_dd = metrics.max_drawdown(single_equity)
        assert max_dd == 0.0

    def test_negative_equity_handling(self, metrics):
        """Test: manejo de equity negativa (cuenta quebrada)"""
        # Equity que va a negativo
        equity = pd.Series([50000, 40000, 20000, 5000, -1000])

        max_dd = metrics.max_drawdown(equity)
        # Debe calcular correctamente incluso con valores negativos
        assert max_dd < -1.0  # Más del 100% de pérdida

        max_dd_usd = metrics.max_drawdown_usd(equity)
        assert max_dd_usd == -51000  # De 50000 a -1000

    def test_extreme_values(self, metrics):
        """Test: manejo de valores extremos"""
        # Retornos extremos
        extreme_returns = pd.Series([10.0, -0.99, 5.0, -0.95])

        # No debe crashear
        sharpe = metrics.sharpe_ratio(extreme_returns)
        sortino = metrics.sortino_ratio(extreme_returns)

        assert not np.isnan(sharpe)
        assert not np.isnan(sortino)

    def test_deflated_sharpe_edge_cases(self, metrics):
        """Test: casos límite para Deflated Sharpe Ratio"""
        # Sharpe negativo
        dsr_negative = metrics.deflated_sharpe_ratio(
            sharpe_ratio=-1.0,
            n_trials=10,
            n_observations=252
        )
        assert 0.0 <= dsr_negative <= 1.0

        # Sharpe muy alto
        dsr_high = metrics.deflated_sharpe_ratio(
            sharpe_ratio=5.0,
            n_trials=1,
            n_observations=252
        )
        assert 0.0 <= dsr_high <= 1.0

        # Pocas observaciones
        dsr_few_obs = metrics.deflated_sharpe_ratio(
            sharpe_ratio=1.5,
            n_trials=10,
            n_observations=10
        )
        assert 0.0 <= dsr_few_obs <= 1.0

        # Skewness y kurtosis extremos
        dsr_extreme_moments = metrics.deflated_sharpe_ratio(
            sharpe_ratio=1.5,
            n_trials=10,
            n_observations=252,
            skewness=3.0,
            kurtosis=10.0
        )
        assert 0.0 <= dsr_extreme_moments <= 1.0