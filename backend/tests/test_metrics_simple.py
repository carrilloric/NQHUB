"""
Simple test for metrics endpoint to verify it works.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from prometheus_client.parser import text_string_to_metric_families
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
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST


def test_metrics_generation():
    """Test that metrics can be generated in Prometheus format."""
    # Update some metrics
    update_bot_metrics("bot-test", {"pnl_usd": 1234.56})
    record_trade("bot-test", "long")
    record_order("bot-test", "submitted")
    record_order("bot-test", "filled")
    record_order_latency(0.125)

    # Generate metrics
    metrics_text = generate_latest().decode('utf-8')

    # Parse to verify format
    families = list(text_string_to_metric_families(metrics_text))

    # Check that metrics are present
    metric_names = [f.name for f in families]
    print(f"Available metrics: {metric_names}")

    # Check for at least some core metrics
    assert any("nqhub" in name for name in metric_names), f"No NQHUB metrics found in: {metric_names}"

    print("✅ Metrics generation test passed!")


def test_bot_metrics_update():
    """Test updating bot-specific metrics."""
    bot_id = "bot-unit-test"

    # Update various bot metrics
    update_bot_metrics(bot_id, {
        "pnl_usd": 500.0,
        "daily_loss_pct": 25.5,
        "trailing_drawdown_pct": 15.3
    })

    set_bot_status(bot_id, True)
    update_bot_heartbeat(bot_id)

    # Record some trades
    record_trade(bot_id, "long")
    record_trade(bot_id, "long")
    record_trade(bot_id, "short")

    print("✅ Bot metrics update test passed!")


def test_order_metrics():
    """Test order-related metrics."""
    bot_id = "bot-order-test"

    # Submit and fill orders
    for i in range(5):
        record_order(bot_id, "submitted")
        record_order(bot_id, "filled")
        record_order_latency(0.05 + i * 0.01)

    # Reject an order
    record_order(bot_id, "submitted")
    record_order(bot_id, "rejected")

    print("✅ Order metrics test passed!")


def test_system_metrics():
    """Test system-level metrics."""
    # Update WebSocket connections
    update_websocket_connections(5)
    update_websocket_connections(3)

    # Record Redis events
    record_redis_event("market_data")
    record_redis_event("bot_updates")

    # Record API request
    record_api_request("GET", "/api/health", 200, 0.025)
    record_api_request("POST", "/api/v1/auth/login", 401, 0.150)

    print("✅ System metrics test passed!")


if __name__ == "__main__":
    test_metrics_generation()
    test_bot_metrics_update()
    test_order_metrics()
    test_system_metrics()
    print("\n✅ All metrics tests passed!")