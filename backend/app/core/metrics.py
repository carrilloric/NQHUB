"""
Prometheus Metrics for NQ-HUB Monitoring
AUT-360: Monitoring stack with Prometheus, Grafana, and Loki
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse
import time
from typing import Dict, Any

# Create router for metrics endpoint
router = APIRouter()

# ==================== Bot Metrics ====================
bot_pnl_usd = Gauge(
    'nqhub_bot_pnl_usd',
    'P&L in USD for each bot',
    ['bot_id']
)

bot_daily_loss_pct = Gauge(
    'nqhub_bot_daily_loss_pct',
    'Daily loss percentage of limit',
    ['bot_id']
)

bot_trailing_drawdown_pct = Gauge(
    'nqhub_bot_trailing_drawdown_pct',
    'Trailing drawdown percentage',
    ['bot_id']
)

bot_heartbeat_age_seconds = Gauge(
    'nqhub_bot_heartbeat_age_seconds',
    'Seconds since last heartbeat',
    ['bot_id']
)

bot_status = Gauge(
    'nqhub_bot_status',
    'Bot status: 1=running, 0=stopped',
    ['bot_id']
)

bot_trades_total = Counter(
    'nqhub_bot_trades_total',
    'Total trades executed',
    ['bot_id', 'direction']
)

# ==================== Order Metrics ====================
orders_submitted_total = Counter(
    'nqhub_orders_submitted_total',
    'Total orders submitted',
    ['bot_id']
)

orders_filled_total = Counter(
    'nqhub_orders_filled_total',
    'Total orders filled/executed',
    ['bot_id']
)

orders_rejected_total = Counter(
    'nqhub_orders_rejected_total',
    'Total orders rejected',
    ['bot_id']
)

order_latency_seconds = Histogram(
    'nqhub_order_latency_seconds',
    'Latency from order submit to fill in seconds',
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# ==================== System Metrics ====================
api_request_duration = Histogram(
    'nqhub_api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint', 'status'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

websocket_connections = Gauge(
    'nqhub_websocket_connections_active',
    'Number of active WebSocket connections'
)

redis_pub_events = Counter(
    'nqhub_redis_pub_events_total',
    'Total Redis pub/sub events',
    ['channel']
)

# ==================== Application-specific Metrics ====================
pattern_detection_total = Counter(
    'nqhub_pattern_detection_total',
    'Total patterns detected',
    ['pattern_type']  # fvg, ob, lp
)

backtest_runs_total = Counter(
    'nqhub_backtest_runs_total',
    'Total backtest runs completed',
    ['strategy_type']  # rule_based, ml, rl, hybrid
)

etl_jobs_total = Counter(
    'nqhub_etl_jobs_total',
    'Total ETL jobs processed',
    ['status']  # completed, failed, pending
)

database_query_duration = Histogram(
    'nqhub_database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)

# ==================== Metrics Endpoint ====================
@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """
    Expose Prometheus metrics in the standard format.
    This endpoint is scraped by Prometheus at regular intervals.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# ==================== Helper Functions ====================
def update_bot_metrics(bot_id: str, metrics: Dict[str, Any]):
    """Update bot-related metrics from bot state"""
    if 'pnl_usd' in metrics:
        bot_pnl_usd.labels(bot_id=bot_id).set(metrics['pnl_usd'])

    if 'daily_loss_pct' in metrics:
        bot_daily_loss_pct.labels(bot_id=bot_id).set(metrics['daily_loss_pct'])

    if 'trailing_drawdown_pct' in metrics:
        bot_trailing_drawdown_pct.labels(bot_id=bot_id).set(metrics['trailing_drawdown_pct'])

    if 'last_heartbeat' in metrics:
        age = time.time() - metrics['last_heartbeat']
        bot_heartbeat_age_seconds.labels(bot_id=bot_id).set(age)

    if 'status' in metrics:
        status_value = 1 if metrics['status'] == 'running' else 0
        bot_status.labels(bot_id=bot_id).set(status_value)

def record_trade(bot_id: str, direction: str):
    """Record a trade execution"""
    bot_trades_total.labels(bot_id=bot_id, direction=direction).inc()

def record_order(bot_id: str, order_type: str):
    """Record order submission/fill/rejection"""
    if order_type == 'submitted':
        orders_submitted_total.labels(bot_id=bot_id).inc()
    elif order_type == 'filled':
        orders_filled_total.labels(bot_id=bot_id).inc()
    elif order_type == 'rejected':
        orders_rejected_total.labels(bot_id=bot_id).inc()

def record_order_latency(latency_seconds: float):
    """Record order execution latency"""
    order_latency_seconds.observe(latency_seconds)

def record_api_request(method: str, endpoint: str, status: int, duration: float):
    """Record API request metrics"""
    api_request_duration.labels(
        method=method,
        endpoint=endpoint,
        status=str(status)
    ).observe(duration)

def update_websocket_connections(count: int):
    """Update active WebSocket connections count"""
    websocket_connections.set(count)

def record_redis_event(channel: str):
    """Record Redis pub/sub event"""
    redis_pub_events.labels(channel=channel).inc()

def record_pattern_detection(pattern_type: str):
    """Record pattern detection event"""
    pattern_detection_total.labels(pattern_type=pattern_type).inc()

def record_backtest_run(strategy_type: str):
    """Record backtest run completion"""
    backtest_runs_total.labels(strategy_type=strategy_type).inc()

def record_etl_job(status: str):
    """Record ETL job completion"""
    etl_jobs_total.labels(status=status).inc()

def record_database_query(query_type: str, duration: float):
    """Record database query duration"""
    database_query_duration.labels(query_type=query_type).observe(duration)


def update_bot_heartbeat(bot_id: str):
    """Update bot heartbeat timestamp."""
    # In a real implementation, this would track the timestamp
    # For now, we'll set it to 0 to indicate recent heartbeat
    bot_heartbeat_age_seconds.labels(bot_id=bot_id).set(0)


def set_bot_status(bot_id: str, is_running: bool):
    """Set bot status (1 for running, 0 for stopped)."""
    bot_status.labels(bot_id=bot_id).set(1 if is_running else 0)