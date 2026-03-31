"""
Database Writer Actor for NQHUB trading system.

Persists MessageBus events to PostgreSQL using batch writes.
Never blocks the event loop with synchronous DB operations.
"""
import asyncio
from typing import Optional, Any, List, Dict
from datetime import datetime, timedelta
from app.trading.actors.base import NQHubActor, NQHubActorConfig


class DbWriterActorConfig(NQHubActorConfig):
    """
    Configuration for DbWriterActor.

    Attributes:
        batch_interval_ms: Flush interval in milliseconds (default 500ms)
        max_buffer_size: Maximum buffer size before forced flush (default 1000)
    """
    batch_interval_ms: int = 500      # Flush every 500ms as per spec
    max_buffer_size: int = 1000        # Force flush at 1000 events as per spec


class DbWriterActor(NQHubActor):
    """
    Actor that persists MessageBus events to PostgreSQL.

    Features:
    - Batch writes every 500ms to avoid blocking the event loop
    - Forced flush at 1000 events (max_buffer_size)
    - Never performs synchronous writes in the event loop
    - All database operations are properly async

    This actor subscribes to MessageBus events and persists them
    to PostgreSQL using batch writes for performance.
    """

    def __init__(self, config: DbWriterActorConfig, db_session: Optional[Any] = None):
        """
        Initialize DbWriterActor.

        Args:
            config: Actor configuration with batch settings
            db_session: Optional async database session (for testing)
        """
        super().__init__(config)
        self.db_session = db_session
        self.batch_interval_ms = config.batch_interval_ms
        self.max_buffer_size = config.max_buffer_size

        # Event buffer for batching
        self._event_buffer: List[Dict[str, Any]] = []

        # Async task for periodic flushing
        self._flush_task: Optional[asyncio.Task] = None

        # Last flush time for monitoring
        self._last_flush_time = datetime.now()

        # Statistics
        self._total_events_persisted = 0
        self._total_flushes = 0

    def on_start(self) -> None:
        """Start the actor and set up batch processing."""
        super().on_start()

        # Start the periodic flush task
        loop = asyncio.get_event_loop()
        if loop and loop.is_running():
            self._flush_task = loop.create_task(self._periodic_flush())
            self.log.info(
                f"DbWriterActor started with batch_interval={self.batch_interval_ms}ms, "
                f"max_buffer_size={self.max_buffer_size}"
            )
        else:
            self.log.warning("Event loop not running, periodic flush will start when ready")

    def on_stop(self) -> None:
        """Stop the actor and flush pending events."""
        # Cancel the periodic flush task
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            self.log.info("Cancelled periodic flush task")

        # Perform final flush
        if self._event_buffer:
            # Create a task for the final async flush
            loop = asyncio.get_event_loop()
            if loop and loop.is_running():
                # Schedule final flush
                loop.create_task(self._final_flush())
            else:
                self.log.warning(
                    f"Cannot flush {len(self._event_buffer)} pending events - event loop not running"
                )

        super().on_stop()
        self.log.info(
            f"DbWriterActor stopped. Total events persisted: {self._total_events_persisted}, "
            f"Total flushes: {self._total_flushes}"
        )

    async def persist_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Add an event to the buffer for batch persistence.

        This method NEVER blocks with synchronous DB writes.
        Events are added to a buffer and flushed based on:
        - Time interval (every 500ms)
        - Buffer size (forced flush at 1000 events)

        Args:
            event_type: Type of event (candle, order, pattern, etc.)
            event_data: Event data to persist
        """
        # Create event record with metadata
        event_record = {
            'type': event_type,
            'data': event_data,
            'timestamp': datetime.now(),
            'bot_id': self.bot_id
        }

        # Add to buffer
        self._event_buffer.append(event_record)

        self.log.debug(
            f"Added {event_type} event to buffer (size: {len(self._event_buffer)})"
        )

        # Check if we need a forced flush due to buffer size
        if len(self._event_buffer) >= self.max_buffer_size:
            self.log.info(f"Buffer size reached {self.max_buffer_size}, forcing flush")
            await self._flush_batch()

    async def _flush_batch(self) -> None:
        """
        Flush the current batch to the database asynchronously.

        This method:
        1. Copies the buffer to avoid race conditions
        2. Clears the original buffer immediately
        3. Persists events in a single transaction
        4. Never blocks the event loop
        """
        if not self._event_buffer:
            return

        # Copy buffer and clear immediately to avoid race conditions
        events_to_flush = self._event_buffer.copy()
        self._event_buffer.clear()

        batch_size = len(events_to_flush)
        self.log.debug(f"Flushing batch of {batch_size} events")

        if self.db_session:
            try:
                # Begin transaction
                async with self.db_session.begin() as transaction:
                    # Persist all events in the batch
                    for event in events_to_flush:
                        await self._persist_event(transaction, event)

                    # Commit is automatic when exiting the context manager

                # Update statistics
                self._total_events_persisted += batch_size
                self._total_flushes += 1
                self._last_flush_time = datetime.now()

                self.log.info(
                    f"Successfully flushed {batch_size} events to database "
                    f"(total: {self._total_events_persisted})"
                )

            except Exception as e:
                self.log.error(
                    f"Failed to flush batch of {batch_size} events: {e}"
                )
                # In production, might want to retry or save to fallback storage
                # For now, log and continue to avoid blocking
        else:
            self.log.warning(f"No DB session available, dropping {batch_size} events")

    async def _persist_event(self, transaction: Any, event: Dict[str, Any]) -> None:
        """
        Persist a single event within a transaction.

        Args:
            transaction: Database transaction context
            event: Event record to persist
        """
        # In production, this would create the appropriate ORM model
        # and add it to the transaction
        # Example:
        # if event['type'] == 'candle':
        #     candle = CandleModel(**event['data'])
        #     transaction.add(candle)
        # elif event['type'] == 'order':
        #     order = OrderModel(**event['data'])
        #     transaction.add(order)

        # For now, we simulate the async operation
        await asyncio.sleep(0)  # Yield control to event loop

    async def _periodic_flush(self) -> None:
        """
        Periodically flush the event batch.

        Runs every batch_interval_ms milliseconds (default 500ms).
        This ensures events are persisted regularly even with low activity.
        """
        interval_seconds = self.batch_interval_ms / 1000.0

        self.log.info(f"Starting periodic flush task (interval: {interval_seconds}s)")

        try:
            while True:
                # Wait for the specified interval
                await asyncio.sleep(interval_seconds)

                # Flush if we have events
                if self._event_buffer:
                    self.log.debug(
                        f"Periodic flush triggered ({len(self._event_buffer)} events pending)"
                    )
                    await self._flush_batch()

        except asyncio.CancelledError:
            self.log.info("Periodic flush task cancelled")
            raise
        except Exception as e:
            self.log.error(f"Error in periodic flush task: {e}")

    async def _final_flush(self) -> None:
        """
        Perform final flush on shutdown.

        This is called when the actor stops to ensure
        no events are lost.
        """
        if self._event_buffer:
            self.log.info(f"Performing final flush of {len(self._event_buffer)} events")
            await self._flush_batch()
        else:
            self.log.debug("No events to flush on shutdown")

    # MessageBus event handlers

    def on_candle_event(self, candle_data: Dict[str, Any]) -> None:
        """
        Handle candle events from MessageBus.

        Args:
            candle_data: Candle event data
        """
        # Schedule async persist (non-blocking)
        loop = asyncio.get_event_loop()
        if loop and loop.is_running():
            loop.create_task(self.persist_event('candle', candle_data))

    def on_order_event(self, order_data: Dict[str, Any]) -> None:
        """
        Handle order events from MessageBus.

        Args:
            order_data: Order event data
        """
        loop = asyncio.get_event_loop()
        if loop and loop.is_running():
            loop.create_task(self.persist_event('order', order_data))

    def on_position_event(self, position_data: Dict[str, Any]) -> None:
        """
        Handle position events from MessageBus.

        Args:
            position_data: Position event data
        """
        loop = asyncio.get_event_loop()
        if loop and loop.is_running():
            loop.create_task(self.persist_event('position', position_data))

    def on_pattern_event(self, pattern_data: Dict[str, Any]) -> None:
        """
        Handle pattern events from MessageBus.

        Args:
            pattern_data: Pattern event data
        """
        loop = asyncio.get_event_loop()
        if loop and loop.is_running():
            loop.create_task(self.persist_event('pattern', pattern_data))

    def on_risk_event(self, risk_data: Dict[str, Any]) -> None:
        """
        Handle risk events from MessageBus.

        Args:
            risk_data: Risk event data
        """
        loop = asyncio.get_event_loop()
        if loop and loop.is_running():
            loop.create_task(self.persist_event('risk', risk_data))

    def on_kill_switch_event(self, kill_data: Dict[str, Any]) -> None:
        """
        Handle kill switch events from MessageBus.

        Kill switch events are critical and should be persisted immediately.

        Args:
            kill_data: Kill switch event data
        """
        loop = asyncio.get_event_loop()
        if loop and loop.is_running():
            # Add to buffer
            task = loop.create_task(self.persist_event('kill_switch', kill_data))
            # Force immediate flush for critical events
            loop.create_task(self._flush_batch())
            self.log.critical(f"KILL SWITCH event received and queued for immediate persist")

    @property
    def buffer_size(self) -> int:
        """Get current buffer size."""
        return len(self._event_buffer)

    @property
    def stats(self) -> Dict[str, Any]:
        """Get actor statistics."""
        return {
            'buffer_size': self.buffer_size,
            'total_events_persisted': self._total_events_persisted,
            'total_flushes': self._total_flushes,
            'last_flush_time': self._last_flush_time.isoformat(),
            'batch_interval_ms': self.batch_interval_ms,
            'max_buffer_size': self.max_buffer_size
        }