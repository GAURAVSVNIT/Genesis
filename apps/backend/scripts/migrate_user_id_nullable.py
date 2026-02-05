"""Apply database migration to make usage_metrics.user_id nullable"""

from database.database import engine
from sqlalchemy import text

def apply_migration():
    with engine.begin() as conn:
        try:
            # Drop the foreign key constraint to allow guest IDs (guests don't have user records)
            print("Dropping foreign key constraint - allowing guest metrics...")
            conn.execute(text('ALTER TABLE usage_metrics DROP CONSTRAINT usage_metrics_user_id_fkey'))
            
            # Make user_id nullable for guests
            print("Making user_id nullable for guest metrics...")
            conn.execute(text('ALTER TABLE usage_metrics ALTER COLUMN user_id DROP NOT NULL'))
            
            print("✅ Migration successful: usage_metrics.user_id is now nullable")
            return True
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            return False

if __name__ == "__main__":
    apply_migration()
