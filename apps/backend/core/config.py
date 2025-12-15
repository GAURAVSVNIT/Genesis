from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Genesis"
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        case_sensitive = True

settings = Settings()
