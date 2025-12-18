"""Sliding window rate limiter with Redis backend."""

from typing import Tuple
from core.upstash_redis import RedisManager
import time
import math


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter using Redis.
    
    Better than fixed window because:
    - Fixed window: resets at exact times, allows burst at boundaries
    - Sliding window: smooth rate limiting, prevents burst attacks
    
    Example:
    - Fixed window (5 req/60s): User can send 10 in 2 seconds at boundary
    - Sliding window: Always enforces 5 per 60s moving window
    """
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Max requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.redis = RedisManager.get_instance()
    
    def check_rate_limit(
        self,
        identifier: str,
        is_premium: bool = False
    ) -> Tuple[bool, int, int]:
        """
        Check if request is allowed (sliding window algorithm).
        
        Args:
            identifier: Unique ID (user_id, session_id, or IP)
            is_premium: If True, use higher limits
            
        Returns:
            (allowed: bool, remaining: int, reset_after: int)
        """
        
        # Premium users get 3x the limit
        limit = self.max_requests * 3 if is_premium else self.max_requests
        
        current_time = time.time()
        key = f"rate_limit:sliding:{identifier}"
        
        # Get all timestamps in current window
        window_start = current_time - self.window_seconds
        
        try:
            # Use Redis sorted set to store request timestamps
            # This is perfect for sliding window!
            
            # 1. Remove old requests outside window
            self.redis.zremrangebyscore(key, 0, window_start)
            
            # 2. Count requests in current window
            count = self.redis.zcard(key)
            
            # 3. Check if limit exceeded
            if count >= limit:
                # Get oldest request timestamp to calculate reset time
                oldest = self.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    reset_after = int(oldest[0][1] + self.window_seconds - current_time)
                else:
                    reset_after = self.window_seconds
                
                return False, 0, max(1, reset_after)
            
            # 4. Add current request with timestamp as score
            self.redis.zadd(key, {str(current_time): current_time})
            
            # 5. Set expiration on key (cleanup old data)
            self.redis.expire(key, self.window_seconds + 1)
            
            remaining = limit - count - 1
            return True, remaining, 0
            
        except Exception as e:
            print(f"Rate limit check error: {e}")
            # Fail open: allow if Redis fails
            return True, limit, 0


# Preset configurations
RATE_LIMITERS = {
    "free_user": SlidingWindowRateLimiter(max_requests=5, window_seconds=60),      # 5 req/min
    "premium_user": SlidingWindowRateLimiter(max_requests=100, window_seconds=60),  # 100 req/min
    "guest": SlidingWindowRateLimiter(max_requests=3, window_seconds=60),           # 3 req/min
    "api_key": SlidingWindowRateLimiter(max_requests=1000, window_seconds=3600),   # 1000 req/hour
}
