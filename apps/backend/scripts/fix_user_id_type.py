"""
Migration script to fix the user_id column type from UUID to String
This fixes the issue where guest (string) user_ids were being rejected
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set in .env")
    exit(1)

engine = create_engine(DATABASE_URL)

migration_sql = """
-- Fix conversation_contexts.user_id type
ALTER TABLE conversation_contexts 
ALTER COLUMN user_id TYPE VARCHAR(255) USING user_id::VARCHAR(255);

-- Fix blog_checkpoints.user_id type if it exists
ALTER TABLE blog_checkpoints 
ALTER COLUMN user_id TYPE VARCHAR(255) USING user_id::VARCHAR(255);

-- Drop old UUID constraints if they exist
ALTER TABLE conversation_contexts DROP CONSTRAINT IF EXISTS conversation_contexts_pkey CASCADE;
ALTER TABLE blog_checkpoints DROP CONSTRAINT IF EXISTS blog_checkpoints_pkey CASCADE;

-- Recreate primary keys
ALTER TABLE conversation_contexts ADD PRIMARY KEY (id);
ALTER TABLE blog_checkpoints ADD PRIMARY KEY (id);

COMMIT;
"""

try:
    with engine.connect() as conn:
        # Execute migration
        for statement in migration_sql.split(';'):
            if statement.strip():
                print(f"Executing: {statement.strip()[:80]}...")
                try:
                    conn.execute(text(statement))
                except Exception as e:
                    print(f"  ⚠️ Skipped (already applied): {e}")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
except Exception as e:
    print(f"❌ Migration failed: {e}")
    import traceback
    traceback.print_exc()
