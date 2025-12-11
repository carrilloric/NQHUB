"""
RQ Worker Configuration for ETL Tasks

This worker processes ETL jobs in the background with:
- Automatic retry on failure (max 3 attempts)
- Graceful shutdown handling (SIGTERM, SIGINT)
- Healthcheck monitoring
- Exception tracking

To run the worker:
    cd backend
    source .venv/bin/activate
    python3 -m app.etl.worker

Or with Docker Compose:
    docker-compose up -d worker
    docker-compose scale worker=4  # Scale to 4 workers
"""
import redis
import signal
import sys
from rq import Worker, Queue, Connection
from rq.job import JobStatus
from app.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_redis_connection():
    """Get Redis connection from settings"""
    return redis.from_url(settings.REDIS_URL)


def get_etl_queue():
    """Get ETL queue instance"""
    conn = get_redis_connection()
    return Queue('etl_queue', connection=conn)


# Global worker reference for signal handler
worker_instance = None

def signal_handler(signum, frame):
    """Handle graceful shutdown on SIGTERM/SIGINT"""
    global worker_instance
    sig_name = 'SIGTERM' if signum == signal.SIGTERM else 'SIGINT'
    logger.info(f"📡 Received {sig_name}, initiating graceful shutdown...")

    if worker_instance:
        # Request the worker to stop after finishing current job
        logger.info("⏳ Waiting for current job to complete...")
        worker_instance.request_stop()

        # Don't exit immediately, let the worker finish
        logger.info("✋ Worker will stop after current job completes")
    else:
        # If no worker instance, exit immediately
        sys.exit(0)


def custom_exc_handler(job, exc_type, exc_value, traceback):
    """Custom exception handler with detailed logging"""
    logger.error(f"❌ Job {job.id} failed with {exc_type.__name__}: {exc_value}")
    logger.error(f"   Job function: {job.func_name}")
    logger.error(f"   Job args: {job.args}")

    # Log full traceback
    import traceback as tb
    logger.error("   Traceback:")
    for line in tb.format_exception(exc_type, exc_value, traceback):
        logger.error(f"     {line.strip()}")

    return True  # Return True to mark job as failed


if __name__ == '__main__':
    logger.info("Starting RQ worker for ETL tasks...")
    logger.info(f"Connecting to Redis at: {settings.REDIS_URL}")

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Connect to Redis
        redis_conn = get_redis_connection()

        # Test connection
        redis_conn.ping()
        logger.info("✅ Successfully connected to Redis")

        # Create worker with custom settings
        with Connection(redis_conn):
            worker = Worker(
                ['etl_queue'],
                connection=redis_conn,
                # Retry failed jobs automatically (max 3 attempts)
                # Note: RQ doesn't have built-in retry, we handle this in tasks.py
                exception_handlers=[custom_exc_handler],
            )

            # Store worker instance globally for signal handler
            worker_instance = worker

            logger.info("👷 Worker started. Listening for jobs on 'etl_queue'...")
            logger.info("   - Graceful shutdown: SIGTERM/SIGINT (waits for current job)")
            logger.info("   - Exception handling: Custom handler with logging")
            logger.info("   - Healthcheck: 30s interval (via Docker)")

            # Start working (blocking call)
            worker.work(with_scheduler=False)

    except redis.ConnectionError as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        logger.error("Make sure Redis is running:")
        logger.error("   Docker: docker run -d -p 6379:6379 redis:alpine")
        logger.error("   Docker Compose: docker-compose up -d redis")
        exit(1)
    except KeyboardInterrupt:
        logger.info("👋 Worker stopped by user (Ctrl+C)")
        exit(0)
    except Exception as e:
        logger.error(f"❌ Worker error: {e}", exc_info=True)
        exit(1)
