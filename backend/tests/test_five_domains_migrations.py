"""
Unit tests for five domains schema foundation
Tests migrations and model constraints
"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config
from datetime import datetime
import uuid
import os

from app.models.strategy import Strategy, BacktestRun
from app.models.production import BotInstance, Order
from app.db.session import Base


class TestMigrations:
    """Test migration operations for 5 domains"""

    @pytest.fixture(scope="function")
    def alembic_config(self, tmp_path):
        """Create Alembic config for testing"""
        # Create a temporary database for testing
        db_url = os.getenv("TEST_DATABASE_URL", "postgresql://nqhub:nqhub_password@localhost:5433/nqhub_test")

        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", db_url)
        return config

    def test_all_migrations_apply_clean(self, alembic_config):
        """Test that alembic upgrade head applies cleanly from base"""
        try:
            # Downgrade to base first
            command.downgrade(alembic_config, "base")

            # Upgrade to head
            command.upgrade(alembic_config, "head")

            # Verify tables exist by checking information_schema
            engine = create_engine(alembic_config.get_main_option("sqlalchemy.url"))
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN (
                        'indicators', 'feature_values',
                        'strategies', 'backtest_runs', 'strategy_approvals',
                        'model_registry', 'dataset_registry',
                        'bot_instances', 'bot_state_log', 'orders', 'trades',
                        'risk_config', 'apex_accounts', 'trading_schedules'
                    )
                    ORDER BY table_name
                """))
                tables = [row[0] for row in result]

                expected_tables = [
                    'apex_accounts', 'backtest_runs', 'bot_instances', 'bot_state_log',
                    'dataset_registry', 'feature_values', 'indicators', 'model_registry',
                    'orders', 'risk_config', 'strategies', 'strategy_approvals',
                    'trades', 'trading_schedules'
                ]

                assert set(tables) == set(expected_tables), f"Missing tables: {set(expected_tables) - set(tables)}"

        except Exception as e:
            pytest.fail(f"Migration upgrade failed: {str(e)}")

    def test_all_migrations_revert_clean(self, alembic_config):
        """Test that alembic downgrade base reverts cleanly"""
        try:
            # First upgrade to head
            command.upgrade(alembic_config, "head")

            # Then downgrade to base
            command.downgrade(alembic_config, "base")

            # Verify tables don't exist
            engine = create_engine(alembic_config.get_main_option("sqlalchemy.url"))
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN (
                        'indicators', 'feature_values',
                        'strategies', 'backtest_runs', 'strategy_approvals',
                        'model_registry', 'dataset_registry',
                        'bot_instances', 'bot_state_log', 'orders', 'trades',
                        'risk_config', 'apex_accounts', 'trading_schedules'
                    )
                """))
                count = result.scalar()

                assert count == 0, f"Found {count} tables that should have been dropped"

        except Exception as e:
            pytest.fail(f"Migration downgrade failed: {str(e)}")


class TestModelConstraints:
    """Test model constraints and defaults"""

    @pytest.fixture(scope="function")
    def db_session(self):
        """Create a test database session"""
        db_url = os.getenv("TEST_DATABASE_URL", "postgresql://nqhub:nqhub_password@localhost:5433/nqhub_test")
        engine = create_engine(db_url)

        # Create all tables
        Base.metadata.create_all(engine)

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()

        yield session

        session.close()
        # Clean up
        Base.metadata.drop_all(engine)

    def test_strategies_unique_name_version(self, db_session):
        """Test that inserting duplicate strategy name/version raises IntegrityError"""
        # Create first strategy
        strategy1 = Strategy(
            id=uuid.uuid4(),
            name="TestStrategy",
            version="1.0.0",
            type="rule_based"
        )
        db_session.add(strategy1)
        db_session.commit()

        # Try to create duplicate
        strategy2 = Strategy(
            id=uuid.uuid4(),
            name="TestStrategy",
            version="1.0.0",
            type="ml"
        )
        db_session.add(strategy2)

        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()

        assert "uq_strategy_name_version" in str(exc_info.value) or "duplicate key" in str(exc_info.value)

        db_session.rollback()

    def test_orders_default_status_pending(self, db_session):
        """Test that order inserted without status has PENDING default"""
        # First create required parent records
        strategy = Strategy(
            id=uuid.uuid4(),
            name="TestStrategy",
            version="1.0.0",
            type="rule_based"
        )
        db_session.add(strategy)
        db_session.commit()

        bot = BotInstance(
            id=uuid.uuid4(),
            name="TestBot",
            strategy_id=strategy.id
        )
        db_session.add(bot)
        db_session.commit()

        # Create order without specifying status
        order = Order(
            id=uuid.uuid4(),
            bot_id=bot.id,
            side="BUY",
            type="MARKET",
            quantity=1
            # status not specified - should default to PENDING
        )
        db_session.add(order)
        db_session.commit()

        # Refresh to get defaults
        db_session.refresh(order)

        assert order.status == "PENDING", f"Expected status PENDING, got {order.status}"

    def test_bot_params_modified_flag(self, db_session):
        """Test that params_modified initiates as FALSE"""
        # First create required parent
        strategy = Strategy(
            id=uuid.uuid4(),
            name="TestStrategy",
            version="1.0.0",
            type="rule_based"
        )
        db_session.add(strategy)
        db_session.commit()

        # Create bot without specifying params_modified
        bot = BotInstance(
            id=uuid.uuid4(),
            name="TestBot",
            strategy_id=strategy.id
            # params_modified not specified - should default to false
        )
        db_session.add(bot)
        db_session.commit()

        # Refresh to get defaults
        db_session.refresh(bot)

        assert bot.params_modified is False, f"Expected params_modified=False, got {bot.params_modified}"


class TestIntegration:
    """Integration tests for the complete schema"""

    @pytest.fixture(scope="function")
    def db_session(self):
        """Create a test database session"""
        db_url = os.getenv("TEST_DATABASE_URL", "postgresql://nqhub:nqhub_password@localhost:5433/nqhub_test")
        engine = create_engine(db_url)

        # Create all tables
        Base.metadata.create_all(engine)

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()

        yield session

        session.close()
        # Clean up
        Base.metadata.drop_all(engine)

    def test_full_schema_no_orphan_fks(self, db_session):
        """Test that all foreign keys reference existing tables"""
        # This test verifies FK integrity by checking information_schema
        engine = db_session.bind

        with engine.connect() as conn:
            # Query all foreign key constraints
            result = conn.execute(text("""
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
                AND tc.table_name IN (
                    'feature_values', 'backtest_runs', 'strategy_approvals',
                    'bot_instances', 'bot_state_log', 'orders', 'trades', 'risk_config'
                )
            """))

            fk_constraints = result.fetchall()

            # Verify each FK references an existing table
            for fk in fk_constraints:
                table_name, column_name, foreign_table, foreign_column = fk

                # Check that foreign table exists
                check_result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = :table_name
                    )
                """), {"table_name": foreign_table})

                exists = check_result.scalar()
                assert exists, f"FK from {table_name}.{column_name} references non-existent table {foreign_table}"

    def test_bot_instance_strategy_cascade(self, db_session):
        """Test that bot instance correctly references strategy"""
        # Create a strategy
        strategy = Strategy(
            id=uuid.uuid4(),
            name="CascadeTest",
            version="1.0.0",
            type="rule_based"
        )
        db_session.add(strategy)
        db_session.commit()

        # Create bot instance referencing the strategy
        bot = BotInstance(
            id=uuid.uuid4(),
            name="CascadeBot",
            strategy_id=strategy.id
        )
        db_session.add(bot)
        db_session.commit()

        # Verify relationship works
        assert bot.strategy_id == strategy.id
        assert bot.strategy.name == "CascadeTest"

    def test_backtest_run_results_jsonb(self, db_session):
        """Test that backtest results are stored and retrieved as correct JSONB"""
        # Create strategy
        strategy = Strategy(
            id=uuid.uuid4(),
            name="JSONBTest",
            version="1.0.0",
            type="ml"
        )
        db_session.add(strategy)
        db_session.commit()

        # Create backtest run with complex JSONB results
        test_results = {
            "metrics": {
                "sharpe_ratio": 1.85,
                "sortino_ratio": 2.34,
                "max_drawdown": -0.15,
                "win_rate": 0.62,
                "profit_factor": 1.45
            },
            "trades": 125,
            "period": {
                "start": "2025-01-01T00:00:00Z",
                "end": "2025-12-31T23:59:59Z"
            }
        }

        backtest = BacktestRun(
            id=uuid.uuid4(),
            strategy_id=strategy.id,
            params={"learning_rate": 0.001, "epochs": 100},
            config={"commission": 2.25, "slippage": 0.25},
            results=test_results,
            status="completed"
        )
        db_session.add(backtest)
        db_session.commit()

        # Refresh and verify JSONB is correctly stored/retrieved
        db_session.refresh(backtest)

        assert backtest.results["metrics"]["sharpe_ratio"] == 1.85
        assert backtest.results["trades"] == 125
        assert backtest.results["period"]["start"] == "2025-01-01T00:00:00Z"

        # Verify we can query JSONB fields
        result = db_session.execute(text("""
            SELECT results->>'trades' as trades
            FROM backtest_runs
            WHERE id = :id
        """), {"id": str(backtest.id)})

        trades = result.scalar()
        assert int(trades) == 125