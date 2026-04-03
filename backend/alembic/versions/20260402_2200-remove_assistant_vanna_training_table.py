"""Remove assistant_vanna_training table

Revision ID: remove_vanna_001
Revises: add_bracket_order_fields_to_orders
Create Date: 2026-04-02 22:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'remove_vanna_001'
down_revision = 'add_bracket_order_fields_to_orders'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the assistant_vanna_training table
    op.drop_index('ix_assistant_vanna_training_created_at', table_name='assistant_vanna_training', if_exists=True)
    op.drop_table('assistant_vanna_training', if_exists=True)


def downgrade() -> None:
    # Recreate the assistant_vanna_training table
    op.create_table(
        'assistant_vanna_training',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('sql_query', sa.Text(), nullable=False),
        sa.Column('was_successful', sa.Boolean(), server_default=sa.text("TRUE"), nullable=False),
        sa.Column('feedback_score', sa.Integer(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_assistant_vanna_training_created_at', 'assistant_vanna_training', ['created_at'])