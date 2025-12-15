from redis import asyncio as aioredis
from typing import Optional

from core.config import settings

class RedisClient:
    _instance: Optional[aioredis.Redis] = None

    @classmethod
    def get_instance(cls) -> aioredis.Redis:
        if cls._instance is None:
            cls._instance = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.close()
            cls._instance = None

async def get_redis_client() -> aioredis.Redis:
    return RedisClient.get_instance()
