"""Streaming-specific rate limiting for RAG Phase 4."""

import time
from typing import Optional
import structlog

from app.core.redis_client import redis_client
from app.core.settings import get_settings
from app.core.constants import CachePrefix
from app.domain.exceptions import RateLimitExceededError
from app.infrastructure.ai.rag.metrics import record_rate_limit_event

logger = structlog.get_logger(__name__)


class StreamingRateLimiter:
    """Redis-based token bucket rate limiter for streaming endpoints."""
    
    def __init__(self):
        self.settings = get_settings()
        self.limit = self.settings.rag_stream_rate_limit  # 20 requests
        self.window_seconds = self.settings.rag_stream_rate_window_seconds  # 300 seconds (5 min)
    
    def _get_redis_key(self, user_id: Optional[str]) -> str:
        """Generate Redis key for streaming rate limiting."""
        user_key = f"user_{user_id}" if user_id else "anonymous"
        return f"{CachePrefix.RATE_LIMIT_STREAM}:{user_key}"
    
    async def check_rate_limit(self, user_id: Optional[str] = None) -> bool:
        """
        Check if the user is within streaming rate limits.
        
        Uses Redis sliding window with ZSET for accurate rate limiting.
        
        Args:
            user_id: User identifier (None for anonymous)
            
        Returns:
            True if within limits, False if rate limited
            
        Raises:
            RateLimitExceededError: If rate limit is exceeded
        """
        redis_key = self._get_redis_key(user_id)
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        try:
            if not redis_client.is_connected:
                # Fallback: allow the request but log warning
                logger.warning(
                    "Redis unavailable for rate limiting, allowing request",
                    user_id=user_id,
                    endpoint="rag_stream"
                )
                return True
            
            # Use Redis pipeline for atomic operations
            async with redis_client.pipeline() as pipe:
                # Remove expired entries
                await pipe.zremrangebyscore(redis_key, 0, window_start)
                
                # Count current requests in window
                current_count = await pipe.zcard(redis_key)
                
                # Execute pipeline
                results = await pipe.execute()
                current_count = results[1] if len(results) > 1 else 0
                
                if current_count >= self.limit:
                    # Rate limit exceeded
                    record_rate_limit_event("rag_stream", user_id)
                    
                    logger.warning(
                        "Streaming rate limit exceeded",
                        user_id=user_id,
                        current_count=current_count,
                        limit=self.limit,
                        window_seconds=self.window_seconds
                    )
                    
                    raise RateLimitExceededError(
                        limit=self.limit,
                        window_seconds=self.window_seconds,
                        endpoint="rag_stream"
                    )
                
                # Add current request
                await redis_client.zadd(redis_key, {str(current_time): current_time})
                
                # Set expiration for cleanup
                await redis_client.expire(redis_key, self.window_seconds + 60)
                
                logger.debug(
                    "Streaming rate limit check passed",
                    user_id=user_id,
                    current_count=current_count + 1,
                    limit=self.limit
                )
                
                return True
                
        except RateLimitExceededError:
            # Re-raise rate limit errors
            raise
        except Exception as e:
            # Log error but allow request to proceed
            logger.error(
                "Rate limiting error, allowing request",
                error=str(e),
                user_id=user_id,
                endpoint="rag_stream"
            )
            return True


# Global instance
streaming_rate_limiter = StreamingRateLimiter()


async def check_streaming_rate_limit(user_id: Optional[str] = None) -> bool:
    """
    Convenience function to check streaming rate limits.
    
    Args:
        user_id: User identifier
        
    Returns:
        True if within limits
        
    Raises:
        RateLimitExceededError: If rate limit exceeded
    """
    return await streaming_rate_limiter.check_rate_limit(user_id)