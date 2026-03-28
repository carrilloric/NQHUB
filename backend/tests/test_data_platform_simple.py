"""
Simple tests for Data Platform API to verify endpoints are registered correctly.
"""

import pytest
from app.main import app

def test_data_platform_endpoints_registered():
    """Test that all Data Platform endpoints are registered."""
    routes = [route.path for route in app.routes]

    # Check that our endpoints are registered
    required_endpoints = [
        "/api/v1/data/candles/{tf}",
        "/api/v1/data/candles/{tf}/{timestamp}",
        "/api/v1/data/ticks",
        "/api/v1/data/coverage",
        "/api/v1/data/contracts/active",
        "/api/v1/data/rollover-periods",
        "/api/v1/data/export",
        "/api/v1/data/export/{job_id}",
    ]

    for endpoint in required_endpoints:
        assert endpoint in routes, f"Missing endpoint: {endpoint}"

    print(f"✓ All {len(required_endpoints)} Data Platform endpoints are registered")

def test_data_platform_methods():
    """Test that endpoints have correct HTTP methods."""
    route_methods = {}
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            route_methods[route.path] = route.methods

    # Check GET endpoints
    get_endpoints = [
        "/api/v1/data/candles/{tf}",
        "/api/v1/data/candles/{tf}/{timestamp}",
        "/api/v1/data/ticks",
        "/api/v1/data/coverage",
        "/api/v1/data/contracts/active",
        "/api/v1/data/rollover-periods",
        "/api/v1/data/export/{job_id}",
    ]

    for endpoint in get_endpoints:
        assert endpoint in route_methods, f"Endpoint not found: {endpoint}"
        assert "GET" in route_methods[endpoint], f"GET method not allowed for {endpoint}"

    # Check POST endpoint
    assert "/api/v1/data/export" in route_methods
    assert "POST" in route_methods["/api/v1/data/export"], "POST method not allowed for /api/v1/data/export"

    print("✓ All endpoint methods are correctly configured")

def test_data_platform_tags():
    """Test that endpoints are tagged correctly."""
    for route in app.routes:
        if hasattr(route, 'path') and route.path.startswith("/api/v1/data/"):
            if hasattr(route, 'endpoint') and hasattr(route.endpoint, '__name__'):
                # Endpoints should be from data_platform module
                module = getattr(route.endpoint, '__module__', '')
                assert 'data_platform' in module, f"Endpoint {route.path} not from data_platform module"

    print("✓ All Data Platform endpoints are properly tagged")

if __name__ == "__main__":
    test_data_platform_endpoints_registered()
    test_data_platform_methods()
    test_data_platform_tags()
    print("\n✅ All Data Platform API integration tests passed!")