"""
Empty all tables - Clear all data but keep schema
"""

from database.database import engine
from sqlalchemy import text

def empty_all_tables():
    """Truncate all tables to remove all data"""
    
    tables_to_empty = [
        'conversation_cache',
        'message_cache',
        'prompt_cache',
        'cache_embeddings',
        'cache_metrics',
        'generated_content',
        'content_embeddings',
        'usage_metrics',
    ]
    
    print("=" * 70)
    print("  EMPTYING ALL TABLES")
    print("=" * 70)
    
    print("\n📋 Tables to EMPTY:")
    for table in tables_to_empty:
        print(f"  🗑️  {table}")
    
    confirm = input("\n⚠️  Are you sure? This will DELETE ALL DATA permanently. (yes/no): ")
    
    if confirm.lower() != "yes":
        print("❌ Cancelled - no changes made")
        return False
    
    with engine.begin() as conn:
        for table in tables_to_empty:
            try:
                # Truncate table (much faster than delete, resets sequences)
                conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
                print(f"✅ Emptied: {table}")
            except Exception as e:
                print(f"⚠️  Could not empty {table}: {str(e)}")
    
    print("\n" + "=" * 70)
    print("✅ ALL TABLES EMPTIED - Ready for fresh data!")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    empty_all_tables()
