"""Create BlogCheckpoint and ConversationContext tables

Revision ID: 004
Revises: 003
Create Date: 2025-12-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create blog_checkpoints table
    op.create_table(
        'blog_checkpoints',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('conversation_id', sa.String(255), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('context_snapshot', postgresql.JSON(), nullable=True),
        sa.Column('chat_messages_snapshot', postgresql.JSON(), nullable=True),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('tone', sa.String(50), nullable=True),
        sa.Column('length', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes for blog_checkpoints
    op.create_index('idx_checkpoints_user', 'blog_checkpoints', ['user_id'])
    op.create_index('idx_checkpoints_conversation', 'blog_checkpoints', ['conversation_id'])
    op.create_index('idx_checkpoints_active', 'blog_checkpoints', ['is_active'])
    op.create_index('idx_checkpoints_created', 'blog_checkpoints', ['created_at'])
    
    # Create conversation_contexts table
    op.create_table(
        'conversation_contexts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('conversation_id', sa.String(255), nullable=False),
        sa.Column('messages_context', postgresql.JSON(), nullable=False),
        sa.Column('chat_context', sa.Text(), nullable=True),
        sa.Column('blog_context', sa.Text(), nullable=True),
        sa.Column('full_context', sa.Text(), nullable=True),
        sa.Column('last_updated_at', sa.DateTime(), nullable=False),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes for conversation_contexts
    op.create_index('idx_context_user', 'conversation_contexts', ['user_id'])
    op.create_index('idx_context_conversation', 'conversation_contexts', ['conversation_id'])
    op.create_index('idx_context_updated', 'conversation_contexts', ['last_updated_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_context_updated')
    op.drop_index('idx_context_conversation')
    op.drop_index('idx_context_user')
    
    # Drop conversation_contexts table
    op.drop_table('conversation_contexts')
    
    # Drop indexes
    op.drop_index('idx_checkpoints_created')
    op.drop_index('idx_checkpoints_active')
    op.drop_index('idx_checkpoints_conversation')
    op.drop_index('idx_checkpoints_user')
    
    # Drop blog_checkpoints table
    op.drop_table('blog_checkpoints')
