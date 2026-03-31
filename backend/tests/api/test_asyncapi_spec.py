"""
Tests for AsyncAPI WebSocket Spec (AUT-365)

Verifies that the AsyncAPI 2.6.0 spec is properly formatted and includes
all required channels, schemas, and documentation.

Tests:
1. test_spec_has_8_channels
2. test_all_channels_have_descriptions
3. test_candle_event_schema_has_required_fields
4. test_risk_channel_documented_as_priority
5. test_subscribe_protocol_documented
6. test_spec_is_valid_yaml
"""
import pytest
import yaml
from pathlib import Path


# ============= Fixtures =============

@pytest.fixture
def spec_path():
    """Path to AsyncAPI spec file"""
    project_root = Path(__file__).parent.parent.parent.parent
    return project_root / "docs" / "api" / "websocket.yaml"


@pytest.fixture
def asyncapi_spec(spec_path):
    """Load AsyncAPI spec from YAML"""
    with open(spec_path, "r") as f:
        return yaml.safe_load(f)


# ============= Test 1: Spec Has 8 Channels =============

def test_spec_has_8_channels(asyncapi_spec):
    """
    Test that AsyncAPI spec includes all 8 required channels.

    Required channels:
    1. price - OHLCV candles
    2. orderflow - Delta and POC
    3. patterns - ICT patterns (FVG, OB, LP, BB)
    4. orders - Order status changes
    5. positions - Position updates
    6. portfolio - Portfolio snapshots
    7. risk - Risk checks and kill switch
    8. bot - Bot status changes
    """
    channels = asyncapi_spec.get("channels", {})

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

    # Verify exactly 8 channels
    assert len(channels) == 8, \
        f"Expected exactly 8 channels, found {len(channels)}: {list(channels.keys())}"

    # Verify all required channels are present
    for channel_name in required_channels:
        assert channel_name in channels, \
            f"Required channel '{channel_name}' not found in spec"

    # Verify each channel has a subscribe operation
    for channel_name, channel_spec in channels.items():
        assert "subscribe" in channel_spec, \
            f"Channel '{channel_name}' must have a subscribe operation"


# ============= Test 2: All Channels Have Descriptions =============

def test_all_channels_have_descriptions(asyncapi_spec):
    """
    Test that all channels have non-empty descriptions.

    Descriptions should explain:
    - What the channel does
    - Update frequency
    - Channel format (if applicable)
    - Example channel names (if multiple variants)
    """
    channels = asyncapi_spec.get("channels", {})

    for channel_name, channel_spec in channels.items():
        assert "description" in channel_spec, \
            f"Channel '{channel_name}' is missing a description"

        description = channel_spec["description"]
        assert description and description.strip(), \
            f"Channel '{channel_name}' has an empty description"

        # Verify description is reasonably detailed (at least 20 characters)
        assert len(description.strip()) >= 20, \
            f"Channel '{channel_name}' description is too short: {description}"


# ============= Test 3: CandleEvent Schema Has Required Fields =============

def test_candle_event_schema_has_required_fields(asyncapi_spec):
    """
    Test that CandleEvent schema has all required OHLCV fields.

    Required fields (from AUT-366 schemas):
    - channel: Redis pub/sub channel name
    - ts: Timestamp in UTC
    - bot_id: Bot identifier
    - timeframe: Candle timeframe
    - open: Open price
    - high: High price
    - low: Low price
    - close: Close price
    - volume: Total volume
    - delta: Buy volume - Sell volume
    - poc: Point of Control price
    """
    schemas = asyncapi_spec.get("components", {}).get("schemas", {})

    assert "CandleEvent" in schemas, \
        "CandleEvent schema not found in components/schemas"

    candle_schema = schemas["CandleEvent"]

    # CandleEvent uses allOf (BaseEvent + candle-specific fields)
    assert "allOf" in candle_schema, \
        "CandleEvent should use allOf to extend BaseEvent"

    # Get the candle-specific schema (second element in allOf)
    candle_object = candle_schema["allOf"][1]

    assert "required" in candle_object, \
        "CandleEvent schema must have required fields"

    required_fields = candle_object["required"]

    # Verify all candle-specific fields are required
    expected_fields = [
        "timeframe",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "delta",
        "poc"
    ]

    for field in expected_fields:
        assert field in required_fields, \
            f"CandleEvent missing required field: {field}"

    # Verify properties exist
    properties = candle_object.get("properties", {})

    for field in expected_fields:
        assert field in properties, \
            f"CandleEvent missing property definition for: {field}"

    # Verify specific field types
    assert properties["timeframe"]["type"] == "string", \
        "timeframe must be a string"

    assert properties["open"]["type"] == "number", \
        "open must be a number"

    assert properties["volume"]["type"] == "integer", \
        "volume must be an integer"

    assert properties["delta"]["type"] == "integer", \
        "delta must be an integer"


# ============= Test 4: Risk Channel Documented As Priority =============

def test_risk_channel_documented_as_priority(asyncapi_spec):
    """
    Test that risk channel is documented with maximum priority note.

    The risk channel handles:
    - Risk check events (pre-trade validation)
    - Kill switch events (emergency shutdown)

    This channel MUST be documented as HIGHEST PRIORITY because:
    - Kill switch events are critical safety mechanisms
    - Frontend must process risk events before other channels
    - Can trigger immediate position closure and order cancellation
    """
    channels = asyncapi_spec.get("channels", {})

    assert "risk" in channels, \
        "Risk channel not found in spec"

    risk_channel = channels["risk"]
    description = risk_channel.get("description", "")

    # Verify priority is mentioned in description
    priority_keywords = [
        "HIGHEST PRIORITY",
        "maximum priority",
        "CRITICAL PRIORITY",
        "top priority"
    ]

    priority_mentioned = any(
        keyword.lower() in description.lower()
        for keyword in priority_keywords
    )

    assert priority_mentioned, \
        f"Risk channel description must mention priority (expected one of: {priority_keywords}). " \
        f"Got: {description[:100]}..."

    # Verify description mentions kill switch
    assert "kill switch" in description.lower(), \
        "Risk channel description must mention kill switch"

    # Verify description has a warning or critical note
    critical_indicators = ["⚠️", "CRITICAL", "WARNING", "EMERGENCY"]
    has_critical_indicator = any(
        indicator in description.upper()
        for indicator in critical_indicators
    )

    assert has_critical_indicator, \
        "Risk channel description should have a critical/warning indicator"


# ============= Test 5: Subscribe Protocol Documented =============

def test_subscribe_protocol_documented(asyncapi_spec):
    """
    Test that the subscribe/unsubscribe protocol is documented.

    The protocol should define:
    - SubscribeMessage schema
    - action field with enum: [subscribe, unsubscribe]
    - channels field with list of channel names

    This allows clients to subscribe/unsubscribe from channels dynamically.
    """
    schemas = asyncapi_spec.get("components", {}).get("schemas", {})

    assert "SubscribeMessage" in schemas, \
        "SubscribeMessage schema not found in components/schemas"

    subscribe_schema = schemas["SubscribeMessage"]

    # Verify required fields
    assert "required" in subscribe_schema, \
        "SubscribeMessage must have required fields"

    required_fields = subscribe_schema["required"]
    assert "action" in required_fields, \
        "SubscribeMessage must require 'action' field"

    assert "channels" in required_fields, \
        "SubscribeMessage must require 'channels' field"

    # Verify properties
    properties = subscribe_schema.get("properties", {})

    assert "action" in properties, \
        "SubscribeMessage must have 'action' property"

    assert "channels" in properties, \
        "SubscribeMessage must have 'channels' property"

    # Verify action enum
    action_property = properties["action"]
    assert "enum" in action_property, \
        "action property must have enum constraint"

    action_enum = action_property["enum"]
    assert "subscribe" in action_enum, \
        "action enum must include 'subscribe'"

    assert "unsubscribe" in action_enum, \
        "action enum must include 'unsubscribe'"

    # Verify channels is an array
    channels_property = properties["channels"]
    assert channels_property["type"] == "array", \
        "channels property must be an array"

    # Verify channels items have enum of valid channel names
    items = channels_property.get("items", {})
    assert "enum" in items, \
        "channels items must have enum of valid channel names"

    valid_channels = items["enum"]
    expected_channels = ["price", "orderflow", "patterns", "orders", "positions", "portfolio", "risk", "bot"]

    for channel_name in expected_channels:
        assert channel_name in valid_channels, \
            f"channels enum must include '{channel_name}'"


# ============= Test 6: Spec Is Valid YAML =============

def test_spec_is_valid_yaml(spec_path):
    """
    Test that the AsyncAPI spec is valid YAML and has correct structure.

    Verifies:
    1. File exists
    2. YAML can be parsed without errors
    3. AsyncAPI version is 2.6.0
    4. Required top-level keys are present (info, servers, channels, components)
    5. Info section has title, version, and description
    """
    # Verify file exists
    assert spec_path.exists(), \
        f"AsyncAPI spec file not found: {spec_path}"

    # Verify YAML can be parsed
    try:
        with open(spec_path, "r") as f:
            spec = yaml.safe_load(f)
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML: {e}")

    # Verify AsyncAPI version
    assert "asyncapi" in spec, \
        "Spec must have 'asyncapi' field"

    assert spec["asyncapi"] == "2.6.0", \
        f"AsyncAPI version must be 2.6.0, got: {spec['asyncapi']}"

    # Verify required top-level keys
    required_keys = ["info", "servers", "channels", "components"]

    for key in required_keys:
        assert key in spec, \
            f"Spec must have '{key}' section"

    # Verify info section
    info = spec["info"]
    assert "title" in info and info["title"], \
        "Info section must have a non-empty title"

    assert "version" in info and info["version"], \
        "Info section must have a version"

    assert "description" in info and info["description"], \
        "Info section must have a description"

    # Verify servers section has at least one server
    servers = spec["servers"]
    assert len(servers) > 0, \
        "Spec must define at least one server"

    # Verify components section has messages and schemas
    components = spec["components"]
    assert "messages" in components, \
        "Components must have 'messages' section"

    assert "schemas" in components, \
        "Components must have 'schemas' section"

    assert len(components["messages"]) > 0, \
        "Components must define at least one message"

    assert len(components["schemas"]) > 0, \
        "Components must define at least one schema"


# ============= Additional Validation Tests =============

def test_all_messages_have_payloads(asyncapi_spec):
    """
    Verify that all message definitions have payload references.
    """
    messages = asyncapi_spec.get("components", {}).get("messages", {})

    for message_name, message_spec in messages.items():
        assert "payload" in message_spec, \
            f"Message '{message_name}' must have a payload reference"


def test_all_channels_reference_valid_messages(asyncapi_spec):
    """
    Verify that all channels reference messages that exist in components.
    """
    channels = asyncapi_spec.get("channels", {})
    messages = asyncapi_spec.get("components", {}).get("messages", {})

    for channel_name, channel_spec in channels.items():
        subscribe = channel_spec.get("subscribe", {})

        # Check single message reference
        if "message" in subscribe:
            message_ref = subscribe["message"].get("$ref", "")
            message_name = message_ref.split("/")[-1]

            assert message_name in messages, \
                f"Channel '{channel_name}' references non-existent message: {message_name}"

        # Check oneOf messages (for risk channel)
        if "messages" in subscribe and "oneOf" in subscribe["messages"]:
            for message_item in subscribe["messages"]["oneOf"]:
                message_ref = message_item.get("$ref", "")
                message_name = message_ref.split("/")[-1]

                assert message_name in messages, \
                    f"Channel '{channel_name}' references non-existent message: {message_name}"


def test_base_event_schema_exists(asyncapi_spec):
    """
    Verify that BaseEvent schema exists and has required fields.

    All events should extend BaseEvent via allOf.
    """
    schemas = asyncapi_spec.get("components", {}).get("schemas", {})

    assert "BaseEvent" in schemas, \
        "BaseEvent schema must be defined in components/schemas"

    base_event = schemas["BaseEvent"]

    # Verify BaseEvent has required fields
    assert "required" in base_event, \
        "BaseEvent must have required fields"

    required_fields = base_event["required"]
    expected_base_fields = ["channel", "ts", "bot_id"]

    for field in expected_base_fields:
        assert field in required_fields, \
            f"BaseEvent missing required field: {field}"
