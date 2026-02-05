"""
Audit all cache tables to check current data status.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import SessionLocal
from database.models.cache import (
    ConversationCache, MessageCache, PromptCache, 
    CacheEmbedding, CacheMetrics, CacheMigration
)
from sqlalchemy import func

db = SessionLocal()

print("\n" + "="*70)
print("CURRENT CACHE TABLES DATA STATUS")
print("="*70)

tables = [
    ("conversation_cache", ConversationCache, "user_id, platform, message_count"),
    ("message_cache", MessageCache, "role, conversation_id"),
    ("prompt_cache", PromptCache, "model, hits"),
    ("cache_embeddings", CacheEmbedding, "embedding_model, embedding_dim"),
    ("cache_metrics", CacheMetrics, "cache_hits, cache_misses, hit_rate"),
    ("cache_migrations", CacheMigration, "migration_type, status"),
]

for table_name, model, display_fields in tables:
    count = db.query(func.count(model.id)).scalar()
    
    print(f"\n[{table_name}]")
    print(f"  Total Records: {count}")
    
    if count == 0:
        print(f"  Status: [EMPTY] - NO DATA")
    elif count > 0:
        print(f"  Status: [HAS DATA]")
        
        # Show sample records
        records = db.query(model).limit(3).all()
        for i, record in enumerate(records, 1):
            print(f"    Sample {i}:")
            if table_name == "conversation_cache":
                print(f"      - user_id: {record.user_id}, platform: {record.platform}, messages: {record.message_count}")
            elif table_name == "message_cache":
                print(f"      - role: {record.role}, sequence: {record.sequence}")
            elif table_name == "prompt_cache":
                print(f"      - model: {record.model}, hits: {record.hits}")
            elif table_name == "cache_embeddings":
                print(f"      - model: {record.embedding_model}, dimensions: {record.embedding_dim}")
            elif table_name == "cache_metrics":
                print(f"      - hits: {record.cache_hits}, misses: {record.cache_misses}, hit_rate: {record.hit_rate:.1f}%")
            elif table_name == "cache_migrations":
                print(f"      - type: {record.migration_type}, status: {record.status}, records: {record.records_migrated}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)

total_records = 0
empty_tables = []

for table_name, model, _ in tables:
    count = db.query(func.count(model.id)).scalar()
    total_records += count
    if count == 0:
        empty_tables.append(table_name)

print(f"\nTotal Records Across All Tables: {total_records}")
print(f"Empty Tables: {len(empty_tables)}")

if empty_tables:
    print("\nTables With NO Data:")
    for table in empty_tables:
        print(f"  - {table}")
else:
    print("\nAll tables have data!")

print("\n" + "="*70)
