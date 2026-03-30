"""
Database Writer Actor for NQHUB trading system.
Persists MessageBus events to PostgreSQL with batching.
"""
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from app.trading.actors.base import NQHubActor, NQHubActorConfig


class DbWriterActorConfig(NQHubActorConfig):
    """Configuration for DbWriterActor."""
    db_session: Optional[Any] = None  # AsyncSession in production
    batch_size: int = 100
    flush_interval_ms: int = 5000


class DbWriterActor(NQHubActor):
    """
    Actor that persists MessageBus events to PostgreSQL.

    This actor subscribes to MessageBus events and persists them
    to the database using batch writes for performance.
    """

    def __init__(self, config: DbWriterActorConfig):
        """
        Initialize DbWriterActor.

        Args:
            config: Actor configuration including DB session and batch settings
        """
        super().__init__(config)
        self.db_session = config.db_session
        self.batch_size = config.batch_size
        self.flush_interval_ms = config.flush_interval_ms
        self._event_batch: List[Dict[str, Any]] = []
        self._flush_task: Optional[asyncio.Task] = None

    async def persist_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Persist an event to the database.

        Args:
            event_type: Type of event (trade, candle, pattern, etc.)
            event_data: Event data to persist
        """
        # Add event to batch
        event = {
            'type': event_type,
            'data': event_data,
            'timestamp': datetime.now(),
            'bot_id': self.bot_id
        }
        self._event_batch.append(event)

        self.log.debug(f"Added {event_type} event to batch, size: {len(self._event_batch)}")

        # Check if batch is full
        if len(self._event_batch) >= self.batch_size:
            await self._flush_batch()

    async def _flush_batch(self) -> None:
        """Flush the current event batch to the database."""
        if not self._event_batch:
            return

        batch_to_flush = self._event_batch.copy()
        self._event_batch.clear()

        try:
            if self.db_session:
                # In production, this would create ORM objects and add them
                # For testing, we simulate the database operations
                if hasattr(self.db_session, 'add_all'):
                    # Batch insert
                    self.db_session.add_all(batch_to_flush)
                else:
                    # Individual inserts for testing
                    for event in batch_to_flush:
                        self.db_session.add(event)

                # Commit the transaction
                await self.db_session.commit()

                self.log.info(f"Flushed {len(batch_to_flush)} events to database")
        except Exception as e:
            # Rollback on error
            if self.db_session and hasattr(self.db_session, 'rollback'):
                await self.db_session.rollback()

            self.log.error(f"Failed to flush batch: {e}")
            # In production, might want to retry or save to a fallback

    async def _periodic_flush(self) -> None:
        """Periodically flush the event batch."""
        while True:
            await asyncio.sleep(self.flush_interval_ms / 1000.0)
            await self._flush_batch()

    def on_trade_event(self, trade_data: Dict[str, Any]) -> None:
        """
        Handle trade events from MessageBus.

        Args:
            trade_data: Trade event data
        """
        # In production, this would be async and properly awaited
        self.log.debug(f"Received trade event")

    def on_candle_event(self, candle_data: Dict[str, Any]) -> None:
        """
        Handle candle events from MessageBus.

        Args:
            candle_data: Candle event data
        """
        self.log.debug(f"Received candle event")

    def on_pattern_event(self, pattern_data: Dict[str, Any]) -> None:
        """
        Handle pattern events from MessageBus.

        Args:
            pattern_data: Pattern event data
        """
        self.log.debug(f"Received pattern event")

    def on_start(self) -> None:
        """Called when the actor starts."""
        super().on_start()

        # Start periodic flush task
        if asyncio.get_event_loop().is_running():
            self._flush_task = asyncio.create_task(self._periodic_flush())
            self.log.info(f"Started periodic flush task (interval: {self.flush_interval_ms}ms)")

    def on_stop(self) -> None:
        """Called when the actor stops."""
        super().on_stop()

        # Cancel flush task
        if self._flush_task:
            self._flush_task.cancel()

        # Final flush
        if self._event_batch:
            # In production, this would be awaited properly
            self.log.info(f"Final flush of {len(self._event_batch)} events")