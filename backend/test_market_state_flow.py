#!/usr/bin/env python3
"""
Test Market State Complete Flow
Tests progress tracking, generation, and detail retrieval
"""
import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8002/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjIxOTU2NzQsInN1YiI6IjEifQ.rSnLmwsSR7v1TJ4rvKyt0d4vTvHI1yPpZ8tvmcdVqKM"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("=" * 80)
print("MARKET STATE FLOW TEST")
print("=" * 80)

# Test 1: Generate small batch of snapshots with progress tracking
print("\n1. Testing snapshot generation with progress tracking...")
print("-" * 80)

request_data = {
    "symbol": "NQZ5",
    "start_time": "2025-11-24T09:00:00",
    "end_time": "2025-11-24T09:15:00",  # 15 minutes = 4 snapshots at 5min interval
    "interval_minutes": 5
}

print(f"Request: POST /market-state/generate")
print(f"  Symbol: {request_data['symbol']}")
print(f"  Start: {request_data['start_time']}")
print(f"  End: {request_data['end_time']}")
print(f"  Interval: {request_data['interval_minutes']} minutes")
print(f"  Expected snapshots: ~4")

response = requests.post(
    f"{BASE_URL}/market-state/generate",
    json=request_data,
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    print(f"\n✓ Generation started successfully!")
    print(f"  Job ID: {data['job_id']}")
    print(f"  Total snapshots: {data['total_snapshots']}")

    job_id = data['job_id']

    # Test 2: Poll progress
    print("\n2. Polling progress every 500ms...")
    print("-" * 80)

    completed = False
    poll_count = 0
    max_polls = 60  # Max 30 seconds

    while not completed and poll_count < max_polls:
        poll_count += 1
        time.sleep(0.5)

        progress_response = requests.get(
            f"{BASE_URL}/market-state/progress/{job_id}",
            headers=headers
        )

        if progress_response.status_code == 200:
            progress = progress_response.json()

            print(f"Poll #{poll_count}: {progress['completed_snapshots']}/{progress['total_snapshots']} " +
                  f"({progress['percentage']}%) - Status: {progress['status']}")
            print(f"  Elapsed: {progress['elapsed_seconds']:.1f}s, " +
                  f"Remaining: {progress['estimated_seconds_remaining']:.1f}s")

            if progress['status'] == 'completed':
                print(f"\n✓ Generation completed!")
                completed = True
            elif progress['status'] == 'error':
                print(f"\n✗ Generation failed: {progress.get('error_message', 'Unknown error')}")
                break
        else:
            print(f"✗ Failed to get progress: {progress_response.status_code}")
            print(f"  Response: {progress_response.text}")
            break

    if not completed:
        print(f"\n⚠ Polling stopped after {poll_count} attempts")

    # Test 3: Get detail for first snapshot
    print("\n3. Testing snapshot detail retrieval...")
    print("-" * 80)

    if data['snapshots']:
        first_snapshot = data['snapshots'][0]
        snapshot_time = first_snapshot['snapshot_time']

        print(f"Request: GET /market-state/detail")
        print(f"  Symbol: {request_data['symbol']}")
        print(f"  Snapshot time: {snapshot_time}")

        detail_response = requests.get(
            f"{BASE_URL}/market-state/detail",
            params={
                "symbol": request_data['symbol'],
                "snapshot_time": snapshot_time
            },
            headers=headers
        )

        if detail_response.status_code == 200:
            detail = detail_response.json()
            print(f"\n✓ Detail retrieved successfully!")
            print(f"  Snapshot time EST: {detail['snapshot_time_est']}")
            print(f"  Total patterns: {detail['summary']['total_patterns_all_timeframes']}")
            print(f"\n  Patterns by timeframe:")
            for tf, count in detail['summary']['by_timeframe'].items():
                print(f"    {tf}: {count}")

            # Check if we have actual pattern data
            if '5min' in detail['timeframes']:
                tf_data = detail['timeframes']['5min']
                print(f"\n  5min timeframe details:")
                print(f"    Active FVGs: {len(tf_data['active_fvgs'])}")
                print(f"    Active Session Levels: {len(tf_data['active_session_levels'])}")
                print(f"    Active OBs: {len(tf_data['active_obs'])}")

                if tf_data['active_fvgs']:
                    print(f"\n  Sample FVG:")
                    fvg = tf_data['active_fvgs'][0]
                    print(f"    ID: {fvg['fvg_id']}")
                    print(f"    Type: {fvg['fvg_type']}")
                    print(f"    Formation: {fvg['formation_time']}")
                    print(f"    Range: {fvg['fvg_start']:.2f} - {fvg['fvg_end']:.2f}")
                    print(f"    Gap size: {fvg['gap_size']:.2f}")
                    print(f"    Status: {fvg['status']}")
        else:
            print(f"\n✗ Failed to get detail: {detail_response.status_code}")
            print(f"  Response: {detail_response.text}")

    # Test 4: List snapshots
    print("\n4. Testing snapshot list...")
    print("-" * 80)

    list_response = requests.get(
        f"{BASE_URL}/market-state/list",
        params={
            "symbol": request_data['symbol'],
            "limit": 10
        },
        headers=headers
    )

    if list_response.status_code == 200:
        list_data = list_response.json()
        print(f"\n✓ List retrieved successfully!")
        print(f"  Total snapshots for {request_data['symbol']}: {list_data['total']}")
        print(f"\n  Recent snapshots (limit 10):")
        for snap in list_data['snapshots'][:5]:
            print(f"    {snap['snapshot_time_est']}: {snap['total_patterns']} patterns")
    else:
        print(f"\n✗ Failed to get list: {list_response.status_code}")
        print(f"  Response: {list_response.text}")

else:
    print(f"\n✗ Generation failed: {response.status_code}")
    print(f"Response: {response.text}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
