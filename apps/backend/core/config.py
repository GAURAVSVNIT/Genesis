from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Genesis"
    
    # Upstash Redis Configuration
    UPSTASH_REDIS_REST_URL: str
    UPSTASH_REDIS_REST_TOKEN: str
    GOOGLE_API_KEY: str
    
    # Legacy Redis URL (for backward compatibility)
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        case_sensitive = True

settings = Settings()
