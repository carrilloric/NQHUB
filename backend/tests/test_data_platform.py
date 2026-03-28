"""
Tests for Data Platform API Endpoints

Tests the implementation against CONTRACT-001 specification.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from fastapi import status
from httpx import AsyncClient
from uuid import uuid4

from app.models.user import User
from app.models.candlestick import Candlestick5Min


class TestDataPlatformAPI:
    """Test suite for Data Platform API endpoints."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user."""
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.is_active = True
        return user

    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        return {"Authorization": "Bearer test-token"}

    @pytest.fixture
    def sample_candle(self):
        """Create a sample candle for testing."""
        candle = MagicMock(spec=Candlestick5Min)
        candle.time_interval = datetime(2024, 11, 29, 14, 30, 0)
        candle.symbol = "NQH25"
        candle.open = 21534.25
        candle.high = 21542.50
        candle.low = 21532.00
        candle.close = 21540.75
        candle.volume = 3827
        candle.delta = 245
        candle.poc = 21537.50
        candle.real_poc = 21537.75
        candle.oflow_detail = {"test": "data"}
        candle.tick_count = 892
        candle.body = 6.50
        candle.upper_wick = 1.75
        candle.lower_wick = 2.25
        return candle

    async def test_get_candles_by_timeframe_success(self, client: AsyncClient, mock_user, auth_headers, sample_candle, mocker):
        """Test successful retrieval of candles by timeframe."""
        # Mock database query
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_candle]
        mock_db.execute.return_value = mock_result

        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mocker.patch("app.api.v1.endpoints.data_platform.get_db", return_value=mock_db)
        mocker.patch("app.api.v1.endpoints.data_platform.get_current_user", return_value=mock_user)

        response = await client.get(
            "/api/v1/data/candles/5min",
            headers=auth_headers,
            params={
                "symbol": "NQH25",
                "limit": 100
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Validate response structure matches CONTRACT-001
        assert "data" in data
        assert "total" in data
        assert "has_more" in data
        assert isinstance(data["data"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["has_more"], bool)

    async def test_get_candles_invalid_timeframe(self, client: AsyncClient, mock_user, auth_headers, mocker):
        """Test error handling for invalid timeframe."""
        mocker.patch("app.api.v1.endpoints.data_platform.get_current_user", return_value=mock_user)

        response = await client.get(
            "/api/v1/data/candles/invalid",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_get_candle_by_timestamp_not_found(self, client: AsyncClient, mock_user, auth_headers, mocker):
        """Test 404 response when candle not found."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        mocker.patch("app.api.v1.endpoints.data_platform.get_db", return_value=mock_db)
        mocker.patch("app.api.v1.endpoints.data_platform.get_current_user", return_value=mock_user)

        response = await client.get(
            "/api/v1/data/candles/5min/2024-11-29T14:30:00Z",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["code"] == "NOT_FOUND"

    async def test_get_candle_with_oflow_detail(self, client: AsyncClient, mock_user, auth_headers, sample_candle, mocker):
        """Test candle retrieval with order flow details."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_candle
        mock_db.execute.return_value = mock_result

        mocker.patch("app.api.v1.endpoints.data_platform.get_db", return_value=mock_db)
        mocker.patch("app.api.v1.endpoints.data_platform.get_current_user", return_value=mock_user)

        response = await client.get(
            "/api/v1/data/candles/5min/2024-11-29T14:30:00Z",
            headers=auth_headers,
            params={"include_oflow": True}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "oflow_detail" in data
        assert "price_levels" in data["oflow_detail"]

    async def test_get_ticks_empty_response(self, client: AsyncClient, mock_user, auth_headers, mocker):
        """Test ticks endpoint returns empty response (not implemented yet)."""
        mocker.patch("app.api.v1.endpoints.data_platform.get_current_user", return_value=mock_user)
        mocker.patch("app.api.v1.endpoints.data_platform.get_db", return_value=AsyncMock())

        response = await client.get(
            "/api/v1/data/ticks",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0

    async def test_get_coverage(self, client: AsyncClient, mock_user, auth_headers, mocker):
        """Test coverage endpoint returns timeframe information."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.count = 105120
        mock_row.start = datetime(2024, 1, 1, 0, 0, 0)
        mock_row.end = datetime(2024, 11, 29, 23, 55, 0)
        mock_result.one_or_none.return_value = mock_row
        mock_db.execute.return_value = mock_result

        mocker.patch("app.api.v1.endpoints.data_platform.get_db", return_value=mock_db)
        mocker.patch("app.api.v1.endpoints.data_platform.get_current_user", return_value=mock_user)

        response = await client.get(
            "/api/v1/data/coverage",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "timeframes" in data
        assert isinstance(data["timeframes"], list)
        assert len(data["timeframes"]) == 7  # All valid timeframes

        # Check 5min timeframe has data
        five_min = next(tf for tf in data["timeframes"] if tf["tf"] == "5min")
        assert five_min["count"] == 105120
        assert five_min["start"] is not None
        assert five_min["end"] is not None

    async def test_get_active_contracts(self, client: AsyncClient, mock_user, auth_headers, mocker):
        """Test active contracts endpoint."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = ["NQH25", "NQM25", "NQU25"]
        mock_db.execute.return_value = mock_result

        mocker.patch("app.api.v1.endpoints.data_platform.get_db", return_value=mock_db)
        mocker.patch("app.api.v1.endpoints.data_platform.get_current_user", return_value=mock_user)

        response = await client.get(
            "/api/v1/data/contracts/active",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "contracts" in data
        assert isinstance(data["contracts"], list)
        assert len(data["contracts"]) == 3

        # Check first contract structure
        first_contract = data["contracts"][0]
        assert "symbol" in first_contract
        assert "expiry" in first_contract
        assert "is_front_month" in first_contract
        assert first_contract["is_front_month"] is True  # First one is front month

    async def test_get_rollover_periods(self, client: AsyncClient, mock_user, auth_headers, mocker):
        """Test rollover periods endpoint."""
        mocker.patch("app.api.v1.endpoints.data_platform.get_current_user", return_value=mock_user)
        mocker.patch("app.api.v1.endpoints.data_platform.get_db", return_value=AsyncMock())

        response = await client.get(
            "/api/v1/data/rollover-periods",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "rollovers" in data
        assert isinstance(data["rollovers"], list)

        # Check rollover structure
        if data["rollovers"]:
            rollover = data["rollovers"][0]
            assert "from_symbol" in rollover
            assert "to_symbol" in rollover
            assert "rollover_date" in rollover

    async def test_create_export_job_success(self, client: AsyncClient, mock_user, auth_headers, mocker):
        """Test successful export job creation."""
        mocker.patch("app.api.v1.endpoints.data_platform.get_current_user", return_value=mock_user)
        mocker.patch("app.api.v1.endpoints.data_platform.get_db", return_value=AsyncMock())

        request_data = {
            "table": "candles_5min",
            "start": "2024-11-01T00:00:00Z",
            "end": "2024-11-30T23:59:59Z",
            "include_oflow": True,
            "format": "parquet"
        }

        response = await client.post(
            "/api/v1/data/export",
            headers=auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "job_id" in data
        assert "status" in data
        assert data["status"] == "queued"

    async def test_create_export_job_invalid_table(self, client: AsyncClient, mock_user, auth_headers, mocker):
        """Test export job creation with invalid table."""
        mocker.patch("app.api.v1.endpoints.data_platform.get_current_user", return_value=mock_user)
        mocker.patch("app.api.v1.endpoints.data_platform.get_db", return_value=AsyncMock())

        request_data = {
            "table": "invalid_table",
            "start": "2024-11-01T00:00:00Z",
            "end": "2024-11-30T23:59:59Z",
            "format": "parquet"
        }

        response = await client.post(
            "/api/v1/data/export",
            headers=auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["code"] == "INVALID_TABLE"

    async def test_create_export_job_missing_fields(self, client: AsyncClient, mock_user, auth_headers, mocker):
        """Test export job creation with missing required fields."""
        mocker.patch("app.api.v1.endpoints.data_platform.get_current_user", return_value=mock_user)
        mocker.patch("app.api.v1.endpoints.data_platform.get_db", return_value=AsyncMock())

        request_data = {
            "table": "candles_5min",
            # Missing start and end
            "format": "parquet"
        }

        response = await client.post(
            "/api/v1/data/export",
            headers=auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["code"] == "VALIDATION_ERROR"

    async def test_get_export_job_status_not_found(self, client: AsyncClient, mock_user, auth_headers, mocker):
        """Test export job status with non-existent job ID."""
        mocker.patch("app.api.v1.endpoints.data_platform.get_current_user", return_value=mock_user)
        mocker.patch("app.api.v1.endpoints.data_platform.get_db", return_value=AsyncMock())

        job_id = str(uuid4())
        response = await client.get(
            f"/api/v1/data/export/{job_id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["code"] == "NOT_FOUND"

    async def test_authentication_required(self, client: AsyncClient):
        """Test that endpoints require authentication."""
        # Test without auth header
        response = await client.get("/api/v1/data/candles/5min")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = await client.get("/api/v1/data/coverage")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = await client.get("/api/v1/data/contracts/active")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = await client.post("/api/v1/data/export", json={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_candles_pagination(self, client: AsyncClient, mock_user, auth_headers, mocker):
        """Test pagination parameters for candles endpoint."""
        mock_db = AsyncMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        mock_db.execute.return_value.scalar.return_value = 100

        mocker.patch("app.api.v1.endpoints.data_platform.get_db", return_value=mock_db)
        mocker.patch("app.api.v1.endpoints.data_platform.get_current_user", return_value=mock_user)

        response = await client.get(
            "/api/v1/data/candles/5min",
            headers=auth_headers,
            params={
                "limit": 50,
                "offset": 50
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["has_more"] is False  # offset + limit >= total

    async def test_candles_date_filtering(self, client: AsyncClient, mock_user, auth_headers, sample_candle, mocker):
        """Test date filtering for candles endpoint."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_candle]
        mock_db.execute.return_value = mock_result

        mocker.patch("app.api.v1.endpoints.data_platform.get_db", return_value=mock_db)
        mocker.patch("app.api.v1.endpoints.data_platform.get_current_user", return_value=mock_user)

        response = await client.get(
            "/api/v1/data/candles/5min",
            headers=auth_headers,
            params={
                "start": "2024-11-01T00:00:00Z",
                "end": "2024-11-30T23:59:59Z"
            }
        )

        assert response.status_code == status.HTTP_200_OK

    async def test_error_response_format(self, client: AsyncClient, mock_user, auth_headers, mocker):
        """Test that error responses follow CONTRACT-001 format."""
        mock_db = AsyncMock()
        # Simulate database error
        mock_db.execute.side_effect = Exception("Database connection error")

        mocker.patch("app.api.v1.endpoints.data_platform.get_db", return_value=mock_db)
        mocker.patch("app.api.v1.endpoints.data_platform.get_current_user", return_value=mock_user)

        response = await client.get(
            "/api/v1/data/candles/5min",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data
        assert "code" in data
        assert data["code"] == "INTERNAL_ERROR"