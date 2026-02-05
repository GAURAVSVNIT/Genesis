"""
Comprehensive test to check all cache tables and their data
"""

from database.database import SessionLocal
from database.models.cache import (
    ConversationCache, MessageCache, PromptCache,
    CacheEmbedding, CacheMetrics, CacheMigration
)
from sqlalchemy import text

def test_all_cache_tables():
    """Test all cache tables and show their row counts and sample data"""
    
    db = SessionLocal()
    
    print("=" * 80)
    print("COMPREHENSIVE CACHE TABLE AUDIT")
    print("=" * 80)
    
    # Table info
    tables_info = {
        "conversation_cache": {
            "model": ConversationCache,
            "description": "Guest/User Conversations",
            "key_fields": ["id", "user_id", "session_id", "title", "platform"]
        },
        "message_cache": {
            "model": MessageCache,
            "description": "Individual Messages in Conversations",
            "key_fields": ["id", "conversation_id", "role", "content"]
        },
        "prompt_cache": {
            "model": PromptCache,
            "description": "Cached Prompt-Response Pairs",
            "key_fields": ["id", "prompt_hash", "prompt_text", "response_text"]
        },
        "cache_embeddings": {
            "model": CacheEmbedding,
            "description": "Embeddings for Semantic Search",
            "key_fields": ["id", "conversation_id", "embedding_model"]
        },
        "cache_metrics": {
            "model": CacheMetrics,
            "description": "Cache Performance Metrics",
            "key_fields": ["id", "cache_hits", "cache_misses", "hit_rate"]
        },
        "cache_migrations": {
            "model": CacheMigration,
            "description": "Migration History",
            "key_fields": ["id", "version", "migration_type", "status"]
        },
    }
    
    # Check each table
    total_rows = 0
    for table_name, info in tables_info.items():
        model = info["model"]
        description = info["description"]
        
        print(f"\n[TABLE: {table_name}]")
        print(f"Description: {description}")
        print("-" * 80)
        
        try:
            # Get row count
            query = db.query(model)
            count = query.count()
            total_rows += count
            
            print(f"Total Rows: {count}")
            
            if count == 0:
                print("Status: EMPTY (No data)")
            else:
                print("Status: HAS DATA")
                
                # Get sample data
                sample = query.limit(3).all()
                for i, record in enumerate(sample, 1):
                    print(f"\n  Sample Record {i}:")
                    if hasattr(record, 'to_dict'):
                        data = record.to_dict()
                        for key, value in data.items():
                            if isinstance(value, str) and len(str(value)) > 60:
                                print(f"    {key}: {str(value)[:60]}...")
                            else:
                                print(f"    {key}: {value}")
                    else:
                        # Manual display
                        for field in info["key_fields"]:
                            if hasattr(record, field):
                                value = getattr(record, field)
                                if isinstance(value, str) and len(str(value)) > 60:
                                    print(f"    {field}: {str(value)[:60]}...")
                                else:
                                    print(f"    {field}: {value}")
        
        except Exception as e:
            print(f"Error querying table: {str(e)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total rows across all cache tables: {total_rows}")
    
    # Check which tables have data
    tables_with_data = []
    tables_without_data = []
    
    for table_name, info in tables_info.items():
        model = info["model"]
        count = db.query(model).count()
        if count > 0:
            tables_with_data.append(f"{table_name} ({count} rows)")
        else:
            tables_without_data.append(table_name)
    
    if tables_with_data:
        print("\nTables WITH Data:")
        for table in tables_with_data:
            print(f"  ✓ {table}")
    
    if tables_without_data:
        print("\nTables WITHOUT Data (EMPTY):")
        for table in tables_without_data:
            print(f"  ✗ {table}")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS:")
    print("=" * 80)
    
    if "prompt_cache" in tables_without_data:
        print("- prompt_cache is empty: Used for caching AI responses. Populated by API calls.")
    
    if "cache_embeddings" in tables_without_data:
        print("- cache_embeddings is empty: Used for semantic search. Needs embedding generation.")
    
    if "cache_metrics" in tables_without_data:
        print("- cache_metrics is empty: Performance tracking. Can be populated periodically.")
    
    if "cache_migrations" in tables_without_data:
        print("- cache_migrations is empty: Migration history. Tracked when moving data between systems.")
    
    db.close()

if __name__ == "__main__":
    test_all_cache_tables()
