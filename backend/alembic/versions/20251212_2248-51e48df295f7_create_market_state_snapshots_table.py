"""create_market_state_snapshots_table

Revision ID: 51e48df295f7
Revises: 6545cb8844bb
Create Date: 2025-12-12 22:48:02.077701

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51e48df295f7'
down_revision: Union[str, None] = '6545cb8844bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create market_state_snapshots table
    op.create_table(
        'market_state_snapshots',
        sa.Column('snapshot_id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('snapshot_time', sa.DateTime(timezone=False), nullable=False),
        sa.Column('total_patterns_all_timeframes', sa.Integer(), server_default='0', nullable=False),
        sa.Column('timeframe_breakdown', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=False), server_default=sa.text("(NOW() AT TIME ZONE 'UTC')"), nullable=False),
        sa.PrimaryKeyConstraint('snapshot_id'),
        sa.UniqueConstraint('symbol', 'snapshot_time', name='uq_snapshot')
    )

    # Create indexes
    op.create_index('idx_snapshots_symbol_time', 'market_state_snapshots', ['symbol', 'snapshot_time'], unique=False, postgresql_ops={'snapshot_time': 'DESC'})
    op.create_index('idx_snapshots_time', 'market_state_snapshots', ['snapshot_time'], unique=False, postgresql_ops={'snapshot_time': 'DESC'})

    # Create GIN index for JSONB column
    op.execute(
        'CREATE INDEX idx_snapshots_breakdown ON market_state_snapshots USING GIN(timeframe_breakdown)'
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_snapshots_breakdown', table_name='market_state_snapshots')
    op.drop_index('idx_snapshots_time', table_name='market_state_snapshots')
    op.drop_index('idx_snapshots_symbol_time', table_name='market_state_snapshots')

    # Drop table
    op.drop_table('market_state_snapshots')
