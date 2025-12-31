from sqlalchemy import create_engine, text
import uuid
import sys
import os

# Adjust path to find core/database modules
sys.path.append(os.path.join(os.getcwd(), "apps/backend"))

from dotenv import load_dotenv
import os

# Load env from apps/backend/.env
env_path = os.path.join(os.getcwd(), "apps/backend/.env")
load_dotenv(env_path)

db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("Error: DATABASE_URL not found in .env")
    # Fallback/Debug
    print(f"Current Env: {os.getcwd()}")
    sys.exit(1)

print(f"Connecting to DB...")
engine = create_engine(db_url)

# The User ID that caused the error
MISSING_USER_ID = "3540555e-1e14-4b98-b413-99cc7086fa48" 

def seed_missing_user():
    with engine.connect() as conn:
        # Check if user exists
        result = conn.execute(text("SELECT id FROM users WHERE id = :uid"), {"uid": MISSING_USER_ID})
        user = result.fetchone()
        
        if user:
            print(f"User {MISSING_USER_ID} already exists.")
            return

        print(f"Creating user {MISSING_USER_ID}...")
        
        # Simple Insert - adjust columns based on your User model
        # Assuming minimal columns needed: id, email, created_at, etc.
        # If your user table has other constraints, add them here.
        try:
            conn.execute(
                text("""
                    INSERT INTO users (id, email, username, password_hash, full_name, status, account_type, created_at, updated_at)
                    VALUES (:uid, :email, :username, :password_hash, :name, :status, :account_type, NOW(), NOW())
                """),
                {
                    "uid": MISSING_USER_ID,
                    "email": "debug_user@example.com",
                    "username": "debug_user_3540555e",
                    "password_hash": "placeholder_hash_not_for_login",
                    "name": "Debug User",
                    "status": "active",
                    "account_type": "free"
                }
            )
            conn.commit()
            print("User created successfully!")
        except Exception as e:
            print(f"Failed to create user: {e}")

if __name__ == "__main__":
    seed_missing_user()
