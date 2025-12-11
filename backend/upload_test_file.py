"""
Script to upload test file and monitor ETL job
"""
import asyncio
import httpx
import time
from pathlib import Path

API_BASE = "http://localhost:8002/api/v1"
TEST_FILE = "/mnt/c/Users/ricar/Downloads/GLBX-20241230-YY4Y8YJGH8.zip"

async def main():
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Login
        print("🔑 Logging in...")
        response = await client.post(
            f"{API_BASE}/auth/login",
            json={"email": "admin@nqhub.com", "password": "admin_inicial_2024"}
        )

        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            print(response.text)
            return

        data = response.json()
        token = data.get('token') or data.get('access_token')
        print(f"✅ Logged in successfully")

        # Upload file
        print(f"\n📤 Uploading file: {Path(TEST_FILE).name} (62MB)...")
        with open(TEST_FILE, 'rb') as f:
            response = await client.post(
                f"{API_BASE}/etl/upload-zip",
                files={'file': (Path(TEST_FILE).name, f, 'application/zip')},
                headers={"Authorization": f"Bearer {token}"}
            )

        if response.status_code != 201:
            print(f"❌ Upload failed: {response.status_code}")
            print(response.text)
            return

        job_data = response.json()
        job_id = job_data['id']
        print(f"✅ Upload successful! Job ID: {job_id}")

        # Monitor job
        print(f"\n👀 Monitoring job progress...")
        last_status = None
        start_time = time.time()

        while time.time() - start_time < 600:  # 10 min max
            await asyncio.sleep(2)

            response = await client.get(
                f"{API_BASE}/etl/jobs/{job_id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code != 200:
                print(f"⚠️  Failed to get status: {response.status_code}")
                continue

            job = response.json()
            status = job['status']
            progress = job.get('progress_pct', 0)
            ticks = job.get('ticks_inserted', 0)

            if status != last_status:
                print(f"📊 Status: {status} ({progress}%) - Ticks: {ticks:,}")
                last_status = status

            if status == 'completed':
                print(f"\n{'='*60}")
                print(f"✅ JOB COMPLETED!")
                print(f"CSV files: {job.get('csv_files_processed', 0)}")
                print(f"Ticks inserted: {job.get('ticks_inserted', 0):,}")
                print(f"Candles created: {job.get('candles_created', 0):,}")
                print(f"Duration: {time.time() - start_time:.1f}s")
                print(f"{'='*60}")
                return True

            elif status == 'failed':
                print(f"\n❌ JOB FAILED!")
                print(f"Error: {job.get('error_message', 'Unknown')}")
                return False

        print(f"\n⏱️  Timeout after 10 minutes")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
