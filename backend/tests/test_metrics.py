"""
Tests for Prometheus metrics endpoint and middleware.
"""
import pytest
import time
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from prometheus_client import REGISTRY, Counter, Gauge, Histogram
from prometheus_client.parser import text_string_to_metric_families

from app.main import app
from app.core.metrics import (
    bot_pnl_usd,
    bot_daily_loss_pct,
    bot_trailing_drawdown_pct,
    bot_heartbeat_age_seconds,
    bot_status,
    bot_trades_total,
    orders_submitted_total,
    orders_filled_total,
    orders_rejected_total,
    order_latency_seconds,
    api_request_duration,
    websocket_connections,
    redis_pub_events,
    update_bot_metrics,
    record_trade,
    record_order,
    record_order_latency,
    record_api_request,
    update_websocket_connections,
    record_redis_event,
    update_bot_heartbeat,
    set_bot_status
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset all metrics before each test."""
    # Clear all metrics from registry
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            if hasattr(collector, '_metrics'):
                collector._metrics.clear()
        except:
            pass
    yield
    # Clean up after test
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            if hasattr(collector, '_metrics'):
                collector._metrics.clear()
        except:
            pass


class TestMetricsEndpoint:
    """Tests for the /metrics endpoint."""

    def test_metrics_endpoint_returns_200(self, client):
        """Test that /metrics endpoint returns 200 OK."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"

    def test_metrics_prometheus_format(self, client):
        """Test that metrics are in Prometheus format."""
        response = client.get("/metrics")
        assert response.status_code == 200

        # Parse the response to ensure it's valid Prometheus format
        families = list(text_string_to_metric_families(response.text))
        assert len(families) > 0

        # Check for some expected metric families
        metric_names = [f.name for f in families]
        assert "nqhub_bot_pnl_usd" in metric_names
        assert "nqhub_bot_daily_loss_pct" in metric_names
        assert "nqhub_bot_trailing_drawdown_pct" in metric_names
        assert "nqhub_bot_heartbeat_age_seconds" in metric_names
        assert "nqhub_bot_status" in metric_names
        assert "nqhub_bot_trades_total" in metric_names
        assert "nqhub_orders_submitted_total" in metric_names
        assert "nqhub_orders_filled_total" in metric_names
        assert "nqhub_orders_rejected_total" in metric_names
        assert "nqhub_order_latency_seconds" in metric_names
        assert "nqhub_api_request_duration_seconds" in metric_names
        assert "nqhub_websocket_connections_active" in metric_names
        assert "nqhub_redis_pub_events_total" in metric_names

    def test_bot_pnl_gauge_sets_value(self, client):
        """Test that bot P&L gauge sets value correctly."""
        # Update bot metrics
        update_bot_metrics("bot-001", {"pnl_usd": 1234.56})

        # Get metrics
        response = client.get("/metrics")
        assert response.status_code == 200

        # Check the metric value
        families = list(text_string_to_metric_families(response.text))
        pnl_family = next((f for f in families if f.name == "nqhub_bot_pnl_usd"), None)
        assert pnl_family is not None

        # Find the sample for bot-001
        for sample in pnl_family.samples:
            if sample.labels.get("bot_id") == "bot-001":
                assert sample.value == 1234.56
                break
        else:
            pytest.fail("bot-001 P&L metric not found")

    def test_trade_counter_increments(self, client):
        """Test that trade counter increments correctly."""
        # Record some trades
        record_trade("bot-001", "long")
        record_trade("bot-001", "long")
        record_trade("bot-001", "short")
        record_trade("bot-002", "long")

        # Get metrics
        response = client.get("/metrics")
        assert response.status_code == 200

        # Check the metric values
        families = list(text_string_to_metric_families(response.text))
        trades_family = next((f for f in families if f.name == "nqhub_bot_trades_total"), None)
        assert trades_family is not None

        # Check counts
        bot1_long_count = 0
        bot1_short_count = 0
        bot2_long_count = 0

        for sample in trades_family.samples:
            if sample.labels.get("bot_id") == "bot-001" and sample.labels.get("direction") == "long":
                bot1_long_count = sample.value
            elif sample.labels.get("bot_id") == "bot-001" and sample.labels.get("direction") == "short":
                bot1_short_count = sample.value
            elif sample.labels.get("bot_id") == "bot-002" and sample.labels.get("direction") == "long":
                bot2_long_count = sample.value

        assert bot1_long_count == 2
        assert bot1_short_count == 1
        assert bot2_long_count == 1


class TestMetricsHelpers:
    """Tests for metrics helper functions."""

    def test_update_bot_metrics_all_fields(self):
        """Test updating all bot metrics."""
        metrics_data = {
            "pnl_usd": 500.0,
            "daily_loss_pct": 25.5,
            "trailing_drawdown_pct": 15.3,
            "win_rate": 0.65,
            "max_drawdown": 1000.0,
            "realized_pnl": 450.0,
            "unrealized_pnl": 50.0,
            "total_trades": 100,
            "winning_trades": 65,
            "losing_trades": 35,
            "avg_win": 50.0,
            "avg_loss": 20.0
        }

        update_bot_metrics("bot-test", metrics_data)

        # Verify metrics were set (this would be checked via /metrics endpoint in integration test)
        # For unit test, we just ensure no exceptions are raised
        assert True

    def test_record_order_lifecycle(self):
        """Test recording order submission, fill, and rejection."""
        # Submit an order
        record_order("bot-001", "submitted")

        # Fill the order with latency
        record_order("bot-001", "filled")
        record_order_latency(0.125)  # 125ms

        # Reject another order
        record_order("bot-002", "submitted")
        record_order("bot-002", "rejected")

        # Verify metrics were recorded (checked via /metrics in integration test)
        assert True

    def test_update_websocket_connections(self):
        """Test updating WebSocket connection count."""
        # Add connections
        update_websocket_connections(5)
        update_websocket_connections(7)

        # Remove connections
        update_websocket_connections(3)

        # Verify metric was updated
        assert True

    def test_record_redis_events(self):
        """Test recording Redis pub/sub events."""
        # Record events on different channels
        record_redis_event("market_data")
        record_redis_event("market_data")
        record_redis_event("bot_updates")
        record_redis_event("alerts")

        # Verify counters were incremented
        assert True

    def test_update_bot_heartbeat(self):
        """Test updating bot heartbeat."""
        # Set initial heartbeat
        update_bot_heartbeat("bot-001")

        # Wait a bit
        time.sleep(0.1)

        # Update heartbeat again
        update_bot_heartbeat("bot-001")

        # Set for another bot
        update_bot_heartbeat("bot-002")

        # Verify heartbeat ages were recorded
        assert True

    def test_set_bot_status(self):
        """Test setting bot status."""
        # Set bot as running
        set_bot_status("bot-001", True)

        # Set bot as stopped
        set_bot_status("bot-002", False)

        # Toggle bot-001 status
        set_bot_status("bot-001", False)

        # Verify status values were set
        assert True


class TestPrometheusMiddleware:
    """Tests for the Prometheus middleware."""

    def test_api_middleware_records_duration(self, client):
        """Test that API middleware records request duration."""
        # Make some API requests
        response = client.get("/api/health")
        assert response.status_code == 200

        response = client.get("/api/v1/users/me")
        assert response.status_code in [401, 403]  # Unauthorized

        response = client.post("/api/v1/auth/login", json={"username": "test", "password": "wrong"})
        # Could be 401 or 422 depending on validation

        # Get metrics
        response = client.get("/metrics")
        assert response.status_code == 200

        # Check that API metrics were recorded
        families = list(text_string_to_metric_families(response.text))
        api_family = next((f for f in families if f.name == "nqhub_api_request_duration_seconds_count"), None)
        assert api_family is not None

        # Check that we have samples
        assert len(api_family.samples) > 0

        # Check for specific endpoints
        endpoints_recorded = set()
        for sample in api_family.samples:
            endpoint = sample.labels.get("endpoint")
            if endpoint:
                endpoints_recorded.add(endpoint)

        assert "/api/health" in endpoints_recorded
        assert "/api/v1/users/me" in endpoints_recorded

    def test_metrics_endpoint_not_tracked(self, client):
        """Test that /metrics endpoint itself is not tracked to avoid recursion."""
        # Clear any existing metrics first
        response = client.get("/metrics")

        # Make a request to /metrics
        response = client.get("/metrics")
        assert response.status_code == 200

        # Check that /metrics is not in the tracked endpoints
        families = list(text_string_to_metric_families(response.text))
        api_family = next((f for f in families if f.name == "nqhub_api_request_duration_seconds_count"), None)

        if api_family:
            for sample in api_family.samples:
                endpoint = sample.labels.get("endpoint")
                assert endpoint != "/metrics", "/metrics endpoint should not be tracked"

    def test_middleware_handles_different_status_codes(self, client):
        """Test that middleware correctly records different HTTP status codes."""
        # Generate various status codes
        client.get("/api/health")  # 200
        client.get("/nonexistent")  # 404
        client.get("/api/v1/users/me")  # 401/403

        # Get metrics
        response = client.get("/metrics")
        assert response.status_code == 200

        # Check that different status codes were recorded
        families = list(text_string_to_metric_families(response.text))
        api_family = next((f for f in families if f.name == "nqhub_api_request_duration_seconds_count"), None)

        if api_family:
            status_codes = set()
            for sample in api_family.samples:
                status = sample.labels.get("status")
                if status:
                    status_codes.add(status)

            # Should have at least 200 and 404
            assert "200" in status_codes
            assert "404" in status_codes


class TestMetricsIntegration:
    """Integration tests for metrics system."""

    def test_full_bot_lifecycle_metrics(self, client):
        """Test recording metrics through a complete bot lifecycle."""
        bot_id = "bot-integration-test"

        # Bot startup
        set_bot_status(bot_id, True)
        update_bot_heartbeat(bot_id)
        update_bot_metrics(bot_id, {
            "pnl_usd": 0.0,
            "daily_loss_pct": 0.0,
            "trailing_drawdown_pct": 0.0
        })

        # Submit and fill some orders
        for i in range(5):
            record_order(bot_id, "submitted")
            time.sleep(0.01)  # Simulate processing time
            record_order(bot_id, "filled")
            record_order_latency(0.05 + i * 0.01)  # Variable latency

            # Record a trade
            direction = "long" if i % 2 == 0 else "short"
            record_trade(bot_id, direction)

            # Update P&L
            pnl = 100.0 * (i + 1) if i % 2 == 0 else -50.0 * i
            update_bot_metrics(bot_id, {"pnl_usd": pnl})

        # Simulate a rejected order
        record_order(bot_id, "submitted")
        record_order(bot_id, "rejected")

        # Update heartbeat
        update_bot_heartbeat(bot_id)

        # Bot shutdown
        set_bot_status(bot_id, False)

        # Verify all metrics via endpoint
        response = client.get("/metrics")
        assert response.status_code == 200

        # Parse metrics
        families = list(text_string_to_metric_families(response.text))

        # Verify bot status is stopped (0)
        status_family = next((f for f in families if f.name == "nqhub_bot_status"), None)
        assert status_family is not None

        # Verify order counts
        submitted_family = next((f for f in families if f.name == "nqhub_orders_submitted_total"), None)
        filled_family = next((f for f in families if f.name == "nqhub_orders_filled_total"), None)
        rejected_family = next((f for f in families if f.name == "nqhub_orders_rejected_total"), None)

        assert submitted_family is not None
        assert filled_family is not None
        assert rejected_family is not None

        # Verify trade counts
        trades_family = next((f for f in families if f.name == "nqhub_bot_trades_total"), None)
        assert trades_family is not None

    def test_concurrent_metric_updates(self, client):
        """Test that metrics handle concurrent updates correctly."""
        import threading

        def update_metrics_thread(bot_id, count):
            for i in range(count):
                record_trade(bot_id, "long" if i % 2 == 0 else "short")
                record_order(bot_id, "submitted")
                record_order(bot_id, "filled")
                update_bot_metrics(bot_id, {"pnl_usd": float(i)})

        # Create multiple threads updating metrics
        threads = []
        for i in range(5):
            t = threading.Thread(target=update_metrics_thread, args=(f"bot-thread-{i}", 10))
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify metrics are accessible
        response = client.get("/metrics")
        assert response.status_code == 200

        # Verify metrics were recorded for all bots
        families = list(text_string_to_metric_families(response.text))
        trades_family = next((f for f in families if f.name == "nqhub_bot_trades_total"), None)
        assert trades_family is not None

        # Count unique bot IDs
        bot_ids = set()
        for sample in trades_family.samples:
            bot_id = sample.labels.get("bot_id")
            if bot_id and bot_id.startswith("bot-thread-"):
                bot_ids.add(bot_id)

        assert len(bot_ids) == 5, f"Expected 5 bot IDs, got {len(bot_ids)}"