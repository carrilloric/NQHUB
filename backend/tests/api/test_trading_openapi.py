"""OpenAPI tests for AUT-364"""
import pytest


def test_kill_requires_reason_field():
    """KillRequest.reason must be required with no default"""
    from app.api.v1.trading.schemas import KillRequest
    
    # Try creating without reason - should fail
    with pytest.raises(Exception):
        KillRequest()
    
    # With reason should work
    kill_req = KillRequest(reason="Test reason for kill switch")
    assert kill_req.reason == "Test reason for kill switch"


def test_bot_status_includes_halt_reason():
    """BotStatusResponse must include halt_reason field"""
    from app.api.v1.trading.schemas import BotStatusResponse
    
    # Check schema has halt_reason
    assert 'halt_reason' in BotStatusResponse.model_fields
    
    # Field should be optional
    bot_status = BotStatusResponse(
        bot_id="123",
        strategy_id="456",
        status="RUNNING",
        mode="paper",
        apex_account_id="789",
        created_at="2026-03-31T10:00:00Z"
    )
    assert hasattr(bot_status, 'halt_reason')


def test_order_response_includes_bracket_role():
    """OrderResponse must include bracket_role field"""
    from app.api.v1.trading.schemas import OrderResponse
    
    assert 'bracket_role' in OrderResponse.model_fields
    
    order = OrderResponse(
        id="1",
        bot_id="2",
        order_type="LIMIT",
        bracket_role="ENTRY",
        side="BUY",
        contracts=2,
        status="FILLED",
        submitted_at="2026-03-31T10:00:00Z"
    )
    assert order.bracket_role == "ENTRY"


def test_risk_status_includes_trailing_threshold_remaining():
    """RiskStatusResponse must include trailing_threshold_remaining"""
    from app.api.v1.trading.schemas import RiskStatusResponse
    
    assert 'trailing_threshold_remaining' in RiskStatusResponse.model_fields
    
    # Check field has description
    field = RiskStatusResponse.model_fields['trailing_threshold_remaining']
    assert field.description and 'threshold' in field.description.lower()
    
    risk_status = RiskStatusResponse(
        bot_id="1",
        account_balance=52500.0,
        trailing_threshold=50000.0,
        trailing_threshold_remaining=2500.0,
        daily_pnl=250.0,
        apex_compliant=True
    )
    assert risk_status.trailing_threshold_remaining == 2500.0
