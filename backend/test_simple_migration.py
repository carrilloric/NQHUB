#!/usr/bin/env python3
"""
Simple test to verify migrations and model constraints
"""
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from app.models.strategy import Strategy
from app.models.production import BotInstance, Order
from app.db.session import Base
import uuid


def test_migrations_applied():
    """Test that all tables exist"""
    engine = create_engine("postgresql://nqhub:nqhub_password@localhost:5433/nqhub")

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
        print("✅ test_migrations_applied: All tables exist")


def test_strategies_unique_constraint():
    """Test unique constraint on strategy name/version"""
    engine = create_engine("postgresql://nqhub:nqhub_password@localhost:5433/nqhub")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        # Clean up any existing test data
        session.execute(text("DELETE FROM strategies WHERE name = 'TestStrategy'"))
        session.commit()

        # Create first strategy
        strategy1 = Strategy(
            id=uuid.uuid4(),
            name="TestStrategy",
            version="1.0.0",
            type="rule_based"
        )
        session.add(strategy1)
        session.commit()

        # Try to create duplicate
        strategy2 = Strategy(
            id=uuid.uuid4(),
            name="TestStrategy",
            version="1.0.0",
            type="ml"
        )
        session.add(strategy2)

        try:
            session.commit()
            assert False, "Should have raised IntegrityError"
        except IntegrityError as e:
            session.rollback()
            assert "duplicate key" in str(e) or "uq_strategy_name_version" in str(e)
            print("✅ test_strategies_unique_constraint: Unique constraint works")

    finally:
        # Clean up
        session.execute(text("DELETE FROM strategies WHERE name = 'TestStrategy'"))
        session.commit()
        session.close()


def test_orders_default_status():
    """Test orders default status"""
    engine = create_engine("postgresql://nqhub:nqhub_password@localhost:5433/nqhub")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        # Clean up any existing test data
        session.execute(text("DELETE FROM bot_instances WHERE name = 'TestBot'"))
        session.execute(text("DELETE FROM strategies WHERE name = 'TestStrategyForOrder'"))
        session.commit()

        # Create required parent records
        strategy = Strategy(
            id=uuid.uuid4(),
            name="TestStrategyForOrder",
            version="1.0.0",
            type="rule_based"
        )
        session.add(strategy)
        session.commit()

        bot = BotInstance(
            id=uuid.uuid4(),
            name="TestBot",
            strategy_id=strategy.id
        )
        session.add(bot)
        session.commit()

        # Create order without status
        order = Order(
            id=uuid.uuid4(),
            bot_id=bot.id,
            side="BUY",
            type="MARKET",
            quantity=1
        )
        session.add(order)
        session.commit()

        # Refresh to get defaults
        session.refresh(order)

        assert order.status == "PENDING", f"Expected PENDING, got {order.status}"
        print("✅ test_orders_default_status: Default status is PENDING")

    finally:
        # Clean up
        session.execute(text("DELETE FROM orders WHERE bot_id IN (SELECT id FROM bot_instances WHERE name = 'TestBot')"))
        session.execute(text("DELETE FROM bot_instances WHERE name = 'TestBot'"))
        session.execute(text("DELETE FROM strategies WHERE name = 'TestStrategyForOrder'"))
        session.commit()
        session.close()


def test_bot_params_modified_default():
    """Test bot params_modified default value"""
    engine = create_engine("postgresql://nqhub:nqhub_password@localhost:5433/nqhub")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        # Clean up
        session.execute(text("DELETE FROM bot_instances WHERE name = 'TestBot2'"))
        session.execute(text("DELETE FROM strategies WHERE name = 'TestStrategyForBot'"))
        session.commit()

        # Create parent
        strategy = Strategy(
            id=uuid.uuid4(),
            name="TestStrategyForBot",
            version="1.0.0",
            type="rule_based"
        )
        session.add(strategy)
        session.commit()

        # Create bot without params_modified
        bot = BotInstance(
            id=uuid.uuid4(),
            name="TestBot2",
            strategy_id=strategy.id
        )
        session.add(bot)
        session.commit()

        # Refresh to get defaults
        session.refresh(bot)

        assert bot.params_modified is False, f"Expected False, got {bot.params_modified}"
        print("✅ test_bot_params_modified_default: Default is False")

    finally:
        # Clean up
        session.execute(text("DELETE FROM bot_instances WHERE name = 'TestBot2'"))
        session.execute(text("DELETE FROM strategies WHERE name = 'TestStrategyForBot'"))
        session.commit()
        session.close()


if __name__ == "__main__":
    print("Running simple migration tests...\n")

    test_migrations_applied()
    test_strategies_unique_constraint()
    test_orders_default_status()
    test_bot_params_modified_default()

    print("\n✅ All simple tests passed!")