"""
Test script to verify CSV parser fixes.
Tests parsing a Databento CSV file with ISO 8601 timestamps.
"""
from pathlib import Path
from app.etl.services.csv_parser import parse_csv_file
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_csv_parsing():
    """Test parsing a real CSV file from extracted job data."""

    # Find a CSV file in /tmp/etl_jobs
    csv_path = Path("/tmp/etl_jobs/0cc3b062-bd3d-40e9-93d2-33ab08b398f0/extracted/glbx-mdp3-20240618.tbbo.csv")

    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return False

    logger.info(f"Testing CSV parser with: {csv_path.name}")
    logger.info(f"File size: {csv_path.stat().st_size / 1024 / 1024:.2f} MB")

    try:
        total_ticks = 0
        total_batches = 0

        # Parse in batches
        for batch in parse_csv_file(csv_path):
            total_batches += 1
            batch_size = len(batch)
            total_ticks += batch_size

            # Log first batch details
            if total_batches == 1:
                logger.info(f"✓ First batch parsed successfully: {batch_size} ticks")
                first_tick = batch[0]
                logger.info(f"Sample tick: symbol={first_tick['symbol']}, "
                           f"price={first_tick['price']}, "
                           f"ts_event={first_tick['ts_event']}")

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ PARSING TEST SUCCESSFUL")
        logger.info(f"Total batches: {total_batches}")
        logger.info(f"Total ticks parsed: {total_ticks:,}")
        logger.info(f"{'='*60}\n")

        return True

    except Exception as e:
        logger.error(f"\n{'='*60}")
        logger.error(f"❌ PARSING TEST FAILED")
        logger.error(f"Error: {str(e)}")
        logger.error(f"{'='*60}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_csv_parsing()
    exit(0 if success else 1)
