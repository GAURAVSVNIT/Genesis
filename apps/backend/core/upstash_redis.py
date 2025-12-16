from upstash_redis import Redis as UpstashRedis
import redis
from typing import Union, Optional
from core.config import settings

RedisClientType = Union[UpstashRedis, redis.Redis]

class RedisManager:
    """Redis client wrapper supporting both Upstash (HTTP) and Local (TCP) Redis"""
    _instance: Optional[RedisClientType] = None

    @classmethod
    def get_instance(cls) -> RedisClientType:
        if cls._instance is None:
            if settings.USE_LOCAL_REDIS:
                # Use standard Redis client (Local)
                try:
                    cls._instance = redis.from_url(settings.REDIS_URL, decode_responses=True)
                    # Verify connection
                    cls._instance.ping()
                    print(f"Connected to Local Redis at {settings.REDIS_URL}")
                except Exception as e:
                    print(f"Failed to connect to local Redis: {e}")
                    raise
            else:
                # Use Upstash Redis client
                if not settings.UPSTASH_REDIS_REST_URL or not settings.UPSTASH_REDIS_REST_TOKEN:
                     raise ValueError("Upstash configuration missing. Set UPSTASH_REDIS_REST_URL/TOKEN or USE_LOCAL_REDIS=True")
                
                cls._instance = UpstashRedis(
                    url=settings.UPSTASH_REDIS_REST_URL,
                    token=settings.UPSTASH_REDIS_REST_TOKEN
                )
                print("Connected to Upstash Redis")
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance:
             if hasattr(cls._instance, 'close'):
                 cls._instance.close()
             cls._instance = None

# Alias for backward compatibility
UpstashRedisClient = RedisManager

async def get_redis_client() -> RedisClientType:
    """Dependency for FastAPI routes"""
    return RedisManager.get_instance()
