"""
Tests for Backtesting API Endpoints

Tests for CONTRACT-003 Strategy & Backtesting API implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4
import json

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.strategy import Strategy, BacktestRun, StrategyApproval
from app.models.user import User


# ============= Test Fixtures =============

@pytest.fixture
def mock_strategy():
    """Create a mock strategy for testing"""
    strategy = MagicMock(spec=Strategy)
    strategy.id = uuid4()
    strategy.name = "Test Strategy"
    strategy.version = "1.0.0"
    strategy.type = "momentum"
    strategy.status = "draft"
    strategy.source_code = "def strategy_logic(df):\n    return signals"
    strategy.created_at = datetime.utcnow()
    strategy.required_features = ["volume", "delta"]
    return strategy


@pytest.fixture
def mock_backtest_run():
    """Create a mock backtest run for testing"""
    run = MagicMock(spec=BacktestRun)
    run.id = uuid4()
    run.strategy_id = uuid4()
    run.status = "completed"
    run.source = "nqhub"
    run.params = {"fast_ma": 20, "slow_ma": 50}
    run.config = {
        "start": "2025-01-01",
        "end": "2025-12-31",
        "timeframe": "5min",
        "commission": 0.0002,
        "slippage": 1
    }
    run.results = {
        "sharpe": 2.5,
        "sortino": 3.1,
        "max_dd": 0.15,
        "win_rate": 0.65,
        "profit_factor": 2.1,
        "total_trades": 450,
        "net_profit": 125000,
        "avg_win": 350,
        "avg_loss": -150,
        "max_consecutive_wins": 8,
        "max_consecutive_losses": 3
    }
    run.created_at = datetime.utcnow()
    run.completed_at = datetime.utcnow()
    return run


@pytest.fixture
def mock_approval():
    """Create a mock strategy approval for testing"""
    approval = MagicMock(spec=StrategyApproval)
    approval.id = uuid4()
    approval.strategy_id = uuid4()
    approval.backtest_run_id = uuid4()
    approval.approved_params = {"fast_ma": 20, "slow_ma": 50}
    approval.approved_by = "test@example.com"
    approval.approved_at = datetime.utcnow()
    approval.notes = "Approved for production"
    return approval


# ============= Happy Path Tests =============

@pytest.mark.asyncio
async def test_list_strategies_empty(async_client, auth_headers):
    """Test that GET /strategies returns empty list without error"""
    response = await async_client.get("/api/v1/backtest/strategies", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "strategies" in data
    assert data["strategies"] == []


@pytest.mark.asyncio
async def test_save_strategy_creates_draft(async_client, auth_headers, mock_strategy):
    """Test that POST /strategies/save creates strategy with status='draft'"""
    request_data = {
        "code": "def strategy_logic(df):\n    return signals",
        "name": "New Strategy",
        "version": "1.0.0",
        "description": "Test strategy"
    }

    with patch("app.api.v1.endpoints.backtesting.select") as mock_select:
        # Mock no existing strategy
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_execute = AsyncMock(return_value=mock_result)

        response = await async_client.post(
            "/api/v1/strategies/save",
            json=request_data,
            headers=auth_headers
        )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_validate_strategy_valid_code(async_client, auth_headers):
    """Test that valid code returns {valid: true}"""
    request_data = {
        "code": """
import pandas as pd
import numpy as np

def strategy_logic(df):
    # Simple momentum strategy
    df['returns'] = df['close'].pct_change()
    df['signal'] = np.where(df['returns'] > 0, 1, -1)
    return df['signal']
"""
    }

    response = await async_client.post(
        "/api/v1/strategies/validate",
        json=request_data,
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["valid"] == True
    assert data["errors"] == []
    assert "detected_type" in data
    assert data["detected_type"] == "momentum"


@pytest.mark.asyncio
async def test_import_backtest_results(async_client, auth_headers, mock_strategy):
    """Test that POST /results/import returns run_id with source='notebook'"""
    request_data = {
        "strategy_id": str(mock_strategy.id),
        "results": {
            "sharpe": 2.0,
            "sortino": 2.5,
            "max_dd": 0.20,
            "win_rate": 0.60,
            "profit_factor": 1.8,
            "total_trades": 200,
            "net_profit": 50000
        },
        "source": "notebook",
        "params_used": {"fast_ma": 15, "slow_ma": 45}
    }

    with patch("app.api.v1.endpoints.backtesting.select") as mock_select:
        # Mock strategy exists
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_strategy
        mock_execute = AsyncMock(return_value=mock_result)

        response = await async_client.post(
            "/api/v1/backtest/results/import",
            json=request_data,
            headers=auth_headers
        )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "run_id" in data
    assert data["status"] == "imported"


@pytest.mark.asyncio
async def test_screener_filters_by_min_sharpe(async_client, auth_headers, mock_backtest_run):
    """Test that screener only returns runs with sharpe >= threshold"""
    # Create two runs with different sharpe ratios
    run1 = mock_backtest_run
    run1.results["sharpe"] = 2.0  # Above threshold

    run2 = MagicMock(spec=BacktestRun)
    run2.id = uuid4()
    run2.results = {"sharpe": 1.0}  # Below threshold

    with patch("app.api.v1.endpoints.backtesting.select") as mock_select:
        # Mock query results
        mock_result = AsyncMock()
        mock_result.all.return_value = [(run1, "Strategy1", "momentum")]
        mock_execute = AsyncMock(return_value=mock_result)

        response = await async_client.get(
            "/api/v1/backtest/screener?min_sharpe=1.5",
            headers=auth_headers
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "runs" in data
    assert "total" in data
    # Check that results are filtered correctly
    if len(data["runs"]) > 0:
        for run in data["runs"]:
            assert run["results"]["sharpe"] >= 1.5


@pytest.mark.asyncio
async def test_approval_checklist_fails_low_sharpe(async_client, auth_headers, mock_strategy, mock_backtest_run):
    """Test that approval checklist fails when sharpe < 1.5"""
    # Set sharpe below threshold
    mock_backtest_run.results["sharpe"] = 1.2

    with patch("app.api.v1.endpoints.backtesting.select") as mock_select:
        # Mock strategy exists
        strategy_result = AsyncMock()
        strategy_result.scalar_one_or_none.return_value = mock_strategy

        # Mock backtest run with low sharpe
        run_result = AsyncMock()
        run_result.scalar_one_or_none.return_value = mock_backtest_run

        mock_execute = AsyncMock()
        mock_execute.side_effect = [strategy_result, run_result]

        response = await async_client.get(
            f"/api/v1/approval/checklist/{mock_strategy.id}",
            headers=auth_headers
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["overall_passed"] == False

    # Find sharpe check
    sharpe_check = next(
        (c for c in data["checks"] if "Sharpe" in c["name"]),
        None
    )
    if sharpe_check:
        assert sharpe_check["passed"] == False
        assert sharpe_check["value"] == 1.2
        assert sharpe_check["threshold"] == 1.5


@pytest.mark.asyncio
async def test_approve_strategy_freezes_params(async_client, auth_headers, mock_strategy, mock_backtest_run):
    """Test that approval returns approval_id and freezes params"""
    request_data = {
        "strategy_id": str(mock_strategy.id),
        "backtest_run_id": str(mock_backtest_run.id),
        "notes": "Approved for production trading"
    }

    # Ensure backtest meets approval criteria
    mock_backtest_run.results = {
        "sharpe": 2.0,
        "profit_factor": 2.0,
        "total_trades": 200,
        "max_dd": 0.15,
        "sortino": 2.5,
        "win_rate": 0.65
    }

    with patch("app.api.v1.endpoints.backtesting.select") as mock_select:
        # Mock strategy and run exist
        strategy_result = AsyncMock()
        strategy_result.scalar_one_or_none.return_value = mock_strategy

        run_result = AsyncMock()
        run_result.scalar_one_or_none.return_value = mock_backtest_run

        approval_result = AsyncMock()
        approval_result.scalar_one_or_none.return_value = None  # No existing approval

        mock_execute = AsyncMock()
        mock_execute.side_effect = [strategy_result, run_result, approval_result]

        response = await async_client.post(
            "/api/v1/approval/approve",
            json=request_data,
            headers=auth_headers
        )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "approval_id" in data
    assert "approved_at" in data


# ============= Edge Case Tests =============

@pytest.mark.asyncio
async def test_get_nonexistent_run(async_client, auth_headers):
    """Test that GET /runs/{uuid} returns 404 for nonexistent run"""
    nonexistent_id = str(uuid4())

    with patch("app.api.v1.endpoints.backtesting.select") as mock_select:
        # Mock no run found
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_execute = AsyncMock(return_value=mock_result)

        response = await async_client.get(
            f"/api/v1/backtest/runs/{nonexistent_id}",
            headers=auth_headers
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"]["error"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_import_results_missing_strategy(async_client, auth_headers):
    """Test that import results returns 404 when strategy doesn't exist"""
    request_data = {
        "strategy_id": str(uuid4()),
        "results": {
            "sharpe": 2.0,
            "sortino": 2.5,
            "max_dd": 0.20,
            "win_rate": 0.60
        },
        "source": "notebook"
    }

    with patch("app.api.v1.endpoints.backtesting.select") as mock_select:
        # Mock strategy not found
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_execute = AsyncMock(return_value=mock_result)

        response = await async_client.post(
            "/api/v1/backtest/results/import",
            json=request_data,
            headers=auth_headers
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"]["error"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_screener_order_by_sortino(async_client, auth_headers):
    """Test that screener results are ordered correctly by sortino"""
    # Create multiple runs with different sortino values
    run1 = MagicMock(spec=BacktestRun)
    run1.id = uuid4()
    run1.results = {"sortino": 3.0, "sharpe": 2.0}
    run1.created_at = datetime.utcnow()
    run1.config = {"timeframe": "5min"}
    run1.source = "nqhub"

    run2 = MagicMock(spec=BacktestRun)
    run2.id = uuid4()
    run2.results = {"sortino": 4.0, "sharpe": 2.5}
    run2.created_at = datetime.utcnow()
    run2.config = {"timeframe": "5min"}
    run2.source = "nqhub"

    with patch("app.api.v1.endpoints.backtesting.select") as mock_select:
        # Mock ordered query results
        mock_result = AsyncMock()
        mock_result.all.return_value = [
            (run2, "Strategy2", "momentum"),  # Higher sortino first
            (run1, "Strategy1", "momentum")
        ]
        mock_execute = AsyncMock(return_value=mock_result)

        response = await async_client.get(
            "/api/v1/backtest/screener?order_by=sortino",
            headers=auth_headers
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "runs" in data

    # Check ordering
    if len(data["runs"]) >= 2:
        assert data["runs"][0]["results"]["sortino"] >= data["runs"][1]["results"]["sortino"]


# ============= Contract Tests =============

@pytest.mark.asyncio
async def test_backtest_run_response_has_task_id(async_client, auth_headers, mock_strategy):
    """Test that POST /run returns task_id"""
    request_data = {
        "strategy_id": str(mock_strategy.id),
        "params": {"fast_ma": 20, "slow_ma": 50},
        "config": {
            "start": "2025-01-01",
            "end": "2025-12-31",
            "timeframe": "5min",
            "commission": 0.0002,
            "slippage": 1
        }
    }

    with patch("app.api.v1.endpoints.backtesting.select") as mock_select:
        # Mock strategy exists
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_strategy
        mock_execute = AsyncMock(return_value=mock_result)

        response = await async_client.post(
            "/api/v1/backtest/run",
            json=request_data,
            headers=auth_headers
        )

    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert "run_id" in data
    assert "status" in data
    assert "task_id" in data
    assert data["status"] == "queued"


@pytest.mark.asyncio
async def test_screener_response_has_total_count(async_client, auth_headers):
    """Test that screener response includes total field"""
    response = await async_client.get("/api/v1/backtest/screener", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "runs" in data
    assert "total" in data
    assert isinstance(data["total"], int)


@pytest.mark.asyncio
async def test_equity_curve_in_run_detail(async_client, auth_headers, mock_backtest_run):
    """Test that GET /runs/{id} includes equity_curve array"""
    with patch("app.api.v1.endpoints.backtesting.select") as mock_select:
        # Mock run found
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_backtest_run
        mock_execute = AsyncMock(return_value=mock_result)

        response = await async_client.get(
            f"/api/v1/backtest/runs/{mock_backtest_run.id}",
            headers=auth_headers
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "equity_curve" in data
    assert isinstance(data["equity_curve"], list)

    # Check equity curve structure
    if len(data["equity_curve"]) > 0:
        point = data["equity_curve"][0]
        assert "date" in point
        assert "equity" in point


# ============= Validation Tests =============

@pytest.mark.asyncio
async def test_save_strategy_invalid_version_format(async_client, auth_headers):
    """Test that invalid version format returns 400"""
    request_data = {
        "code": "def strategy(): pass",
        "name": "Test Strategy",
        "version": "v1.0",  # Invalid format
        "description": "Test"
    }

    response = await async_client.post(
        "/api/v1/strategies/save",
        json=request_data,
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"]["error"] == "VALIDATION_ERROR"
    assert "semver" in data["detail"]["message"].lower()


@pytest.mark.asyncio
async def test_run_backtest_invalid_timeframe(async_client, auth_headers, mock_strategy):
    """Test that invalid timeframe returns 400"""
    request_data = {
        "strategy_id": str(mock_strategy.id),
        "config": {
            "start": "2025-01-01",
            "end": "2025-12-31",
            "timeframe": "2min"  # Invalid timeframe
        }
    }

    with patch("app.api.v1.endpoints.backtesting.select") as mock_select:
        # Mock strategy exists
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_strategy
        mock_execute = AsyncMock(return_value=mock_result)

        response = await async_client.post(
            "/api/v1/backtest/run",
            json=request_data,
            headers=auth_headers
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"]["error"] == "VALIDATION_ERROR"
    assert "timeframe" in data["detail"]["message"].lower()


@pytest.mark.asyncio
async def test_import_results_missing_required_metrics(async_client, auth_headers, mock_strategy):
    """Test that missing required metrics returns 400"""
    request_data = {
        "strategy_id": str(mock_strategy.id),
        "results": {
            "sharpe": 2.0,
            # Missing sortino, max_dd, win_rate
        },
        "source": "notebook"
    }

    with patch("app.api.v1.endpoints.backtesting.select") as mock_select:
        # Mock strategy exists
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_strategy
        mock_execute = AsyncMock(return_value=mock_result)

        response = await async_client.post(
            "/api/v1/backtest/results/import",
            json=request_data,
            headers=auth_headers
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"]["error"] == "VALIDATION_ERROR"
    assert "required" in data["detail"]["message"].lower()


@pytest.mark.asyncio
async def test_optimize_invalid_method(async_client, auth_headers, mock_strategy):
    """Test that invalid optimization method returns 400"""
    request_data = {
        "strategy_id": str(mock_strategy.id),
        "param_grid": {
            "fast_ma": [10, 20, 30],
            "slow_ma": [40, 50, 60]
        },
        "method": "random_search",  # Invalid method
        "config": {
            "start": "2025-01-01",
            "end": "2025-12-31",
            "timeframe": "5min"
        }
    }

    with patch("app.api.v1.endpoints.backtesting.select") as mock_select:
        # Mock strategy exists
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_strategy
        mock_execute = AsyncMock(return_value=mock_result)

        response = await async_client.post(
            "/api/v1/backtest/optimize",
            json=request_data,
            headers=auth_headers
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"]["error"] == "VALIDATION_ERROR"
    assert "method" in data["detail"]["message"].lower()


@pytest.mark.asyncio
async def test_approve_strategy_without_meeting_criteria(async_client, auth_headers, mock_strategy, mock_backtest_run):
    """Test that approval fails when criteria not met"""
    # Set metrics below thresholds
    mock_backtest_run.results = {
        "sharpe": 1.0,  # Below 1.5 threshold
        "profit_factor": 1.0,  # Below 1.5 threshold
        "total_trades": 50,  # Below 100 threshold
        "max_dd": 0.40,  # Above 0.30 threshold
        "sortino": 1.5,
        "win_rate": 0.50
    }

    request_data = {
        "strategy_id": str(mock_strategy.id),
        "backtest_run_id": str(mock_backtest_run.id),
        "notes": "Trying to approve"
    }

    with patch("app.api.v1.endpoints.backtesting.select") as mock_select:
        # Mock strategy and run exist
        strategy_result = AsyncMock()
        strategy_result.scalar_one_or_none.return_value = mock_strategy

        run_result = AsyncMock()
        run_result.scalar_one_or_none.return_value = mock_backtest_run

        mock_execute = AsyncMock()
        mock_execute.side_effect = [strategy_result, run_result]

        response = await async_client.post(
            "/api/v1/approval/approve",
            json=request_data,
            headers=auth_headers
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"]["error"] == "APPROVAL_FAILED"
    assert "criteria" in data["detail"]["message"].lower()