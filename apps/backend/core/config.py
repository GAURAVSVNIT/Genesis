from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
from pathlib import Path

# Get the backend directory
BACKEND_DIR = Path(__file__).parent.parent

# Load .env file from backend directory
load_dotenv(BACKEND_DIR / '.env')
# Also try from parent directory if not found
# Also try from parent directory if not found
if not os.getenv('UPSTASH_REDIS_REST_URL'):
    load_dotenv(BACKEND_DIR.parent / '.env')

# FIX: Ensure Google Credentials path is correct relative to current project structure
gcp_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if gcp_creds:
    creds_path = Path(gcp_creds)
    if not creds_path.exists():
        # Try to find it in the backend directory
        local_creds = BACKEND_DIR / creds_path.name
        if local_creds.exists():
            print(f"⚠️ Fixing Google Credentials path from '{gcp_creds}' to '{local_creds}'")
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(local_creds)
        else:
             print(f"❌ Google Credentials file not found at '{gcp_creds}' or '{local_creds}'")

class Settings(BaseSettings):
    PROJECT_NAME: str = "Genesis"
    
    # GCP Configuration
    GCP_PROJECT_ID: str | None = None
    
    # Redis Configuration
    USE_LOCAL_REDIS: bool = False
    
    # Upstash Redis Configuration
    UPSTASH_REDIS_REST_URL: str | None = None
    UPSTASH_REDIS_REST_TOKEN: str | None = None
    
    # AI Models
    OPENAI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    
    # Legacy Redis URL (for backward compatibility)
    REDIS_URL: str = "redis://localhost:6379/0"

    # LinkedIn Configuration
    LINKEDIN_CLIENT_ID: str | None = None
    LINKEDIN_CLIENT_SECRET: str | None = None

    # Twitter Configuration
    TWITTER_CLIENT_ID: str | None = None
    TWITTER_CLIENT_SECRET: str | None = None

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields in .env

settings = Settings()
