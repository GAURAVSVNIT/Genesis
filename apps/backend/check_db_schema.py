
import os
import sys
from sqlalchemy import text
sys.path.append(os.getcwd())
from database.database import SessionLocal

def check_schema():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT data_type, udt_name FROM information_schema.columns WHERE table_name = 'content_embeddings' AND column_name = 'embedding'")).fetchone()
        print(f"Column Type: {result}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_schema()
