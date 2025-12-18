"""
Database configuration and session management for Supabase PostgreSQL
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Database Configuration - Support both Supabase (production) and SQLite (local dev)
DATABASE_URL = os.getenv("DATABASE_URL")
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

# Use SQLite for local development without internet
if USE_SQLITE or not DATABASE_URL:
    DATABASE_URL = "sqlite:///./genesis.db"
    print("⚠️  Using SQLite for local development: ./genesis.db")
    # SQLite engine for development
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("DEBUG", "false").lower() == "true",
        connect_args={"check_same_thread": False},
    )
else:
    # Supabase PostgreSQL engine for production
    print("✅ Using Supabase PostgreSQL for production")
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("DEBUG", "false").lower() == "true",
        poolclass=NullPool,  # Important for serverless/railway deployments
        connect_args={
            "options": "-c timezone=utc",  # Set UTC timezone
            "keepalives": 1,
            "keepalives_idle": 30,
        }
    )

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for models
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database - create all tables if they don't exist"""
    # Check if any tables exist
    inspector = __import__('sqlalchemy').inspect(engine)
    existing_tables = inspector.get_table_names()
    
    Base.metadata.create_all(bind=engine)
    
    if existing_tables:
        print("✅ Database already initialized - all tables present")
    else:
        print("✅ Database tables created successfully!")

def drop_db():
    """Drop all tables - ONLY FOR DEVELOPMENT"""
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped!")
