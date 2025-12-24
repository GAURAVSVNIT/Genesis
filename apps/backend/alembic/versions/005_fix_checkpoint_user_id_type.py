"""Fix blog_checkpoints and conversation_contexts user_id column type

Revision ID: 005
Revises: 004
Create Date: 2025-12-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alter blog_checkpoints.user_id from UUID to String
    op.alter_column(
        'blog_checkpoints',
        'user_id',
        existing_type=sa.UUID(),
        type_=sa.String(255),
        existing_nullable=False,
        nullable=False
    )
    
    # Alter conversation_contexts.user_id from UUID to String
    op.alter_column(
        'conversation_contexts',
        'user_id',
        existing_type=sa.UUID(),
        type_=sa.String(255),
        existing_nullable=False,
        nullable=False
    )


def downgrade() -> None:
    # Revert conversation_contexts.user_id from String to UUID
    op.alter_column(
        'conversation_contexts',
        'user_id',
        existing_type=sa.String(255),
        type_=sa.UUID(),
        existing_nullable=False,
        nullable=False
    )
    
    # Revert blog_checkpoints.user_id from String to UUID
    op.alter_column(
        'blog_checkpoints',
        'user_id',
        existing_type=sa.String(255),
        type_=sa.UUID(),
        existing_nullable=False,
        nullable=False
    )
