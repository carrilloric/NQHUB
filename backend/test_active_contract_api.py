"""
Test Active Contract API Endpoints
"""
import requests
import json

# Get auth token
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjIxOTU2NzQsInN1YiI6IjEifQ.rSnLmwsSR7v1TJ4rvKyt0d4vTvHI1yPpZ8tvmcdVqKM"
BASE_URL = "http://localhost:8002/api/v1"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("=" * 80)
print("TESTING ACTIVE CONTRACT API ENDPOINTS")
print("=" * 80)

# Test 1: Get current active contract
print("\n1. GET /etl/active-contract - Current Active Contract")
print("-" * 80)
try:
    response = requests.get(f"{BASE_URL}/etl/active-contract", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, default=str))
        print(f"✅ Current active contract: {data['symbol']}")
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Request failed: {e}")

# Test 2: Get active contract history
print("\n2. GET /etl/active-contract/history - Historical Periods")
print("-" * 80)
try:
    response = requests.get(
        f"{BASE_URL}/etl/active-contract/history?limit=10",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total periods: {data['total']}")
        for period in data['periods']:
            print(f"  {period['symbol']}: {period['start_date']} to {period['end_date']} - "
                  f"Volume: {period['volume_score']:,}, Current: {period['is_current']}")
        print(f"✅ Retrieved {len(data['periods'])} periods")
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Request failed: {e}")

# Test 3: Get rollover periods
print("\n3. GET /etl/rollover-periods - Rollover Events")
print("-" * 80)
try:
    response = requests.get(
        f"{BASE_URL}/etl/rollover-periods?limit=5",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if data:
            for event in data:
                print(f"  {event['from_symbol']} → {event['to_symbol']} on {event['rollover_date']}")
                print(f"    Volume: {event['from_volume']:,} → {event['to_volume']:,}")
            print(f"✅ Retrieved {len(data)} rollover events")
        else:
            print("  ℹ️  No rollover events found (only 1 contract period exists)")
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Request failed: {e}")

print("\n" + "=" * 80)
print("API TEST COMPLETE")
print("=" * 80)
