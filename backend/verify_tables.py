#!/usr/bin/env python3
"""Quick script to verify tables were created"""

from sqlalchemy import create_engine, text

engine = create_engine("postgresql://nqhub:nqhub_password@localhost:5433/nqhub")

with engine.connect() as conn:
    # Query for new tables
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

    tables = result.fetchall()

    print("✅ Tables created successfully:")
    for table in tables:
        print(f"  - {table[0]}")

    print(f"\n📊 Total: {len(tables)} tables")

    expected_count = 14
    if len(tables) == expected_count:
        print(f"✅ All {expected_count} expected tables are present!")
    else:
        print(f"⚠️  Expected {expected_count} tables, found {len(tables)}")