"""
Database migration to add image_url to blog_checkpoints table.

Run this to update your database schema.
"""

from sqlalchemy import text
from database.database import SessionLocal

def migrate():
    """Add image_url column to blog_checkpoints table."""
    db = SessionLocal()
    
    try:
        print("🔄 Adding image_url column to blog_checkpoints...")
        
        # Check if column already exists
        check_sql = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='blog_checkpoints' 
            AND column_name='image_url'
        """)
        
        result = db.execute(check_sql).fetchone()
        
        if result:
            print("✅ Column 'image_url' already exists. No migration needed.")
            return
        
        # Add the column
        alter_sql = text("""
            ALTER TABLE blog_checkpoints 
            ADD COLUMN image_url TEXT NULL
        """)
        
        db.execute(alter_sql)
        db.commit()
        
        print("✅ Migration complete! Column 'image_url' added successfully.")
        print("\nCheckpoints will now store images for full restoration.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("DATABASE MIGRATION: Add Image Support to Checkpoints")
    print("="*60 + "\n")
    
    migrate()
    
    print("\n" + "="*60)
    print("Migration Complete!")
    print("="*60)
