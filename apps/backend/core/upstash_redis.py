from upstash_redis import Redis
from typing import Optional
from core.config import settings

class UpstashRedisClient:
    """Upstash Redis client wrapper for cloud Redis operations"""
    _instance: Optional[Redis] = None

    @classmethod
    def get_instance(cls) -> Redis:
        if cls._instance is None:
            cls._instance = Redis(
                url=settings.UPSTASH_REDIS_REST_URL,
                token=settings.UPSTASH_REDIS_REST_TOKEN
            )
        return cls._instance

    @classmethod
    async def close(cls):
        # Upstash Redis doesn't require explicit connection closing
        cls._instance = None

async def get_redis_client() -> Redis:
    """Dependency for FastAPI routes"""
    return UpstashRedisClient.get_instance()
