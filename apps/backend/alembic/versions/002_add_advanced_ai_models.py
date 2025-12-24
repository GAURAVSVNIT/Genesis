"""
Alembic migration: Add advanced AI agent models for ChatGPT-style functionality.
Creates tables for:
- content_versions (regeneration tracking)
- system_prompts (prompt versioning)
- message_feedback (user ratings)
- rag_sources (source attribution)
- conversation_context (context management)

Revision ID: 002
Revises: 001
Create Date: 2025-12-15 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """Create advanced AI agent tables."""
    
    # 1. Content Versions Table
    op.create_table(
        'content_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('is_selected', sa.Boolean, default=False),
        sa.Column('generated_content', postgresql.JSONB(), nullable=False),
        sa.Column('content_length', sa.Integer),
        sa.Column('content_tokens', sa.Integer),
        sa.Column('model_used', sa.String(100), nullable=False),
        sa.Column('temperature', sa.Float),
        sa.Column('max_tokens', sa.Integer),
        sa.Column('top_p', sa.Float),
        sa.Column('parameters', postgresql.JSONB()),
        sa.Column('seo_score', sa.Float, default=0.0),
        sa.Column('uniqueness_score', sa.Float, default=0.0),
        sa.Column('engagement_score', sa.Float, default=0.0),
        sa.Column('user_rating', sa.Integer),
        sa.Column('user_feedback', sa.Text),
        sa.Column('generation_time_ms', sa.Integer),
        sa.Column('input_tokens_used', sa.Integer),
        sa.Column('output_tokens_used', sa.Integer),
        sa.Column('cost_usd', sa.Float, default=0.0),
        sa.Column('parent_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('regeneration_reason', sa.String(255)),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['generated_content.id']),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['parent_version_id'], ['content_versions.id']),
    )
    op.create_index('idx_content_version_content', 'content_versions', ['content_id'])
    op.create_index('idx_content_version_user', 'content_versions', ['user_id'])
    op.create_index('idx_content_version_conversation', 'content_versions', ['conversation_id'])
    op.create_index('idx_content_version_selected', 'content_versions', ['is_selected'])
    op.create_index('idx_content_version_rating', 'content_versions', ['user_rating'])
    op.create_index('idx_content_version_parent', 'content_versions', ['parent_version_id'])
    
    # 2. System Prompts Table
    op.create_table(
        'system_prompts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('agent_type', sa.String(100), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('prompt_text', sa.Text, nullable=False),
        sa.Column('version', sa.Integer, default=1),
        sa.Column('is_active', sa.Boolean, default=True, index=True),
        sa.Column('is_global', sa.Boolean, default=False),
        sa.Column('is_public', sa.Boolean, default=False),
        sa.Column('tags', postgresql.JSONB()),
        sa.Column('parameters', postgresql.JSONB()),
        sa.Column('total_uses', sa.Integer, default=0),
        sa.Column('average_rating', sa.Float, default=0.0),
        sa.Column('parent_prompt_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.ForeignKeyConstraint(['parent_prompt_id'], ['system_prompts.id']),
    )
    op.create_index('idx_system_prompt_agent', 'system_prompts', ['agent_type'])
    op.create_index('idx_system_prompt_user', 'system_prompts', ['user_id'])
    op.create_index('idx_system_prompt_active', 'system_prompts', ['is_active'])
    op.create_index('idx_system_prompt_parent', 'system_prompts', ['parent_prompt_id'])
    
    # 3. Message Feedback Table
    op.create_table(
        'message_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('content_version_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('rating', sa.Integer),
        sa.Column('is_helpful', sa.Boolean),
        sa.Column('is_accurate', sa.Boolean),
        sa.Column('is_relevant', sa.Boolean),
        sa.Column('feedback_text', sa.Text),
        sa.Column('has_errors', sa.Boolean, default=False),
        sa.Column('has_bias', sa.Boolean, default=False),
        sa.Column('is_inappropriate', sa.Boolean, default=False),
        sa.Column('issue_description', sa.Text),
        sa.Column('suggested_improvement', sa.Text),
        sa.Column('tags', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id']),
        sa.ForeignKeyConstraint(['content_version_id'], ['content_versions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
    )
    op.create_index('idx_feedback_message', 'message_feedback', ['message_id'])
    op.create_index('idx_feedback_user', 'message_feedback', ['user_id'])
    op.create_index('idx_feedback_conversation', 'message_feedback', ['conversation_id'])
    op.create_index('idx_feedback_rating', 'message_feedback', ['rating'])
    op.create_index('idx_feedback_helpful', 'message_feedback', ['is_helpful'])
    
    # 4. RAG Sources Table
    op.create_table(
        'rag_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('content_version_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('source_type', sa.String(50), nullable=False, index=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('source_embedding_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('source_title', sa.String(500)),
        sa.Column('source_text', sa.Text),
        sa.Column('source_url', sa.Text),
        sa.Column('similarity_score', sa.Float),
        sa.Column('relevance_score', sa.Float),
        sa.Column('was_used_in_response', sa.Boolean, default=True),
        sa.Column('usage_position', sa.Integer),
        sa.Column('usage_percentage', sa.Float),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id']),
        sa.ForeignKeyConstraint(['content_version_id'], ['content_versions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['source_embedding_id'], ['content_embeddings.id']),
    )
    op.create_index('idx_rag_source_message', 'rag_sources', ['message_id'])
    op.create_index('idx_rag_source_type', 'rag_sources', ['source_type'])
    op.create_index('idx_rag_source_user', 'rag_sources', ['user_id'])
    op.create_index('idx_rag_source_similarity', 'rag_sources', ['similarity_score'])
    op.create_index('idx_rag_source_used', 'rag_sources', ['was_used_in_response'])
    
    # 5. Conversation Context Table
    op.create_table(
        'conversation_context',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('context_window_tokens', sa.Integer, default=0),
        sa.Column('max_context_tokens', sa.Integer, default=8000),
        sa.Column('context_message_count', sa.Integer, default=0),
        sa.Column('active_system_prompt_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('system_prompt_tokens', sa.Integer, default=0),
        sa.Column('rag_enabled', sa.Boolean, default=True),
        sa.Column('rag_sources_count', sa.Integer, default=3),
        sa.Column('rag_similarity_threshold', sa.Float, default=0.5),
        sa.Column('temperature', sa.Float, default=0.7),
        sa.Column('top_p', sa.Float, default=0.9),
        sa.Column('max_generation_tokens', sa.Integer, default=2000),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['active_system_prompt_id'], ['system_prompts.id']),
    )
    op.create_index('idx_context_conversation', 'conversation_context', ['conversation_id'])
    op.create_index('idx_context_user', 'conversation_context', ['user_id'])


def downgrade():
    """Drop advanced AI agent tables."""
    op.drop_table('conversation_context')
    op.drop_table('rag_sources')
    op.drop_table('message_feedback')
    op.drop_table('system_prompts')
    op.drop_table('content_versions')
