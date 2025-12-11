"""create pattern detection tables

Revision ID: b8b739263c73
Revises: d494630c6cc3
Create Date: 2025-12-04 21:52:53.907108

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8b739263c73'
down_revision: Union[str, None] = 'd494630c6cc3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create detected_fvgs table
    op.create_table(
        'detected_fvgs',
        sa.Column('fvg_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('timeframe', sa.String(10), nullable=False),
        sa.Column('formation_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fvg_type', sa.String(10), nullable=False),  # BULLISH, BEARISH
        sa.Column('fvg_start', sa.Float(), nullable=False),
        sa.Column('fvg_end', sa.Float(), nullable=False),
        sa.Column('gap_size', sa.Float(), nullable=False),
        sa.Column('midpoint', sa.Float(), nullable=False),
        sa.Column('vela1_high', sa.Float(), nullable=False),
        sa.Column('vela1_low', sa.Float(), nullable=False),
        sa.Column('vela3_high', sa.Float(), nullable=False),
        sa.Column('vela3_low', sa.Float(), nullable=False),
        sa.Column('significance', sa.String(10), nullable=False),  # MICRO, SMALL, MEDIUM, LARGE, EXTREME
        sa.Column('status', sa.String(20), nullable=False, server_default='UNMITIGATED'),  # UNMITIGATED, FILLED, BROKEN
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_fvgs_symbol_time', 'detected_fvgs', ['symbol', 'formation_time'])
    op.create_index('idx_fvgs_status', 'detected_fvgs', ['status'])

    # Create detected_liquidity_pools table
    op.create_table(
        'detected_liquidity_pools',
        sa.Column('lp_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('timeframe', sa.String(10), nullable=False),
        sa.Column('formation_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('pool_type', sa.String(15), nullable=False),  # EQH, EQL, TH, TL, SWING_HIGH, SWING_LOW, ASH, ASL, LSH, LSL, NYH, NYL
        sa.Column('level', sa.Float(), nullable=False),
        sa.Column('tolerance', sa.Float(), nullable=False, server_default='10.0'),
        sa.Column('touch_times', sa.ARRAY(sa.DateTime(timezone=True))),
        sa.Column('num_touches', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('total_volume', sa.Float()),
        sa.Column('strength', sa.String(10), nullable=False),  # STRONG, NORMAL, WEAK
        sa.Column('status', sa.String(20), nullable=False, server_default='UNMITIGATED'),  # UNMITIGATED, RESPECTED, SWEPT, MITIGATED
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_lps_symbol_time', 'detected_liquidity_pools', ['symbol', 'formation_time'])
    op.create_index('idx_lps_type', 'detected_liquidity_pools', ['pool_type'])
    op.create_index('idx_lps_status', 'detected_liquidity_pools', ['status'])

    # Create detected_order_blocks table
    op.create_table(
        'detected_order_blocks',
        sa.Column('ob_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('timeframe', sa.String(10), nullable=False),
        sa.Column('formation_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ob_type', sa.String(20), nullable=False),  # BULLISH OB, BEARISH OB, STRONG BULLISH OB, STRONG BEARISH OB
        sa.Column('ob_high', sa.Float(), nullable=False),
        sa.Column('ob_low', sa.Float(), nullable=False),
        sa.Column('ob_open', sa.Float(), nullable=False),
        sa.Column('ob_close', sa.Float(), nullable=False),
        sa.Column('ob_volume', sa.Float(), nullable=False),
        sa.Column('impulse_move', sa.Float(), nullable=False),
        sa.Column('impulse_direction', sa.String(10), nullable=False),  # UP, DOWN
        sa.Column('candle_direction', sa.String(10), nullable=False),  # BULLISH, BEARISH
        sa.Column('quality', sa.String(10), nullable=False),  # HIGH, MEDIUM, LOW
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),  # ACTIVE, TESTED, BROKEN
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_obs_symbol_time', 'detected_order_blocks', ['symbol', 'formation_time'])
    op.create_index('idx_obs_type', 'detected_order_blocks', ['ob_type'])
    op.create_index('idx_obs_quality', 'detected_order_blocks', ['quality'])
    op.create_index('idx_obs_status', 'detected_order_blocks', ['status'])

    # Create pattern_interactions table (unified for all pattern types)
    op.create_table(
        'pattern_interactions',
        sa.Column('interaction_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('pattern_type', sa.String(10), nullable=False),  # FVG, LP, OB
        sa.Column('pattern_id', sa.Integer(), nullable=False),
        sa.Column('interaction_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('interaction_type', sa.String(25), nullable=False),  # R0_CLEAN_BOUNCE, R1_SHALLOW_TOUCH, etc.
        sa.Column('penetration_pts', sa.Float(), nullable=False),
        sa.Column('penetration_pct', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('candle_high', sa.Float(), nullable=False),
        sa.Column('candle_low', sa.Float(), nullable=False),
        sa.Column('candle_close', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_interactions_pattern', 'pattern_interactions', ['pattern_type', 'pattern_id'])
    op.create_index('idx_interactions_time', 'pattern_interactions', ['interaction_time'])
    op.create_index('idx_interactions_type', 'pattern_interactions', ['interaction_type'])


def downgrade() -> None:
    op.drop_table('pattern_interactions')
    op.drop_table('detected_order_blocks')
    op.drop_table('detected_liquidity_pools')
    op.drop_table('detected_fvgs')
