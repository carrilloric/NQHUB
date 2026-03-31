"""
Tests for Data Platform API endpoints.

Tests required per AUT-330:
- test_get_candles_1min_returns_correct_timeframe
- test_get_candles_pagination_cursor
- test_get_candles_limit_enforced
- test_get_candles_include_orderflow_adds_delta
- test_get_candles_invalid_timeframe_returns_422
- test_get_coverage_returns_date_range
- test_get_ticks_pagination
- test_get_active_contract_returns_symbol
- test_post_export_returns_task_id
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np

# Import app for testing
from app.main import app

# NQ Futures constants
NQ_TICK_SIZE = 0.25
NQ_TICK_VALUE = 5.0
NQ_POINT_VALUE = 20.0


class TestCandlesEndpoint:
    """Tests for GET /data/candles/{timeframe} endpoint."""

    def test_get_candles_1min_returns_correct_timeframe(self, client):
        """Test that requesting 1min candles returns correct timeframe."""
        # Setup mock data
        mock_candles = pd.DataFrame({
            'timestamp': pd.date_range('2026-01-01 09:30', periods=100, freq='1min'),
            'symbol': ['NQH26'] * 100,
            'open': np.random.uniform(19000, 20000, 100),
            'high': np.random.uniform(19100, 20100, 100),
            'low': np.random.uniform(18900, 19900, 100),
            'close': np.random.uniform(19000, 20000, 100),
            'volume': np.random.randint(100, 1000, 100)
        })

        with patch('app.api.v1.data.routes.CandleStore') as mock_store_class:
            mock_store = mock_store_class.return_value
            mock_store.get_candles.return_value = mock_candles

            # Make request
            response = client.get(
                "/api/v1/data/candles/1min",
                params={
                    "start": "2026-01-01T09:30:00Z",
                    "end": "2026-01-01T11:00:00Z"
                }
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "candles" in data
            assert len(data["candles"]) > 0
            # Verify candles are 1 minute apart
            if len(data["candles"]) > 1:
                first_ts = datetime.fromisoformat(data["candles"][0]["timestamp"].replace('Z', '+00:00'))
                second_ts = datetime.fromisoformat(data["candles"][1]["timestamp"].replace('Z', '+00:00'))
                assert (second_ts - first_ts).total_seconds() == 60

    def test_get_candles_pagination_cursor(self, client):
        """Test cursor-based pagination for candles."""
        # Setup mock data with more candles than limit
        mock_candles = pd.DataFrame({
            'timestamp': pd.date_range('2026-01-01 09:30', periods=600, freq='1min'),
            'symbol': ['NQH26'] * 600,
            'open': np.random.uniform(19000, 20000, 600),
            'high': np.random.uniform(19100, 20100, 600),
            'low': np.random.uniform(18900, 19900, 600),
            'close': np.random.uniform(19000, 20000, 600),
            'volume': np.random.randint(100, 1000, 600)
        })

        with patch('app.api.v1.data.routes.CandleStore') as mock_store_class:
            mock_store = mock_store_class.return_value

            # Return first 500 candles on first call
            mock_store.get_candles.return_value = mock_candles.iloc[:500]

            # First request
            response = client.get(
                "/api/v1/data/candles/1min",
                params={
                    "start": "2026-01-01T09:30:00Z",
                    "end": "2026-01-01T20:00:00Z",
                    "limit": 500
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "next_cursor" in data
            assert data["next_cursor"] is not None
            assert len(data["candles"]) == 500

            # Second request with cursor
            cursor = data["next_cursor"]
            mock_store.get_candles.return_value = mock_candles.iloc[500:]

            response2 = client.get(
                "/api/v1/data/candles/1min",
                params={
                    "start": "2026-01-01T09:30:00Z",
                    "end": "2026-01-01T20:00:00Z",
                    "limit": 500,
                    "cursor": cursor
                }
            )

            assert response2.status_code == 200
            data2 = response2.json()
            assert len(data2["candles"]) == 100

    def test_get_candles_limit_enforced(self, client):
        """Test that candles limit is enforced (max 5000)."""
        # Try to request more than 5000 candles
        response = client.get(
            "/api/v1/data/candles/1min",
            params={
                "start": "2026-01-01T09:30:00Z",
                "end": "2026-01-01T20:00:00Z",
                "limit": 6000  # Over the limit
            }
        )

        # Should either reject or cap at 5000
        if response.status_code == 200:
            data = response.json()
            assert len(data["candles"]) <= 5000
        else:
            assert response.status_code == 422  # Validation error

    def test_get_candles_include_orderflow_adds_delta(self, client):
        """Test that include_orderflow=true adds delta, poc, and footprint."""
        # Setup mock data with orderflow
        mock_candles = pd.DataFrame({
            'timestamp': pd.date_range('2026-01-01 09:30', periods=10, freq='1min'),
            'symbol': ['NQH26'] * 10,
            'open': np.random.uniform(19000, 20000, 10),
            'high': np.random.uniform(19100, 20100, 10),
            'low': np.random.uniform(18900, 19900, 10),
            'close': np.random.uniform(19000, 20000, 10),
            'volume': np.random.randint(100, 1000, 10),
            'delta': np.random.randint(-100, 100, 10),
            'poc': np.random.uniform(19000, 20000, 10),
            'footprint': [{"levels": {"19000": {"bid": 10, "ask": 20}}} for _ in range(10)]
        })

        with patch('app.api.v1.data.routes.CandleStore') as mock_store_class:
            mock_store = mock_store_class.return_value
            mock_store.get_candles.return_value = mock_candles

            # Request with orderflow
            response = client.get(
                "/api/v1/data/candles/1min",
                params={
                    "start": "2026-01-01T09:30:00Z",
                    "end": "2026-01-01T09:40:00Z",
                    "include_orderflow": True
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Check that orderflow fields are present
            if len(data["candles"]) > 0:
                candle = data["candles"][0]
                assert "delta" in candle
                assert "poc" in candle
                assert "footprint" in candle

    def test_get_candles_invalid_timeframe_returns_422(self, client):
        """Test that invalid timeframe returns 422 error."""
        # Request with invalid timeframe
        response = client.get(
            "/api/v1/data/candles/2min",  # Invalid - not in allowed list
            params={
                "start": "2026-01-01T09:30:00Z",
                "end": "2026-01-01T10:30:00Z"
            }
        )

        assert response.status_code == 422
        error = response.json()
        assert "detail" in error


class TestCoverageEndpoint:
    """Tests for GET /data/coverage endpoint."""

    def test_get_coverage_returns_date_range(self, client):
        """Test that coverage endpoint returns date range and stats."""
        with patch('app.api.v1.data.routes.CandleStore') as mock_store_class:
            mock_store = mock_store_class.return_value
            mock_store.get_coverage.return_value = {
                "earliest": "2024-01-02T00:00:00Z",
                "latest": "2026-03-31T23:59:59Z",
                "total_candles": {
                    "1min": 525600,
                    "5min": 105120,
                    "15min": 35040,
                    "1h": 8760,
                    "4h": 2190,
                    "1d": 365
                },
                "gaps": []
            }

            response = client.get("/api/v1/data/coverage")

            assert response.status_code == 200
            data = response.json()
            assert "earliest" in data
            assert "latest" in data
            assert "total_candles" in data
            assert "gaps" in data
            assert data["total_candles"]["1min"] == 525600


class TestTicksEndpoint:
    """Tests for GET /data/ticks endpoint."""

    def test_get_ticks_pagination(self, client):
        """Test pagination for ticks endpoint."""
        # Mock tick data (TBBO format)
        mock_ticks = [
            {
                "timestamp": "2026-01-01T09:30:00.123456Z",
                "symbol": "NQ",
                "bid_price": 19000.25,
                "bid_size": 5,
                "ask_price": 19000.50,
                "ask_size": 10,
                "last_price": 19000.50,
                "last_size": 2
            } for i in range(1500)
        ]

        with patch('app.api.v1.data.routes.CandleStore') as mock_store_class:
            mock_store = mock_store_class.return_value
            mock_store.get_ticks.return_value = {
                "ticks": mock_ticks[:1000],
                "next_cursor": "2026-01-01T09:30:01.000000Z"
            }

            response = client.get(
                "/api/v1/data/ticks",
                params={
                    "start": "2026-01-01T09:30:00Z",
                    "end": "2026-01-01T10:00:00Z",
                    "limit": 1000
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "ticks" in data
            assert "next_cursor" in data
            assert len(data["ticks"]) == 1000

            # Test second page
            response2 = client.get(
                "/api/v1/data/ticks",
                params={
                    "start": "2026-01-01T09:30:00Z",
                    "end": "2026-01-01T10:00:00Z",
                    "limit": 1000,
                    "cursor": data["next_cursor"]
                }
            )

            assert response2.status_code == 200


class TestContractsEndpoint:
    """Tests for contracts endpoints."""

    def test_get_active_contract_returns_symbol(self, client):
        """Test that active contract endpoint returns current symbol."""
        with patch('app.api.v1.data.routes.get_active_nq_contract') as mock_get_contract:
            mock_get_contract.return_value = {
                "symbol": "NQM26",
                "expiry": "2026-06-20",
                "roll_date": "2026-06-13"
            }

            response = client.get("/api/v1/data/contracts/active")

            assert response.status_code == 200
            data = response.json()
            assert "symbol" in data
            assert "expiry" in data
            assert "roll_date" in data
            assert data["symbol"] == "NQM26"

    def test_get_rollover_periods(self, client):
        """Test rollover periods endpoint."""
        with patch('app.api.v1.data.routes.get_nq_rollover_history') as mock_rollover:
            mock_rollover.return_value = [
                {"from": "NQZ25", "to": "NQH26", "date": "2025-12-13"},
                {"from": "NQH26", "to": "NQM26", "date": "2026-03-14"},
                {"from": "NQM26", "to": "NQU26", "date": "2026-06-13"}
            ]

            response = client.get("/api/v1/data/rollover-periods")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 3
            assert data[0]["from"] == "NQZ25"
            assert data[0]["to"] == "NQH26"


class TestExportEndpoint:
    """Tests for POST /data/export endpoint."""

    def test_post_export_returns_task_id(self, client):
        """Test that export endpoint returns task_id for async processing."""
        with patch('app.api.v1.data.routes.export_to_gcs_task') as mock_task:
            mock_task.delay.return_value = Mock(id="abc-123-def-456")

            response = client.post(
                "/api/v1/data/export",
                json={
                    "timeframe": "1min",
                    "start": "2025-01-01",
                    "end": "2026-01-01",
                    "format": "parquet"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
            assert "status" in data
            assert data["task_id"] == "abc-123-def-456"
            assert data["status"] == "queued"

            # Verify task was called with correct parameters
            mock_task.delay.assert_called_once()
            call_args = mock_task.delay.call_args
            assert call_args[1]["timeframe"] == "1min"
            assert call_args[1]["format"] == "parquet"