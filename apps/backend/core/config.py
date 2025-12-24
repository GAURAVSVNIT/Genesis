from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
from pathlib import Path

# Get the backend directory
BACKEND_DIR = Path(__file__).parent.parent

# Load .env file from backend directory
load_dotenv(BACKEND_DIR / '.env')
# Also try from parent directory if not found
if not os.getenv('UPSTASH_REDIS_REST_URL'):
    load_dotenv(BACKEND_DIR.parent / '.env')

class Settings(BaseSettings):
    PROJECT_NAME: str = "Genesis"
    
    # GCP Configuration
    GCP_PROJECT_ID: str | None = None
    
    # Redis Configuration
    USE_LOCAL_REDIS: bool = False
    
    # Upstash Redis Configuration
    UPSTASH_REDIS_REST_URL: str | None = None
    UPSTASH_REDIS_REST_TOKEN: str | None = None
    
    # Legacy Redis URL (for backward compatibility)
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields in .env

settings = Settings()
