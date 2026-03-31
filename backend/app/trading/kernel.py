"""
<<<<<<< HEAD
TradingNode builder for NautilusTrader.
One TradingNode per bot instance - never shared between bots.
"""
from nautilus_trader.live.node import TradingNode
from nautilus_trader.config import (
    TradingNodeConfig,
    LiveDataEngineConfig,
    LiveExecEngineConfig,
<<<<<<< HEAD
    LiveRiskEngineConfig,
=======
    RiskEngineConfig,
>>>>>>> 1ee3282 (feat(AUT-336): Implement VectorBT Pro backtesting engine with Celery workers)
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
=======
Trading Kernel (Placeholder for AUT-344)

NautilusTrader kernel setup with Rithmic adapter registration.
This file will be completed when AUT-344 (NautilusTrader core) is implemented.

References:
- AUT-344: NautilusTrader core setup
- AUT-345: Rithmic live adapter (this implementation)
"""
from typing import Optional

# Placeholder imports - will be available when AUT-344 is complete
try:
    from nautilus_trader.live.node import TradingNode
    from nautilus_trader.config import TradingNodeConfig
except ImportError:
    TradingNode = None
    TradingNodeConfig = None

from app.trading.adapters.rithmic_data_client import (
    RithmicDataClient,
    RithmicDataClientConfig,
)


class RithmicDataClientFactory:
    """
    Factory for creating RithmicDataClient instances.

    This will be registered with the NautilusTrader node when AUT-344 is complete.
    """

    @staticmethod
    def create(config: RithmicDataClientConfig) -> RithmicDataClient:
        """Create a new RithmicDataClient instance"""
        return RithmicDataClient(config=config)


def setup_trading_node(config: Optional[TradingNodeConfig] = None) -> "TradingNode":
    """
    Setup NautilusTrader trading node with Rithmic adapter.

    This function will be implemented when AUT-344 is complete.

    Args:
        config: Trading node configuration
>>>>>>> a1d42cd (feat(trading): AUT-345 Rithmic live adapter with async_rithmic)

    Returns:
        Configured TradingNode instance

<<<<<<< HEAD
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
<<<<<<< HEAD
        risk_engine=LiveRiskEngineConfig(
=======
        risk_engine=RiskEngineConfig(
>>>>>>> 1ee3282 (feat(AUT-336): Implement VectorBT Pro backtesting engine with Celery workers)
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
=======
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
    node.add_data_client_factory("RITHMIC", RithmicDataClientFactory)

    return node
>>>>>>> a1d42cd (feat(trading): AUT-345 Rithmic live adapter with async_rithmic)
