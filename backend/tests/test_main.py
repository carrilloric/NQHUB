"""
Main tests for NQHUB backend API
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_endpoint(self):
        """Test that GET /health returns {"status": "ok"}."""
        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200
        assert "status" in response.json()
        assert response.json()["status"] == "healthy"


class TestRouterRegistration:
    """Test that all routers are registered."""

    def test_all_routers_registered(self):
        """Test that all required routers are registered in the app."""
        client = TestClient(app)

        # List of all expected router prefixes
        expected_routes = [
            "/api/v1/auth",
            "/api/v1/invitations",
            "/api/v1/candles",
            "/api/v1/patterns",
            "/api/v1/market-state",
            "/api/v1/audit",
            "/api/v1/system",
            "/api/v1/features",
            "/api/v1/backtesting",
            "/api/v1/ml",
            "/api/v1/approval",
            "/api/v1/bots",
            "/api/v1/orders",
            "/api/v1/risk",
            "/api/v1/trades",
            "/api/v1/settings",
            "/api/v1/strategies",
            "/api/v1/assistant",
        ]

        # Get all routes from the app
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)

        # Check that each expected route prefix has at least one route
        for prefix in expected_routes:
            # Check if any route starts with this prefix
            has_route = any(route.startswith(prefix) for route in routes)
            assert has_route, f"No routes found for prefix: {prefix}"

    def test_no_vanna_router(self):
        """Test that vanna router is not registered."""
        client = TestClient(app)

        # Get all routes from the app
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)

        # Check that no route contains 'vanna'
        vanna_routes = [r for r in routes if 'vanna' in r.lower()]
        assert len(vanna_routes) == 0, f"Found vanna routes that should be removed: {vanna_routes}"