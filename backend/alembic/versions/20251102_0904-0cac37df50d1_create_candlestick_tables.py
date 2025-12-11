"""create candlestick tables

Revision ID: 0cac37df50d1
Revises: b215073e64fd
Create Date: 2025-11-02 09:04:38.911682

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '0cac37df50d1'
down_revision: Union[str, None] = 'b215073e64fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Timeframes to create
TIMEFRAMES = ['30s', '1min', '5min', '15min', '1hr', '4hr', 'daily', 'weekly']


def create_candlestick_table(timeframe: str) -> None:
    """Create a candlestick table with complete schema (33 columns)"""
    table_name = f'candlestick_{timeframe}'

    op.create_table(
        table_name,
        sa.Column('time_interval', sa.TIMESTAMP(timezone=True), nullable=False),

        # Symbol tracking (3 columns)
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('is_spread', sa.Boolean(), server_default='false'),
        sa.Column('is_rollover_period', sa.Boolean(), server_default='false'),

        # OHLCV (5 columns)
        sa.Column('open', sa.Float()),
        sa.Column('high', sa.Float()),
        sa.Column('low', sa.Float()),
        sa.Column('close', sa.Float()),
        sa.Column('volume', sa.Float()),

        # Point of Control - Regular (5 columns)
        sa.Column('poc', sa.Float()),
        sa.Column('poc_volume', sa.Float()),
        sa.Column('poc_percentage', sa.Float()),
        sa.Column('poc_location', sa.Text()),
        sa.Column('poc_position', sa.Float()),

        # Point of Control - Real (exact 0.25 tick) (4 columns)
        sa.Column('real_poc', sa.Float()),
        sa.Column('real_poc_volume', sa.Float()),
        sa.Column('real_poc_percentage', sa.Float()),
        sa.Column('real_poc_location', sa.Text()),

        # Candle structure (6 columns)
        sa.Column('upper_wick', sa.Float()),
        sa.Column('lower_wick', sa.Float()),
        sa.Column('body', sa.Float()),
        sa.Column('wick_ratio', sa.Float()),
        sa.Column('rel_uw', sa.Float()),
        sa.Column('rel_lw', sa.Float()),

        # Volume distribution (3 columns)
        sa.Column('upper_wick_volume', sa.Float()),
        sa.Column('lower_wick_volume', sa.Float()),
        sa.Column('body_volume', sa.Float()),

        # Absorption indicators (4 columns)
        sa.Column('asellers_uwick', sa.Float()),
        sa.Column('asellers_lwick', sa.Float()),
        sa.Column('abuyers_uwick', sa.Float()),
        sa.Column('abuyers_lwick', sa.Float()),

        # Order flow (3 columns)
        sa.Column('delta', sa.Float()),
        sa.Column('oflow_detail', JSONB()),
        sa.Column('oflow_unit', JSONB()),

        # Metadata (1 column)
        sa.Column('tick_count', sa.Integer()),

        sa.PrimaryKeyConstraint('time_interval', 'symbol', name=f'{table_name}_pkey')
    )

    # Create indexes
    op.create_index(f'idx_{timeframe}_time', table_name, ['time_interval'], postgresql_using='btree')
    op.create_index(f'idx_{timeframe}_symbol', table_name, ['symbol'])
    op.create_index(f'idx_{timeframe}_rollover', table_name, ['is_rollover_period'])


def upgrade() -> None:
    # Create all 8 candlestick tables
    for timeframe in TIMEFRAMES:
        create_candlestick_table(timeframe)


def downgrade() -> None:
    # Drop all 8 candlestick tables
    for timeframe in TIMEFRAMES:
        table_name = f'candlestick_{timeframe}'
        op.drop_index(f'idx_{timeframe}_rollover', table_name=table_name)
        op.drop_index(f'idx_{timeframe}_symbol', table_name=table_name)
        op.drop_index(f'idx_{timeframe}_time', table_name=table_name)
        op.drop_table(table_name)
