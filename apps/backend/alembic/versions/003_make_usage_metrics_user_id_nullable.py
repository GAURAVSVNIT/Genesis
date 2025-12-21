"""Make usage_metrics.user_id nullable for guest users

Revision ID: 003
Revises: 002
Create Date: 2025-12-21 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the foreign key constraint first
    op.drop_constraint('usage_metrics_user_id_fkey', 'usage_metrics', type_='foreignkey')
    
    # Alter the column to be nullable
    op.alter_column('usage_metrics', 'user_id',
               existing_type=sa.UUID(),
               nullable=True)
    
    # Re-add the foreign key constraint with ondelete CASCADE
    op.create_foreign_key('usage_metrics_user_id_fkey', 'usage_metrics', 'users',
                         ['user_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # Drop the foreign key constraint
    op.drop_constraint('usage_metrics_user_id_fkey', 'usage_metrics', type_='foreignkey')
    
    # Revert column to NOT NULL
    op.alter_column('usage_metrics', 'user_id',
               existing_type=sa.UUID(),
               nullable=False)
    
    # Re-add the original foreign key constraint
    op.create_foreign_key('usage_metrics_user_id_fkey', 'usage_metrics', 'users',
                         ['user_id'], ['id'])
