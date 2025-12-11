"""
Database Session Configuration
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from app.config import settings

# Create declarative base for ORM models
Base = declarative_base()

# Create async engine with connection pooling optimized for ETL workloads
engine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    echo=settings.is_development,
    future=True,
    # Connection pool configuration for handling large datasets
    pool_size=20,           # Number of connections to maintain in pool
    max_overflow=10,        # Maximum overflow connections above pool_size
    pool_pre_ping=True,     # Test connections before using them
    pool_recycle=3600,      # Recycle connections after 1 hour
    pool_timeout=30,        # Timeout for getting connection from pool
    connect_args={
        "server_settings": {
            "application_name": "nqhub_etl",
            "jit": "on"
        },
        "command_timeout": 60,  # Command timeout in seconds
    }
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create synchronous engine for pattern detection and other sync operations
sync_engine = create_engine(
    settings.DATABASE_URL.replace("+asyncpg", ""),  # Remove async driver
    echo=settings.is_development,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create synchronous session factory
SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Dependency to get async database session (for ETL operations)"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_db_sync():
    """Dependency to get synchronous database session (for pattern detection)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
