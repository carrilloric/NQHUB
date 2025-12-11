"""add detailed progress fields to etl_jobs

Revision ID: d207e6ad07eb
Revises: 73668c471717
Create Date: 2025-11-02 16:41:13.134834

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd207e6ad07eb'
down_revision: Union[str, None] = '73668c471717'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add detailed progress tracking fields to etl_jobs
    op.add_column('etl_jobs', sa.Column('current_csv_file', sa.String(255), nullable=True))
    op.add_column('etl_jobs', sa.Column('ticks_per_second', sa.Float(), nullable=True))
    op.add_column('etl_jobs', sa.Column('memory_usage_mb', sa.Float(), nullable=True))
    op.add_column('etl_jobs', sa.Column('estimated_completion', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove detailed progress tracking fields
    op.drop_column('etl_jobs', 'estimated_completion')
    op.drop_column('etl_jobs', 'memory_usage_mb')
    op.drop_column('etl_jobs', 'ticks_per_second')
    op.drop_column('etl_jobs', 'current_csv_file')
