import logging
import time
from datetime import datetime, timedelta

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.redis_client import redis_client, get_redis_client, is_redis_available

logger = logging.getLogger(__name__)

class RateLimitService:
    """Redis-based rate limiting service with in-memory fallback."""

    def __init__(self):
        # In-memory storage for fallback: {user_id: {endpoint: [(timestamp, count), ...]}}
        self._limits: dict[str, dict[str, list]] = {}
        self.requests_per_minute = settings.rate_limit_requests_per_minute
        self.llm_requests_per_minute = settings.llm_rate_limit_requests_per_minute
        self.use_redis = settings.use_redis_rate_limit

    def _cleanup_old_requests(self, requests: list) -> list:
        """Remove requests older than 1 minute (fallback mode)."""
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

    def _get_redis_key(self, user_id: int | None, endpoint: str) -> str:
        """Generate Redis key for rate limiting."""
        key = f"user_{user_id}" if user_id else "anonymous"
        return f"ratelimit:{key}:{endpoint}"

    async def _check_redis_rate_limit(self, user_id: int | None, endpoint: str) -> bool:
        """Check rate limit using Redis ZSET sliding window."""
        if not redis_client.is_connected:
            return await self._check_fallback_rate_limit(user_id, endpoint)
        
        key = self._get_redis_key(user_id, endpoint)
        current_time = time.time()
        window_start = current_time - 60  # 60 seconds sliding window
        rate_limit = self._get_rate_limit(endpoint)
        
        try:
            # Remove old entries
            await redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            current_count = await redis_client.zcard(key)
            
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
            
            # Add current request
            await redis_client.zadd(key, {str(current_time): current_time})
            
            # Set expiration for cleanup
            await redis_client.expire(key, 120)  # 2 minutes to be safe
            
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
            
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(
                f"Redis rate limiting failed, falling back to in-memory: {e}",
                extra={"user_id": user_id, "endpoint": endpoint, "error": str(e)}
            )
            return await self._check_fallback_rate_limit(user_id, endpoint)

    async def _check_fallback_rate_limit(self, user_id: int | None, endpoint: str) -> bool:
        """Check rate limit using in-memory fallback."""
        
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
                    "rate_limit": rate_limit,
                    "backend": "memory"
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
                "rate_limit": rate_limit,
                "backend": "memory"
            }
        )

        return True

    async def check_rate_limit(self, user_id: int | None, endpoint: str) -> bool:
        """
        Check if request is within rate limits.
        
        Args:
            user_id: User ID (None for anonymous users)
            endpoint: Endpoint name
            
        Returns:
            True if request is allowed, raises HTTPException if rate limited
        """
        if self.use_redis and redis_client.is_connected:
            return await self._check_redis_rate_limit(user_id, endpoint)
        else:
            return await self._check_fallback_rate_limit(user_id, endpoint)

    async def get_rate_limit_status(self, user_id: int | None, endpoint: str) -> dict[str, int]:
        """Get current rate limit status for debugging."""
        rate_limit = self._get_rate_limit(endpoint)
        
        if self.use_redis and redis_client.is_connected:
            try:
                key = self._get_redis_key(user_id, endpoint)
                current_time = time.time()
                window_start = current_time - 60
                
                # Clean up and count
                await redis_client.zremrangebyscore(key, 0, window_start)
                current_count = await redis_client.zcard(key)
                
                return {
                    "current_count": current_count,
                    "rate_limit": rate_limit,
                    "remaining": max(0, rate_limit - current_count),
                    "backend": "redis"
                }
            except Exception as e:
                logger.debug(f"Redis rate limit status failed: {e}")
                # Fall through to memory backend
        
        # Fallback to memory backend
        key = f"user_{user_id}" if user_id else "anonymous"

        if key not in self._limits or endpoint not in self._limits[key]:
            return {
                "current_count": 0,
                "rate_limit": rate_limit,
                "remaining": rate_limit,
                "backend": "memory"
            }

        # Clean up old requests
        self._limits[key][endpoint] = self._cleanup_old_requests(self._limits[key][endpoint])
        current_count = len(self._limits[key][endpoint])

        return {
            "current_count": current_count,
            "rate_limit": rate_limit,
            "remaining": max(0, rate_limit - current_count),
            "backend": "memory"
        }


# Global rate limiter instance
rate_limiter = RateLimitService()
