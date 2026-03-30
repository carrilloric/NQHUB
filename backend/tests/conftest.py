"""
Pytest configuration and fixtures for NQHUB backend tests
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import sys
from pathlib import Path
import os

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.db.session import Base, get_db  # Use the same Base as models
from app.models.user import User, UserRole
from app.core.security import create_access_token, hash_password

# Import all models to register them with Base.metadata
from app.models import (  # noqa: F401
    User, UserRole, Invitation, PasswordResetToken,
    Indicator, FeatureValue,
    Strategy, BacktestRun, StrategyApproval,
    ModelRegistry, DatasetRegistry,
    BotInstance, BotStateLog, Order, Trade,
    RiskConfig, ApexAccount, TradingSchedule
)
# Also import pattern models
from app.models import candlestick, patterns  # noqa: F401


# Test database URL - use a separate test database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://nqhub:nqhub_password@localhost:5433/nqhub_test"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create async engine for test database."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,  # Disable connection pooling for tests
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def async_db(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for testing."""
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def async_client(async_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with database override."""
    from httpx import AsyncClient, ASGITransport

    async def override_get_db():
        yield async_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def client() -> Generator:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def test_user(async_db: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="testuser@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        role=UserRole.TRADER,
        is_active=True,
        is_verified=True
    )
    async_db.add(user)
    await async_db.flush()  # Flush instead of commit - will be rolled back
    await async_db.refresh(user)
    return user


@pytest.fixture
async def admin_user(async_db: AsyncSession) -> User:
    """Create an admin user."""
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("adminpassword123"),
        full_name="Admin User",
        role=UserRole.SUPERUSER,
        is_active=True,
        is_verified=True
    )
    async_db.add(user)
    await async_db.flush()  # Flush instead of commit - will be rolled back
    await async_db.refresh(user)
    return user


@pytest.fixture
async def auth_headers(test_user: User) -> dict:
    """Create authentication headers with test user token."""
    access_token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def admin_auth_headers(admin_user: User) -> dict:
    """Create authentication headers with admin user token."""
    access_token = create_access_token(str(admin_user.id))
    return {"Authorization": f"Bearer {access_token}"}


# Cleanup function for tests
async def cleanup_database(engine):
    """Clean up test database after tests."""
    async with engine.begin() as conn:
        # Drop all tables
        await conn.run_sync(Base.metadata.drop_all)
        # Recreate tables
        await conn.run_sync(Base.metadata.create_all)