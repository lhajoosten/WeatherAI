import logging
from datetime import datetime, timedelta

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.redis_client import get_redis_client, is_redis_available

logger = logging.getLogger(__name__)


class InMemoryRateLimitService:
    """Simple in-memory rate limiting service (fallback)."""

    def __init__(self):
        # In-memory storage: {user_id: {endpoint: [(timestamp, count), ...]}}
        self._limits: dict[str, dict[str, list]] = {}
        self.requests_per_minute = settings.rate_limit_requests_per_minute
        self.llm_requests_per_minute = settings.llm_rate_limit_requests_per_minute

    def _cleanup_old_requests(self, requests: list) -> list:
        """Remove requests older than 1 minute."""
        cutoff = datetime.utcnow() - timedelta(minutes=1)
        return [req for req in requests if req[0] > cutoff]

    def _get_rate_limit(self, endpoint: str) -> int:
        """Get rate limit for endpoint."""
        if endpoint in ["explain", "chat", "analytics_llm"]:
            return self.llm_requests_per_minute
        elif endpoint == "analytics":
            # Analytics endpoints have higher limits due to dashboard usage
            # Allow burst of 30 requests per minute for dashboard loading
            return self.requests_per_minute * 3
        return self.requests_per_minute

    async def check_rate_limit(self, user_id: int | None, endpoint: str) -> bool:
        """Check if request is within rate limits."""
        key = f"user_{user_id}" if user_id else "anonymous"

        if key not in self._limits:
            self._limits[key] = {}

        if endpoint not in self._limits[key]:
            self._limits[key][endpoint] = []

        # Clean up old requests
        self._limits[key][endpoint] = self._cleanup_old_requests(self._limits[key][endpoint])

        # Check current count
        current_count = len(self._limits[key][endpoint])
        rate_limit = self._get_rate_limit(endpoint)

        if current_count >= rate_limit:
            logger.warning(
                f"Rate limit exceeded for {key} on {endpoint}",
                extra={
                    "user_id": user_id,
                    "endpoint": endpoint,
                    "current_count": current_count,
                    "rate_limit": rate_limit
                }
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {rate_limit} requests per minute for {endpoint}.",
                headers={"Retry-After": "60"}
            )

        # Record the request
        self._limits[key][endpoint].append((datetime.utcnow(), 1))

        logger.debug(
            f"Rate limit check passed for {key} on {endpoint}",
            extra={
                "user_id": user_id,
                "endpoint": endpoint,
                "current_count": current_count + 1,
                "rate_limit": rate_limit
            }
        )

        return True

    async def get_rate_limit_status(self, user_id: int | None, endpoint: str) -> dict[str, int]:
        """Get current rate limit status for debugging."""
        key = f"user_{user_id}" if user_id else "anonymous"

        if key not in self._limits or endpoint not in self._limits[key]:
            return {
                "current_count": 0,
                "rate_limit": self._get_rate_limit(endpoint),
                "remaining": self._get_rate_limit(endpoint)
            }

        # Clean up old requests
        self._limits[key][endpoint] = self._cleanup_old_requests(self._limits[key][endpoint])
        current_count = len(self._limits[key][endpoint])
        rate_limit = self._get_rate_limit(endpoint)

        return {
            "current_count": current_count,
            "rate_limit": rate_limit,
            "remaining": max(0, rate_limit - current_count)
        }


class RedisRateLimitService:
    """Redis-backed rate limiting service using sliding window (ZSET)."""

    def __init__(self):
        self.requests_per_minute = settings.rate_limit_requests_per_minute
        self.llm_requests_per_minute = settings.llm_rate_limit_requests_per_minute
        self.window_seconds = 60  # 1 minute sliding window

    def _get_rate_limit(self, endpoint: str) -> int:
        """Get rate limit for endpoint."""
        if endpoint in ["explain", "chat", "analytics_llm"]:
            return self.llm_requests_per_minute
        elif endpoint == "analytics":
            return self.requests_per_minute * 3
        return self.requests_per_minute

    def _get_redis_key(self, user_id: int | None, endpoint: str) -> str:
        """Generate Redis key for rate limiting."""
        key = f"user_{user_id}" if user_id else "anonymous"
        return f"rate_limit:{key}:{endpoint}"

    async def check_rate_limit(self, user_id: int | None, endpoint: str) -> bool:
        """Check if request is within rate limits using Redis sliding window."""
        try:
            client = await get_redis_client()
            if not client:
                # Redis unavailable, fall back to in-memory
                logger.debug("Redis unavailable, using in-memory rate limiting fallback")
                return await self._fallback_service.check_rate_limit(user_id, endpoint)

            key = self._get_redis_key(user_id, endpoint)
            rate_limit = self._get_rate_limit(endpoint)
            now = datetime.utcnow().timestamp()
            window_start = now - self.window_seconds

            # Use Redis pipeline for atomic operations
            pipe = client.pipeline()
            
            # Remove expired entries from sorted set
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(key)
            
            # Execute pipeline
            results = await pipe.execute()
            current_count = results[1]  # Result from zcard

            if current_count >= rate_limit:
                logger.warning(
                    f"Rate limit exceeded for {user_id or 'anonymous'} on {endpoint}",
                    extra={
                        "user_id": user_id,
                        "endpoint": endpoint,
                        "current_count": current_count,
                        "rate_limit": rate_limit,
                        "backend": "redis"
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Max {rate_limit} requests per minute for {endpoint}.",
                    headers={"Retry-After": "60"}
                )

            # Add current request to sorted set
            await client.zadd(key, {str(now): now})
            
            # Set expiration for the key (cleanup)
            await client.expire(key, self.window_seconds + 10)

            logger.debug(
                f"Rate limit check passed for {user_id or 'anonymous'} on {endpoint}",
                extra={
                    "user_id": user_id,
                    "endpoint": endpoint,
                    "current_count": current_count + 1,
                    "rate_limit": rate_limit,
                    "backend": "redis"
                }
            )

            return True

        except Exception as e:
            logger.warning(f"Redis rate limiting failed, falling back to in-memory: {e}")
            return await self._fallback_service.check_rate_limit(user_id, endpoint)

    async def get_rate_limit_status(self, user_id: int | None, endpoint: str) -> dict[str, int]:
        """Get current rate limit status for debugging."""
        try:
            client = await get_redis_client()
            if not client:
                return await self._fallback_service.get_rate_limit_status(user_id, endpoint)

            key = self._get_redis_key(user_id, endpoint)
            rate_limit = self._get_rate_limit(endpoint)
            now = datetime.utcnow().timestamp()
            window_start = now - self.window_seconds

            # Clean up and count in one pipeline
            pipe = client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            results = await pipe.execute()
            current_count = results[1]

            return {
                "current_count": current_count,
                "rate_limit": rate_limit,
                "remaining": max(0, rate_limit - current_count)
            }

        except Exception as e:
            logger.debug(f"Redis rate limit status check failed: {e}")
            return await self._fallback_service.get_rate_limit_status(user_id, endpoint)

    def __init__(self):
        self.requests_per_minute = settings.rate_limit_requests_per_minute
        self.llm_requests_per_minute = settings.llm_rate_limit_requests_per_minute
        self.window_seconds = 60
        # Create fallback service for when Redis is unavailable
        self._fallback_service = InMemoryRateLimitService()


class RateLimitService:
    """Adaptive rate limiting service that uses Redis when available, falls back to in-memory."""
    
    def __init__(self):
        self._redis_service = RedisRateLimitService()
        self._memory_service = InMemoryRateLimitService()
        
    async def check_rate_limit(self, user_id: int | None, endpoint: str) -> bool:
        """Check rate limit using Redis if enabled and available, otherwise in-memory."""
        if settings.use_redis_rate_limit and await is_redis_available():
            return await self._redis_service.check_rate_limit(user_id, endpoint)
        else:
            if settings.use_redis_rate_limit:
                logger.debug("Redis rate limiting requested but Redis unavailable, using in-memory fallback")
            return await self._memory_service.check_rate_limit(user_id, endpoint)
    
    async def get_rate_limit_status(self, user_id: int | None, endpoint: str) -> dict[str, int]:
        """Get rate limit status using the same backend as check_rate_limit."""
        if settings.use_redis_rate_limit and await is_redis_available():
            return await self._redis_service.get_rate_limit_status(user_id, endpoint)
        else:
            return await self._memory_service.get_rate_limit_status(user_id, endpoint)


# Global rate limiter instance
rate_limiter = RateLimitService()
