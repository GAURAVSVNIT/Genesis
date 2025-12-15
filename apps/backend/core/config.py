from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Genesis"
    
    # Upstash Redis Configuration
    UPSTASH_REDIS_REST_URL: str = "https://viable-akita-21967.upstash.io"
    UPSTASH_REDIS_REST_TOKEN: str = "AVXPAAIncDExYzU4OGFjYTFkMWI0MmIyOGQ1ZjE1NGRlMzE5YWYxZXAxMjE5Njc"
    
    # Legacy Redis URL (for backward compatibility)
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        case_sensitive = True

settings = Settings()
