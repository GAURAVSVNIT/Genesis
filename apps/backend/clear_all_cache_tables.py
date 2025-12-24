"""
Clear all data from cache tables (respecting foreign key constraints).
WARNING: This will delete ALL records from all cache tables!
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import SessionLocal
from database.models.cache import (
    ConversationCache, MessageCache, PromptCache, 
    CacheEmbedding, CacheMetrics, CacheMigration
)

db = SessionLocal()

print("\n" + "="*70)
print("CLEARING ALL CACHE TABLES")
print("="*70)

# Delete in order respecting foreign key constraints
tables_to_clear = [
    ("cache_embeddings", CacheEmbedding),
    ("message_cache", MessageCache),
    ("cache_migrations", CacheMigration),
    ("cache_metrics", CacheMetrics),
    ("prompt_cache", PromptCache),
    ("conversation_cache", ConversationCache),
]

try:
    for table_name, model in tables_to_clear:
        count_before = db.query(model).count()
        db.query(model).delete()
        db.commit()
        print(f"[OK] {table_name:25} - Cleared {count_before} records")
    
    print("\n" + "="*70)
    print("SUCCESS! All cache tables have been cleared.")
    print("="*70 + "\n")

except Exception as e:
    db.rollback()
    print(f"\n[ERROR] Failed to clear tables: {str(e)}")
    print("="*70 + "\n")
