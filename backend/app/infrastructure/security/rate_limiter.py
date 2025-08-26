"""Rate limiting implementation using Redis.

This module provides rate limiting functionality to prevent abuse
and ensure fair usage of API resources.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
import time

from app.domain.exceptions import DomainError
from app.core.logging import get_logger


logger = get_logger(__name__)


class RateLimitExceededError(DomainError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, limit: int, window_seconds: int, retry_after: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded: {limit} requests per {window_seconds} seconds. "
            f"Retry after {retry_after} seconds."
        )


class RateLimiter(ABC):
    """Abstract base class for rate limiting implementations."""
    
    @abstractmethod
    async def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int
    ) -> tuple[bool, int]:
        """Check if request is allowed.
        
        Args:
            key: Unique identifier for the rate limit (e.g., user_id, ip_address)
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        pass


class InMemoryRateLimiter(RateLimiter):
    """Simple in-memory rate limiter for development/testing."""
    
    def __init__(self):
        self._requests: dict[str, list[float]] = {}
    
    async def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int
    ) -> tuple[bool, int]:
        """Check if request is allowed using in-memory storage."""
        now = time.time()
        
        # Initialize or get existing requests for this key
        if key not in self._requests:
            self._requests[key] = []
        
        requests = self._requests[key]
        
        # Remove requests outside the current window
        cutoff = now - window_seconds
        requests[:] = [req_time for req_time in requests if req_time > cutoff]
        
        # Check if we're within the limit
        if len(requests) >= limit:
            # Calculate retry after based on oldest request in window
            oldest_request = min(requests)
            retry_after = int(oldest_request + window_seconds - now) + 1
            return False, retry_after
        
        # Add current request
        requests.append(now)
        return True, 0


class RedisRateLimiter(RateLimiter):
    """Redis-based rate limiter using sliding window algorithm."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int
    ) -> tuple[bool, int]:
        """Check if request is allowed using Redis sliding window."""
        now = time.time()
        pipeline = self.redis.pipeline()
        
        # Redis key for this rate limit
        redis_key = f"rate_limit:{key}"
        
        # Remove expired entries
        pipeline.zremrangebyscore(redis_key, 0, now - window_seconds)
        
        # Count current requests in window
        pipeline.zcard(redis_key)
        
        # Add current request
        pipeline.zadd(redis_key, {str(now): now})
        
        # Set expiration for cleanup
        pipeline.expire(redis_key, window_seconds + 1)
        
        try:
            results = await pipeline.execute()
            current_requests = results[1]  # Count result
            
            if current_requests >= limit:
                # Get oldest request to calculate retry after
                oldest = await self.redis.zrange(redis_key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = oldest[0][1]
                    retry_after = int(oldest_time + window_seconds - now) + 1
                else:
                    retry_after = window_seconds
                
                # Remove the request we just added since it's not allowed
                await self.redis.zrem(redis_key, str(now))
                return False, retry_after
            
            return True, 0
            
        except Exception as e:
            logger.error("Rate limiter Redis error, allowing request", error=str(e))
            # Fail open - allow request if Redis is down
            return True, 0


# Global rate limiter instance (will be initialized based on configuration)
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        # Default to in-memory for development
        _rate_limiter = InMemoryRateLimiter()
    return _rate_limiter


def set_rate_limiter(limiter: RateLimiter) -> None:
    """Set the global rate limiter instance."""
    global _rate_limiter
    _rate_limiter = limiter


async def check_rate_limit(
    key: str,
    limit: int = 100,
    window_seconds: int = 3600
) -> None:
    """Check rate limit and raise exception if exceeded.
    
    Args:
        key: Unique identifier for rate limiting
        limit: Maximum requests allowed
        window_seconds: Time window in seconds
        
    Raises:
        RateLimitExceededError: If rate limit is exceeded
    """
    limiter = get_rate_limiter()
    is_allowed, retry_after = await limiter.is_allowed(key, limit, window_seconds)
    
    if not is_allowed:
        raise RateLimitExceededError(limit, window_seconds, retry_after)