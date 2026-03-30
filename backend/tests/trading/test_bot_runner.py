"""
Tests for bot_runner module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from datetime import datetime


class TestBotRunner:
    """Tests for bot_runner module."""

    @pytest.mark.asyncio
    async def test_bot_runner_loads_config_from_db(self):
        """Test bot_runner loads bot configuration from PostgreSQL."""
        from app.trading.bot_runner import run_bot

        bot_id = "test-bot-001"

        # Mock database session
        mock_db = AsyncMock()
        mock_bot_config = {
            "id": bot_id,
            "name": "Test Bot",
            "strategy_id": "strategy-001",
            "strategy_type": "rule_based",
            "risk_config": {
                "max_position_size": 5,
                "max_daily_loss": 1000,
                "trailing_drawdown_pct": 0.8
            },
            "enabled": True
        }

        # Mock the database query
        mock_db.query = MagicMock(return_value=MagicMock(
            filter_by=MagicMock(return_value=MagicMock(
                first=MagicMock(return_value=mock_bot_config)
            ))
        ))

        with patch("app.trading.bot_runner.get_async_db", return_value=mock_db), \
             patch("app.trading.bot_runner.build_trading_node") as mock_build_node, \
             patch("app.trading.bot_runner.TradingNode") as mock_node_class:

            mock_node = AsyncMock()
            mock_build_node.return_value = mock_node
            mock_node.run = AsyncMock()

            # Run bot (will load config)
            task = asyncio.create_task(run_bot(bot_id))
            await asyncio.sleep(0.1)  # Let it start

            # Cancel the task
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            # Verify config was loaded from DB
            mock_db.query.assert_called()
            mock_build_node.assert_called_once()

    @pytest.mark.asyncio
    async def test_bot_runner_constructs_trading_node(self):
        """Test bot_runner constructs TradingNode correctly."""
        from app.trading.bot_runner import run_bot

        bot_id = "test-bot-002"
        mock_config = {
            "id": bot_id,
            "strategy_id": "strategy-002",
            "enabled": True
        }

        with patch("app.trading.bot_runner.load_bot_config", return_value=mock_config), \
             patch("app.trading.bot_runner.build_trading_node") as mock_build_node, \
             patch("app.trading.bot_runner.register_data_client") as mock_register_data, \
             patch("app.trading.bot_runner.register_exec_client") as mock_register_exec, \
             patch("app.trading.bot_runner.WsBridgeActor") as mock_ws_actor, \
             patch("app.trading.bot_runner.DbWriterActor") as mock_db_actor:

            mock_node = AsyncMock()
            mock_build_node.return_value = mock_node
            mock_node.run = AsyncMock()

            # Run bot
            task = asyncio.create_task(run_bot(bot_id))
            await asyncio.sleep(0.1)

            # Cancel the task
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            # Verify TradingNode was built
            mock_build_node.assert_called_once_with(bot_id, "redis://localhost:6379/0")

            # Verify clients were registered
            mock_register_data.assert_called_once()
            mock_register_exec.assert_called_once()

            # Verify actors were created
            mock_ws_actor.assert_called_once()
            mock_db_actor.assert_called_once()

    @pytest.mark.asyncio
    async def test_bot_runner_registers_actors(self):
        """Test bot_runner registers WsBridgeActor and DbWriterActor."""
        from app.trading.bot_runner import run_bot

        bot_id = "test-bot-003"

        with patch("app.trading.bot_runner.load_bot_config"), \
             patch("app.trading.bot_runner.build_trading_node") as mock_build_node:

            mock_node = AsyncMock()
            mock_node.run = AsyncMock()
            mock_node.kernel = MagicMock()
            mock_node.kernel.add_actor = MagicMock()

            mock_build_node.return_value = mock_node

            # Mock actors
            with patch("app.trading.bot_runner.WsBridgeActor") as mock_ws_actor_class, \
                 patch("app.trading.bot_runner.DbWriterActor") as mock_db_actor_class:

                mock_ws_actor = MagicMock()
                mock_db_actor = MagicMock()
                mock_ws_actor_class.return_value = mock_ws_actor
                mock_db_actor_class.return_value = mock_db_actor

                # Run bot
                task = asyncio.create_task(run_bot(bot_id))
                await asyncio.sleep(0.1)

                # Cancel the task
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

                # Verify actors were added to the node
                assert mock_node.kernel.add_actor.call_count >= 2
                calls = mock_node.kernel.add_actor.call_args_list
                actors_added = [call[0][0] for call in calls]

                assert mock_ws_actor in actors_added
                assert mock_db_actor in actors_added

    @pytest.mark.asyncio
    async def test_bot_runner_handles_kill_signal(self):
        """Test bot_runner handles kill signal gracefully."""
        from app.trading.bot_runner import run_bot
        import signal

        bot_id = "test-bot-004"

        with patch("app.trading.bot_runner.load_bot_config"), \
             patch("app.trading.bot_runner.build_trading_node") as mock_build_node:

            mock_node = AsyncMock()
            mock_node.run = AsyncMock()
            mock_node.stop = AsyncMock()
            mock_node.dispose = AsyncMock()

            mock_build_node.return_value = mock_node

            # Run bot
            task = asyncio.create_task(run_bot(bot_id))
            await asyncio.sleep(0.1)

            # Send kill signal
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            # Verify node was stopped properly
            mock_node.stop.assert_called_once()
            mock_node.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_bot_runner_error_handling(self):
        """Test bot_runner handles errors gracefully."""
        from app.trading.bot_runner import run_bot

        bot_id = "test-bot-005"

        # Test missing bot config
        with patch("app.trading.bot_runner.load_bot_config", side_effect=ValueError("Bot not found")):
            with pytest.raises(ValueError, match="Bot not found"):
                await run_bot(bot_id)

        # Test disabled bot
        mock_config = {"id": bot_id, "enabled": False}
        with patch("app.trading.bot_runner.load_bot_config", return_value=mock_config):
            with pytest.raises(RuntimeError, match="Bot .* is not enabled"):
                await run_bot(bot_id)