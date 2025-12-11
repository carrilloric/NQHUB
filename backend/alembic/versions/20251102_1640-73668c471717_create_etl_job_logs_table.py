"""create etl_job_logs table

Revision ID: 73668c471717
Revises: 0ab4b7e66309
Create Date: 2025-11-02 16:40:13.368548

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = '73668c471717'
down_revision: Union[str, None] = '0ab4b7e66309'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create etl_job_logs table
    op.create_table(
        'etl_job_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('job_id', UUID(as_uuid=True), sa.ForeignKey('etl_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('level', sa.String(10), nullable=False),  # INFO, WARNING, ERROR, DEBUG
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata', JSONB(), nullable=True),  # Additional context as JSON
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )

    # Create indexes for better query performance
    op.create_index('idx_etl_job_logs_job_id', 'etl_job_logs', ['job_id'])
    op.create_index('idx_etl_job_logs_created_at', 'etl_job_logs', ['created_at'])
    op.create_index('idx_etl_job_logs_level', 'etl_job_logs', ['level'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_etl_job_logs_level', table_name='etl_job_logs')
    op.drop_index('idx_etl_job_logs_created_at', table_name='etl_job_logs')
    op.drop_index('idx_etl_job_logs_job_id', table_name='etl_job_logs')

    # Drop table
    op.drop_table('etl_job_logs')
