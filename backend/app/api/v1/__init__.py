"""API v1 Router"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, invitations, candles, patterns
from app.etl import routes as etl_routes

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(invitations.router, prefix="/invitations", tags=["invitations"])
api_router.include_router(candles.router, prefix="/candles", tags=["candles"])
api_router.include_router(patterns.router, prefix="/patterns", tags=["patterns"])
api_router.include_router(etl_routes.router, tags=["ETL"])
