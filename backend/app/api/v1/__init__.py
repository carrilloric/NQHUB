"""API v1 Router"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, invitations, candles, patterns, pattern_detection, market_state, audit, system,
    features, backtesting, ml, approval, bots, orders, risk, trades, trade_journal,
    settings, strategies, live_trading, screener, bot_management
    # data_platform,  # Replaced by AUT-330 implementation
    # data_export  # Temporarily disabled
)
# Temporarily commented out due to merge conflicts in main branch
# assistant, assistant_tools,
from app.etl import routes as etl_routes
from app.api.v1.data import router as data_router  # AUT-330: New Data Platform API

api_router = APIRouter()

# Authentication & Access Control
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(invitations.router, prefix="/invitations", tags=["invitations"])

# Data Platform API (AUT-330) - Replaces CONTRACT-001 with cursor pagination and CandleStore service
api_router.include_router(data_router, prefix="/api/v1", tags=["data"])

# Dataset Export to GCS
# api_router.include_router(data_export.router, prefix="/data", tags=["data-export"])

# Pattern Detection API (CONTRACT-002)
api_router.include_router(pattern_detection.router, prefix="/patterns", tags=["pattern-detection"])

# Backtesting API (CONTRACT-003)
api_router.include_router(backtesting.router, prefix="/backtest", tags=["backtesting"])
api_router.include_router(screener.router, prefix="/backtest", tags=["backtest-screener"])

# Live Trading API (CONTRACT-004)
api_router.include_router(live_trading.router, prefix="/bots", tags=["live-trading"])

# Bot Management API (AUT-347)
api_router.include_router(bot_management.router, prefix="/bot-management", tags=["bot-management"])

# Data & Analysis
api_router.include_router(candles.router, prefix="/candles", tags=["candles"])
api_router.include_router(patterns.router, prefix="/patterns-legacy", tags=["patterns-legacy"])
api_router.include_router(features.router, prefix="/features", tags=["features"])
api_router.include_router(market_state.router, prefix="/market-state", tags=["market-state"])

# Trading & Strategy
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(trades.router, prefix="/trades", tags=["trades"])
api_router.include_router(trade_journal.router, prefix="/trade-journal", tags=["trade-journal"])

# Risk & Settings
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])

# AI & Machine Learning
api_router.include_router(ml.router, prefix="/ml", tags=["machine-learning"])
# Temporarily commented out due to merge conflicts in main branch
# api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
# api_router.include_router(assistant_tools.router, prefix="/assistant/tools", tags=["assistant-tools"])

# Approval workflow
api_router.include_router(approval.router, prefix="/approval", tags=["approval"])

# System & Monitoring
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(etl_routes.router, tags=["ETL"])
