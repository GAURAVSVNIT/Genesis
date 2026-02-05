"""Clear all data from all tables in the database."""
from database.database import SessionLocal, engine
from sqlalchemy import text, inspect

def clear_all_data():
    """Delete all data from all tables."""
    db = SessionLocal()
    try:
        # Get all table names using inspector
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Found {len(tables)} tables to clear")
        
        for table in tables:
            try:
                db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
                print(f"✓ Cleared: {table}")
            except Exception as e:
                print(f"✗ Error clearing {table}: {str(e)}")
        
        db.commit()
        print("\n✅ All data cleared successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    response = input("⚠️  Are you sure you want to delete ALL data from all tables? (yes/no): ")
    if response.lower() == "yes":
        clear_all_data()
    else:
        print("Cancelled.")
        sys.exit(0)
