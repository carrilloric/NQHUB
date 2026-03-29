"""
Assistant API endpoints - Claude API integration for AI-powered chat
AUT-358: Stateless architecture with Claude Sonnet 3.5
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
import anthropic
from anthropic import AsyncAnthropic, AuthenticationError, RateLimitError
import json
import logging
from datetime import datetime

from app.core.database import get_async_db
from app.core.deps import get_current_user
from app.models.user import User
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Claude API client
client = AsyncAnthropic(
    api_key=settings.ANTHROPIC_API_KEY if hasattr(settings, 'ANTHROPIC_API_KEY') else None
)

# Page contexts - 11 contexts for different frontend pages
PAGE_CONTEXTS = {
    "live_dashboard": "El usuario está viendo el Live Dashboard. Puede preguntarte sobre P&L, posiciones abiertas, y rendimiento del bot activo.",
    "backtesting": "El usuario está en la página de Backtesting. Puede preguntarte sobre resultados de backtests, comparaciones, y métricas de estrategias.",
    "patterns": "El usuario está viendo Pattern Detection. Puede preguntarte sobre FVGs, Order Blocks, y el Market Snapshot actual.",
    "data": "El usuario está en Data Explorer. Puede preguntarte sobre candles NQ históricos y cobertura de datos.",
    "risk": "El usuario está en Risk Monitor. Puede preguntarte sobre daily loss, trailing drawdown, y estado de circuit breakers.",
    "journal": "El usuario está en Trade Journal. Puede preguntarte sobre trades históricos y métricas de performance.",
    "alpha": "El usuario está en Alpha Lab. Puede preguntarte sobre estrategias y backtests.",
    "bots": "El usuario está en Bot Management. Puede preguntarte sobre el estado de los bots.",
    "orders": "El usuario está en Order Management. Puede preguntarte sobre órdenes y fills.",
    "settings": "El usuario está en Settings. Puede preguntarte sobre configuración de riesgo y cuentas Apex.",
    "ml_lab": "El usuario está en ML Lab. Puede preguntarte sobre modelos registrados y datasets.",
}

# System prompt template with context injection
SYSTEM_PROMPT = """Eres el asistente de NQHUB, una plataforma de trading algorítmico de NQ futures.
Tienes acceso a datos en tiempo real del sistema via tools.
Contexto actual: {page_context}
{bot_context}
Responde siempre en el idioma del usuario. Sé conciso y directo.
Cuando uses tools, explica brevemente qué datos estás consultando."""

# Define 12 tools as per AUT-358 specification
TOOLS = [
    {
        "name": "query_candles",
        "description": "Obtiene candles NQ históricos. Úsalo cuando el usuario pregunta sobre precio, OHLCV, o datos de mercado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "timeframe": {
                    "type": "string",
                    "enum": ["30s", "1min", "5min", "15min", "1h", "4h", "1d", "1w"],
                    "description": "Timeframe for the candles"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Number of candles to retrieve"
                }
            },
            "required": ["timeframe"]
        }
    },
    {
        "name": "query_market_snapshot",
        "description": "Obtiene el Market Snapshot actual: bias, breadth, tick, vix. Úsalo para preguntas sobre el estado actual del mercado.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "query_patterns",
        "description": "Busca patrones detectados: FVG, Order Blocks, Liquidity Pools. Úsalo cuando pregunten sobre patrones ICT.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern_type": {
                    "type": "string",
                    "enum": ["fvg", "order_block", "liquidity_pool"],
                    "description": "Type of pattern to query"
                },
                "timeframe": {
                    "type": "string",
                    "enum": ["1min", "5min", "15min", "1h"],
                    "description": "Timeframe for patterns"
                }
            },
            "required": ["pattern_type"]
        }
    },
    {
        "name": "query_risk_status",
        "description": "Consulta el estado de riesgo: daily loss, trailing drawdown, circuit breakers. Úsalo para preguntas sobre risk management.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "query_backtest_results",
        "description": "Obtiene resultados de backtests. Úsalo cuando pregunten sobre performance histórica de estrategias.",
        "input_schema": {
            "type": "object",
            "properties": {
                "strategy_id": {
                    "type": "string",
                    "description": "Strategy identifier"
                }
            }
        }
    },
    {
        "name": "query_trades",
        "description": "Consulta trades históricos y métricas. Úsalo para el Trade Journal.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Number of trades to retrieve"
                }
            }
        }
    },
    {
        "name": "query_performance",
        "description": "Obtiene métricas de performance: sharpe, sortino, win rate. Úsalo para análisis de rendimiento.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["day", "week", "month", "year"],
                    "description": "Time period for performance metrics"
                }
            }
        }
    },
    {
        "name": "run_sql",
        "description": "Ejecuta queries SQL contra la base de datos. Úsalo para consultas complejas no cubiertas por otros tools.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query to execute (SELECT only)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "query_pattern_interactions",
        "description": "Analiza interacciones entre patrones: rebounds (R0-R4), penetrations (P1-P5).",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern_id": {
                    "type": "string",
                    "description": "Pattern identifier to analyze interactions"
                }
            }
        }
    },
    {
        "name": "query_backtest_comparison",
        "description": "Compara múltiples backtests. Úsalo para análisis comparativo de estrategias.",
        "input_schema": {
            "type": "object",
            "properties": {
                "strategy_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of strategy IDs to compare"
                }
            },
            "required": ["strategy_ids"]
        }
    },
    {
        "name": "query_bot_logs",
        "description": "Obtiene logs de bots activos. Úsalo para debugging y monitoreo de bots.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bot_id": {
                    "type": "string",
                    "description": "Bot identifier"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Number of log entries"
                }
            },
            "required": ["bot_id"]
        }
    },
    {
        "name": "query_orders",
        "description": "Consulta órdenes y fills. Úsalo para Order Management.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "filled", "cancelled", "all"],
                    "description": "Order status filter"
                }
            }
        }
    }
]


class MessageRole(str, Enum):
    """Message role in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Individual chat message"""
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    messages: List[ChatMessage] = Field(..., description="Full conversation history")
    page_context: str = Field(..., description="Current page context in the frontend")
    bot_id: Optional[str] = Field(None, description="Active bot ID for context")


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    message: str = Field(..., description="Assistant's response")
    tools_used: List[str] = Field(default_factory=list, description="List of tools used")
    usage: Dict[str, int] = Field(default_factory=dict, description="Token usage statistics")


async def call_tool_endpoint(tool_name: str, tool_input: dict, db: AsyncSession, user_id: int) -> dict:
    """
    Call internal tool endpoint to get data
    Maps tool names to internal API endpoints
    """
    # For now, return mock responses until tool endpoints are implemented
    mock_responses = {
        "query_candles": {
            "candles": [
                {"time": "2024-03-26T14:00:00", "open": 17850, "high": 17860, "low": 17845, "close": 17855, "volume": 1250},
                {"time": "2024-03-26T14:05:00", "open": 17855, "high": 17865, "low": 17850, "close": 17862, "volume": 980}
            ]
        },
        "query_market_snapshot": {
            "bias": "BULLISH",
            "breadth": 72,
            "tick": 850,
            "vix": 14.5,
            "advance_decline": 2.1
        },
        "query_patterns": {
            "patterns": [
                {"id": "fvg_001", "type": "FVG", "level": 17825, "status": "UNMITIGATED"},
                {"id": "ob_002", "type": "ORDER_BLOCK", "zone": [17800, 17810], "quality": "HIGH"}
            ]
        },
        "query_risk_status": {
            "daily_loss": -125.50,
            "daily_limit": -500.00,
            "trailing_drawdown": -350.00,
            "max_drawdown": -1500.00,
            "circuit_breaker": "GREEN"
        },
        "query_backtest_results": {
            "sharpe_ratio": 1.85,
            "win_rate": 0.62,
            "profit_factor": 1.95,
            "total_pnl": 15250.00,
            "max_drawdown": -2100.00
        },
        "query_trades": {
            "trades": [
                {"id": "t001", "direction": "LONG", "entry": 17850, "exit": 17865, "pnl": 75.00},
                {"id": "t002", "direction": "SHORT", "entry": 17870, "exit": 17860, "pnl": 50.00}
            ]
        },
        "query_performance": {
            "sharpe_ratio": 1.65,
            "sortino_ratio": 2.10,
            "win_rate": 0.58,
            "avg_win": 125.00,
            "avg_loss": -75.00
        },
        "run_sql": {
            "rows": [
                {"symbol": "NQZ5", "count": 15000}
            ]
        },
        "query_pattern_interactions": {
            "interactions": [
                {"type": "R2", "pattern_id": "fvg_001", "penetration": 0.15, "bounce": True}
            ]
        },
        "query_backtest_comparison": {
            "comparison": {
                "strategy_1": {"sharpe": 1.85, "win_rate": 0.62},
                "strategy_2": {"sharpe": 1.45, "win_rate": 0.55}
            }
        },
        "query_bot_logs": {
            "logs": [
                {"timestamp": "2024-03-26T14:00:00", "level": "INFO", "message": "Bot started"},
                {"timestamp": "2024-03-26T14:01:00", "level": "INFO", "message": "Signal detected"}
            ]
        },
        "query_orders": {
            "orders": [
                {"id": "ord_001", "side": "BUY", "qty": 1, "status": "FILLED", "price": 17850}
            ]
        }
    }

    return mock_responses.get(tool_name, {})


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    Main chat endpoint - stateless conversation with Claude API
    ADR-020: No session persistence, full history sent each request
    """
    try:
        # Build system prompt with page context
        page_context_text = PAGE_CONTEXTS.get(request.page_context, "")
        bot_context = f"Bot activo: {request.bot_id}" if request.bot_id else ""

        system = SYSTEM_PROMPT.format(
            page_context=page_context_text,
            bot_context=bot_context
        )

        # Convert messages to Claude format
        claude_messages = []
        for msg in request.messages:
            claude_messages.append({
                "role": msg.role.value,
                "content": msg.content
            })

        # Call Claude API with tools
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system,
            tools=TOOLS,
            messages=claude_messages
        )

        # Process response and extract tool usage
        tools_used = []
        final_message = ""

        # Handle tool use in response
        for content in response.content:
            if content.type == "tool_use":
                tools_used.append(content.name)
                # Call the tool endpoint
                tool_result = await call_tool_endpoint(
                    content.name,
                    content.input,
                    db,
                    current_user.id
                )
                # Add tool result to context (in a real implementation)
                logger.info(f"Tool {content.name} called with result: {tool_result}")
            elif content.type == "text":
                final_message = content.text

        # If no text response, generate one
        if not final_message:
            final_message = "He consultado los datos solicitados. ¿En qué más puedo ayudarte?"

        # Build usage statistics
        usage = {
            "input_tokens": response.usage.input_tokens if hasattr(response, 'usage') else 0,
            "output_tokens": response.usage.output_tokens if hasattr(response, 'usage') else 0
        }

        return ChatResponse(
            message=final_message,
            tools_used=tools_used,
            usage=usage
        )

    except AuthenticationError as e:
        logger.error(f"Claude API authentication error: {e}")
        # Fallback to mock response if API key is not configured
        return ChatResponse(
            message="[MOCK] Estoy en modo de desarrollo. Claude API no está configurado. ¿En qué puedo ayudarte?",
            tools_used=[],
            usage={"input_tokens": 0, "output_tokens": 0}
        )

    except RateLimitError as e:
        logger.error(f"Claude API rate limit error: {e}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def get_available_tools(
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get list of available tools for the assistant
    """
    return TOOLS


@router.get("/contexts")
async def get_page_contexts(
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Get available page contexts
    """
    return PAGE_CONTEXTS