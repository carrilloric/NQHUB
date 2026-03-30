"""
Tests for NautilusTrader kernel and TradingNode builder.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio
from nautilus_trader.live.node import TradingNode
from nautilus_trader.config import (
    TradingNodeConfig,
    LiveDataEngineConfig,
    LiveExecEngineConfig,
    RiskEngineConfig,
    MessageBusConfig,
    DatabaseConfig
)


class TestTradingNodeBuilder:
    """Tests for TradingNode builder function."""

    def test_trading_node_builds_correctly(self):
        """Test that TradingNode builds correctly with proper config."""
        from app.trading.kernel import build_trading_node

        bot_id = "test-bot-001"
        redis_url = "redis://localhost:6379/0"

        # Build the node
        node = build_trading_node(bot_id, redis_url)

        # Assertions
        assert isinstance(node, TradingNode)
        assert node.trader_id.value == f"NQHUB-{bot_id}"

        # Verify config components
        assert node.kernel.data_engine is not None
        assert node.kernel.exec_engine is not None
        assert node.kernel.risk_engine is not None
        assert node.kernel.msgbus is not None

        # Verify risk engine is not bypassed
        assert node.kernel.risk_engine.config.bypass is False

    def test_trading_node_uses_redis_for_message_bus(self):
        """Test that TradingNode uses Redis for MessageBus backing."""
        from app.trading.kernel import build_trading_node

        bot_id = "test-bot-002"
        redis_url = "redis://localhost:6379/0"

        with patch("app.trading.kernel.settings.REDIS_HOST", "localhost"), \
             patch("app.trading.kernel.settings.REDIS_PORT", 6379):

            node = build_trading_node(bot_id, redis_url)

            # Check that MessageBus is configured with Redis
            assert node.kernel.msgbus.database.type == "redis"

    def test_trading_node_unique_per_bot(self):
        """Test that each bot gets a unique TradingNode instance."""
        from app.trading.kernel import build_trading_node

        bot_id_1 = "test-bot-003"
        bot_id_2 = "test-bot-004"
        redis_url = "redis://localhost:6379/0"

        # Build two nodes
        node1 = build_trading_node(bot_id_1, redis_url)
        node2 = build_trading_node(bot_id_2, redis_url)

        # Verify they have different trader IDs
        assert node1.trader_id.value != node2.trader_id.value
        assert node1.trader_id.value == f"NQHUB-{bot_id_1}"
        assert node2.trader_id.value == f"NQHUB-{bot_id_2}"

        # Verify they are different instances
        assert node1 is not node2

    def test_trading_node_debug_disabled_in_production(self):
        """Test that debug mode is disabled for production engines."""
        from app.trading.kernel import build_trading_node

        bot_id = "test-bot-005"
        redis_url = "redis://localhost:6379/0"

        node = build_trading_node(bot_id, redis_url)

        # Verify debug is disabled
        assert node.kernel.data_engine.config.debug is False
        assert node.kernel.exec_engine.config.debug is False