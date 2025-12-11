"""
Full ETL integration test - Upload file and verify tick insertion.
"""
import asyncio
import httpx
import time
from pathlib import Path
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8002/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjIxMzkwMTUsInN1YiI6IjEifQ.1eABLPTvJm49Hr-OZJ0eDhl62VWY60ZlS-wg9tlhdQo"

async def check_tick_count():
    """Check total ticks in database."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM market_data_ticks"))
        count = result.scalar()
        return count or 0

async def upload_file_and_monitor(file_path: str):
    """Upload a file and monitor the ETL job."""

    file_path = Path(file_path)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False

    logger.info(f"Testing with file: {file_path.name}")
    logger.info(f"File size: {file_path.stat().st_size / 1024 / 1024:.2f} MB")

    # Check initial tick count
    initial_ticks = await check_tick_count()
    logger.info(f"Initial tick count in database: {initial_ticks:,}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Upload file
        logger.info("Uploading file...")
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/zip')}
            response = await client.post(
                f"{API_BASE}/etl/upload-zip",
                files=files,
                headers={"Authorization": f"Bearer {TOKEN}"}
            )

        if response.status_code != 201:
            logger.error(f"Upload failed: {response.status_code} - {response.text}")
            return False

        data = response.json()
        job_id = data['job_id']
        logger.info(f"✓ Upload successful. Job ID: {job_id}")

        # Monitor job progress
        logger.info("Monitoring job progress...")
        max_wait = 120  # 2 minutes
        start_time = time.time()
        last_status = None

        while time.time() - start_time < max_wait:
            response = await client.get(
                f"{API_BASE}/etl/jobs/{job_id}",
                headers={"Authorization": f"Bearer {TOKEN}"}
            )

            if response.status_code != 200:
                logger.error(f"Failed to get job status: {response.status_code}")
                break

            job = response.json()
            status = job['status']
            progress = job.get('progress_pct', 0)
            ticks = job.get('ticks_inserted', 0)

            # Log status changes
            if status != last_status:
                logger.info(f"Status: {status} ({progress}%) - Ticks: {ticks:,}")
                last_status = status

            if status == 'completed':
                logger.info(f"\n{'='*60}")
                logger.info(f"✅ JOB COMPLETED SUCCESSFULLY")
                logger.info(f"CSV files processed: {job.get('csv_files_processed', 0)}")
                logger.info(f"Ticks inserted: {job.get('ticks_inserted', 0):,}")
                logger.info(f"Candles created: {job.get('candles_created', 0):,}")
                logger.info(f"{'='*60}\n")

                # Verify database
                final_ticks = await check_tick_count()
                new_ticks = final_ticks - initial_ticks
                logger.info(f"Database verification:")
                logger.info(f"  Initial ticks: {initial_ticks:,}")
                logger.info(f"  Final ticks: {final_ticks:,}")
                logger.info(f"  New ticks: {new_ticks:,}")

                if new_ticks > 0:
                    logger.info(f"\n✅ TEST PASSED: {new_ticks:,} ticks inserted into database!")
                    return True
                else:
                    logger.error(f"\n❌ TEST FAILED: No ticks inserted into database")
                    return False

            elif status == 'failed':
                logger.error(f"\n{'='*60}")
                logger.error(f"❌ JOB FAILED")
                logger.error(f"Error: {job.get('error_message', 'Unknown error')}")
                logger.error(f"{'='*60}\n")
                return False

            await asyncio.sleep(2)

        logger.error(f"Timeout waiting for job completion")
        return False

async def main():
    """Run the test."""
    # Use smallest file for quick test
    test_file = "/mnt/c/Users/ricar/Downloads/GLBX-20241230-PRA7BAY34H.zip"

    success = await upload_file_and_monitor(test_file)
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
