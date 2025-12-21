#!/usr/bin/env python3
"""
Test Order Blocks Detection
"""
import requests
import pytz
from datetime import datetime

BASE_URL = "http://localhost:8002/api/v1"

def test_order_blocks():
    print("="*120)
    print("📦 TEST: ORDER BLOCKS DETECTION")
    print("="*120)

    response = requests.post(
        f"{BASE_URL}/patterns/order-blocks/generate",
        json={
            "symbol": "NQZ5",
            "start_date": "2025-11-06",
            "end_date": "2025-11-06",
            "timeframe": "5min"
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return

    data = response.json()
    obs = data.get('order_blocks', [])

    print(f"\n✅ Total Order Blocks detected: {len(obs)}\n")

    # Breakdown
    breakdown = data.get('breakdown', {})
    print("📊 BREAKDOWN BY TYPE:")
    print("="*120)
    for ob_type, count in breakdown.items():
        print(f"   {ob_type}: {count}")

    if not obs:
        print("\n⚠️  No Order Blocks detected for this date")
        return

    # Show top 10 OBs
    print("\n" + "="*120)
    print("🔝 TOP 10 ORDER BLOCKS:")
    print("="*120)
    print(f"{'#':<3} {'Type':<20} {'Time (EST)':<20} {'High':<10} {'Low':<10} {'Impulse':<10} {'Quality':<10} {'Status':<10}")
    print("="*120)

    for i, ob in enumerate(obs[:10], 1):
        formation_time_utc = datetime.fromisoformat(ob['formation_time'].replace('Z', '+00:00'))
        # Convert UTC to EST
        eastern = pytz.timezone('US/Eastern')
        formation_time_est = formation_time_utc.astimezone(eastern)
        time_str = formation_time_est.strftime('%b %d %H:%M')

        print(f"{i:<3} {ob['ob_type']:<20} {time_str:<20} {ob['ob_high']:<10.2f} {ob['ob_low']:<10.2f} "
              f"{ob['impulse_move']:<10.2f} {ob['quality']:<10} {ob['status']:<10}")

    # Detailed view of first 3
    print("\n" + "="*120)
    print("🔍 DETAILED VIEW (First 3):")
    print("="*120)

    for i, ob in enumerate(obs[:3], 1):
        formation_time_utc = datetime.fromisoformat(ob['formation_time'].replace('Z', '+00:00'))
        # Convert UTC to EST
        eastern = pytz.timezone('US/Eastern')
        formation_time_est = formation_time_utc.astimezone(eastern)
        time_str = formation_time_est.strftime('%b %d %H:%M:%S %Z')

        print(f"\n{i}. {ob['ob_type']}")
        print(f"   Formation Time: {time_str}")
        print(f"   OB Range: {ob['ob_low']:.2f} - {ob['ob_high']:.2f}")
        print(f"   OB Body: {ob['ob_open']:.2f} - {ob['ob_close']:.2f}")
        print(f"   Volume: {ob['ob_volume']:,.0f}")
        print(f"   Impulse Move: {ob['impulse_move']:.2f} pts ({ob['impulse_direction']})")
        print(f"   Candle Direction: {ob['candle_direction']}")
        print(f"   Quality: {ob['quality']}")
        print(f"   Status: {ob['status']}")

    # Show text report if available
    text_report = data.get('text_report', '')
    if text_report:
        print("\n" + "="*120)
        print("📄 TEXT REPORT:")
        print("="*120)
        print(text_report[:1000])  # First 1000 chars
        if len(text_report) > 1000:
            print("\n... (truncated)")

    # Auto parameters
    auto_params = data.get('auto_parameters', {})
    print("\n" + "="*120)
    print("⚙️  AUTO-CALIBRATED PARAMETERS:")
    print("="*120)
    for key, value in auto_params.items():
        print(f"   {key}: {value}")

    print("\n" + "="*120)
    print("✅ Order Blocks test complete!")
    print("="*120)

if __name__ == "__main__":
    test_order_blocks()
