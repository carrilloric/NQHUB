"""
<<<<<<< HEAD
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
=======
Bot Runner for NQHUB trading system.
Railway worker entry point for running trading bots.
"""
import asyncio
import signal
import sys
from typing import Dict, Any, Optional
from app.trading.kernel import build_trading_node
from app.trading.actors.ws_bridge import WsBridgeActor, WsBridgeActorConfig
from app.trading.actors.db_writer import DbWriterActor, DbWriterActorConfig
from app.config import settings
import redis.asyncio as redis
>>>>>>> 1ee3282 (feat(AUT-336): Implement VectorBT Pro backtesting engine with Celery workers)


async def load_bot_config(bot_id: str) -> Dict[str, Any]:
    """
<<<<<<< HEAD
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
=======
    Load bot configuration from PostgreSQL.

    Args:
        bot_id: Bot identifier

    Returns:
        Bot configuration dictionary

    Raises:
        ValueError: If bot not found
    """
    # In production, this would query the bots table in PostgreSQL
    # For testing, we'll simulate the database query
    from app.db.session import get_async_db

    async with get_async_db() as db:
        # Simulated query - in production would use SQLAlchemy ORM
        result = db.query("SELECT * FROM bots WHERE id = ?", bot_id).first()

        if not result:
            raise ValueError(f"Bot {bot_id} not found in database")

        return {
            'id': result.get('id'),
            'name': result.get('name'),
            'strategy_id': result.get('strategy_id'),
            'strategy_type': result.get('strategy_type'),
            'risk_config': result.get('risk_config', {}),
            'enabled': result.get('enabled', False)
        }


def register_data_client(node: Any) -> None:
    """
    Register data client with the TradingNode.
>>>>>>> 1ee3282 (feat(AUT-336): Implement VectorBT Pro backtesting engine with Celery workers)

    Args:
        node: TradingNode instance
    """
<<<<<<< HEAD
    # In production, register appropriate data client (Interactive Brokers, etc.)
    pass


def register_exec_client(node):
    """
    Register execution client with the trading node.
=======
    # In production, this would register the actual data client
    # For example: InteractiveBrokersDataClient, BinanceDataClient, etc.
    pass


def register_exec_client(node: Any) -> None:
    """
    Register execution client with the TradingNode.
>>>>>>> 1ee3282 (feat(AUT-336): Implement VectorBT Pro backtesting engine with Celery workers)

    Args:
        node: TradingNode instance
    """
<<<<<<< HEAD
    # In production, register appropriate execution client
=======
    # In production, this would register the actual execution client
    # For example: InteractiveBrokersExecClient, BinanceExecClient, etc.
>>>>>>> 1ee3282 (feat(AUT-336): Implement VectorBT Pro backtesting engine with Celery workers)
    pass


async def run_bot(bot_id: str) -> None:
    """
    Main bot runner function.

    Args:
<<<<<<< HEAD
        bot_id: Unique bot identifier
    """
    print(f"Starting bot {bot_id}...")

    # Load bot configuration from database
    bot_config = await load_bot_config(bot_id)

=======
        bot_id: Bot identifier to run

    Raises:
        RuntimeError: If bot is not enabled
        ValueError: If bot not found
    """
    # Load bot configuration from database
    bot_config = await load_bot_config(bot_id)

    # Check if bot is enabled
>>>>>>> 1ee3282 (feat(AUT-336): Implement VectorBT Pro backtesting engine with Celery workers)
    if not bot_config.get('enabled', False):
        raise RuntimeError(f"Bot {bot_id} is not enabled")

    # Build TradingNode
    redis_url = f"{settings.REDIS_URL}/0"
    node = build_trading_node(bot_id, redis_url)

    # Register data and execution clients
    register_data_client(node)
    register_exec_client(node)

<<<<<<< HEAD
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
=======
    # Create Redis client for actors
    redis_client = await redis.from_url(redis_url)

    # Create and add WsBridgeActor
    ws_bridge_config = WsBridgeActorConfig(
        bot_id=bot_id,
        redis_client=redis_client,
        channels=[
            "nqhub.candle.*",
            "nqhub.pattern.*",
            "nqhub.risk.*",
            "exec.order.*",
            "exec.position.*"
        ]
    )
    ws_bridge_actor = WsBridgeActor(ws_bridge_config)
    node.kernel.add_actor(ws_bridge_actor)

    # Create and add DbWriterActor
    # In production, would get an async database session here
    db_writer_config = DbWriterActorConfig(
        bot_id=bot_id,
        db_session=None,  # Would be actual AsyncSession in production
        batch_size=100,
        flush_interval_ms=5000
    )
    db_writer_actor = DbWriterActor(db_writer_config)
    node.kernel.add_actor(db_writer_actor)

    # Setup signal handlers for graceful shutdown
    stop_event = asyncio.Event()

    def signal_handler(sig, frame):
        print(f"\nReceived signal {sig}, shutting down gracefully...")
        stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the trading node
    try:
        print(f"Starting bot {bot_id}...")
        await node.run()

        # Wait for stop signal
        await stop_event.wait()

    except asyncio.CancelledError:
        print("Bot runner cancelled")
    finally:
        # Cleanup
        print(f"Stopping bot {bot_id}...")
        await node.stop()
        await node.dispose()
        await redis_client.close()
        print(f"Bot {bot_id} stopped successfully")
>>>>>>> 1ee3282 (feat(AUT-336): Implement VectorBT Pro backtesting engine with Celery workers)


def main():
    """
<<<<<<< HEAD
    Main entry point for Railway worker.
    """
    # Get bot ID from environment variable or command line
    bot_id = os.environ.get('BOT_ID') or (sys.argv[1] if len(sys.argv) > 1 else None)

    if not bot_id:
        print("Error: BOT_ID environment variable or command line argument required")
        sys.exit(1)

=======
    Entry point for Railway worker.
    Bot ID should be provided as command line argument.
    """
    if len(sys.argv) != 2:
        print("Usage: python -m app.trading.bot_runner <bot_id>")
        sys.exit(1)

    bot_id = sys.argv[1]

>>>>>>> 1ee3282 (feat(AUT-336): Implement VectorBT Pro backtesting engine with Celery workers)
    # Run the bot
    asyncio.run(run_bot(bot_id))


if __name__ == "__main__":
    main()