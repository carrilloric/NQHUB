"""
Tests for AI Assistant with Claude API integration
AUT-358: Test coverage for stateless assistant implementation
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
async def test_chat_returns_message(async_client: AsyncClient, auth_headers: dict):
    """Test that POST /chat returns a text message response"""

    # Mock Claude API response
    with patch('app.api.v1.endpoints.assistant.client.messages.create') as mock_create:
        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                type='text',
                text='Hola! Soy el asistente de NQHUB. ¿En qué puedo ayudarte hoy?'
            )
        ]
        mock_response.usage = MagicMock(input_tokens=50, output_tokens=30)
        mock_create.return_value = mock_response

        # Make request
        response = await async_client.post(
            "/api/v1/assistant/chat",
            json={
                "messages": [
                    {"role": "user", "content": "Hola"}
                ],
                "page_context": "live_dashboard"
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 0
        assert data["message"] == "Hola! Soy el asistente de NQHUB. ¿En qué puedo ayudarte hoy?"
        assert "usage" in data
        assert data["usage"]["input_tokens"] == 50
        assert data["usage"]["output_tokens"] == 30


@pytest.mark.asyncio
async def test_chat_uses_market_snapshot_tool(async_client: AsyncClient, auth_headers: dict):
    """Test that asking about market bias triggers query_market_snapshot tool"""

    with patch('app.api.v1.endpoints.assistant.client.messages.create') as mock_create:
        # Setup mock response with tool use
        mock_tool_use = MagicMock()
        mock_tool_use.type = 'tool_use'
        mock_tool_use.name = 'query_market_snapshot'
        mock_tool_use.input = {}

        mock_response = MagicMock()
        mock_response.content = [
            mock_tool_use,
            MagicMock(
                type='text',
                text='Basándome en el market snapshot, el bias actual es BULLISH con un breadth de 85%.'
            )
        ]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)
        mock_create.return_value = mock_response

        # Mock the tool endpoint call
        with patch('app.api.v1.endpoints.assistant.call_tool_endpoint') as mock_tool:
            mock_tool.return_value = {
                "bias": "BULLISH",
                "breadth": 85,
                "tick": 1250,
                "vix": 18.5,
                "advance_decline": 2.1
            }

            response = await async_client.post(
                "/api/v1/assistant/chat",
                json={
                    "messages": [
                        {"role": "user", "content": "¿Cuál es el bias del mercado?"}
                    ],
                    "page_context": "patterns"
                },
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "tools_used" in data
            assert "query_market_snapshot" in data["tools_used"]
            assert "bias" in data["message"].lower() or "bullish" in data["message"].lower()

            # Verify tool was called
            mock_tool.assert_called_once()


@pytest.mark.asyncio
async def test_chat_page_context_injected(async_client: AsyncClient, auth_headers: dict):
    """Test that page_context is included in system prompt"""

    with patch('app.api.v1.endpoints.assistant.client.messages.create') as mock_create:
        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                type='text',
                text='Veo que estás en el Live Dashboard. El P&L actual es de +$1,250.'
            )
        ]
        mock_response.usage = MagicMock(input_tokens=75, output_tokens=35)
        mock_create.return_value = mock_response

        response = await async_client.post(
            "/api/v1/assistant/chat",
            json={
                "messages": [
                    {"role": "user", "content": "¿Qué ves en mi pantalla?"}
                ],
                "page_context": "live_dashboard",
                "bot_id": "bot-123"
            },
            headers=auth_headers
        )

        assert response.status_code == 200

        # Verify system prompt was called with correct context
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        system_prompt = call_args.kwargs['system']

        # Check that Live Dashboard context is in system prompt
        assert "Live Dashboard" in system_prompt
        assert "Bot activo: bot-123" in system_prompt


@pytest.mark.asyncio
async def test_chat_no_session_persistence(async_client: AsyncClient, auth_headers: dict):
    """Test that 2 independent requests don't share context (stateless)"""

    with patch('app.api.v1.endpoints.assistant.client.messages.create') as mock_create:
        # Setup first mock response
        mock_response1 = MagicMock()
        mock_response1.content = [
            MagicMock(
                type='text',
                text='Mi nombre es Claude, el asistente de NQHUB.'
            )
        ]
        mock_response1.usage = MagicMock(input_tokens=30, output_tokens=20)

        # Setup second mock response - should not know previous context
        mock_response2 = MagicMock()
        mock_response2.content = [
            MagicMock(
                type='text',
                text='No tengo información sobre lo que mencionaste anteriormente. Por favor, proporciona más contexto.'
            )
        ]
        mock_response2.usage = MagicMock(input_tokens=25, output_tokens=30)

        mock_create.side_effect = [mock_response1, mock_response2]

        # First request
        response1 = await async_client.post(
            "/api/v1/assistant/chat",
            json={
                "messages": [
                    {"role": "user", "content": "¿Cómo te llamas?"}
                ],
                "page_context": "dashboard"
            },
            headers=auth_headers
        )

        assert response1.status_code == 200
        data1 = response1.json()
        assert "Claude" in data1["message"]

        # Second request - no history provided
        response2 = await async_client.post(
            "/api/v1/assistant/chat",
            json={
                "messages": [
                    {"role": "user", "content": "¿Qué te dije antes?"}
                ],
                "page_context": "dashboard"
            },
            headers=auth_headers
        )

        assert response2.status_code == 200
        data2 = response2.json()

        # Should not know previous conversation
        assert "no tengo información" in data2["message"].lower() or \
               "contexto" in data2["message"].lower() or \
               "anterior" in data2["message"].lower()

        # Verify each request got its own Claude API call
        assert mock_create.call_count == 2

        # Verify messages sent to Claude - should be independent
        first_call_messages = mock_create.call_args_list[0].kwargs['messages']
        second_call_messages = mock_create.call_args_list[1].kwargs['messages']

        # Each should only have 1 user message
        assert len(first_call_messages) == 1
        assert len(second_call_messages) == 1

        # Messages should be different
        assert first_call_messages[0]['content'] != second_call_messages[0]['content']


@pytest.mark.asyncio
async def test_chat_requires_auth(async_client: AsyncClient):
    """Test that chat endpoint requires authentication"""

    # Request without auth headers
    response = await async_client.post(
        "/api/v1/assistant/chat",
        json={
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "page_context": "dashboard"
        }
    )

    # Should return 403 Forbidden (FastAPI returns 403 for missing auth)
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "not authenticated" in data["detail"].lower() or \
           "forbidden" in data["detail"].lower() or \
           "credentials" in data["detail"].lower()


@pytest.mark.asyncio
async def test_chat_full_history_sent(async_client: AsyncClient, auth_headers: dict):
    """Test that full conversation history is sent to Claude API"""

    with patch('app.api.v1.endpoints.assistant.client.messages.create') as mock_create:
        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                type='text',
                text='Basándome en nuestra conversación previa sobre trading de NQ futures...'
            )
        ]
        mock_response.usage = MagicMock(input_tokens=250, output_tokens=50)
        mock_create.return_value = mock_response

        # Send request with 5 messages in history
        conversation_history = [
            {"role": "user", "content": "¿Qué es NQ?"},
            {"role": "assistant", "content": "NQ es el E-mini Nasdaq 100 futures."},
            {"role": "user", "content": "¿Cuál es el tick size?"},
            {"role": "assistant", "content": "El tick size de NQ es 0.25 puntos."},
            {"role": "user", "content": "¿Y cuánto vale cada tick?"}
        ]

        response = await async_client.post(
            "/api/v1/assistant/chat",
            json={
                "messages": conversation_history,
                "page_context": "data"
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify Claude was called with all 5 messages
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        messages_sent = call_args.kwargs['messages']

        # Should have all 5 messages
        assert len(messages_sent) == 5

        # Verify content matches
        for i, msg in enumerate(conversation_history):
            assert messages_sent[i]['role'] == msg['role']
            assert messages_sent[i]['content'] == msg['content']

        # Check token usage reflects larger input
        assert data["usage"]["input_tokens"] == 250  # Higher due to full history


@pytest.mark.asyncio
async def test_get_tools_endpoint(async_client: AsyncClient, auth_headers: dict):
    """Test that GET /tools returns list of available tools"""

    response = await async_client.get(
        "/api/v1/assistant/tools",
        headers=auth_headers
    )

    assert response.status_code == 200
    tools = response.json()

    # Should have 12 tools
    assert len(tools) == 12

    # Check some expected tools
    tool_names = [tool['name'] for tool in tools]
    assert 'query_candles' in tool_names
    assert 'query_market_snapshot' in tool_names
    assert 'query_patterns' in tool_names
    assert 'query_risk_status' in tool_names
    assert 'run_sql' in tool_names


@pytest.mark.asyncio
async def test_get_contexts_endpoint(async_client: AsyncClient, auth_headers: dict):
    """Test that GET /contexts returns available page contexts"""

    response = await async_client.get(
        "/api/v1/assistant/contexts",
        headers=auth_headers
    )

    assert response.status_code == 200
    contexts = response.json()

    # Should have 11 contexts
    assert len(contexts) == 11

    # Check some expected contexts
    assert 'live_dashboard' in contexts
    assert 'backtesting' in contexts
    assert 'patterns' in contexts
    assert 'risk' in contexts

    # Verify context descriptions
    assert 'Live Dashboard' in contexts['live_dashboard']
    assert 'Backtesting' in contexts['backtesting']


@pytest.mark.asyncio
async def test_chat_handles_claude_api_error(async_client: AsyncClient, auth_headers: dict):
    """Test graceful handling of Claude API errors"""

    from anthropic import AuthenticationError

    with patch('app.api.v1.endpoints.assistant.client.messages.create') as mock_create:
        # Simulate API authentication error
        mock_create.side_effect = AuthenticationError(
            message="Invalid API key",
            response=None,
            body=None
        )

        response = await async_client.post(
            "/api/v1/assistant/chat",
            json={
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "page_context": "dashboard"
            },
            headers=auth_headers
        )

        # Should fallback to mock response
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "MOCK" in data["message"] or "desarrollo" in data["message"].lower()


@pytest.mark.asyncio
async def test_chat_with_tool_error_handling(async_client: AsyncClient, auth_headers: dict):
    """Test handling of tool execution errors"""

    with patch('app.api.v1.endpoints.assistant.client.messages.create') as mock_create:
        # Setup mock response with tool use
        mock_tool_use = MagicMock()
        mock_tool_use.type = 'tool_use'
        mock_tool_use.name = 'query_candles'
        mock_tool_use.input = {"timeframe": "1min", "limit": 50}

        mock_response = MagicMock()
        mock_response.content = [mock_tool_use]
        mock_response.usage = MagicMock(input_tokens=50, output_tokens=30)
        mock_create.return_value = mock_response

        # Mock tool endpoint to raise error
        with patch('app.api.v1.endpoints.assistant.call_tool_endpoint') as mock_tool:
            mock_tool.side_effect = Exception("Database connection error")

            response = await async_client.post(
                "/api/v1/assistant/chat",
                json={
                    "messages": [
                        {"role": "user", "content": "Show me the last 50 candles"}
                    ],
                    "page_context": "data"
                },
                headers=auth_headers
            )

            # Should still return 200 with error message
            assert response.status_code == 200
            data = response.json()
            assert "error" in data["message"].lower() or "problema" in data["message"].lower()
