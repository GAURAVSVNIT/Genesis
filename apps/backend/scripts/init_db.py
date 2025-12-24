"""
Database initialization script
Run: python scripts/init_db.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import engine, Base, init_db, drop_db
from database.models import (
    User, UserSettings, APIKey,
    Conversation, ConversationFolder, Message,
    GeneratedContent, ContentEmbedding, FileAttachment,
    UsageStatistics, SearchHistory, ActivityLog, ConversationShare
)

def create_tables():
    """Create all tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")

def drop_tables():
    """Drop all tables - ONLY FOR DEVELOPMENT"""
    confirm = input("⚠️  Are you sure you want to drop ALL tables? (yes/no): ")
    if confirm.lower() == "yes":
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped!")
    else:
        print("❌ Cancelled")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "create":
            create_tables()
        elif sys.argv[1] == "drop":
            drop_tables()
        else:
            print("Usage: python init_db.py [create|drop]")
    else:
        create_tables()
