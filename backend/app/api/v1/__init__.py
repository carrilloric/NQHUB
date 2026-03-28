"""API v1 Router"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, invitations, candles, patterns, pattern_detection, market_state, audit, system,
    features, backtesting, ml, approval, bots, orders, risk, trades,
    settings, strategies, assistant, data_platform, live_trading
)
from app.etl import routes as etl_routes

api_router = APIRouter()

# Authentication & Access Control
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(invitations.router, prefix="/invitations", tags=["invitations"])

# Data Platform API (CONTRACT-001)
api_router.include_router(data_platform.router, prefix="/data", tags=["data-platform"])

# Pattern Detection API (CONTRACT-002)
api_router.include_router(pattern_detection.router, prefix="/patterns", tags=["pattern-detection"])

# Backtesting API (CONTRACT-003)
api_router.include_router(backtesting.router, prefix="/backtest", tags=["backtesting"])

# Live Trading API (CONTRACT-004)
api_router.include_router(live_trading.router, prefix="/bots", tags=["live-trading"])

# Data & Analysis
api_router.include_router(candles.router, prefix="/candles", tags=["candles"])
api_router.include_router(patterns.router, prefix="/patterns-legacy", tags=["patterns-legacy"])
api_router.include_router(features.router, prefix="/features", tags=["features"])
api_router.include_router(market_state.router, prefix="/market-state", tags=["market-state"])

# Trading & Strategy
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(trades.router, prefix="/trades", tags=["trades"])

# Risk & Settings
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])

# AI & Machine Learning
api_router.include_router(ml.router, prefix="/ml", tags=["machine-learning"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])

# Approval workflow
api_router.include_router(approval.router, prefix="/approval", tags=["approval"])

# System & Monitoring
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(etl_routes.router, tags=["ETL"])
