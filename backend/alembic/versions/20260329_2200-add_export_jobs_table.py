"""Add export_jobs table for GCS dataset export

Revision ID: export_jobs_001
Revises: 5a7b8c9d1234
Create Date: 2026-03-29 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'export_jobs_001'
down_revision: Union[str, None] = '5a7b8c9d1234'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create export_jobs table"""
    op.create_table(
        'export_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timeframe', sa.String(length=10), nullable=False),
        sa.Column('start_date', sa.String(length=10), nullable=False),
        sa.Column('end_date', sa.String(length=10), nullable=False),
        sa.Column('include_oflow', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('flatten_oflow', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='queued'),
        sa.Column('progress_pct', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('current_step', sa.String(length=100), nullable=True),
        sa.Column('estimated_rows', sa.Integer(), nullable=True),
        sa.Column('estimated_size_mb', sa.Integer(), nullable=True),
        sa.Column('files', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for common queries
    op.create_index('ix_export_jobs_status', 'export_jobs', ['status'])
    op.create_index('ix_export_jobs_created_by_id', 'export_jobs', ['created_by_id'])
    op.create_index('ix_export_jobs_created_at', 'export_jobs', ['created_at'])


def downgrade() -> None:
    """Drop export_jobs table"""
    op.drop_index('ix_export_jobs_created_at', table_name='export_jobs')
    op.drop_index('ix_export_jobs_created_by_id', table_name='export_jobs')
    op.drop_index('ix_export_jobs_status', table_name='export_jobs')
    op.drop_table('export_jobs')
