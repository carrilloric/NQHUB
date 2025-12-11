"""create etl_jobs and candle_coverage tables

Revision ID: 0ab4b7e66309
Revises: c32f6b61196a
Create Date: 2025-11-02 09:48:15.849725

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = '0ab4b7e66309'
down_revision: Union[str, None] = 'c32f6b61196a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create etl_jobs table
    op.create_table(
        'etl_jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('zip_filename', sa.String(255), nullable=False),
        sa.Column('file_size_mb', sa.Float()),

        # Status tracking
        sa.Column('status', sa.String(20), server_default='pending'),
        # Statuses: pending, extracting, parsing, loading_ticks,
        #           building_candles, detecting_rollovers, completed, failed

        # Progress tracking
        sa.Column('total_steps', sa.Integer(), server_default='8'),
        sa.Column('current_step', sa.Integer(), server_default='0'),
        sa.Column('progress_pct', sa.Integer(), server_default='0'),

        # Statistics
        sa.Column('csv_files_found', sa.Integer()),
        sa.Column('csv_files_processed', sa.Integer(), server_default='0'),
        sa.Column('ticks_inserted', sa.BigInteger(), server_default='0'),
        sa.Column('candles_created', sa.Integer(), server_default='0'),

        # Timeframe selection
        sa.Column('selected_timeframes', JSONB()),  # List of selected timeframes

        # Timing
        sa.Column('started_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True)),

        # Error handling
        sa.Column('error_message', sa.Text()),
        sa.Column('error_details', JSONB()),

        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),

        sa.PrimaryKeyConstraint('id', name='etl_jobs_pkey')
    )

    # Create indexes for etl_jobs
    op.create_index('idx_etl_jobs_status', 'etl_jobs', ['status'])
    op.create_index('idx_etl_jobs_user', 'etl_jobs', ['user_id'])
    op.create_index('idx_etl_jobs_created', 'etl_jobs', ['created_at'])

    # Create candle_coverage table
    op.create_table(
        'candle_coverage',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('timeframe', sa.String(10), nullable=False),
        # Timeframe values: '30s', '1min', '5min', '15min', '1hr', '4hr', 'daily', 'weekly'

        # Status tracking
        sa.Column('status', sa.String(20), server_default='pending'),
        # Status values: pending, processing, completed, failed

        # Statistics
        sa.Column('candles_count', sa.Integer()),
        sa.Column('first_candle', sa.TIMESTAMP(timezone=True)),
        sa.Column('last_candle', sa.TIMESTAMP(timezone=True)),

        # Processing info
        sa.Column('processed_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('error_message', sa.Text()),

        sa.PrimaryKeyConstraint('id', name='candle_coverage_pkey'),
        sa.UniqueConstraint('date', 'symbol', 'timeframe', name='uq_candle_coverage')
    )

    # Create indexes for candle_coverage
    op.create_index('idx_coverage_date', 'candle_coverage', ['date'])
    op.create_index('idx_coverage_timeframe', 'candle_coverage', ['timeframe'])
    op.create_index('idx_coverage_status', 'candle_coverage', ['status'])
    op.create_index('idx_coverage_symbol', 'candle_coverage', ['symbol'])

    # Add check constraint for valid timeframes
    op.create_check_constraint(
        'check_timeframe',
        'candle_coverage',
        "timeframe IN ('30s', '1min', '5min', '15min', '1hr', '4hr', 'daily', 'weekly')"
    )


def downgrade() -> None:
    # Drop candle_coverage table
    op.drop_index('idx_coverage_symbol', table_name='candle_coverage')
    op.drop_index('idx_coverage_status', table_name='candle_coverage')
    op.drop_index('idx_coverage_timeframe', table_name='candle_coverage')
    op.drop_index('idx_coverage_date', table_name='candle_coverage')
    op.drop_table('candle_coverage')

    # Drop etl_jobs table
    op.drop_index('idx_etl_jobs_created', table_name='etl_jobs')
    op.drop_index('idx_etl_jobs_user', table_name='etl_jobs')
    op.drop_index('idx_etl_jobs_status', table_name='etl_jobs')
    op.drop_table('etl_jobs')
