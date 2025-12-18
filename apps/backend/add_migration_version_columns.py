#!/usr/bin/env python3
"""
Script to add migration_version columns to cache tables if they don't exist.
"""
import os
from sqlalchemy import text, inspect
from sqlalchemy.orm import sessionmaker
from database.database import engine

def add_migration_version_columns():
    """Add migration_version column to cache tables if missing."""
    inspector = inspect(engine)
    
    tables_to_update = {
        'conversation_cache': 'migration_version VARCHAR(20) DEFAULT \'1.0\'',
        'message_cache': 'migration_version VARCHAR(20) DEFAULT \'1.0\'',
        'prompt_cache': 'migration_version VARCHAR(20) DEFAULT \'1.0\'',
        'cache_embeddings': 'migration_version VARCHAR(20) DEFAULT \'1.0\''
    }
    
    with engine.connect() as conn:
        for table_name, column_def in tables_to_update.items():
            # Check if table exists
            if table_name not in inspector.get_table_names():
                print(f"⚠️  Table '{table_name}' does not exist, skipping...")
                continue
            
            # Get existing columns
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            
            if 'migration_version' in columns:
                print(f"✅ Column 'migration_version' already exists in '{table_name}'")
            else:
                # Add the column
                try:
                    alter_query = f"ALTER TABLE {table_name} ADD COLUMN {column_def};"
                    conn.execute(text(alter_query))
                    conn.commit()
                    print(f"✅ Added 'migration_version' column to '{table_name}'")
                except Exception as e:
                    print(f"❌ Error adding column to '{table_name}': {e}")
                    conn.rollback()

if __name__ == '__main__':
    print("🔄 Adding migration_version columns to cache tables...\n")
    add_migration_version_columns()
    print("\n✅ Migration complete!")
