"""
Remove final unwanted tables
"""

from database.database import engine
from sqlalchemy import text

def remove_final_unwanted():
    """Drop remaining unwanted tables"""
    
    tables = [
        'cache_content_mapping',
        'cache_migrations',
        'chats',
        'file_attachments',
    ]
    
    print("=" * 70)
    print("  REMOVING FINAL UNWANTED TABLES")
    print("=" * 70)
    
    print("\n📋 Tables to REMOVE:")
    for table in tables:
        print(f"  ❌ {table}")
    
    confirm = input("\n⚠️  Remove these tables? (yes/no): ")
    
    if confirm.lower() != "yes":
        print("❌ Cancelled")
        return False
    
    with engine.begin() as conn:
        for table in tables:
            try:
                conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                print(f"✅ Dropped: {table}")
            except Exception as e:
                print(f"⚠️  {table}: {str(e)}")
    
    print("\n✅ CLEANUP COMPLETE!")
    return True

if __name__ == "__main__":
    remove_final_unwanted()
