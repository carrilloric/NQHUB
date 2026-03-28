"""
Setup test database for NQHUB backend tests
"""
import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.db.base_class import Base

# Import all models to ensure they're registered with Base.metadata
from app.models.user import User
from app.models.invitation import Invitation
from app.models.password_reset import PasswordResetToken
from app.models.candlestick import *
from app.models.patterns import *
from app.models.strategy import *
from app.models.feature_store import *
from app.models.ml_lab import *
from app.models.production import *
from app.models.risk_config import *

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://nqhub:nqhub_password@localhost:5433/nqhub_test"

async def setup_test_db():
    """Create tables in test database"""
    # First try to create the database
    engine_postgres = create_async_engine(
        "postgresql+asyncpg://nqhub:nqhub_password@localhost:5433/postgres",
        echo=False,
        isolation_level="AUTOCOMMIT"
    )

    try:
        async with engine_postgres.connect() as conn:
            # Check if database exists
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = 'nqhub_test'")
            )
            if not result.scalar():
                # Create database
                await conn.execute(text("CREATE DATABASE nqhub_test"))
                print("✓ Created database 'nqhub_test'")
            else:
                print("✓ Database 'nqhub_test' already exists")
    except Exception as e:
        if "already exists" in str(e):
            print("✓ Database 'nqhub_test' already exists")
        else:
            raise
    finally:
        await engine_postgres.dispose()

    # Now create tables in test database
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    try:
        async with engine.begin() as conn:
            # Drop all existing tables first
            await conn.run_sync(Base.metadata.drop_all)
            print("✓ Dropped existing tables")

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            print("✓ Created all tables in test database")

            # List created tables
            result = await conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
            )
            tables = [row[0] for row in result.fetchall()]
            print(f"✓ Tables created: {', '.join(tables)}")
    finally:
        await engine.dispose()

    print("\n✅ Test database setup complete!")

if __name__ == "__main__":
    asyncio.run(setup_test_db())