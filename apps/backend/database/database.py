"""
Database configuration and session management for Supabase PostgreSQL
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()

# Database Configuration - Supabase PostgreSQL (production)
DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")  # Default to 'postgres' if not set

logger.info(f"🔍 Checking DATABASE_URL: {'SET' if DATABASE_URL else 'NOT SET'}")
logger.info(f"🔍 Checking SUPABASE_URL: {'SET' if SUPABASE_URL else 'NOT SET'}")
logger.info(f"🔍 Checking DB_PASSWORD: {'SET' if DB_PASSWORD and DB_PASSWORD != 'postgres' else 'USING DEFAULT'}")

if not DATABASE_URL and SUPABASE_URL:
    # Transform https://[REF].supabase.co to postgresql://postgres:[PASS]@db.[REF].supabase.co:5432/postgres
    try:
        project_ref = SUPABASE_URL.split("://")[1].split(".")[0]
        DATABASE_URL = f"postgresql://postgres:{DB_PASSWORD}@db.{project_ref}.supabase.co:5432/postgres"
        logger.info(f"🔗 Derived DATABASE_URL from SUPABASE_URL for project: {project_ref}")
    except Exception as e:
        logger.error(f"❌ Failed to derive DATABASE_URL: {e}")

if not DATABASE_URL:
    logger.error("ERROR: DATABASE_URL (or SUPABASE_URL + DB_PASSWORD) is not set!")
    logger.error("Please set these in your .env file.")
    raise ValueError("DATABASE_URL not found")

# Log the masked URL for debugging
masked_url = DATABASE_URL.replace(DB_PASSWORD, "***") if DB_PASSWORD in DATABASE_URL else DATABASE_URL
logger.info(f"✅ Using DATABASE_URL: {masked_url}")

try:
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
    logger.info("✅ SQLAlchemy engine created successfully")
    
    # Test connection
    with engine.connect() as conn:
        logger.info("✅ Database connection test SUCCESSFUL")
except Exception as e:
    logger.error(f"❌ Failed to create engine or test connection: {e}")
    import traceback
    logger.error(traceback.format_exc())

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
    try:
        # Check if any tables exist
        inspector = __import__('sqlalchemy').inspect(engine)
        existing_tables = inspector.get_table_names()
        
        logger.info(f"📊 Existing tables in database: {existing_tables}")
        
        Base.metadata.create_all(bind=engine)
        
        logger.info(f"✅ All base model tables created (total: {len(Base.metadata.tables)})")
        logger.info(f"📋 Tables created: {list(Base.metadata.tables.keys())}")
        
        if existing_tables:
            logger.info("✅ Database already initialized - all tables present")
        else:
            logger.info("✅ Database tables created successfully!")
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

def drop_db():
    """Drop all tables - ONLY FOR DEVELOPMENT"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ All tables dropped!")
    except Exception as e:
        logger.error(f"❌ Error dropping tables: {e}")
        raise
