"""
NQHUB Backend - FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import settings
from app.api.v1 import api_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NQHUB API",
    description="Trading Analytics Platform API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "version": "0.1.0"
        }
    )

# Root endpoint
@app.get("/api")
async def root():
    """Root API endpoint"""
    return {
        "message": "NQHUB API",
        "version": "0.1.0",
        "docs": "/api/docs"
    }

# Include API routers
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info(f"Starting NQHUB API - Environment: {settings.ENVIRONMENT}")
    logger.info(f"CORS origins: {settings.ALLOWED_ORIGINS}")
    # TODO: Initialize database connections
    # TODO: Initialize Redis connection
    # TODO: Initialize Neo4j connection

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Shutting down NQHUB API")
    # TODO: Close database connections
    # TODO: Close Redis connection
    # TODO: Close Neo4j connection

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
