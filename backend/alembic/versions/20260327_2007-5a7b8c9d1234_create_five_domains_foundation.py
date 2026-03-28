"""create five domains foundation

Revision ID: 5a7b8c9d1234
Revises: 26c1b6c3c358
Create Date: 2026-03-27 20:07:00.000000

Creates the foundation schema for 5 domains:
1. Feature Store
2. Strategy & Backtesting
3. ML Lab
4. Production
5. Risk & Config
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '5a7b8c9d1234'
down_revision: Union[str, None] = '26c1b6c3c358'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========== 1. Feature Store Domain ==========

    # Create indicators table
    op.create_table(
        'indicators',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),  # smc, orderflow, custom
        sa.Column('params', JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    # Create feature_values table
    op.create_table(
        'feature_values',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('indicator_id', UUID(as_uuid=True), sa.ForeignKey('indicators.id'), nullable=False),
        sa.Column('timeframe', sa.String(10), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('value', JSONB, nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_feature_values_indicator_timeframe', 'feature_values', ['indicator_id', 'timeframe'])
    op.create_index('idx_feature_values_timestamp', 'feature_values', ['timestamp'])

    # ========== 2. Strategy & Backtesting Domain ==========

    # Create strategies table
    op.create_table(
        'strategies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),  # rule_based, ml, rl, hybrid
        sa.Column('source_code', sa.Text, nullable=True),
        sa.Column('required_features', JSONB, server_default='[]'),
        sa.Column('model_id', sa.String(200), nullable=True),  # HuggingFace model ID
        sa.Column('status', sa.String(50), server_default='draft'),  # draft, approved, deprecated
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('name', 'version', name='uq_strategy_name_version')
    )
    op.create_index('idx_strategies_status', 'strategies', ['status'])
    op.create_index('idx_strategies_type', 'strategies', ['type'])

    # Create backtest_runs table
    op.create_table(
        'backtest_runs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('strategy_id', UUID(as_uuid=True), sa.ForeignKey('strategies.id'), nullable=False),
        sa.Column('params', JSONB, nullable=False),
        sa.Column('config', JSONB, nullable=False),  # dates, commission, slippage, tp, sl
        sa.Column('results', JSONB, nullable=True),  # metrics: sharpe, sortino, dd, etc.
        sa.Column('source', sa.String(50), server_default='nqhub'),  # nqhub | notebook
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('idx_backtest_runs_strategy', 'backtest_runs', ['strategy_id'])
    op.create_index('idx_backtest_runs_status', 'backtest_runs', ['status'])
    op.create_index('idx_backtest_runs_created', 'backtest_runs', ['created_at'])

    # Create strategy_approvals table
    op.create_table(
        'strategy_approvals',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('strategy_id', UUID(as_uuid=True), sa.ForeignKey('strategies.id'), nullable=False),
        sa.Column('backtest_run_id', UUID(as_uuid=True), sa.ForeignKey('backtest_runs.id'), nullable=False),
        sa.Column('approved_params', JSONB, nullable=False),
        sa.Column('approved_by', sa.String(200), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('notes', sa.Text, nullable=True)
    )
    op.create_index('idx_approvals_strategy', 'strategy_approvals', ['strategy_id'])
    op.create_index('idx_approvals_approved_at', 'strategy_approvals', ['approved_at'])

    # ========== 3. ML Lab Domain ==========

    # Create model_registry table
    op.create_table(
        'model_registry',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),  # onnx, pytorch, sklearn
        sa.Column('huggingface_repo', sa.String(200), nullable=True),
        sa.Column('wandb_run_id', sa.String(200), nullable=True),
        sa.Column('metrics', JSONB, server_default='{}'),
        sa.Column('status', sa.String(50), server_default='staging'),  # staging, production, archived
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_model_registry_name_version', 'model_registry', ['name', 'version'])
    op.create_index('idx_model_registry_status', 'model_registry', ['status'])
    op.create_index('idx_model_registry_type', 'model_registry', ['type'])

    # Create dataset_registry table
    op.create_table(
        'dataset_registry',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('gcs_path', sa.String(500), nullable=True),
        sa.Column('size_mb', sa.Float, nullable=True),
        sa.Column('row_count', sa.BigInteger, nullable=True),
        sa.Column('schema', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_dataset_registry_name', 'dataset_registry', ['name'])
    op.create_index('idx_dataset_registry_created', 'dataset_registry', ['created_at'])

    # ========== 4. Production Domain ==========

    # Create apex_accounts table (must be created before bot_instances due to FK)
    op.create_table(
        'apex_accounts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('account_name', sa.String(200), nullable=False),
        sa.Column('account_size_usd', sa.DECIMAL(12, 2), nullable=False),
        sa.Column('trailing_threshold_usd', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('daily_loss_limit_usd', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('rithmic_credentials', JSONB, nullable=True),  # encrypted
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_apex_accounts_name', 'apex_accounts', ['account_name'])
    op.create_index('idx_apex_accounts_active', 'apex_accounts', ['is_active'])

    # Create bot_instances table
    op.create_table(
        'bot_instances',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('strategy_id', UUID(as_uuid=True), sa.ForeignKey('strategies.id'), nullable=False),
        sa.Column('approval_id', UUID(as_uuid=True), sa.ForeignKey('strategy_approvals.id'), nullable=True),
        sa.Column('apex_account_id', UUID(as_uuid=True), sa.ForeignKey('apex_accounts.id'), nullable=True),
        sa.Column('mode', sa.String(50), server_default='paper'),  # paper | live
        sa.Column('status', sa.String(50), server_default='stopped'),  # stopped, running, error, killed
        sa.Column('approved_params', JSONB, nullable=True),
        sa.Column('active_params', JSONB, nullable=True),
        sa.Column('params_modified', sa.Boolean, server_default='false'),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_bot_instances_status', 'bot_instances', ['status'])
    op.create_index('idx_bot_instances_mode', 'bot_instances', ['mode'])
    op.create_index('idx_bot_instances_strategy', 'bot_instances', ['strategy_id'])

    # Create bot_state_log table
    op.create_table(
        'bot_state_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('bot_id', UUID(as_uuid=True), sa.ForeignKey('bot_instances.id'), nullable=False),
        sa.Column('from_status', sa.String(50), nullable=True),
        sa.Column('to_status', sa.String(50), nullable=True),
        sa.Column('reason', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_bot_state_log_bot', 'bot_state_log', ['bot_id'])
    op.create_index('idx_bot_state_log_created', 'bot_state_log', ['created_at'])

    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('bot_id', UUID(as_uuid=True), sa.ForeignKey('bot_instances.id'), nullable=False),
        sa.Column('rithmic_order_id', sa.String(200), nullable=True),
        sa.Column('symbol', sa.String(20), server_default='NQ'),
        sa.Column('side', sa.String(10), nullable=False),  # BUY | SELL
        sa.Column('type', sa.String(20), nullable=False),  # MARKET | LIMIT | STOP
        sa.Column('quantity', sa.Integer, nullable=False),
        sa.Column('price', sa.DECIMAL(12, 2), nullable=True),
        sa.Column('fill_price', sa.DECIMAL(12, 2), nullable=True),
        sa.Column('status', sa.String(50), server_default='PENDING'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('filled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('idx_orders_bot', 'orders', ['bot_id'])
    op.create_index('idx_orders_status', 'orders', ['status'])
    op.create_index('idx_orders_submitted', 'orders', ['submitted_at'])
    op.create_index('idx_orders_rithmic', 'orders', ['rithmic_order_id'])

    # Create trades table
    op.create_table(
        'trades',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('bot_id', UUID(as_uuid=True), sa.ForeignKey('bot_instances.id'), nullable=False),
        sa.Column('strategy_id', UUID(as_uuid=True), sa.ForeignKey('strategies.id'), nullable=False),
        sa.Column('entry_order_id', UUID(as_uuid=True), sa.ForeignKey('orders.id'), nullable=True),
        sa.Column('exit_order_id', UUID(as_uuid=True), sa.ForeignKey('orders.id'), nullable=True),
        sa.Column('direction', sa.String(10), nullable=True),  # LONG | SHORT
        sa.Column('entry_price', sa.DECIMAL(12, 2), nullable=True),
        sa.Column('exit_price', sa.DECIMAL(12, 2), nullable=True),
        sa.Column('quantity', sa.Integer, nullable=True),
        sa.Column('pnl_ticks', sa.Integer, nullable=True),
        sa.Column('pnl_usd', sa.DECIMAL(12, 2), nullable=True),
        sa.Column('commission', sa.DECIMAL(8, 2), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('tags', JSONB, server_default='[]'),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('idx_trades_bot', 'trades', ['bot_id'])
    op.create_index('idx_trades_strategy', 'trades', ['strategy_id'])
    op.create_index('idx_trades_opened', 'trades', ['opened_at'])
    op.create_index('idx_trades_closed', 'trades', ['closed_at'])

    # ========== 5. Risk & Config Domain ==========

    # Create risk_config table
    op.create_table(
        'risk_config',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('bot_id', UUID(as_uuid=True), sa.ForeignKey('bot_instances.id'), nullable=False),
        sa.Column('max_daily_loss_usd', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('max_trailing_drawdown_usd', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('max_contracts', sa.Integer, server_default='1'),
        sa.Column('max_orders_per_minute', sa.Integer, server_default='10'),
        sa.Column('news_blackout_minutes', sa.Integer, server_default='5'),
        sa.Column('apex_consistency_pct', sa.DECIMAL(5, 2), server_default='30.0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_risk_config_bot', 'risk_config', ['bot_id'])

    # Create trading_schedules table
    op.create_table(
        'trading_schedules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('timezone', sa.String(50), server_default='America/New_York'),
        sa.Column('sessions', JSONB, nullable=False),  # [{start: "08:00", end: "16:00", days: [1,2,3,4,5]}]
        sa.Column('is_active', sa.Boolean, server_default='true')
    )
    op.create_index('idx_trading_schedules_name', 'trading_schedules', ['name'])
    op.create_index('idx_trading_schedules_active', 'trading_schedules', ['is_active'])


def downgrade() -> None:
    # Drop tables in reverse order due to foreign key dependencies

    # 5. Risk & Config Domain
    op.drop_table('trading_schedules')
    op.drop_table('risk_config')

    # 4. Production Domain
    op.drop_table('trades')
    op.drop_table('orders')
    op.drop_table('bot_state_log')
    op.drop_table('bot_instances')
    op.drop_table('apex_accounts')

    # 3. ML Lab Domain
    op.drop_table('dataset_registry')
    op.drop_table('model_registry')

    # 2. Strategy & Backtesting Domain
    op.drop_table('strategy_approvals')
    op.drop_table('backtest_runs')
    op.drop_table('strategies')

    # 1. Feature Store Domain
    op.drop_table('feature_values')
    op.drop_table('indicators')