"""
Tests for Bot Runner component.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from app.trading.bot_runner import load_bot_config, register_data_client, register_exec_client


class TestBotRunner:
    """Test suite for bot runner functions."""

    @pytest.mark.asyncio
    async def test_load_bot_config(self):
        """Test loading bot configuration."""
        config = await load_bot_config("test-bot-1")

        assert config["bot_id"] == "test-bot-1"
        assert config["enabled"] is True
        assert "strategy_id" in config
        assert "risk_config" in config
        assert "data_config" in config

    @pytest.mark.asyncio
    async def test_load_bot_config_structure(self):
        """Test bot configuration structure."""
        config = await load_bot_config("test-bot-2")

        # Check risk config
        assert "max_position_size" in config["risk_config"]
        assert "max_daily_loss" in config["risk_config"]
        assert "max_drawdown" in config["risk_config"]

        # Check data config
        assert "symbols" in config["data_config"]
        assert "timeframes" in config["data_config"]
        assert isinstance(config["data_config"]["symbols"], list)
        assert isinstance(config["data_config"]["timeframes"], list)

    def test_register_data_client(self):
        """Test registering data client."""
        mock_node = Mock()
        # Should not raise exception
        register_data_client(mock_node)

    def test_register_exec_client(self):
        """Test registering execution client."""
        mock_node = Mock()
        # Should not raise exception
        register_exec_client(mock_node)

    @pytest.mark.asyncio
    async def test_run_bot_disabled(self):
        """Test that disabled bot raises error."""
        with patch("app.trading.bot_runner.load_bot_config") as mock_load:
            mock_load.return_value = {"enabled": False}

            with pytest.raises(RuntimeError, match="not enabled"):
                from app.trading.bot_runner import run_bot
                await run_bot("disabled-bot")