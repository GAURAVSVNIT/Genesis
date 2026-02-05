"""
Verify remaining tables in database
"""

from database.database import engine
from sqlalchemy import inspect

def verify_database():
    """Check what tables exist"""
    
    inspector = inspect(engine)
    tables = sorted(inspector.get_table_names())
    
    print("=" * 70)
    print("  CURRENT DATABASE TABLES")
    print("=" * 70)
    
    # Expected tables (should keep)
    expected = {
        'conversation_cache',
        'message_cache',
        'prompt_cache',
        'cache_embeddings',
        'cache_metrics',
        'generated_content',
        'content_embeddings',
        'usage_metrics',
        # Main user/conversation tables
        'users',
        'user_settings',
        'api_keys',
        'conversations',
        'conversation_folders',
        'messages',
    }
    
    # Find unwanted tables
    unwanted = set(tables) - expected
    
    print(f"\n✅ EXPECTED TABLES ({len(expected & set(tables))}):")
    for table in sorted(expected & set(tables)):
        print(f"  ✅ {table}")
    
    if unwanted:
        print(f"\n❌ UNWANTED TABLES STILL PRESENT ({len(unwanted)}):")
        for table in sorted(unwanted):
            print(f"  ❌ {table}")
    else:
        print(f"\n✅ NO UNWANTED TABLES - Database is clean!")
    
    print("\n" + "=" * 70)
    print(f"Total tables: {len(tables)}")
    print("=" * 70)
    
    return len(unwanted) == 0

if __name__ == "__main__":
    clean = verify_database()
    if clean:
        print("✅ Database cleanup SUCCESSFUL!")
    else:
        print("⚠️  Some unwanted tables remain")
