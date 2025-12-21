"""create_assistant_tables

Revision ID: eb92517323ec
Revises: 51e48df295f7
Create Date: 2025-12-13 19:15:51.153588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb92517323ec'
down_revision: Union[str, None] = '51e48df295f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create assistant_conversations table
    op.create_table(
        'assistant_conversations',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_assistant_conversations_user_id', 'assistant_conversations', ['user_id'])
    op.create_index('ix_assistant_conversations_created_at', 'assistant_conversations', ['created_at'])

    # Create assistant_messages table
    op.create_table(
        'assistant_messages',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['assistant_conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_assistant_messages_conversation_id', 'assistant_messages', ['conversation_id'])
    op.create_index('ix_assistant_messages_created_at', 'assistant_messages', ['created_at'])

    # Create assistant_system_events table
    op.create_table(
        'assistant_system_events',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=False),
        sa.Column('notified', sa.Boolean(), server_default=sa.text('FALSE'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_assistant_system_events_event_type', 'assistant_system_events', ['event_type'])
    op.create_index('ix_assistant_system_events_notified', 'assistant_system_events', ['notified'])
    op.create_index('ix_assistant_system_events_created_at', 'assistant_system_events', ['created_at'])

    # Create assistant_vanna_training table
    op.create_table(
        'assistant_vanna_training',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('sql_query', sa.Text(), nullable=False),
        sa.Column('was_successful', sa.Boolean(), server_default=sa.text('TRUE'), nullable=False),
        sa.Column('feedback_score', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_assistant_vanna_training_created_at', 'assistant_vanna_training', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_assistant_vanna_training_created_at', table_name='assistant_vanna_training')
    op.drop_table('assistant_vanna_training')

    op.drop_index('ix_assistant_system_events_created_at', table_name='assistant_system_events')
    op.drop_index('ix_assistant_system_events_notified', table_name='assistant_system_events')
    op.drop_index('ix_assistant_system_events_event_type', table_name='assistant_system_events')
    op.drop_table('assistant_system_events')

    op.drop_index('ix_assistant_messages_created_at', table_name='assistant_messages')
    op.drop_index('ix_assistant_messages_conversation_id', table_name='assistant_messages')
    op.drop_table('assistant_messages')

    op.drop_index('ix_assistant_conversations_created_at', table_name='assistant_conversations')
    op.drop_index('ix_assistant_conversations_user_id', table_name='assistant_conversations')
    op.drop_table('assistant_conversations')
