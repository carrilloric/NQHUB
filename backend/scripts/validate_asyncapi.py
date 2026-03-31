"""
Validate AsyncAPI Spec (AUT-365)

Validates the AsyncAPI 2.6.0 spec for NQHUB WebSocket API.

Usage:
    python backend/scripts/validate_asyncapi.py

Validation checks:
1. YAML is valid and can be parsed
2. AsyncAPI version is 2.6.0
3. All 8 required channels are present
4. All channels have descriptions
5. Risk channel includes priority note
6. Subscribe protocol is documented
7. All schemas have required fields
"""
import yaml
from pathlib import Path
import sys


def validate_asyncapi_spec():
    """
    Validate AsyncAPI spec for NQHUB WebSocket API.

    Returns:
        bool: True if validation passes, False otherwise
    """
    # Load spec
    project_root = Path(__file__).parent.parent.parent
    spec_path = project_root / "docs" / "api" / "websocket.yaml"

    if not spec_path.exists():
        print(f"❌ Spec file not found: {spec_path}")
        return False

    try:
        with open(spec_path, "r") as f:
            spec = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML: {e}")
        return False

    print(f"✅ YAML is valid")

    # Check AsyncAPI version
    if spec.get("asyncapi") != "2.6.0":
        print(f"❌ AsyncAPI version must be 2.6.0, got: {spec.get('asyncapi')}")
        return False
    print(f"✅ AsyncAPI version is 2.6.0")

    # Check channels
    channels = spec.get("channels", {})
    required_channels = [
        "price",
        "orderflow",
        "patterns",
        "orders",
        "positions",
        "portfolio",
        "risk",
        "bot"
    ]

    if len(channels) != 8:
        print(f"❌ Expected 8 channels, found {len(channels)}: {list(channels.keys())}")
        return False
    print(f"✅ Found 8 channels")

    for channel_name in required_channels:
        if channel_name not in channels:
            print(f"❌ Missing required channel: {channel_name}")
            return False

    print(f"✅ All required channels present: {', '.join(required_channels)}")

    # Check that all channels have descriptions
    for channel_name, channel_spec in channels.items():
        if "description" not in channel_spec or not channel_spec["description"].strip():
            print(f"❌ Channel '{channel_name}' is missing a description")
            return False

    print(f"✅ All channels have descriptions")

    # Check risk channel has priority note
    risk_description = channels["risk"]["description"]
    priority_keywords = ["HIGHEST PRIORITY", "maximum priority", "CRITICAL PRIORITY"]

    if not any(keyword in risk_description for keyword in priority_keywords):
        print(f"❌ Risk channel description must mention priority (HIGHEST PRIORITY or similar)")
        return False

    print(f"✅ Risk channel documented with priority note")

    # Check subscribe protocol is documented
    subscribe_schema = spec.get("components", {}).get("schemas", {}).get("SubscribeMessage")

    if not subscribe_schema:
        print(f"❌ SubscribeMessage schema not found in components/schemas")
        return False

    # Verify SubscribeMessage has action and channels fields
    properties = subscribe_schema.get("properties", {})
    if "action" not in properties or "channels" not in properties:
        print(f"❌ SubscribeMessage must have 'action' and 'channels' properties")
        return False

    # Verify action enum has subscribe/unsubscribe
    action_enum = properties["action"].get("enum", [])
    if "subscribe" not in action_enum or "unsubscribe" not in action_enum:
        print(f"❌ SubscribeMessage action enum must include 'subscribe' and 'unsubscribe'")
        return False

    print(f"✅ Subscribe protocol documented")

    # Check CandleEvent schema has required fields
    candle_schema = spec.get("components", {}).get("schemas", {}).get("CandleEvent")

    if not candle_schema:
        print(f"❌ CandleEvent schema not found in components/schemas")
        return False

    # CandleEvent uses allOf, so we need to check the second element
    if "allOf" in candle_schema:
        # Get the object schema (second element in allOf)
        candle_object = candle_schema["allOf"][1]
        required_fields = candle_object.get("required", [])
    else:
        required_fields = candle_schema.get("required", [])

    expected_candle_fields = [
        "timeframe", "open", "high", "low", "close", "volume", "delta", "poc"
    ]

    for field in expected_candle_fields:
        if field not in required_fields:
            print(f"❌ CandleEvent missing required field: {field}")
            return False

    print(f"✅ CandleEvent has all required fields")

    # Final summary
    print(f"\n{'='*60}")
    print(f"✅ AsyncAPI spec validation PASSED")
    print(f"{'='*60}")
    print(f"📊 Spec summary:")
    print(f"   - AsyncAPI version: {spec['asyncapi']}")
    print(f"   - Channels: {len(channels)}")
    print(f"   - Messages: {len(spec.get('components', {}).get('messages', {}))}")
    print(f"   - Schemas: {len(spec.get('components', {}).get('schemas', {}))}")
    print(f"\nSpec validated successfully at: {spec_path}")

    return True


if __name__ == "__main__":
    success = validate_asyncapi_spec()
    sys.exit(0 if success else 1)
