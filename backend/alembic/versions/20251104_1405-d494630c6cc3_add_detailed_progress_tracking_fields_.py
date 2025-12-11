"""add detailed progress tracking fields to etl_jobs

Revision ID: d494630c6cc3
Revises: 8ab5a70c73df
Create Date: 2025-11-04 14:05:28.475091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd494630c6cc3'
down_revision: Union[str, None] = '8ab5a70c73df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add detailed progress tracking fields to ETL jobs table.

    These fields enable better visibility of ETL progress:
    - Total ticks estimated from pre-analysis
    - Total days and days processed
    - Duplicates skipped count
    """
    # Add new columns for detailed progress tracking
    op.add_column('etl_jobs',
        sa.Column('total_ticks_estimated', sa.BigInteger(), nullable=True)
    )
    op.add_column('etl_jobs',
        sa.Column('total_days', sa.Integer(), nullable=True)
    )
    op.add_column('etl_jobs',
        sa.Column('days_processed', sa.Integer(), nullable=False, server_default='0')
    )
    op.add_column('etl_jobs',
        sa.Column('duplicates_skipped', sa.BigInteger(), nullable=False, server_default='0')
    )


def downgrade() -> None:
    """Remove the detailed progress tracking columns."""
    op.drop_column('etl_jobs', 'duplicates_skipped')
    op.drop_column('etl_jobs', 'days_processed')
    op.drop_column('etl_jobs', 'total_days')
    op.drop_column('etl_jobs', 'total_ticks_estimated')