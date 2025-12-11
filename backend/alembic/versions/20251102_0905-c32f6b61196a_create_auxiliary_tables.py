"""create auxiliary tables

Revision ID: c32f6b61196a
Revises: 0cac37df50d1
Create Date: 2025-11-02 09:05:13.708174

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c32f6b61196a'
down_revision: Union[str, None] = '0cac37df50d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create rollover_periods table
    op.create_table(
        'rollover_periods',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('contract_old', sa.String(10), nullable=False),
        sa.Column('contract_new', sa.String(10), nullable=False),
        sa.Column('start_date', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('end_date', sa.TIMESTAMP(timezone=True)),
        sa.Column('total_spread_ticks', sa.Integer()),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('detected_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id', name='rollover_periods_pkey')
    )

    # Create processed_files table
    op.create_table(
        'processed_files',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('zip_filename', sa.String(255), nullable=False),
        sa.Column('csv_filename', sa.String(255), nullable=False),
        sa.Column('row_count', sa.Integer()),
        sa.Column('start_date', sa.TIMESTAMP(timezone=True)),
        sa.Column('end_date', sa.TIMESTAMP(timezone=True)),
        sa.Column('processed_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id', name='processed_files_pkey'),
        sa.UniqueConstraint('zip_filename', 'csv_filename', name='uq_processed_files')
    )


def downgrade() -> None:
    op.drop_table('processed_files')
    op.drop_table('rollover_periods')
