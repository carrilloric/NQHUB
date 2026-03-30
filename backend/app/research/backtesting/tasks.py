"""
Celery tasks for async backtest execution.

Tasks run backtests without blocking the API and save results to database.
"""

from celery import shared_task
from datetime import datetime
import json
import time
from typing import Dict, Any

from app.research.backtesting.engine import BacktestEngine, ApexValidator
from app.research.backtesting.schemas import BacktestConfig, BacktestResults
from app.research.strategies.registry import StrategyRegistry
# from app.core.database import get_async_db  # Will use when implementing real DB save
# from app.models.backtest import BacktestRun  # Will create when needed
import pandas as pd


@shared_task(bind=True, max_retries=0)  # NO retry en backtests — pueden tardar mucho
def run_backtest_task(self, backtest_config: dict) -> dict:
    """
    Task Celery async para correr backtests sin bloquear el API.

    Guarda resultados en backtest_runs table.
    Publica progreso via Redis pub/sub.

    Args:
        backtest_config: Dictionary with BacktestConfig data

    Returns:
        Dictionary with BacktestResults data
    """
    import redis
    from app.config import settings

    # Initialize Redis client for progress updates
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True
    )

    # Parse config
    config = BacktestConfig(**backtest_config)

    # Publish start event
    task_id = self.request.id
    publish_event(
        redis_client,
        "backtest.started",
        {
            "task_id": task_id,
            "strategy_id": config.strategy_id,
            "started_at": datetime.utcnow().isoformat()
        }
    )

    try:
        # Update progress: loading data
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Loading data...'}
        )
        publish_progress(redis_client, task_id, 10, 'Loading data')

        # Load candle data from TimescaleDB
        candles = load_candles_from_db(
            timeframe=config.timeframe,
            start_date=config.start_date,
            end_date=config.end_date
        )

        # Update progress: loading strategy
        self.update_state(
            state='PROGRESS',
            meta={'current': 30, 'total': 100, 'status': 'Loading strategy...'}
        )
        publish_progress(redis_client, task_id, 30, 'Loading strategy')

        # Get strategy instance from registry
        registry = StrategyRegistry()
        strategy = registry.get_strategy(config.strategy_id)

        # Update progress: running backtest
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Running backtest...'}
        )
        publish_progress(redis_client, task_id, 50, 'Running backtest')

        # Initialize engine with ApexValidator
        apex_validator = ApexValidator()
        engine = BacktestEngine(apex_validator=apex_validator)

        # Run the backtest
        results = engine.run_backtest(
            strategy=strategy,
            candles=candles,
            config=config
        )

        # Update progress: saving results
        self.update_state(
            state='PROGRESS',
            meta={'current': 90, 'total': 100, 'status': 'Saving results...'}
        )
        publish_progress(redis_client, task_id, 90, 'Saving results')

        # Save results to database
        save_backtest_results(results)

        # Publish completion event
        publish_event(
            redis_client,
            "backtest.completed",
            {
                "task_id": task_id,
                "backtest_id": results.backtest_id,
                "strategy_id": results.strategy_id,
                "total_return": results.total_return,
                "sharpe_ratio": results.sharpe_ratio,
                "completed_at": datetime.utcnow().isoformat()
            }
        )

        # Update final progress
        self.update_state(
            state='SUCCESS',
            meta={'current': 100, 'total': 100, 'status': 'Completed'}
        )
        publish_progress(redis_client, task_id, 100, 'Completed')

        return results.dict()

    except Exception as e:
        # Publish error event
        publish_event(
            redis_client,
            "backtest.failed",
            {
                "task_id": task_id,
                "strategy_id": config.strategy_id,
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            }
        )

        # Update state to failure
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )

        # Re-raise the exception (no retry configured)
        raise


@shared_task(bind=True)
def optimize_backtest_task(self, optimization_config: dict) -> dict:
    """
    Celery task for running optimization (grid search or walk-forward).

    Args:
        optimization_config: Configuration for optimization

    Returns:
        Dictionary with optimization results
    """
    from app.research.backtesting.optimizer import BacktestOptimizer

    # Parse config type
    optimization_type = optimization_config.get('optimization_type')

    # Initialize optimizer
    optimizer = BacktestOptimizer()

    # Load candles
    candles = load_candles_from_db(
        timeframe=optimization_config.get('timeframe'),
        start_date=datetime.fromisoformat(optimization_config.get('start_date')),
        end_date=datetime.fromisoformat(optimization_config.get('end_date'))
    )

    # Get strategy class
    strategy_class_name = optimization_config.get('strategy_class')
    registry = StrategyRegistry()
    strategy_class = registry.get_strategy_class(strategy_class_name)

    if optimization_type == 'grid_search':
        param_grid = optimization_config.get('param_grid', {})
        results = optimizer.grid_search(
            strategy_class=strategy_class,
            param_grid=param_grid,
            candles=candles
        )
    elif optimization_type == 'walk_forward':
        n_splits = optimization_config.get('n_splits', 5)
        results = optimizer.walk_forward(
            strategy_class=strategy_class,
            candles=candles,
            n_splits=n_splits
        )
    else:
        raise ValueError(f"Unknown optimization type: {optimization_type}")

    # Convert results to dict for serialization
    return {
        'optimization_type': optimization_type,
        'n_results': len(results),
        'results': [r.dict() for r in results]
    }


def save_backtest_results(results: BacktestResults) -> None:
    """
    Save backtest results to database.

    Args:
        results: BacktestResults to save
    """
    # This would typically use SQLAlchemy session
    # For now, we'll mock the implementation
    # Real implementation would be:

    # from app.core.database import SessionLocal
    # from app.models.backtest import BacktestRun
    #
    # db = SessionLocal()
    # try:
    #     backtest_run = BacktestRun(
    #         backtest_id=results.backtest_id,
    #         strategy_id=results.strategy_id,
    #         total_return=results.total_return,
    #         sharpe_ratio=results.sharpe_ratio,
    #         # ... other fields ...
    #         created_at=datetime.utcnow()
    #     )
    #     db.add(backtest_run)
    #     db.commit()
    # finally:
    #     db.close()

    print(f"Saving backtest results: {results.backtest_id}")
    pass  # Mock implementation for now


def load_candles_from_db(
    timeframe: str,
    start_date: datetime,
    end_date: datetime
) -> pd.DataFrame:
    """
    Load candle data from TimescaleDB.

    Args:
        timeframe: Timeframe string (1min, 5min, etc.)
        start_date: Start date for data
        end_date: End date for data

    Returns:
        DataFrame with OHLCV data
    """
    # This would typically query TimescaleDB
    # For now, return mock data for testing

    # Real implementation would be:
    # from app.services.data_platform import DataPlatform
    # platform = DataPlatform()
    # candles = platform.get_candles(
    #     symbol='NQ',
    #     timeframe=timeframe,
    #     start_date=start_date,
    #     end_date=end_date
    # )

    # Mock implementation for testing
    import numpy as np

    n_bars = 1000
    dates = pd.date_range(start=start_date, end=end_date, freq='1min')[:n_bars]

    # Generate synthetic data
    start_price = 15000.0
    returns = np.random.normal(0.0001, 0.001, len(dates))
    prices = start_price * (1 + returns).cumprod()

    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.uniform(-0.0001, 0.0001, len(dates))),
        'high': prices * (1 + np.abs(np.random.uniform(0, 0.0002, len(dates)))),
        'low': prices * (1 - np.abs(np.random.uniform(0, 0.0002, len(dates)))),
        'close': prices,
        'volume': np.random.uniform(100, 1000, len(dates)).astype(int)
    })

    # Ensure OHLC relationships
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)

    # Round to tick size
    for col in ['open', 'high', 'low', 'close']:
        df[col] = np.round(df[col] * 4) / 4

    df.set_index('timestamp', inplace=True)
    return df


def publish_event(redis_client, event_name: str, data: Dict[str, Any]) -> None:
    """
    Publish event to Redis pub/sub.

    Args:
        redis_client: Redis client instance
        event_name: Name of the event
        data: Event data
    """
    channel = f"backtest.events.{event_name}"
    message = json.dumps(data)
    redis_client.publish(channel, message)


def publish_progress(redis_client, task_id: str, progress: int, status: str) -> None:
    """
    Publish progress update to Redis.

    Args:
        redis_client: Redis client instance
        task_id: Celery task ID
        progress: Progress percentage (0-100)
        status: Status message
    """
    channel = f"backtest.progress.{task_id}"
    message = json.dumps({
        'task_id': task_id,
        'progress': progress,
        'status': status,
        'timestamp': datetime.utcnow().isoformat()
    })
    redis_client.publish(channel, message)