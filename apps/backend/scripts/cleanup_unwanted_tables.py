"""
Remove unwanted/unused tables from the database
Keep only essential tables for guest chat functionality
"""

from database.database import engine
from sqlalchemy import text

def cleanup_database():
    """Drop all unwanted tables"""
    
    # Tables to remove (unused/redundant)
    unwanted_tables = [
        'message_feedback',      # Not used
        'content_versions',      # Not integrated
        'system_prompts',        # Not used
        'rag_sources',          # Not used
        'conversation_context',  # Not used
        'activity_logs',        # Not used
        'search_history',       # Not used
        'conversation_shares',  # Not used
        'usage_statistics',     # Duplicate of usage_metrics
        'file_attachments',     # Not needed
        'cache_content_mapping', # Not needed for guest chat
        'cache_migrations',     # Not used
        # Keep main user/conversation tables for future
        # 'users',
        # 'conversations',
        # 'messages',
    ]
    
    # Tables to keep (essential for guest chat)
    keep_tables = [
        'conversation_cache',   # Guest sessions
        'message_cache',        # Guest messages
        'prompt_cache',         # Deduplication
        'cache_embeddings',     # Message embeddings
        'cache_metrics',        # Cache performance
        'generated_content',    # Content storage
        'content_embeddings',   # Content vectors
        'usage_metrics',        # Guest usage tracking
    ]
    
    print("=" * 70)
    print("  CLEANING UP UNWANTED TABLES")
    print("=" * 70)
    
    print("\n📋 Tables to REMOVE:")
    for table in unwanted_tables:
        print(f"  ❌ {table}")
    
    print("\n📋 Tables to KEEP:")
    for table in keep_tables:
        print(f"  ✅ {table}")
    
    confirm = input("\n⚠️  Are you sure? This will DELETE unwanted tables permanently. (yes/no): ")
    
    if confirm.lower() != "yes":
        print("❌ Cancelled - no changes made")
        return False
    
    with engine.begin() as conn:
        for table in unwanted_tables:
            try:
                # Drop with cascade to handle foreign keys
                conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                print(f"✅ Dropped: {table}")
            except Exception as e:
                print(f"⚠️  Could not drop {table}: {str(e)}")
    
    print("\n" + "=" * 70)
    print("✅ CLEANUP COMPLETE - Database optimized for guest chat!")
    print("=" * 70)
    print("\nRemaining tables:")
    print("  • conversation_cache   - Guest chat sessions")
    print("  • message_cache        - Guest messages")
    print("  • prompt_cache         - Prompt deduplication")
    print("  • cache_embeddings     - Message embeddings")
    print("  • cache_metrics        - Cache stats")
    print("  • generated_content    - Generated content")
    print("  • content_embeddings   - Content vectors")
    print("  • usage_metrics        - Guest usage tracking")
    
    return True

if __name__ == "__main__":
    cleanup_database()
