"""
Database migrations for cache and main content tables.
Supports seamless migration between Redis, PostgreSQL, and BigQuery.

Revision ID: 001
Revises: 
Create Date: 2025-12-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create cache and main database tables."""
    
    # ============ CACHE TABLES ============
    
    # 1. Conversation Cache Table
    op.create_table(
        'conversation_cache',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=True, index=True),
        sa.Column('session_id', sa.String(36), nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('conversation_hash', sa.String(64), nullable=False, index=True),
        sa.Column('message_count', sa.Integer, default=0),
        sa.Column('total_tokens', sa.Integer, default=0),
        sa.Column('platform', sa.String(50), nullable=True),
        sa.Column('tone', sa.String(50), nullable=True),
        sa.Column('language', sa.String(10), default='en'),
        sa.Column('created_at', sa.DateTime, nullable=False, index=True),
        sa.Column('accessed_at', sa.DateTime, nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=True, index=True),
        sa.Column('migration_version', sa.String(20), default='1.0'),
    )
    op.create_index('idx_conversation_session_created', 'conversation_cache', 
                   ['session_id', 'created_at'])
    
    # 2. Message Cache Table
    op.create_table(
        'message_cache',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('conversation_id', sa.String(36), 
                 sa.ForeignKey('conversation_cache.id'), nullable=False, index=True),
        sa.Column('role', sa.String(20), nullable=False),  # 'user' or 'assistant'
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('message_hash', sa.String(64), nullable=False, index=True),
        sa.Column('tokens', sa.Integer, default=0),
        sa.Column('sequence', sa.Integer, nullable=False),
        sa.Column('is_edited', sa.Boolean, default=False),
        sa.Column('quality_score', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('migration_version', sa.String(20), default='1.0'),
    )
    op.create_index('idx_message_conversation_sequence', 'message_cache',
                   ['conversation_id', 'sequence'])
    
    # 3. Prompt Cache Table (Deduplication)
    op.create_table(
        'prompt_cache',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('prompt_hash', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('prompt_text', sa.Text, nullable=False),
        sa.Column('response_text', sa.Text, nullable=False),
        sa.Column('response_hash', sa.String(64), nullable=False, index=True),
        sa.Column('model', sa.String(100), default='gemini-2.0-flash'),
        sa.Column('temperature', sa.Float, default=0.7),
        sa.Column('max_tokens', sa.Integer, default=2000),
        sa.Column('generation_time', sa.Float, nullable=True),
        sa.Column('input_tokens', sa.Integer, default=0),
        sa.Column('output_tokens', sa.Integer, default=0),
        sa.Column('hits', sa.Integer, default=0),
        sa.Column('last_accessed', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, index=True),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('migration_version', sa.String(20), default='1.0'),
    )
    op.create_index('idx_prompt_hash_created', 'prompt_cache', 
                   ['prompt_hash', 'created_at'])
    
    # 4. Cache Embeddings Table
    op.create_table(
        'cache_embeddings',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('conversation_id', sa.String(36), 
                 sa.ForeignKey('conversation_cache.id'), nullable=False, index=True),
        sa.Column('message_id', sa.String(36), nullable=True),
        sa.Column('embedding', postgresql.JSON, nullable=False),
        sa.Column('embedding_model', sa.String(100), default='all-MiniLM-L6-v2'),
        sa.Column('embedding_dim', sa.Integer, default=384),
        sa.Column('text_chunk', sa.Text, nullable=False),
        sa.Column('chunk_index', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False, index=True),
        sa.Column('migration_version', sa.String(20), default='1.0'),
    )
    
    # 5. Cache Metrics Table
    op.create_table(
        'cache_metrics',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('total_entries', sa.Integer, default=0),
        sa.Column('cache_hits', sa.Integer, default=0),
        sa.Column('cache_misses', sa.Integer, default=0),
        sa.Column('total_requests', sa.Integer, default=0),
        sa.Column('avg_response_time', sa.Float, default=0.0),
        sa.Column('avg_generation_time', sa.Float, default=0.0),
        sa.Column('storage_size_mb', sa.Float, default=0.0),
        sa.Column('recorded_at', sa.DateTime, nullable=False, index=True),
    )
    
    # 6. Cache Migrations Table
    op.create_table(
        'cache_migrations',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('migration_type', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), default='pending', index=True),
        sa.Column('records_migrated', sa.Integer, default=0),
        sa.Column('records_failed', sa.Integer, default=0),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('destination', sa.String(50), nullable=True),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
    )
    
    # ============ MAIN CONTENT TABLES ============
    
    # 7. Generated Content Table (Main DB)
    op.create_table(
        'generated_content',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=True, index=True),
        sa.Column('session_id', sa.String(36), nullable=False, index=True),
        sa.Column('prompt', sa.Text, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('content_type', sa.String(50), default='text'),  # text, image, video
        sa.Column('platform', sa.String(50), nullable=True),
        sa.Column('tone', sa.String(50), nullable=True),
        sa.Column('language', sa.String(10), default='en'),
        sa.Column('model', sa.String(100), default='gemini-2.0-flash'),
        sa.Column('input_tokens', sa.Integer, default=0),
        sa.Column('output_tokens', sa.Integer, default=0),
        sa.Column('generation_time', sa.Float, nullable=True),
        sa.Column('status', sa.String(20), default='draft'),  # draft, published, archived
        sa.Column('created_at', sa.DateTime, nullable=False, index=True),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('published_at', sa.DateTime, nullable=True),
        sa.Column('cached_from', sa.String(36), nullable=True),  # Reference to prompt_cache if from cache
        sa.Column('migration_version', sa.String(20), default='1.0'),
    )
    op.create_index('idx_generated_user_created', 'generated_content',
                   ['user_id', 'created_at'])
    op.create_index('idx_generated_status', 'generated_content', ['status'])
    
    # 8. Content Embeddings Table (Main DB)
    op.create_table(
        'content_embeddings',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('content_id', sa.String(36), 
                 sa.ForeignKey('generated_content.id'), nullable=False, index=True),
        sa.Column('embedding', postgresql.JSON, nullable=False),
        sa.Column('embedding_model', sa.String(100), default='all-MiniLM-L6-v2'),
        sa.Column('embedding_dim', sa.Integer, default=384),
        sa.Column('text_chunk', sa.Text, nullable=False),
        sa.Column('chunk_index', sa.Integer, default=0),
        sa.Column('is_valid', sa.Boolean, default=True),
        sa.Column('confidence_score', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('migration_version', sa.String(20), default='1.0'),
    )
    op.create_index('idx_content_embeddings_content', 'content_embeddings',
                   ['content_id', 'chunk_index'])
    
    # 9. Usage Metrics Table (Main DB)
    op.create_table(
        'usage_metrics',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=True, index=True),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('content_id', sa.String(36), 
                 sa.ForeignKey('generated_content.id'), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),  # generated, cached_hit, published, viewed
        sa.Column('tokens_used', sa.Integer, default=0),
        sa.Column('cost_cents', sa.Float, default=0.0),
        sa.Column('response_time_ms', sa.Float, nullable=True),
        sa.Column('platform', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, index=True),
        sa.Column('migration_version', sa.String(20), default='1.0'),
    )
    op.create_index('idx_usage_user_created', 'usage_metrics',
                   ['user_id', 'created_at'])
    op.create_index('idx_usage_action', 'usage_metrics', ['action'])
    
    # 10. Cache to Content Mapping (for migration tracking)
    op.create_table(
        'cache_content_mapping',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('conversation_id', sa.String(36), 
                 sa.ForeignKey('conversation_cache.id'), nullable=False),
        sa.Column('content_id', sa.String(36), 
                 sa.ForeignKey('generated_content.id'), nullable=False),
        sa.Column('prompt_cache_id', sa.String(36), nullable=True),
        sa.Column('mapping_type', sa.String(50)),  # 'full_conversation', 'single_prompt', 'multi_message'
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    op.create_index('idx_mapping_conversation', 'cache_content_mapping',
                   ['conversation_id'])
    op.create_index('idx_mapping_content', 'cache_content_mapping', ['content_id'])


def downgrade():
    """Drop all cache and content tables (for rollback)."""
    
    tables_to_drop = [
        'cache_content_mapping',
        'usage_metrics',
        'content_embeddings',
        'generated_content',
        'cache_migrations',
        'cache_metrics',
        'cache_embeddings',
        'prompt_cache',
        'message_cache',
        'conversation_cache',
    ]
    
    for table in tables_to_drop:
        op.drop_table(table, if_exists=True)
