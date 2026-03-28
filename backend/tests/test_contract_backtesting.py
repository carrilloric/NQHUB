"""
Tests for Strategy & Backtesting OpenAPI Contract
Validates contract-003-backtesting.yaml
"""

import pytest
import yaml
import json
from pathlib import Path
from typing import Dict, Any
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

CONTRACT_FILE = Path(__file__).parent.parent / "docs" / "contracts" / "contract-003-backtesting.yaml"


class TestBacktestingContract:
    """Test suite for Strategy & Backtesting OpenAPI specification."""

    @pytest.fixture
    def openapi_spec(self) -> Dict[str, Any]:
        """Load and parse the OpenAPI specification."""
        with open(CONTRACT_FILE, 'r') as f:
            return yaml.safe_load(f)

    def test_contract_003_valid_openapi(self, openapi_spec):
        """Test that the spec is valid OpenAPI 3.1."""
        assert openapi_spec is not None, "OpenAPI spec should load successfully"
        assert 'openapi' in openapi_spec, "Must have openapi version"
        assert openapi_spec['openapi'].startswith('3.1'), "Must be OpenAPI 3.1"

        # Check required top-level fields
        assert 'info' in openapi_spec, "Must have info section"
        assert 'paths' in openapi_spec, "Must have paths section"
        assert 'components' in openapi_spec, "Must have components section"

        # Check info section
        assert 'title' in openapi_spec['info'], "Info must have title"
        assert 'version' in openapi_spec['info'], "Info must have version"
        assert 'description' in openapi_spec['info'], "Info must have description"

    def test_backtest_run_schema_has_config(self, openapi_spec):
        """Test that backtest run request body has config with dates."""
        backtest_run = openapi_spec['paths']['/api/v1/backtest/run']['post']

        assert 'requestBody' in backtest_run, "Backtest run must have request body"
        assert backtest_run['requestBody']['required'] is True, "Request body must be required"

        # Get the schema
        content = backtest_run['requestBody']['content']['application/json']['schema']
        assert 'required' in content, "Request schema must have required fields"
        assert 'config' in content['required'], "config must be required"

        # Check properties
        assert 'config' in content['properties'], "Request must have config property"

        # Check that config references the BacktestConfig schema
        assert '$ref' in content['properties']['config'], "config should reference BacktestConfig schema"
        assert content['properties']['config']['$ref'] == '#/components/schemas/BacktestConfig'

        # Check BacktestConfig schema
        config_schema = openapi_spec['components']['schemas']['BacktestConfig']
        assert 'start' in config_schema['required'], "BacktestConfig must require start date"
        assert 'end' in config_schema['required'], "BacktestConfig must require end date"
        assert 'timeframe' in config_schema['required'], "BacktestConfig must require timeframe"

        # Check date format
        assert config_schema['properties']['start']['format'] == 'date', "start must be date format"
        assert config_schema['properties']['end']['format'] == 'date', "end must be date format"

    def test_screener_supports_all_metrics(self, openapi_spec):
        """Test that screener accepts order_by for sharpe, sortino, dd, win_rate."""
        screener_endpoint = openapi_spec['paths']['/api/v1/backtest/screener']['get']

        assert 'parameters' in screener_endpoint, "Screener must have parameters"

        # Find order_by parameter
        order_by_param = next(
            (p for p in screener_endpoint['parameters'] if p['name'] == 'order_by'),
            None
        )

        assert order_by_param is not None, "Screener must have order_by parameter"
        assert 'enum' in order_by_param['schema'], "order_by must have enum values"

        # Check that all required metrics are supported
        required_metrics = ['sharpe', 'sortino', 'max_dd', 'win_rate']
        actual_metrics = order_by_param['schema']['enum']

        for metric in required_metrics:
            assert metric in actual_metrics, f"order_by must support metric: {metric}"

    def test_equity_curve_in_results(self, openapi_spec):
        """Test that GET /backtest/runs/{id} includes equity_curve array."""
        run_detail_endpoint = openapi_spec['paths']['/api/v1/backtest/runs/{id}']['get']

        # Check response schema
        response_schema = run_detail_endpoint['responses']['200']['content']['application/json']['schema']
        assert '$ref' in response_schema, "Response should reference BacktestRunDetail schema"

        # Check BacktestRunDetail schema
        run_detail = openapi_spec['components']['schemas']['BacktestRunDetail']
        assert 'equity_curve' in run_detail['properties'], "BacktestRunDetail must have equity_curve"

        # Verify equity_curve structure
        equity_curve = run_detail['properties']['equity_curve']
        assert equity_curve['type'] == 'array', "equity_curve must be an array"
        assert 'items' in equity_curve, "equity_curve must have items definition"

        # Check equity curve item structure
        item = equity_curve['items']
        assert 'date' in item['properties'], "equity_curve item must have date"
        assert 'equity' in item['properties'], "equity_curve item must have equity"
        assert 'date' in item['required'], "date must be required in equity_curve item"
        assert 'equity' in item['required'], "equity must be required in equity_curve item"

    def test_all_strategy_endpoints_defined(self, openapi_spec):
        """Test that all required strategy endpoints are defined."""
        paths = openapi_spec['paths']

        required_endpoints = [
            '/api/v1/backtest/strategies',
            '/api/v1/strategies/validate',
            '/api/v1/strategies/save',
            '/api/v1/strategies/{id}/source'
        ]

        for endpoint in required_endpoints:
            assert endpoint in paths, f"Missing required strategy endpoint: {endpoint}"

    def test_all_backtest_endpoints_defined(self, openapi_spec):
        """Test that all required backtest endpoints are defined."""
        paths = openapi_spec['paths']

        required_endpoints = [
            '/api/v1/backtest/run',
            '/api/v1/backtest/results/import',
            '/api/v1/backtest/runs',
            '/api/v1/backtest/runs/{id}',
            '/api/v1/backtest/screener',
            '/api/v1/backtest/optimize'
        ]

        for endpoint in required_endpoints:
            assert endpoint in paths, f"Missing required backtest endpoint: {endpoint}"

    def test_all_approval_endpoints_defined(self, openapi_spec):
        """Test that all required approval endpoints are defined."""
        paths = openapi_spec['paths']

        required_endpoints = [
            '/api/v1/approval/checklist/{strategy_id}',
            '/api/v1/approval/approve'
        ]

        for endpoint in required_endpoints:
            assert endpoint in paths, f"Missing required approval endpoint: {endpoint}"

    def test_strategy_validation_response_schema(self, openapi_spec):
        """Test strategy validation response has all required fields."""
        validate_endpoint = openapi_spec['paths']['/api/v1/strategies/validate']['post']
        response = validate_endpoint['responses']['200']['content']['application/json']['schema']

        # Check reference
        assert '$ref' in response, "Response should reference ValidationResult schema"

        # Check ValidationResult schema
        validation_result = openapi_spec['components']['schemas']['ValidationResult']

        required_fields = ['valid', 'errors', 'warnings']
        for field in required_fields:
            assert field in validation_result['required'], f"ValidationResult must require: {field}"
            assert field in validation_result['properties'], f"ValidationResult must have property: {field}"

        # Check optional fields that aid detection
        optional_fields = ['detected_name', 'detected_type', 'required_features']
        for field in optional_fields:
            assert field in validation_result['properties'], f"ValidationResult should have property: {field}"

    def test_backtest_results_schema(self, openapi_spec):
        """Test BacktestResults schema has all key metrics."""
        results_schema = openapi_spec['components']['schemas']['BacktestResults']

        # Check required metrics
        required_metrics = ['sharpe', 'sortino', 'max_dd', 'win_rate']
        for metric in required_metrics:
            assert metric in results_schema['required'], f"BacktestResults must require: {metric}"
            assert metric in results_schema['properties'], f"BacktestResults must have property: {metric}"

        # Check optional but important metrics
        optional_metrics = ['profit_factor', 'total_trades', 'net_profit', 'avg_win', 'avg_loss']
        for metric in optional_metrics:
            assert metric in results_schema['properties'], f"BacktestResults should have property: {metric}"

    def test_strategy_status_enum(self, openapi_spec):
        """Test strategy status has correct enum values."""
        # Check in StrategyListItem schema
        strategy_item = openapi_spec['components']['schemas']['StrategyListItem']
        status = strategy_item['properties']['status']

        assert 'enum' in status, "status must have enum values"
        expected_statuses = ['draft', 'validated', 'approved', 'deprecated']
        actual_statuses = status['enum']

        assert set(actual_statuses) == set(expected_statuses), \
            f"Strategy status must have: {expected_statuses}"

    def test_backtest_run_status_enum(self, openapi_spec):
        """Test backtest run status has correct enum values."""
        # Check in BacktestRunSummary schema
        run_summary = openapi_spec['components']['schemas']['BacktestRunSummary']
        status = run_summary['properties']['status']

        assert 'enum' in status, "status must have enum values"
        expected_statuses = ['queued', 'running', 'completed', 'failed', 'imported']
        actual_statuses = status['enum']

        assert set(actual_statuses) == set(expected_statuses), \
            f"Backtest run status must have: {expected_statuses}"

    def test_optimization_method_enum(self, openapi_spec):
        """Test optimization endpoint has correct method enum."""
        optimize_endpoint = openapi_spec['paths']['/api/v1/backtest/optimize']['post']
        request_body = optimize_endpoint['requestBody']['content']['application/json']['schema']

        method = request_body['properties']['method']
        assert 'enum' in method, "method must have enum values"

        expected_methods = ['grid', 'walk_forward']
        actual_methods = method['enum']

        assert set(actual_methods) == set(expected_methods), \
            f"Optimization methods must be: {expected_methods}"

    def test_approval_checklist_structure(self, openapi_spec):
        """Test approval checklist response structure."""
        checklist_endpoint = openapi_spec['paths']['/api/v1/approval/checklist/{strategy_id}']['get']
        response = checklist_endpoint['responses']['200']['content']['application/json']['schema']

        # Check required fields
        assert 'checks' in response['properties'], "Response must have checks array"
        assert 'overall_passed' in response['properties'], "Response must have overall_passed"

        # Verify ApprovalCheck schema
        check_schema = openapi_spec['components']['schemas']['ApprovalCheck']

        required_fields = ['name', 'passed']
        for field in required_fields:
            assert field in check_schema['required'], f"ApprovalCheck must require: {field}"
            assert field in check_schema['properties'], f"ApprovalCheck must have property: {field}"

        # Check optional fields for threshold comparison
        optional_fields = ['value', 'threshold']
        for field in optional_fields:
            assert field in check_schema['properties'], f"ApprovalCheck should have property: {field}"

    def test_import_results_source_enum(self, openapi_spec):
        """Test import results has correct source enum."""
        import_endpoint = openapi_spec['paths']['/api/v1/backtest/results/import']['post']
        request_body = import_endpoint['requestBody']['content']['application/json']['schema']

        source = request_body['properties']['source']
        assert 'enum' in source, "source must have enum values"

        expected_sources = ['notebook', 'external', 'manual']
        actual_sources = source['enum']

        # notebook must be supported for Jupyter integration
        assert 'notebook' in actual_sources, "source enum must include 'notebook'"

    def test_security_scheme_defined(self, openapi_spec):
        """Test that Bearer authentication is defined."""
        assert 'securitySchemes' in openapi_spec['components'], \
            "Components must have securitySchemes"

        assert 'BearerAuth' in openapi_spec['components']['securitySchemes'], \
            "Must define BearerAuth security scheme"

        bearer = openapi_spec['components']['securitySchemes']['BearerAuth']
        assert bearer['type'] == 'http', "BearerAuth must be http type"
        assert bearer['scheme'] == 'bearer', "Must use bearer scheme"
        assert bearer['bearerFormat'] == 'JWT', "Must use JWT format"

    def test_error_response_schema(self, openapi_spec):
        """Test error response schema is properly defined."""
        error_schema = openapi_spec['components']['schemas']['ErrorResponse']

        required_fields = ['error', 'message']
        for field in required_fields:
            assert field in error_schema['required'], f"ErrorResponse must require: {field}"
            assert field in error_schema['properties'], f"ErrorResponse must have property: {field}"

        # Check optional details field
        assert 'details' in error_schema['properties'], "ErrorResponse should have details"

    def test_common_responses_defined(self, openapi_spec):
        """Test common response types are defined."""
        responses = openapi_spec['components']['responses']

        expected_responses = ['BadRequest', 'Unauthorized', 'NotFound', 'Conflict', 'InternalServerError']
        for response in expected_responses:
            assert response in responses, f"Must define common response: {response}"

    def test_backtest_config_defaults(self, openapi_spec):
        """Test BacktestConfig has sensible defaults."""
        config_schema = openapi_spec['components']['schemas']['BacktestConfig']

        # Check commission default
        commission = config_schema['properties']['commission']
        assert 'default' in commission, "commission should have a default"
        assert commission['default'] == 0.0002, "commission default should be 0.0002 (2 bps)"

        # Check slippage default
        slippage = config_schema['properties']['slippage']
        assert 'default' in slippage, "slippage should have a default"
        assert slippage['default'] == 1, "slippage default should be 1 tick"

    def test_timeframe_enum_values(self, openapi_spec):
        """Test timeframe enum has correct values."""
        config_schema = openapi_spec['components']['schemas']['BacktestConfig']
        timeframe = config_schema['properties']['timeframe']

        assert 'enum' in timeframe, "timeframe must have enum values"
        expected_timeframes = ['1min', '5min', '15min', '30min', '1hour', '4hour', '1day']
        actual_timeframes = timeframe['enum']

        assert set(actual_timeframes) == set(expected_timeframes), \
            f"Timeframe must have: {expected_timeframes}"

    def test_strategy_type_enum(self, openapi_spec):
        """Test strategy type enum values."""
        strategy_item = openapi_spec['components']['schemas']['StrategyListItem']
        strategy_type = strategy_item['properties']['type']

        assert 'enum' in strategy_type, "type must have enum values"
        expected_types = ['momentum', 'mean_reversion', 'trend_following', 'breakout', 'scalping']
        actual_types = strategy_type['enum']

        assert set(actual_types) == set(expected_types), \
            f"Strategy types must be: {expected_types}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])