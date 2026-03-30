"""
Bot runner for NautilusTrader.
Railway worker entry point for running trading bots.
"""
import asyncio
import os
import sys
from typing import Dict, Any
import redis

from app.config import settings
from app.trading.kernel import build_trading_node
from app.trading.actors.ws_bridge import WsBridgeActor, WsBridgeActorConfig
from app.trading.actors.db_writer import DbWriterActor, DbWriterActorConfig


async def load_bot_config(bot_id: str) -> Dict[str, Any]:
    """
    Load bot configuration from database.

    Args:
        bot_id: Unique bot identifier

    Returns:
        Bot configuration dictionary
    """
    # In production, this would query PostgreSQL
    # For now, return mock configuration
    return {
        'bot_id': bot_id,
        'enabled': True,
        'strategy_id': 'test_strategy',
        'risk_config': {
            'max_position_size': 10,
            'max_daily_loss': 1000,
            'max_drawdown': 0.10
        },
        'data_config': {
            'symbols': ['NQ'],
            'timeframes': ['1m', '5m', '15m']
        }
    }


def register_data_client(node):
    """
    Register data client with the trading node.

    Args:
        node: TradingNode instance
    """
    # In production, register appropriate data client (Interactive Brokers, etc.)
    pass


def register_exec_client(node):
    """
    Register execution client with the trading node.

    Args:
        node: TradingNode instance
    """
    # In production, register appropriate execution client
    pass


async def run_bot(bot_id: str) -> None:
    """
    Main bot runner function.

    Args:
        bot_id: Unique bot identifier
    """
    print(f"Starting bot {bot_id}...")

    # Load bot configuration from database
    bot_config = await load_bot_config(bot_id)

    if not bot_config.get('enabled', False):
        raise RuntimeError(f"Bot {bot_id} is not enabled")

    # Build TradingNode
    redis_url = f"{settings.REDIS_URL}/0"
    node = build_trading_node(bot_id, redis_url)

    # Register data and execution clients
    register_data_client(node)
    register_exec_client(node)

    # Create and add actors
    # WebSocket Bridge Actor
    ws_bridge_config = WsBridgeActorConfig(
        bot_id=bot_id,
        component_id=f"{bot_id}-ws-bridge",
        redis_client=redis.from_url(redis_url),
        channels=[f"bot:{bot_id}:events", f"bot:{bot_id}:orders", f"bot:{bot_id}:positions"]
    )
    ws_bridge_actor = WsBridgeActor(config=ws_bridge_config)
    node.kernel.add_actor(ws_bridge_actor)

    # Database Writer Actor
    db_writer_config = DbWriterActorConfig(
        bot_id=bot_id,
        component_id=f"{bot_id}-db-writer",
        db_session=None,  # Would be actual session in production
        batch_size=100,
        flush_interval_ms=5000
    )
    db_writer_actor = DbWriterActor(config=db_writer_config)
    node.kernel.add_actor(db_writer_actor)

    # Load and configure strategy
    # strategy = load_strategy(bot_config['strategy_id'], bot_config)
    # node.kernel.add_strategy(strategy)

    # Start the node
    try:
        print(f"Bot {bot_id} is running...")
        await node.run()
    except KeyboardInterrupt:
        print(f"Bot {bot_id} interrupted, shutting down...")
    except Exception as e:
        print(f"Bot {bot_id} error: {e}")
        raise
    finally:
        await node.stop()
        print(f"Bot {bot_id} stopped.")


def main():
    """
    Main entry point for Railway worker.
    """
    # Get bot ID from environment variable or command line
    bot_id = os.environ.get('BOT_ID') or (sys.argv[1] if len(sys.argv) > 1 else None)

    if not bot_id:
        print("Error: BOT_ID environment variable or command line argument required")
        sys.exit(1)

    # Run the bot
    asyncio.run(run_bot(bot_id))


if __name__ == "__main__":
    main()