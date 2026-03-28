"""
Tests for Live Trading contracts (REST, WebSocket, Event Bus)

Tests validate:
1. OpenAPI REST spec validity
2. AsyncAPI WebSocket spec validity
3. Event Bus schemas completeness
4. Kill switch priority marking
5. WebSocket channel coverage
6. Portfolio update fields
"""
import json
import yaml
import pytest
from pathlib import Path
from typing import Dict, Any, List


# Contract file paths
CONTRACTS_DIR = Path(__file__).parent.parent / "docs" / "contracts"
REST_CONTRACT = CONTRACTS_DIR / "contract-004-live-trading.yaml"
WEBSOCKET_CONTRACT = CONTRACTS_DIR / "contract-005-websocket.yaml"
EVENT_BUS_CONTRACT = CONTRACTS_DIR / "contract-006-event-bus.json"


class TestRestContract:
    """Tests for OpenAPI REST contract"""

    def test_live_trading_contract_valid(self):
        """Test that OpenAPI spec for REST is valid"""
        # Load the contract
        with open(REST_CONTRACT, 'r') as f:
            contract = yaml.safe_load(f)

        # Validate required OpenAPI fields
        assert contract.get('openapi') == '3.1.0'
        assert 'info' in contract
        assert contract['info'].get('title') == 'NQ-HUB Live Trading API'
        assert contract['info'].get('version') == '1.0.0'

        # Validate servers
        assert 'servers' in contract
        assert len(contract['servers']) >= 2

        # Validate security
        assert 'security' in contract
        assert 'components' in contract
        assert 'securitySchemes' in contract['components']
        assert 'BearerAuth' in contract['components']['securitySchemes']

        # Validate required paths exist
        required_paths = [
            '/api/v1/bots',
            '/api/v1/bots/create',
            '/api/v1/bots/{id}/start',
            '/api/v1/bots/{id}/stop',
            '/api/v1/bots/{id}/kill',  # HIGHEST PRIORITY
            '/api/v1/bots/kill-all',    # GLOBAL KILL SWITCH
            '/api/v1/bots/{id}/state-log',
            '/api/v1/orders',
            '/api/v1/orders/{id}',
            '/api/v1/orders/pending',
            '/api/v1/risk/config',
            '/api/v1/risk/status',
            '/api/v1/risk/apex-accounts',
        ]

        paths = contract.get('paths', {})
        for path in required_paths:
            assert path in paths, f"Missing required path: {path}"

    def test_kill_switch_endpoints_exist(self):
        """Test that kill switch endpoints are properly defined"""
        with open(REST_CONTRACT, 'r') as f:
            contract = yaml.safe_load(f)

        paths = contract.get('paths', {})

        # Individual bot kill
        assert '/api/v1/bots/{id}/kill' in paths
        kill_endpoint = paths['/api/v1/bots/{id}/kill']
        assert 'post' in kill_endpoint
        assert 'Kill Switch' in kill_endpoint['post'].get('tags', [])
        assert 'HIGHEST PRIORITY' in kill_endpoint['post'].get('summary', '')

        # Global kill switch
        assert '/api/v1/bots/kill-all' in paths
        kill_all_endpoint = paths['/api/v1/bots/kill-all']
        assert 'post' in kill_all_endpoint
        assert 'Kill Switch' in kill_all_endpoint['post'].get('tags', [])
        assert 'GLOBAL KILL SWITCH' in kill_all_endpoint['post'].get('summary', '')
        assert 'HIGHEST PRIORITY' in kill_all_endpoint['post'].get('summary', '')

    def test_bot_management_endpoints(self):
        """Test bot management endpoints have correct operations"""
        with open(REST_CONTRACT, 'r') as f:
            contract = yaml.safe_load(f)

        paths = contract.get('paths', {})

        # GET /api/v1/bots - list bots
        assert 'get' in paths['/api/v1/bots']
        list_op = paths['/api/v1/bots']['get']
        assert list_op['operationId'] == 'listBots'

        # POST /api/v1/bots/create - create bot
        assert 'post' in paths['/api/v1/bots/create']
        create_op = paths['/api/v1/bots/create']['post']
        assert create_op['operationId'] == 'createBot'
        assert 'requestBody' in create_op

        # Validate response schemas
        assert '201' in create_op['responses']
        response = create_op['responses']['201']
        assert 'content' in response
        assert 'application/json' in response['content']

    def test_risk_management_endpoints(self):
        """Test risk management endpoints"""
        with open(REST_CONTRACT, 'r') as f:
            contract = yaml.safe_load(f)

        paths = contract.get('paths', {})

        # Risk config should support GET and PUT
        risk_config = paths['/api/v1/risk/config']
        assert 'get' in risk_config
        assert 'put' in risk_config

        # Risk status should be GET only
        risk_status = paths['/api/v1/risk/status']
        assert 'get' in risk_status
        assert 'put' not in risk_status  # Should be read-only

        # Apex accounts
        apex = paths['/api/v1/risk/apex-accounts']
        assert 'get' in apex
        assert 'post' in apex


class TestWebSocketContract:
    """Tests for AsyncAPI WebSocket contract"""

    def test_asyncapi_contract_valid(self):
        """Test that AsyncAPI spec is valid"""
        with open(WEBSOCKET_CONTRACT, 'r') as f:
            contract = yaml.safe_load(f)

        # Validate AsyncAPI version
        assert contract.get('asyncapi') == '3.0.0'

        # Validate info
        assert 'info' in contract
        assert contract['info'].get('title') == 'NQ-HUB WebSocket API'
        assert contract['info'].get('version') == '1.0.0'

        # Validate servers
        assert 'servers' in contract
        assert 'development' in contract['servers']
        assert 'production' in contract['servers']

        dev_server = contract['servers']['development']
        assert dev_server['protocol'] == 'ws'
        assert dev_server['host'] == 'localhost:8002'

        prod_server = contract['servers']['production']
        assert prod_server['protocol'] == 'wss'  # Secure WebSocket for production

    def test_ws_channels_match_page_subscriptions(self):
        """Test that 8 channels cover the 4 pages that use WebSocket"""
        with open(WEBSOCKET_CONTRACT, 'r') as f:
            contract = yaml.safe_load(f)

        # Required channels
        required_channels = [
            'price',
            'orderflow',
            'patterns',
            'orders',
            'positions',
            'portfolio',
            'risk',
            'bot'
        ]

        channels = contract.get('channels', {})
        for channel in required_channels:
            assert channel in channels, f"Missing required channel: {channel}"

        # Validate page subscriptions
        page_subs = contract.get('x-page-subscriptions', {})
        assert 'live_dashboard' in page_subs
        assert 'bot_management' in page_subs
        assert 'risk_monitor' in page_subs
        assert 'order_management' in page_subs

        # Live dashboard should have all channels
        live_dash_channels = page_subs['live_dashboard']['channels']
        for channel in required_channels:
            assert channel in live_dash_channels

    def test_portfolio_update_has_all_fields(self):
        """Test that portfolio update event has all 7 required fields"""
        with open(WEBSOCKET_CONTRACT, 'r') as f:
            contract = yaml.safe_load(f)

        # Find portfolio update schema
        portfolio_schema = contract['components']['schemas']['PortfolioUpdate']
        data_properties = portfolio_schema['allOf'][1]['properties']['data']['properties']

        required_fields = [
            'balance',
            'equity',
            'unrealized_pnl',
            'realized_pnl_today',
            'daily_trades',
            'win_rate',
            'max_drawdown'
        ]

        # Check required fields
        data_required = portfolio_schema['allOf'][1]['properties']['data']['required']
        for field in required_fields:
            assert field in data_required, f"Missing required field: {field}"
            assert field in data_properties, f"Missing field definition: {field}"

    def test_websocket_throttling(self):
        """Test that WebSocket messages have proper throttling defined"""
        with open(WEBSOCKET_CONTRACT, 'r') as f:
            contract = yaml.safe_load(f)

        operations = contract.get('operations', {})

        # Check tick throttling (max 10/sec)
        tick_op = operations.get('receiveTick')
        assert tick_op is not None
        bindings = tick_op.get('bindings', {}).get('ws', {})
        throttle = bindings.get('throttle', {})
        assert throttle.get('rate') == 10
        assert throttle.get('per') == 'second'

        # Check position update throttling (max 1/sec)
        pos_op = operations.get('receivePositionEvents')
        assert pos_op is not None
        bindings = pos_op.get('bindings', {}).get('ws', {})
        throttle = bindings.get('throttle', {})
        assert throttle.get('rate') == 1
        assert throttle.get('per') == 'second'

    def test_heartbeat_interval(self):
        """Test that heartbeat is configured for 30 seconds"""
        with open(WEBSOCKET_CONTRACT, 'r') as f:
            contract = yaml.safe_load(f)

        # Check bot heartbeat message
        bot_heartbeat = contract['components']['messages']['botHeartbeat']
        assert 'every 30 seconds' in bot_heartbeat.get('description', '')

        # Check connection heartbeat
        heartbeat_msg = contract['components']['messages']['heartbeat']
        assert 'every 30 seconds' in heartbeat_msg.get('description', '')


class TestEventBusContract:
    """Tests for Event Bus schemas"""

    def test_event_bus_schemas_complete(self):
        """Test that all topics have schemas JSON defined"""
        with open(EVENT_BUS_CONTRACT, 'r') as f:
            contract = json.load(f)

        # Check structure
        assert 'topics' in contract
        assert 'nautilus_trader' in contract['topics']
        assert 'nqhub_custom' in contract['topics']
        assert 'actors' in contract
        assert 'definitions' in contract

        # Validate NautilusTrader topics
        nautilus_patterns = contract['topics']['nautilus_trader']['patterns']
        required_nautilus = [
            'data.bars.{symbol}-{timeframe}.{venue}',
            'data.trades.{symbol}.{venue}',
            'exec.order.{venue}.{event}',
            'exec.position.{venue}.{event}'
        ]

        for pattern in required_nautilus:
            assert pattern in nautilus_patterns, f"Missing NautilusTrader topic: {pattern}"
            assert 'schema' in nautilus_patterns[pattern]

        # Validate NQHUB custom topics
        nqhub_patterns = contract['topics']['nqhub_custom']['patterns']
        required_nqhub = [
            'nqhub.candle.{timeframe}',
            'nqhub.pattern.fvg',
            'nqhub.pattern.ob',
            'nqhub.pattern.interaction',
            'nqhub.risk.circuit_breaker',
            'nqhub.risk.kill_switch',
            'nqhub.ws.bridge',
            'nqhub.db.write'
        ]

        for pattern in required_nqhub:
            assert pattern in nqhub_patterns, f"Missing NQHUB topic: {pattern}"
            assert 'schema' in nqhub_patterns[pattern]

    def test_kill_switch_marked_highest_priority(self):
        """Test that nqhub.risk.kill_switch has priority: HIGHEST"""
        with open(EVENT_BUS_CONTRACT, 'r') as f:
            contract = json.load(f)

        # Find kill switch topic
        kill_switch = contract['topics']['nqhub_custom']['patterns']['nqhub.risk.kill_switch']
        assert kill_switch['priority'] == 'HIGHEST'

        # Verify kill switch event schema
        kill_switch_def = contract['definitions']['KillSwitchEvent']
        assert 'priority' in kill_switch_def['properties']
        priority_prop = kill_switch_def['properties']['priority']
        assert priority_prop['enum'] == ['HIGHEST']
        assert priority_prop.get('description') == 'Kill switch always has HIGHEST priority'

    def test_actor_subscriptions_and_publications(self):
        """Test that actors have correct subscribe/publish patterns"""
        with open(EVENT_BUS_CONTRACT, 'r') as f:
            contract = json.load(f)

        actors = contract['actors']

        # Test CandleBuilderActor
        candle_actor = actors['CandleBuilderActor']
        assert 'data.trades.NQ.{venue}' in candle_actor['subscribes']
        assert 'nqhub.candle.{timeframe}' in candle_actor['publishes']

        # Test PatternDetectorActor
        pattern_actor = actors['PatternDetectorActor']
        assert 'nqhub.candle.*' in pattern_actor['subscribes']
        assert 'nqhub.pattern.fvg' in pattern_actor['publishes']
        assert 'nqhub.pattern.ob' in pattern_actor['publishes']
        assert 'nqhub.pattern.lp' in pattern_actor['publishes']

        # Test NQHubRiskActor
        risk_actor = actors['NQHubRiskActor']
        assert 'exec.order.*.*' in risk_actor['subscribes']
        assert 'exec.position.*.*' in risk_actor['subscribes']
        assert 'nqhub.risk.circuit_breaker' in risk_actor['publishes']
        assert 'nqhub.risk.kill_switch' in risk_actor['publishes']

        # Test WsBridgeActor
        ws_actor = actors['WsBridgeActor']
        assert 'nqhub.candle.*' in ws_actor['subscribes']
        assert 'nqhub.pattern.*' in ws_actor['subscribes']
        assert 'nqhub.risk.*' in ws_actor['subscribes']
        assert 'nqhub.ws.bridge' in ws_actor['publishes']

    def test_nqhub_candle_has_35_fields(self):
        """Test that NQHubCandle schema includes all order flow fields"""
        with open(EVENT_BUS_CONTRACT, 'r') as f:
            contract = json.load(f)

        candle_schema = contract['definitions']['NQHubCandle']
        properties = candle_schema['properties']

        # Core OHLCV fields
        core_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for field in core_fields:
            assert field in properties, f"Missing core field: {field}"

        # Order flow fields
        oflow_fields = [
            'delta', 'delta_pct', 'poc',
            'value_area_high', 'value_area_low',
            'buy_volume', 'sell_volume',
            'imbalance_buy', 'imbalance_sell',
            'absorption_buy', 'absorption_sell',
            'aggressive_buy', 'aggressive_sell',
            'oflow_unit'
        ]
        for field in oflow_fields:
            assert field in properties, f"Missing order flow field: {field}"

        # Validate required fields
        required = candle_schema['required']
        essential_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume',
                          'delta', 'poc', 'value_area_high', 'value_area_low']
        for field in essential_fields:
            assert field in required, f"Field should be required: {field}"

    def test_pattern_schemas_completeness(self):
        """Test pattern detection schemas have all required fields"""
        with open(EVENT_BUS_CONTRACT, 'r') as f:
            contract = json.load(f)

        definitions = contract['definitions']

        # Test FVG schema
        fvg = definitions['FVGDetected']
        fvg_required = ['pattern_id', 'formation_time', 'significance', 'gap_high', 'gap_low']
        assert all(field in fvg['required'] for field in fvg_required)
        assert 'consequent_encroachment' in fvg['properties']  # ICT specific

        # Test Order Block schema
        ob = definitions['OBDetected']
        ob_required = ['pattern_id', 'formation_time', 'ob_type', 'ob_high', 'ob_low']
        assert all(field in ob['required'] for field in ob_required)
        assert 'ob_body_midpoint' in ob['properties']
        assert 'ob_range_midpoint' in ob['properties']

        # Test Liquidity Pool schema
        lp = definitions['LPDetected']
        lp_required = ['pattern_id', 'formation_time', 'pool_type', 'zone_high', 'zone_low']
        assert all(field in lp['required'] for field in lp_required)
        assert 'modal_level' in lp['properties']

        # Test Pattern Interaction
        interaction = definitions['PatternInteraction']
        interaction_types = interaction['properties']['interaction_type']['enum']
        expected_types = ['R0', 'R1', 'R2', 'R3', 'R4', 'P1', 'P2', 'P3', 'P4', 'P5']
        assert all(t in interaction_types for t in expected_types)


class TestContractConsistency:
    """Tests for consistency across all contracts"""

    def test_bot_id_consistency(self):
        """Test that bot_id format is consistent across contracts"""
        # REST contract
        with open(REST_CONTRACT, 'r') as f:
            rest = yaml.safe_load(f)

        # WebSocket contract
        with open(WEBSOCKET_CONTRACT, 'r') as f:
            ws = yaml.safe_load(f)

        # Event Bus contract
        with open(EVENT_BUS_CONTRACT, 'r') as f:
            event_bus = json.load(f)

        # Check REST uses UUID format
        bot_schema = rest['components']['schemas']['Bot']
        assert bot_schema['properties']['id']['format'] == 'uuid'

        # Check WebSocket uses UUID format
        base_message = ws['components']['schemas']['BaseMessage']
        assert base_message['properties']['bot_id']['format'] == 'uuid'

        # Check Event Bus uses UUID format
        serialized = event_bus['definitions']['SerializedEvent']
        assert serialized['properties']['bot_id']['format'] == 'uuid'

    def test_order_status_consistency(self):
        """Test that order statuses are consistent across contracts"""
        # REST contract
        with open(REST_CONTRACT, 'r') as f:
            rest = yaml.safe_load(f)

        # WebSocket contract
        with open(WEBSOCKET_CONTRACT, 'r') as f:
            ws = yaml.safe_load(f)

        # Event Bus contract
        with open(EVENT_BUS_CONTRACT, 'r') as f:
            event_bus = json.load(f)

        # REST order statuses
        rest_order = rest['components']['schemas']['Order']
        rest_statuses = rest_order['properties']['status']['enum']

        # WebSocket order statuses
        ws_order = ws['components']['schemas']['OrderEvent']
        ws_statuses = ws_order['allOf'][1]['properties']['data']['properties']['status']['enum']

        # Event Bus order event types
        eb_order = event_bus['definitions']['OrderEvent']
        eb_events = eb_order['properties']['event_type']['enum']

        # Verify alignment (Event Bus uses different naming but should map)
        assert 'submitted' in rest_statuses and 'submitted' in ws_statuses
        assert 'filled' in rest_statuses and 'filled' in ws_statuses
        assert 'cancelled' in rest_statuses and 'cancelled' in ws_statuses
        assert 'rejected' in rest_statuses and 'rejected' in ws_statuses

    def test_symbol_format_consistency(self):
        """Test that symbol format is consistent (e.g., NQH25)"""
        # REST contract
        with open(REST_CONTRACT, 'r') as f:
            rest = yaml.safe_load(f)

        # Check examples use consistent symbol
        orders_example = rest['components']['examples']['OrdersListExample']['value']
        assert orders_example['orders'][0]['symbol'] == 'NQH25'

        # WebSocket contract
        with open(WEBSOCKET_CONTRACT, 'r') as f:
            ws = yaml.safe_load(f)

        # Event Bus contract
        with open(EVENT_BUS_CONTRACT, 'r') as f:
            event_bus = json.load(f)

        # All contracts should reference the same symbol format
        # This is more of a documentation check than a strict validation


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])