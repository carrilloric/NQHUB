"""create_active_contracts_table

Revision ID: f1a8f69db2a6
Revises: 1999c1774198
Create Date: 2025-11-03 14:38:50.309085

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a8f69db2a6'
down_revision: Union[str, None] = '1999c1774198'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'active_contracts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('volume_score', sa.BigInteger(), nullable=True),
        sa.Column('tick_count', sa.BigInteger(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('rollover_period', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'start_date', name='uq_symbol_start_date')
    )

    # Create indexes for common queries
    op.create_index('idx_active_contracts_is_current', 'active_contracts', ['is_current'])
    op.create_index('idx_active_contracts_symbol', 'active_contracts', ['symbol'])
    op.create_index('idx_active_contracts_date_range', 'active_contracts', ['start_date', 'end_date'])


def downgrade() -> None:
    op.drop_index('idx_active_contracts_date_range', table_name='active_contracts')
    op.drop_index('idx_active_contracts_symbol', table_name='active_contracts')
    op.drop_index('idx_active_contracts_is_current', table_name='active_contracts')
    op.drop_table('active_contracts')
