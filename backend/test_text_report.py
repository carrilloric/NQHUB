#!/usr/bin/env python3
"""
Test improved text report (FASE 7)
"""
import requests

BASE_URL = "http://localhost:8002/api/v1"

def test_text_report():
    print("="*120)
    print("TEST: Improved Text Report (FASE 7)")
    print("="*120)

    response = requests.post(
        f"{BASE_URL}/patterns/liquidity-pools/generate",
        json={
            "symbol": "NQZ5",
            "date": "2025-11-06",
            "timeframe": "5min",
            "pool_types": ["EQH", "EQL"]
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return

    data = response.json()
    text_report = data.get('text_report', '')

    if not text_report:
        print("❌ No text_report found in response!")
        return

    print("\n" + "="*120)
    print("📄 TEXT REPORT OUTPUT:")
    print("="*120)
    print(text_report)
    print("="*120)

    # Verify key sections are present
    print("\n✅ VERIFICATION:")
    checks = {
        "Header": "# Liquidity Pool Analysis" in text_report,
        "Detection Summary": "## 📊 Detection Summary" in text_report,
        "Current Price": "Current Price" in text_report,
        "Modal Level": "Modal Level" in text_report,
        "Importance Score": "Importance Score" in text_report,
        "Distance from Current": "Distance from Current" in text_report,
        "Spread": "Spread" in text_report,
        "Trading Implications": "## 💡 Trading Implications" in text_report,
        "ICT Framework": "ICT Framework" in text_report,
    }

    all_present = True
    for section, present in checks.items():
        status = "✅" if present else "❌"
        print(f"   {status} {section}: {'Found' if present else 'MISSING'}")
        if not present:
            all_present = False

    print("\n" + "="*120)
    if all_present:
        print("✅ ALL SECTIONS PRESENT - Text report is properly formatted")
    else:
        print("❌ SOME SECTIONS MISSING - Check report structure")
    print("="*120)

if __name__ == "__main__":
    test_text_report()
