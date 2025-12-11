"""create market data ticks table

Revision ID: b215073e64fd
Revises: 8d5b0d19c24e
Create Date: 2025-11-02 09:04:11.823615

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b215073e64fd'
down_revision: Union[str, None] = '8d5b0d19c24e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create market_data_ticks table
    op.create_table(
        'market_data_ticks',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('ts_recv', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('ts_event', sa.TIMESTAMP(timezone=True), nullable=False),

        # Symbol tracking
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('is_spread', sa.Boolean(), server_default='false'),
        sa.Column('is_rollover_period', sa.Boolean(), server_default='false'),

        # Market data
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('side', sa.String(1), nullable=False),
        sa.Column('action', sa.String(1)),

        # Order book snapshots
        sa.Column('bid_px', sa.Float()),
        sa.Column('ask_px', sa.Float()),
        sa.Column('bid_sz', sa.Integer()),
        sa.Column('ask_sz', sa.Integer()),
        sa.Column('bid_ct', sa.Integer()),
        sa.Column('ask_ct', sa.Integer()),

        # Databento metadata
        sa.Column('rtype', sa.Integer()),
        sa.Column('publisher_id', sa.Integer()),
        sa.Column('instrument_id', sa.Integer()),
        sa.Column('sequence', sa.BigInteger()),
        sa.Column('flags', sa.Integer()),
        sa.Column('ts_in_delta', sa.Integer()),
        sa.Column('depth', sa.Integer()),

        sa.PrimaryKeyConstraint('id', 'ts_event', name='market_data_ticks_pkey')
    )

    # Create indexes
    op.create_index('idx_ticks_ts_event', 'market_data_ticks', ['ts_event'], postgresql_using='btree')
    op.create_index('idx_ticks_symbol', 'market_data_ticks', ['symbol'])
    op.create_index('idx_ticks_rollover', 'market_data_ticks', ['is_rollover_period'])

    # Create TimescaleDB hypertable
    op.execute(
        "SELECT create_hypertable('market_data_ticks', 'ts_event', "
        "chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE)"
    )


def downgrade() -> None:
    op.drop_index('idx_ticks_rollover', table_name='market_data_ticks')
    op.drop_index('idx_ticks_symbol', table_name='market_data_ticks')
    op.drop_index('idx_ticks_ts_event', table_name='market_data_ticks')
    op.drop_table('market_data_ticks')
