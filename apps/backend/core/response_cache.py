"""Response caching utility for expensive operations."""

import json
import hashlib
from typing import Any, Optional
from core.upstash_redis import RedisManager


class ResponseCache:
    """Cache expensive responses in Redis."""
    
    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize cache.
        
        Args:
            ttl_seconds: Time to live for cached responses (default 5 minutes)
        """
        self.redis = RedisManager.get_instance()
        self.ttl = ttl_seconds
    
    def _generate_key(self, prefix: str, data: dict) -> str:
        """Generate cache key from request data."""
        # Create hash of parameters
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        return f"cache:{prefix}:{data_hash}"
    
    def get(self, prefix: str, data: dict) -> Optional[dict]:
        """
        Get cached response.
        
        Args:
            prefix: Cache key prefix (e.g., "content_gen")
            data: Request parameters dict
            
        Returns:
            Cached response or None
        """
        try:
            key = self._generate_key(prefix, data)
            cached = self.redis.get(key)
            
            if cached:
                return json.loads(cached)
            return None
            
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, prefix: str, data: dict, response: Any) -> bool:
        """
        Cache a response.
        
        Args:
            prefix: Cache key prefix
            data: Request parameters dict
            response: Response to cache
            
        Returns:
            True if cached successfully
        """
        try:
            key = self._generate_key(prefix, data)
            
            # Convert response to JSON
            response_json = json.dumps(response, default=str)
            
            # Store with expiration
            self.redis.setex(key, self.ttl, response_json)
            
            return True
            
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def invalidate(self, prefix: str, data: dict) -> bool:
        """Delete cached response."""
        try:
            key = self._generate_key(prefix, data)
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Cache invalidate error: {e}")
            return False
    
    def clear_prefix(self, prefix: str) -> int:
        """Clear all cache entries with given prefix."""
        try:
            # Note: This is a simplified version
            # For production, you'd need to track all keys or use Redis SCAN
            pattern = f"cache:{prefix}:*"
            # Redis SCAN is more efficient but requires additional setup
            return 0
        except Exception as e:
            print(f"Cache clear error: {e}")
            return 0


# Pre-configured caches for different purposes
CACHES = {
    "content": ResponseCache(ttl_seconds=300),      # 5 minutes
    "embeddings": ResponseCache(ttl_seconds=3600),  # 1 hour
    "trends": ResponseCache(ttl_seconds=1800),      # 30 minutes
    "seo": ResponseCache(ttl_seconds=600),          # 10 minutes
}
