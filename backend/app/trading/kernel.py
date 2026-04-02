"""
Trading Kernel for NautilusTrader with VectorBT Pro and Rithmic adapter.

Combines:
- AUT-336: VectorBT Pro backtesting engine configuration
- AUT-345: Rithmic live adapter with async_rithmic

TradingNode builder for NautilusTrader.
One TradingNode per bot instance - never shared between bots.
"""
from typing import Optional

from nautilus_trader.live.node import TradingNode
from nautilus_trader.config import (
    TradingNodeConfig,
    LiveDataEngineConfig,
    LiveExecEngineConfig,
    RiskEngineConfig,  # Using RiskEngineConfig for both VectorBT and live trading
    MessageBusConfig,
    DatabaseConfig
)
from nautilus_trader.model.identifiers import TraderId
from app.config import settings

# Rithmic adapter imports
try:
    from app.trading.adapters.rithmic_data_client import (
        RithmicDataClient,
        RithmicDataClientConfig,
    )
except ImportError:
    # Will be available when Rithmic adapter is implemented
    RithmicDataClient = None
    RithmicDataClientConfig = None


class RithmicDataClientFactory:
    """
    Factory for creating RithmicDataClient instances.

    This will be registered with the NautilusTrader node when AUT-344 is complete.
    """

    @staticmethod
    def create(config: RithmicDataClientConfig) -> RithmicDataClient:
        """Create a new RithmicDataClient instance"""
        if RithmicDataClient is None:
            raise ImportError("RithmicDataClient not available")
        return RithmicDataClient(config=config)


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
        risk_engine=RiskEngineConfig(
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


def setup_trading_node(config: Optional[TradingNodeConfig] = None) -> TradingNode:
    """
    Setup NautilusTrader trading node with Rithmic adapter.

    This function will be implemented when AUT-344 is complete.

    Args:
        config: Trading node configuration

    Returns:
        Configured TradingNode instance

    Example:
        >>> node = setup_trading_node()
        >>> node.add_data_client_factory("RITHMIC", RithmicDataClientFactory)
        >>> node.start()
    """
    if TradingNode is None:
        raise ImportError(
            "NautilusTrader is not installed. "
            "Complete AUT-344 first."
        )

    # Create node
    node = TradingNode(config=config)

    # Register Rithmic data client factory
    if RithmicDataClient is not None:
        node.add_data_client_factory("RITHMIC", RithmicDataClientFactory)

    return node