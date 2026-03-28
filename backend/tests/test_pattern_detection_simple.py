"""
Simple tests for Pattern Detection REST API to verify endpoints are registered correctly.
"""

import pytest
from app.main import app

def test_pattern_detection_endpoints_registered():
    """Test that all Pattern Detection REST endpoints are registered."""
    routes = [route.path for route in app.routes]

    # Check that our endpoints are registered
    required_endpoints = [
        "/api/v1/patterns/fvgs",
        "/api/v1/patterns/order-blocks",
        "/api/v1/patterns/liquidity-pools",
        "/api/v1/patterns/snapshot",
        "/api/v1/patterns/interactions",
    ]

    for endpoint in required_endpoints:
        assert endpoint in routes, f"Missing endpoint: {endpoint}"

    print(f"✓ All {len(required_endpoints)} Pattern Detection REST endpoints are registered")

def test_pattern_detection_methods():
    """Test that endpoints have correct HTTP methods."""
    route_methods = {}
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            route_methods[route.path] = route.methods

    # All Pattern Detection REST endpoints should be GET only
    get_endpoints = [
        "/api/v1/patterns/fvgs",
        "/api/v1/patterns/order-blocks",
        "/api/v1/patterns/liquidity-pools",
        "/api/v1/patterns/snapshot",
        "/api/v1/patterns/interactions",
    ]

    for endpoint in get_endpoints:
        assert endpoint in route_methods, f"Endpoint not found: {endpoint}"
        assert "GET" in route_methods[endpoint], f"GET method not allowed for {endpoint}"
        # Ensure these are READ-ONLY (no POST/PUT/DELETE)
        assert "POST" not in route_methods[endpoint], f"POST should not be allowed for READ-ONLY endpoint {endpoint}"
        assert "PUT" not in route_methods[endpoint], f"PUT should not be allowed for READ-ONLY endpoint {endpoint}"
        assert "DELETE" not in route_methods[endpoint], f"DELETE should not be allowed for READ-ONLY endpoint {endpoint}"

    print("✓ All endpoints have correct HTTP methods (GET only)")

def test_pattern_detection_tags():
    """Test that endpoints are tagged correctly."""
    for route in app.routes:
        if hasattr(route, 'path') and route.path in [
            "/api/v1/patterns/fvgs",
            "/api/v1/patterns/order-blocks",
            "/api/v1/patterns/liquidity-pools",
            "/api/v1/patterns/snapshot",
            "/api/v1/patterns/interactions",
        ]:
            if hasattr(route, 'endpoint') and hasattr(route.endpoint, '__name__'):
                # Endpoints should be from pattern_detection module
                module = getattr(route.endpoint, '__module__', '')
                assert 'pattern_detection' in module, f"Endpoint {route.path} not from pattern_detection module"

    print("✓ All Pattern Detection REST endpoints are properly tagged")

def test_existing_pattern_endpoints_still_work():
    """Test that existing pattern generation endpoints are still registered."""
    routes = [route.path for route in app.routes]

    # Check that existing generation endpoints are still there
    existing_endpoints = [
        "/api/v1/patterns/fvgs/generate",
        "/api/v1/patterns/fvgs/list",
        "/api/v1/patterns/liquidity-pools/generate",
        "/api/v1/patterns/liquidity-pools/list",
        "/api/v1/patterns/order-blocks/generate",
        "/api/v1/patterns/order-blocks/list",
    ]

    for endpoint in existing_endpoints:
        assert endpoint in routes, f"Existing endpoint missing: {endpoint}"

    print(f"✓ All {len(existing_endpoints)} existing pattern generation endpoints still work")

if __name__ == "__main__":
    test_pattern_detection_endpoints_registered()
    test_pattern_detection_methods()
    test_pattern_detection_tags()
    test_existing_pattern_endpoints_still_work()
    print("\n✅ All Pattern Detection REST API integration tests passed!")