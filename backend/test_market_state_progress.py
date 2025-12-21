#!/usr/bin/env python3
"""
Test Market State with Progress Tracking (Background Generation)
"""
import requests
import time

BASE_URL = "http://localhost:8002/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjIxOTU2NzQsInN1YiI6IjEifQ.rSnLmwsSR7v1TJ4rvKyt0d4vTvHI1yPpZ8tvmcdVqKM"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("=" * 80)
print("MARKET STATE BACKGROUND GENERATION TEST")
print("=" * 80)

# Generate snapshots (should return immediately)
print("\n1. Starting generation (should return immediately with job_id)...")
request_data = {
    "symbol": "NQZ5",
    "start_time": "2025-11-24T09:00:00",
    "end_time": "2025-11-24T10:00:00",  # 1 hour = 13 snapshots at 5min interval
    "interval_minutes": 5
}

start_time = time.time()
response = requests.post(
    f"{BASE_URL}/market-state/generate",
    json=request_data,
    headers=headers
)

response_time = time.time() - start_time

if response.status_code == 200:
    data = response.json()
    print(f"✓ Response received in {response_time:.2f}s (should be < 1s)")
    print(f"  Job ID: {data['job_id']}")
    print(f"  Total snapshots (expected): {data['total_snapshots']}")
    print(f"  Snapshots returned: {len(data['snapshots'])} (should be 0 initially)")

    if response_time < 2.0:
        print(f"  ✓ API returned immediately! Generation happening in background.")
    else:
        print(f"  ⚠ API took {response_time:.2f}s - might be waiting for generation")

    job_id = data['job_id']

    # Poll progress
    print("\n2. Polling progress...")
    completed = False
    poll_count = 0

    while not completed and poll_count < 50:
        poll_count += 1
        time.sleep(0.5)

        progress_response = requests.get(
            f"{BASE_URL}/market-state/progress/{job_id}",
            headers=headers
        )

        if progress_response.status_code == 200:
            progress = progress_response.json()

            print(f"  Poll #{poll_count}: {progress['completed_snapshots']}/{progress['total_snapshots']} " +
                  f"({progress['percentage']}%) - Status: {progress['status']}")

            if progress['status'] == 'completed':
                print(f"\n✓ Generation completed!")
                print(f"  Total time: {progress['elapsed_seconds']:.1f}s")
                completed = True
                break
            elif progress['status'] == 'error':
                print(f"\n✗ Generation failed: {progress.get('error_message', 'Unknown')}")
                break

    if completed:
        # Verify snapshots exist
        print("\n3. Verifying snapshots in database...")
        list_response = requests.get(
            f"{BASE_URL}/market-state/list",
            params={"symbol": "NQZ5", "limit": 20},
            headers=headers
        )

        if list_response.status_code == 200:
            list_data = list_response.json()
            print(f"✓ Found {list_data['total']} snapshots for NQZ5")
        else:
            print(f"✗ Failed to list snapshots: {list_response.status_code}")

else:
    print(f"✗ Generation failed: {response.status_code}")
    print(f"  Response: {response.text}")

print("\n" + "=" * 80)
