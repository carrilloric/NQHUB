"""
TradingNode builder for NautilusTrader.
One TradingNode per bot instance - never shared between bots.
"""
from nautilus_trader.live.node import TradingNode
from nautilus_trader.config import (
    TradingNodeConfig,
    LiveDataEngineConfig,
    LiveExecEngineConfig,
    LiveRiskEngineConfig,
    MessageBusConfig,
    DatabaseConfig
)
from nautilus_trader.model.identifiers import TraderId
from app.config import settings


def build_trading_node(bot_id: str, redis_url: str) -> TradingNode:
    """
    Build a TradingNode for a specific bot instance.

    Args:
        bot_id: Unique bot identifier
        redis_url: Redis connection URL for MessageBus backing

    Returns:
        Configured TradingNode instance

    Notes:
        - One TradingNode per bot - never share between bots
        - Redis backing for MessageBus for event distribution
        - Debug disabled for production engines
        - Risk engine bypass set to False for safety
    """
    # Create node configuration
    node_config = TradingNodeConfig(
        trader_id=TraderId(f"NQHUB-{bot_id}"),
        data_engine=LiveDataEngineConfig(
            debug=False  # Disable debug in production
        ),
        exec_engine=LiveExecEngineConfig(
            debug=False  # Disable debug in production
        ),
        risk_engine=LiveRiskEngineConfig(
            bypass=False  # Never bypass risk checks
        ),
        message_bus=MessageBusConfig(
            database=DatabaseConfig(
                type="redis",
                host="localhost",  # Extract from redis_url in production
                port=6379  # Extract from redis_url in production
            )
        ),
    )

    # Build and return the node
    return TradingNode(config=node_config)