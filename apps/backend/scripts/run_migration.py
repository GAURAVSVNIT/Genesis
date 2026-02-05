#!/usr/bin/env python3
"""Direct migration runner - creates missing tables"""

from sqlalchemy import text
from database.database import engine

def run_migration():
    """Create the 4 missing tables directly"""
    
    with engine.connect() as conn:
        # Read the migration file
        with open('alembic/versions/002_add_advanced_ai_models.py', 'r') as f:
            content = f.read()
        
        print("Executing migration: Create Advanced AI Models\n")
        
        # Extract and run SQL
        # The migration has upgrade() and downgrade() functions
        # We'll execute the SQL directly
        
        sqls = [
            # ContentVersion table
            """
            CREATE TABLE IF NOT EXISTS content_versions (
                id UUID PRIMARY KEY,
                content_id UUID NOT NULL REFERENCES generated_content(id) ON DELETE CASCADE,
                conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                version_number INTEGER NOT NULL,
                is_selected BOOLEAN DEFAULT false,
                generated_content JSONB,
                model_used VARCHAR(255),
                temperature FLOAT,
                seo_score FLOAT,
                uniqueness_score FLOAT,
                engagement_score FLOAT,
                user_rating INTEGER,
                parent_version_id UUID REFERENCES content_versions(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP
            )
            """,
            
            # MessageFeedback table
            """
            CREATE TABLE IF NOT EXISTS message_feedback (
                id UUID PRIMARY KEY,
                message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                rating INTEGER,
                is_helpful BOOLEAN,
                is_accurate BOOLEAN,
                is_relevant BOOLEAN,
                feedback_text TEXT,
                has_errors BOOLEAN,
                suggested_improvement TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP
            )
            """,
            
            # RAGSource table
            """
            CREATE TABLE IF NOT EXISTS rag_sources (
                id UUID PRIMARY KEY,
                message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                source_type VARCHAR(50),
                source_id UUID,
                similarity_score FLOAT,
                was_used_in_response BOOLEAN DEFAULT false,
                source_content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP
            )
            """,
            
            # ConversationContext table
            """
            CREATE TABLE IF NOT EXISTS conversation_context (
                id UUID PRIMARY KEY,
                conversation_id UUID NOT NULL UNIQUE REFERENCES conversations(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                context_window_tokens INTEGER DEFAULT 2000,
                max_context_tokens INTEGER DEFAULT 8000,
                rag_enabled BOOLEAN DEFAULT true,
                temperature FLOAT,
                top_p FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP
            )
            """
        ]
        
        for i, sql in enumerate(sqls, 1):
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"[OK] Created table {i}/4")
            except Exception as e:
                print(f"[ERROR] Table {i}: {str(e)}")
                conn.rollback()
        
        print("\n" + "="*60)
        print("Migration complete!")
        print("="*60)

if __name__ == "__main__":
    run_migration()
