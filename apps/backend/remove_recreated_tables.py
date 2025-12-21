"""
Remove tables created by advanced.py and analytics.py models
"""

from database.database import engine
from sqlalchemy import text

def remove_recreated_tables():
    """Drop tables that were recreated"""
    
    # Tables from advanced.py
    advanced_tables = [
        'content_versions',
        'system_prompts',
        'message_feedback',
        'rag_sources',
        'conversation_context',
    ]
    
    # Tables from analytics.py
    analytics_tables = [
        'usage_statistics',
        'search_history',
        'activity_logs',
        'conversation_shares',
    ]
    
    tables_to_drop = advanced_tables + analytics_tables
    
    print("=" * 70)
    print("  REMOVING RECREATED TABLES")
    print("=" * 70)
    
    print("\n📋 Tables to REMOVE:")
    for table in tables_to_drop:
        print(f"  ❌ {table}")
    
    confirm = input("\n⚠️  Are you sure? This will DELETE these tables permanently. (yes/no): ")
    
    if confirm.lower() != "yes":
        print("❌ Cancelled - no changes made")
        return False
    
    with engine.begin() as conn:
        for table in tables_to_drop:
            try:
                conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                print(f"✅ Dropped: {table}")
            except Exception as e:
                print(f"⚠️  Could not drop {table}: {str(e)}")
    
    print("\n" + "=" * 70)
    print("✅ TABLES REMOVED - No longer will be recreated!")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    remove_recreated_tables()
