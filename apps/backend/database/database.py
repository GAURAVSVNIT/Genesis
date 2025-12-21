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

# Database Configuration - Supabase PostgreSQL (production)
DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")  # Default to 'postgres' if not set

if not DATABASE_URL and SUPABASE_URL:
    # Transform https://[REF].supabase.co to postgresql://postgres:[PASS]@db.[REF].supabase.co:5432/postgres
    try:
        project_ref = SUPABASE_URL.split("://")[1].split(".")[0]
        DATABASE_URL = f"postgresql://postgres:{DB_PASSWORD}@db.{project_ref}.supabase.co:5432/postgres"
        print(f"🔗 Derived DATABASE_URL from SUPABASE_URL for project: {project_ref}")
    except Exception as e:
        print(f"❌ Failed to derive DATABASE_URL: {e}")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL (or SUPABASE_URL + DB_PASSWORD) is not set!")
    print("Please set these in your .env file.")
    raise ValueError("DATABASE_URL not found")

print("Using production database configuration")
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
