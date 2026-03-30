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

<<<<<<< HEAD
# Claude API client
client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY if hasattr(settings, 'ANTHROPIC_API_KEY') else None)


class MessageRole(str, Enum):
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
>>>>>>> 0643333 (feat(backend): AUT-358 Implement AI Assistant with Claude API and 12 tools)
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


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


<<<<<<< HEAD
# Page context definitions
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

# System prompt template
SYSTEM_PROMPT = """Eres el asistente de NQHUB, una plataforma de trading algorítmico de NQ futures.
Tienes acceso a datos en tiempo real del sistema via tools.
Contexto actual: {page_context}
{bot_context}
Responde siempre en el idioma del usuario. Sé conciso y directo.
Cuando uses tools, explica brevemente qué datos estás consultando."""

# Tool definitions for Claude API
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
        "description": "Obtiene el Market State actual: bias por timeframe, patrones activos, sesión. Úsalo para preguntas sobre bias o condiciones actuales del mercado.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "query_patterns",
        "description": "Obtiene patrones ICT detectados (FVG, Order Block, Liquidity Pool).",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["fvg", "ob", "lp"],
                    "description": "Pattern type to query"
                },
                "timeframe": {
                    "type": "string",
                    "description": "Timeframe for the patterns"
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "mitigated", "broken"],
                    "description": "Pattern status filter"
                }
            },
            "required": ["type"]
        }
    },
    {
        "name": "query_risk_status",
        "description": "Obtiene el estado de riesgo actual: daily loss %, trailing drawdown proximity, circuit breakers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bot_id": {
                    "type": "string",
                    "description": "Bot ID to check risk status for"
                }
            },
            "required": []
        }
    },
    {
        "name": "query_backtest_results",
        "description": "Obtiene métricas de un backtest específico.",
        "input_schema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "Backtest run ID"
                }
            },
            "required": ["run_id"]
        }
    },
    {
        "name": "query_trades",
        "description": "Obtiene trades ejecutados con P&L.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bot_id": {
                    "type": "string",
                    "description": "Bot ID to filter trades"
                },
                "limit": {
                    "type": "integer",
                    "default": 20,
                    "description": "Number of trades to retrieve"
                }
            },
            "required": []
        }
    },
    {
        "name": "query_performance",
        "description": "Obtiene métricas de performance de un bot activo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bot_id": {
                    "type": "string",
                    "description": "Bot ID"
                },
                "period": {
                    "type": "string",
                    "enum": ["today", "week", "month"],
                    "description": "Time period for performance metrics"
                }
            },
            "required": ["bot_id"]
        }
    },
    {
        "name": "run_sql",
        "description": "Ejecuta una query SQL SELECT read-only contra la base de datos de NQHUB. Solo para usuarios avanzados. Solo SELECT permitido.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL SELECT query to execute"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "query_pattern_interactions",
        "description": "Obtiene interacciones entre patrones (rebotes, penetraciones, mitigaciones).",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern_type": {
                    "type": "string",
                    "enum": ["fvg", "ob", "lp"],
                    "description": "Pattern type"
                },
                "interaction_type": {
                    "type": "string",
                    "enum": ["bounce", "penetration", "mitigation"],
                    "description": "Interaction type"
                }
            },
            "required": []
        }
    },
    {
        "name": "query_backtest_comparison",
        "description": "Compara resultados de múltiples backtests.",
        "input_schema": {
            "type": "object",
            "properties": {
                "run_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of backtest run IDs to compare"
                }
            },
            "required": ["run_ids"]
        }
    },
    {
        "name": "query_bot_logs",
        "description": "Obtiene logs de ejecución de un bot específico.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bot_id": {
                    "type": "string",
                    "description": "Bot ID"
                },
                "level": {
                    "type": "string",
                    "enum": ["debug", "info", "warning", "error"],
                    "description": "Log level filter"
                },
                "limit": {
                    "type": "integer",
                    "default": 100,
                    "description": "Number of log entries"
                }
            },
            "required": ["bot_id"]
        }
    },
    {
        "name": "query_orders",
        "description": "Obtiene órdenes y su estado (pending, filled, cancelled).",
        "input_schema": {
            "type": "object",
            "properties": {
                "bot_id": {
                    "type": "string",
                    "description": "Bot ID to filter orders"
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "filled", "cancelled", "rejected"],
                    "description": "Order status filter"
                },
                "limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Number of orders to retrieve"
                }
            },
            "required": []
        }
    }
]


async def call_tool_endpoint(
    tool_name: str,
    tool_input: Dict[str, Any],
    current_user: User,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Call internal tool endpoint based on tool name.
    Maps tool calls to /api/v1/assistant/tools/* endpoints.
    """
    # Map tool names to internal endpoints
    tool_endpoints = {
        "query_candles": "/api/v1/assistant/tools/candles",
        "query_market_snapshot": "/api/v1/assistant/tools/market-snapshot",
        "query_patterns": "/api/v1/assistant/tools/patterns",
        "query_risk_status": "/api/v1/assistant/tools/risk-status",
        "query_backtest_results": "/api/v1/assistant/tools/backtest-results",
        "query_trades": "/api/v1/assistant/tools/trades",
        "query_performance": "/api/v1/assistant/tools/performance",
        "run_sql": "/api/v1/assistant/tools/sql",
        "query_pattern_interactions": "/api/v1/assistant/tools/pattern-interactions",
        "query_backtest_comparison": "/api/v1/assistant/tools/backtest-comparison",
        "query_bot_logs": "/api/v1/assistant/tools/bot-logs",
        "query_orders": "/api/v1/assistant/tools/orders",
    }

    endpoint = tool_endpoints.get(tool_name)
    if not endpoint:
        logger.error(f"Unknown tool: {tool_name}")
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        # For now, return mock data based on tool name
        # In production, this would make actual HTTP calls to the tool endpoints
        mock_responses = {
            "query_candles": {
                "candles": [
                    {"timestamp": "2024-03-29T15:00:00Z", "open": 17850, "high": 17880, "low": 17845, "close": 17875, "volume": 1250},
                    {"timestamp": "2024-03-29T15:05:00Z", "open": 17875, "high": 17890, "low": 17870, "close": 17885, "volume": 980},
                ],
                "timeframe": tool_input.get("timeframe", "5min")
            },
            "query_market_snapshot": {
                "current_price": 17885,
                "session": "NY",
                "bias": {
                    "5min": "bullish",
                    "15min": "bullish",
                    "1h": "neutral",
                    "4h": "bearish"
                },
                "active_patterns": {
                    "fvg": 3,
                    "order_blocks": 2,
                    "liquidity_pools": 1
                }
            },
            "query_patterns": {
                "patterns": [
                    {
                        "id": "fvg_001",
                        "type": tool_input.get("type", "fvg"),
                        "timeframe": tool_input.get("timeframe", "5min"),
                        "status": tool_input.get("status", "active"),
                        "level": 17860,
                        "created_at": "2024-03-29T14:30:00Z"
                    }
                ]
            },
            "query_risk_status": {
                "bot_id": tool_input.get("bot_id", "bot_001"),
                "daily_loss_pct": -0.5,
                "max_daily_loss": -2.0,
                "trailing_drawdown": -750,
                "max_trailing_drawdown": -1500,
                "circuit_breakers": {
                    "max_loss": False,
                    "max_trades": False,
                    "time_based": False
                }
            },
            "query_performance": {
                "bot_id": tool_input.get("bot_id"),
                "period": tool_input.get("period", "today"),
                "metrics": {
                    "total_pnl": 1250,
                    "win_rate": 0.65,
                    "sharpe_ratio": 1.8,
                    "total_trades": 23,
                    "winning_trades": 15,
                    "losing_trades": 8
                }
            },
            "query_trades": {
                "trades": [
                    {
                        "id": "trade_001",
                        "bot_id": tool_input.get("bot_id", "bot_001"),
                        "entry_time": "2024-03-29T10:30:00Z",
                        "exit_time": "2024-03-29T10:45:00Z",
                        "pnl": 125,
                        "side": "long"
                    }
                ]
            },
            "run_sql": {
                "query": tool_input.get("query"),
                "results": [],
                "message": "Query executed successfully (mock)"
            },
            "query_orders": {
                "orders": [
                    {
                        "id": "order_001",
                        "bot_id": tool_input.get("bot_id", "bot_001"),
                        "status": tool_input.get("status", "filled"),
                        "side": "buy",
                        "quantity": 1,
                        "price": 17850
                    }
                ]
            },
            "query_backtest_results": {
                "run_id": tool_input.get("run_id"),
                "metrics": {
                    "total_return": 0.15,
                    "sharpe_ratio": 2.1,
                    "max_drawdown": -0.08,
                    "win_rate": 0.58
                }
            },
            "query_pattern_interactions": {
                "interactions": []
            },
            "query_backtest_comparison": {
                "comparison": []
            },
            "query_bot_logs": {
                "logs": []
            }
        }

        return mock_responses.get(tool_name, {"status": "success", "data": {}})

    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {str(e)}")
        return {"error": str(e)}


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    Main chat endpoint for AI Assistant.

    - Receives full conversation history from frontend
    - No session persistence (stateless)
    - Integrates with Claude API using tool use
    - Returns assistant response with tool usage info
    """
=======
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
>>>>>>> 0643333 (feat(backend): AUT-358 Implement AI Assistant with Claude API and 12 tools)
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

<<<<<<< HEAD
        # Check if we have API key configured
        if not client.api_key:
            # Return mock response if no API key
            logger.warning("No Anthropic API key configured, returning mock response")
            return ChatResponse(
                message="I can help you analyze markets and trading strategies. (Mock response - API key not configured)",
                tools_used=[],
                usage={"input_tokens": 0, "output_tokens": 0}
            )

        # Call Claude API with tools
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Latest Claude 3.5 Sonnet model
=======
        # Call Claude API with tools
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
>>>>>>> 0643333 (feat(backend): AUT-358 Implement AI Assistant with Claude API and 12 tools)
            max_tokens=1024,
            system=system,
            tools=TOOLS,
            messages=claude_messages
        )

<<<<<<< HEAD
        # Process response and handle tool use
        tools_used = []
        final_response = ""

        # Check if Claude used any tools
        for content in response.content:
            if content.type == "tool_use":
                tool_name = content.name
                tool_input = content.input
                tools_used.append(tool_name)

                # Call the tool endpoint
                tool_result = await call_tool_endpoint(
                    tool_name,
                    tool_input,
                    current_user,
                    db
                )

                # Add tool result to the conversation
                claude_messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                claude_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": json.dumps(tool_result)
                    }]
                })

                # Get final response from Claude with tool results
                final_response_obj = await client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    system=system,
                    tools=TOOLS,
                    messages=claude_messages
                )

                if final_response_obj.content:
                    final_response = final_response_obj.content[0].text if hasattr(final_response_obj.content[0], 'text') else str(final_response_obj.content[0])
            elif hasattr(content, 'text'):
                final_response = content.text

        # If no tools were used, use the direct response
        if not final_response and response.content:
            final_response = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])

        # Calculate usage
        usage = {
            "input_tokens": response.usage.input_tokens if hasattr(response, 'usage') else 0,
            "output_tokens": response.usage.output_tokens if hasattr(response, 'usage') else 0
        }

        return ChatResponse(
            message=final_response or "I can help you with market analysis and trading strategies.",
            tools_used=tools_used,
            usage=usage
        )

    except anthropic.AuthenticationError as e:
        logger.error(f"Claude API authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Claude API authentication failed"
        )
    except anthropic.RateLimitError as e:
        logger.error(f"Claude API rate limit error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded, please try again later"
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/tools")
async def get_available_tools(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get list of available tools for the assistant.

    Returns tool definitions and descriptions.
    """
    return {
        "status": "success",
        "data": {
            "tools": TOOLS,
            "total": len(TOOLS)
        }
    }


@router.get("/contexts")
async def get_page_contexts(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get available page contexts.

    Returns all defined page contexts for the frontend.
    """
    return {
        "status": "success",
        "data": {
            "contexts": PAGE_CONTEXTS,
            "total": len(PAGE_CONTEXTS)
        }
    }
=======
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
>>>>>>> 0643333 (feat(backend): AUT-358 Implement AI Assistant with Claude API and 12 tools)
