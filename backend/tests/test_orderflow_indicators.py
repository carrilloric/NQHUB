"""
Tests for Order Flow Indicators

Tests con DataFrames sintéticos con los campos del schema real de candles.
No necesita TimescaleDB — trabaja con datos en memoria.

Author: NQHUB Research Team
"""

import json
import pytest
import pandas as pd
import numpy as np

from app.research.indicators.orderflow import OrderFlowIndicators


@pytest.fixture
def indicators():
    """Fixture para instancia de OrderFlowIndicators"""
    return OrderFlowIndicators()


class TestCVD:
    """Tests for Cumulative Volume Delta"""

    def test_cvd_accumulates_delta(self, indicators):
        """CVD debe acumular el delta correctamente"""
        candles = pd.DataFrame({
            'delta': [10, -5, 8]
        })
        cvd = indicators.cvd(candles)

        assert len(cvd) == 3
        assert cvd.iloc[0] == 10
        assert cvd.iloc[1] == 5
        assert cvd.iloc[2] == 13

    def test_cvd_with_zero_delta(self, indicators):
        """CVD debe manejar deltas en cero correctamente"""
        candles = pd.DataFrame({
            'delta': [0, 0, 0]
        })
        cvd = indicators.cvd(candles)

        assert all(cvd == 0)

    def test_cvd_negative_trend(self, indicators):
        """CVD debe decrecer con deltas negativos sostenidos"""
        candles = pd.DataFrame({
            'delta': [-10, -5, -8]
        })
        cvd = indicators.cvd(candles)

        assert cvd.iloc[0] == -10
        assert cvd.iloc[1] == -15
        assert cvd.iloc[2] == -23
        assert cvd.is_monotonic_decreasing

    def test_cvd_missing_delta_column(self, indicators):
        """CVD debe lanzar error si falta columna delta"""
        candles = pd.DataFrame({
            'volume': [100, 200, 300]
        })

        with pytest.raises(ValueError, match="must contain 'delta' column"):
            indicators.cvd(candles)


class TestPOCMigration:
    """Tests for POC Migration"""

    def test_poc_migration_positive(self, indicators):
        """Migration positivo cuando POC sube"""
        candles = pd.DataFrame({
            'poc': [18250, 18260, 18270]
        })
        migration = indicators.poc_migration(candles)

        assert pd.isna(migration.iloc[0])  # First value is NaN
        assert migration.iloc[1] == 10.0
        assert migration.iloc[2] == 10.0

    def test_poc_migration_negative(self, indicators):
        """Migration negativo cuando POC baja"""
        candles = pd.DataFrame({
            'poc': [18270, 18260, 18250]
        })
        migration = indicators.poc_migration(candles)

        assert pd.isna(migration.iloc[0])  # First value is NaN
        assert migration.iloc[1] == -10.0
        assert migration.iloc[2] == -10.0

    def test_poc_migration_mixed(self, indicators):
        """Migration con POC oscilante"""
        candles = pd.DataFrame({
            'poc': [18250, 18260, 18255, 18265]
        })
        migration = indicators.poc_migration(candles)

        assert pd.isna(migration.iloc[0])
        assert migration.iloc[1] == 10.0
        assert migration.iloc[2] == -5.0
        assert migration.iloc[3] == 10.0

    def test_poc_migration_missing_column(self, indicators):
        """Migration debe lanzar error si falta columna poc"""
        candles = pd.DataFrame({
            'delta': [10, 20, 30]
        })

        with pytest.raises(ValueError, match="must contain 'poc' column"):
            indicators.poc_migration(candles)


class TestAbsorptionScore:
    """Tests for Absorption Score"""

    def test_absorption_score_range(self, indicators):
        """Score debe estar siempre entre 0.0 y 1.0"""
        candles = pd.DataFrame({
            'delta': [0, 50, -50, 100, -100],
            'volume': [100, 100, 100, 100, 100]
        })
        score = indicators.absorption_score(candles)

        assert all(score >= 0.0)
        assert all(score <= 1.0)

    def test_absorption_high_volume_small_delta(self, indicators):
        """Volumen alto + delta pequeño = score bajo (absorción)"""
        candles = pd.DataFrame({
            'delta': [2, -3, 1],  # Small deltas
            'volume': [1000, 1000, 1000]  # High volume
        })
        score = indicators.absorption_score(candles)

        # All scores should be very low (close to 0)
        assert all(score < 0.01)

    def test_absorption_balanced_flow(self, indicators):
        """Delta balanceado (cerca de 0) = absorción perfecta"""
        candles = pd.DataFrame({
            'delta': [0, 0, 0],
            'volume': [100, 200, 300]
        })
        score = indicators.absorption_score(candles)

        assert all(score == 0.0)

    def test_absorption_directional_flow(self, indicators):
        """Delta alto relativo al volumen = flujo direccional"""
        candles = pd.DataFrame({
            'delta': [90, -80],
            'volume': [100, 100]
        })
        score = indicators.absorption_score(candles)

        # High scores indicating directional flow
        assert score.iloc[0] == 0.90
        assert score.iloc[1] == 0.80

    def test_absorption_zero_volume(self, indicators):
        """Volumen cero debe manejarse sin división por cero"""
        candles = pd.DataFrame({
            'delta': [10, -5],
            'volume': [0, 0]
        })
        score = indicators.absorption_score(candles)

        # Should fill NaN with 0
        assert all(score == 0.0)

    def test_absorption_missing_columns(self, indicators):
        """Debe lanzar error si faltan columnas"""
        candles = pd.DataFrame({
            'delta': [10, 20]
        })

        with pytest.raises(ValueError, match="must contain 'delta' and 'volume' columns"):
            indicators.absorption_score(candles)


class TestFootprintImbalance:
    """Tests for Footprint Imbalance"""

    def test_footprint_imbalance_range(self, indicators):
        """Imbalance debe estar siempre entre 0.0 y 1.0"""
        candles = pd.DataFrame({
            'oflow_detail': [
                json.dumps({"18250.25": {"asks": 10, "bids": 90}}),
                json.dumps({"18250.50": {"asks": 50, "bids": 50}}),
                json.dumps({"18250.75": {"asks": 100, "bids": 0}})
            ]
        })
        imbalance = indicators.footprint_imbalance(candles)

        assert all(imbalance >= 0.0)
        assert all(imbalance <= 1.0)

    def test_footprint_imbalance_total_bid(self, indicators):
        """100% bids = imbalance de 1.0"""
        candles = pd.DataFrame({
            'oflow_detail': [
                json.dumps({"18250.00": {"asks": 0, "bids": 100}})
            ]
        })
        imbalance = indicators.footprint_imbalance(candles)

        assert imbalance.iloc[0] == 1.0

    def test_footprint_imbalance_balanced(self, indicators):
        """50/50 bids/asks = imbalance de 0.0"""
        candles = pd.DataFrame({
            'oflow_detail': [
                json.dumps({"18250.00": {"asks": 50, "bids": 50}})
            ]
        })
        imbalance = indicators.footprint_imbalance(candles)

        assert imbalance.iloc[0] == 0.0

    def test_footprint_imbalance_max_across_levels(self, indicators):
        """Debe retornar el imbalance máximo entre todos los niveles"""
        candles = pd.DataFrame({
            'oflow_detail': [
                json.dumps({
                    "18250.00": {"asks": 50, "bids": 50},  # balanced
                    "18250.25": {"asks": 10, "bids": 90},  # 80% imbalance
                    "18250.50": {"asks": 30, "bids": 70}   # 40% imbalance
                })
            ]
        })
        imbalance = indicators.footprint_imbalance(candles)

        # Should return max imbalance (80% from 18250.25)
        assert imbalance.iloc[0] == 0.80

    def test_footprint_imbalance_empty_detail(self, indicators):
        """oflow_detail vacío o None debe retornar 0.0"""
        candles = pd.DataFrame({
            'oflow_detail': [None, '', json.dumps({})]
        })
        imbalance = indicators.footprint_imbalance(candles)

        assert all(imbalance == 0.0)

    def test_footprint_imbalance_invalid_json(self, indicators):
        """JSON inválido debe manejarse sin errores"""
        candles = pd.DataFrame({
            'oflow_detail': [
                'invalid json',
                '{broken',
                '{"18250": "not a dict"}'
            ]
        })
        imbalance = indicators.footprint_imbalance(candles)

        # Should handle gracefully and return 0
        assert all(imbalance == 0.0)

    def test_footprint_imbalance_dict_input(self, indicators):
        """Debe aceptar dict en lugar de JSON string"""
        candles = pd.DataFrame({
            'oflow_detail': [
                {"18250.00": {"asks": 20, "bids": 80}}
            ]
        })
        imbalance = indicators.footprint_imbalance(candles)

        assert imbalance.iloc[0] == 0.60

    def test_footprint_imbalance_missing_column(self, indicators):
        """Debe lanzar error si falta columna oflow_detail"""
        candles = pd.DataFrame({
            'delta': [10, 20]
        })

        with pytest.raises(ValueError, match="must contain 'oflow_detail' column"):
            indicators.footprint_imbalance(candles)


class TestDeltaDivergence:
    """Tests for Delta Divergence"""

    def test_delta_divergence_detects_bearish(self, indicators):
        """Delta positivo + precio baja = divergencia bajista"""
        candles = pd.DataFrame({
            'delta': [10, 15, 20],  # Positive delta (buying)
            'close': [18250, 18240, 18230]  # Price falling
        })
        divergence = indicators.delta_divergence(candles)

        assert divergence.iloc[0] == 0  # First always 0
        assert divergence.iloc[1] == 1  # Divergence detected
        assert divergence.iloc[2] == 1  # Divergence detected

    def test_delta_divergence_detects_bullish(self, indicators):
        """Delta negativo + precio sube = divergencia alcista"""
        candles = pd.DataFrame({
            'delta': [-10, -15, -20],  # Negative delta (selling)
            'close': [18250, 18260, 18270]  # Price rising
        })
        divergence = indicators.delta_divergence(candles)

        assert divergence.iloc[0] == 0  # First always 0
        assert divergence.iloc[1] == 1  # Divergence detected
        assert divergence.iloc[2] == 1  # Divergence detected

    def test_delta_divergence_no_divergence(self, indicators):
        """Delta y precio alineados = no divergencia"""
        candles = pd.DataFrame({
            'delta': [10, 15, 20],  # Positive delta
            'close': [18250, 18260, 18270]  # Price rising
        })
        divergence = indicators.delta_divergence(candles)

        assert divergence.iloc[0] == 0
        assert divergence.iloc[1] == 0  # No divergence
        assert divergence.iloc[2] == 0  # No divergence

    def test_delta_divergence_mixed_signals(self, indicators):
        """Mix de divergencia y no divergencia"""
        candles = pd.DataFrame({
            'delta': [10, -5, 8, -3],
            'close': [18250, 18260, 18255, 18270]
        })
        divergence = indicators.delta_divergence(candles)

        assert divergence.iloc[0] == 0  # First always 0
        assert divergence.iloc[1] == 1  # Div: neg delta, price up (bullish divergence)
        assert divergence.iloc[2] == 1  # Div: pos delta, price down (bearish divergence)
        assert divergence.iloc[3] == 1  # Div: neg delta, price up (bullish divergence)

    def test_delta_divergence_zero_delta(self, indicators):
        """Delta cero no genera divergencia"""
        candles = pd.DataFrame({
            'delta': [0, 0, 0],
            'close': [18250, 18260, 18240]
        })
        divergence = indicators.delta_divergence(candles)

        assert all(divergence == 0)

    def test_delta_divergence_missing_columns(self, indicators):
        """Debe lanzar error si faltan columnas"""
        candles = pd.DataFrame({
            'delta': [10, 20]
        })

        with pytest.raises(ValueError, match="must contain 'delta' and 'close' columns"):
            indicators.delta_divergence(candles)


class TestWickAbsorptionRatio:
    """Tests for Wick Absorption Ratio"""

    def test_wick_absorption_ratio_range(self, indicators):
        """Ratio debe estar siempre entre 0.0 y 1.0"""
        candles = pd.DataFrame({
            'abuyers_uwick': [100, 0, 50, 80],
            'asellers_uwick': [0, 100, 50, 20]
        })
        ratio = indicators.wick_absorption_ratio(candles, wick='upper')

        assert all(ratio >= 0.0)
        assert all(ratio <= 1.0)

    def test_wick_absorption_upper_buyers_dominant(self, indicators):
        """Alta proporción de compradores en upper wick"""
        candles = pd.DataFrame({
            'abuyers_uwick': [80, 90],
            'asellers_uwick': [20, 10]
        })
        ratio = indicators.wick_absorption_ratio(candles, wick='upper')

        assert ratio.iloc[0] == 0.80
        assert ratio.iloc[1] == 0.90

    def test_wick_absorption_upper_sellers_dominant(self, indicators):
        """Alta proporción de vendedores en upper wick"""
        candles = pd.DataFrame({
            'abuyers_uwick': [20, 10],
            'asellers_uwick': [80, 90]
        })
        ratio = indicators.wick_absorption_ratio(candles, wick='upper')

        assert ratio.iloc[0] == 0.20
        assert ratio.iloc[1] == 0.10

    def test_wick_absorption_lower_buyers_dominant(self, indicators):
        """Alta proporción de compradores en lower wick (soporte)"""
        candles = pd.DataFrame({
            'abuyers_lwick': [85, 75],
            'asellers_lwick': [15, 25]
        })
        ratio = indicators.wick_absorption_ratio(candles, wick='lower')

        assert ratio.iloc[0] == 0.85
        assert ratio.iloc[1] == 0.75

    def test_wick_absorption_balanced(self, indicators):
        """50/50 = ratio de 0.5 (neutral)"""
        candles = pd.DataFrame({
            'abuyers_uwick': [50, 100],
            'asellers_uwick': [50, 100]
        })
        ratio = indicators.wick_absorption_ratio(candles, wick='upper')

        assert ratio.iloc[0] == 0.50
        assert ratio.iloc[1] == 0.50

    def test_wick_absorption_zero_activity(self, indicators):
        """Sin actividad en wick = 0.5 (neutral)"""
        candles = pd.DataFrame({
            'abuyers_uwick': [0, 0],
            'asellers_uwick': [0, 0]
        })
        ratio = indicators.wick_absorption_ratio(candles, wick='upper')

        # Should fill with 0.5 when no activity
        assert all(ratio == 0.50)

    def test_wick_absorption_invalid_wick_type(self, indicators):
        """Tipo de wick inválido debe lanzar error"""
        candles = pd.DataFrame({
            'abuyers_uwick': [50],
            'asellers_uwick': [50]
        })

        with pytest.raises(ValueError, match="wick must be 'upper' or 'lower'"):
            indicators.wick_absorption_ratio(candles, wick='middle')

    def test_wick_absorption_missing_columns_upper(self, indicators):
        """Debe lanzar error si faltan columnas de upper wick"""
        candles = pd.DataFrame({
            'delta': [10, 20]
        })

        with pytest.raises(ValueError, match="must contain 'abuyers_uwick' and 'asellers_uwick' columns"):
            indicators.wick_absorption_ratio(candles, wick='upper')

    def test_wick_absorption_missing_columns_lower(self, indicators):
        """Debe lanzar error si faltan columnas de lower wick"""
        candles = pd.DataFrame({
            'delta': [10, 20]
        })

        with pytest.raises(ValueError, match="must contain 'abuyers_lwick' and 'asellers_lwick' columns"):
            indicators.wick_absorption_ratio(candles, wick='lower')


class TestIntegration:
    """Integration tests with realistic candle data"""

    def test_all_indicators_on_realistic_data(self, indicators):
        """Todos los indicadores funcionan con datos realistas"""
        candles = pd.DataFrame({
            'delta': [150, -80, 200, -50, 100],
            'volume': [5000, 4500, 6000, 4000, 5500],
            'poc': [18250, 18255, 18260, 18255, 18258],
            'close': [18252, 18254, 18262, 18258, 18265],
            'open': [18248, 18252, 18254, 18262, 18258],
            'high': [18253, 18256, 18264, 18263, 18267],
            'low': [18246, 18251, 18253, 18255, 18257],
            'oflow_detail': [
                json.dumps({"18250": {"asks": 2000, "bids": 3000}}),
                json.dumps({"18255": {"asks": 2500, "bids": 2000}}),
                json.dumps({"18260": {"asks": 1800, "bids": 4200}}),
                json.dumps({"18255": {"asks": 2200, "bids": 1800}}),
                json.dumps({"18258": {"asks": 2200, "bids": 3300}})
            ],
            'abuyers_uwick': [300, 200, 450, 250, 350],
            'asellers_uwick': [100, 350, 150, 300, 200],
            'abuyers_lwick': [400, 300, 350, 500, 400],
            'asellers_lwick': [200, 200, 250, 150, 250]
        })

        # All indicators should run without errors
        cvd = indicators.cvd(candles)
        poc_mig = indicators.poc_migration(candles)
        absorption = indicators.absorption_score(candles)
        imbalance = indicators.footprint_imbalance(candles)
        divergence = indicators.delta_divergence(candles)
        upper_ratio = indicators.wick_absorption_ratio(candles, wick='upper')
        lower_ratio = indicators.wick_absorption_ratio(candles, wick='lower')

        # Basic validations
        assert len(cvd) == 5
        assert len(poc_mig) == 5
        assert len(absorption) == 5
        assert len(imbalance) == 5
        assert len(divergence) == 5
        assert len(upper_ratio) == 5
        assert len(lower_ratio) == 5

        # Range validations
        assert all(absorption >= 0) and all(absorption <= 1)
        assert all(imbalance >= 0) and all(imbalance <= 1)
        assert all(divergence.isin([0, 1]))
        assert all(upper_ratio >= 0) and all(upper_ratio <= 1)
        assert all(lower_ratio >= 0) and all(lower_ratio <= 1)

    def test_empty_dataframe(self, indicators):
        """DataFrames vacíos deben manejarse correctamente"""
        candles = pd.DataFrame({
            'delta': [],
            'volume': [],
            'poc': [],
            'close': [],
            'oflow_detail': [],
            'abuyers_uwick': [],
            'asellers_uwick': []
        })

        cvd = indicators.cvd(candles)
        assert len(cvd) == 0

        poc_mig = indicators.poc_migration(candles)
        assert len(poc_mig) == 0

    def test_single_candle(self, indicators):
        """Single candle debe manejarse correctamente"""
        candles = pd.DataFrame({
            'delta': [100],
            'volume': [5000],
            'poc': [18250],
            'close': [18252],
            'oflow_detail': [json.dumps({"18250": {"asks": 2000, "bids": 3000}})],
            'abuyers_uwick': [300],
            'asellers_uwick': [200]
        })

        cvd = indicators.cvd(candles)
        assert cvd.iloc[0] == 100

        poc_mig = indicators.poc_migration(candles)
        assert pd.isna(poc_mig.iloc[0])  # First value is NaN

        divergence = indicators.delta_divergence(candles)
        assert divergence.iloc[0] == 0  # First value is always 0
