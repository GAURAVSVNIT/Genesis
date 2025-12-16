from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Genesis"
    
    # Redis Configuration
    USE_LOCAL_REDIS: bool = False
    
    # Upstash Redis Configuration
    UPSTASH_REDIS_REST_URL: str | None = None
    UPSTASH_REDIS_REST_TOKEN: str | None = None
    GOOGLE_API_KEY: str
    
    # Legacy Redis URL (for backward compatibility)
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore" # Ignore extra fields in .env

settings = Settings()
