"""API v1 Router"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, invitations, candles, patterns, market_state, audit, system,
    features, backtesting, ml, approval, bots, orders, risk, trades,
    settings, strategies, assistant
)
from app.etl import routes as etl_routes

api_router = APIRouter()

# Authentication & Access Control
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(invitations.router, prefix="/invitations", tags=["invitations"])
api_router.include_router(approval.router, prefix="/approval", tags=["approval"])

# Data & Analysis
api_router.include_router(candles.router, prefix="/candles", tags=["candles"])
api_router.include_router(patterns.router, prefix="/patterns", tags=["patterns"])
api_router.include_router(features.router, prefix="/features", tags=["features"])
api_router.include_router(market_state.router, prefix="/market-state", tags=["market-state"])

# Trading & Strategy
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(backtesting.router, prefix="/backtesting", tags=["backtesting"])
api_router.include_router(bots.router, prefix="/bots", tags=["bots"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(trades.router, prefix="/trades", tags=["trades"])

# Risk & Settings
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])

# AI & Machine Learning
api_router.include_router(ml.router, prefix="/ml", tags=["machine-learning"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])

# System & Monitoring
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(etl_routes.router, tags=["ETL"])
