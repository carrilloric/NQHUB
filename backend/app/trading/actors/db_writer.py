"""
Database Writer Actor for NautilusTrader.
Persists MessageBus events to PostgreSQL using batch writes.
"""
from datetime import datetime
from typing import Optional, Any, List, Dict
from app.trading.actors.base import NQHubActor, NQHubActorConfig


class DbWriterActorConfig(NQHubActorConfig, kw_only=True):
    """Configuration for DbWriterActor."""
    db_session: Optional[Any] = None
    batch_size: int = 100
    flush_interval_ms: int = 5000


class DbWriterActor(NQHubActor):
    """
    Actor that persists MessageBus events to PostgreSQL.

    This actor collects events from the MessageBus and writes them
    to PostgreSQL using batch writes for performance.
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
        self._last_flush = datetime.now()

    def on_start(self) -> None:
        """Start the actor and set up batch processing."""
        super().on_start()
        # Subscribe to relevant MessageBus events for persistence
        # self.subscribe_events()
        self.log.info(
            f"DbWriterActor started with batch_size={self.batch_size}, "
            f"flush_interval={self.flush_interval_ms}ms"
        )

    def on_stop(self) -> None:
        """Stop the actor and flush pending events."""
        # Flush any remaining events before stopping
        if self._event_batch:
            self._flush_batch_sync()
        super().on_stop()

    async def persist_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Persist an event to the database.

        Args:
            event_type: Type of event to persist
            event_data: Event data to persist
        """
        event = {
            'type': event_type,
            'data': event_data,
            'timestamp': datetime.now(),
            'bot_id': self.bot_id
        }
        self._event_batch.append(event)

        # Check if we need to flush
        if len(self._event_batch) >= self.batch_size:
            await self._flush_batch()
        elif self._should_flush_by_time():
            await self._flush_batch()

    def _should_flush_by_time(self) -> bool:
        """Check if enough time has passed to flush the batch."""
        elapsed_ms = (datetime.now() - self._last_flush).total_seconds() * 1000
        return elapsed_ms >= self.flush_interval_ms

    async def _flush_batch(self) -> None:
        """Flush the current batch to the database asynchronously."""
        if not self._event_batch:
            return

        if self.db_session:
            try:
                # Perform batch insert
                # In real implementation, this would use SQLAlchemy bulk operations
                self.log.debug(f"Flushing {len(self._event_batch)} events to database")
                # await self.db_session.bulk_insert(self._event_batch)
                self._event_batch.clear()
                self._last_flush = datetime.now()
            except Exception as e:
                self.log.error(f"Error flushing batch to database: {e}")

    def _flush_batch_sync(self) -> None:
        """Flush the current batch to the database synchronously (for shutdown)."""
        if not self._event_batch:
            return

        if self.db_session:
            try:
                self.log.info(f"Final flush of {len(self._event_batch)} events to database")
                # Synchronous bulk insert for shutdown
                # self.db_session.bulk_insert(self._event_batch)
                self._event_batch.clear()
            except Exception as e:
                self.log.error(f"Error in final batch flush: {e}")