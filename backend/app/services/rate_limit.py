from typing import Dict, Optional
from datetime import datetime, timedelta
import logging
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitService:
    """Simple in-memory rate limiting service.
    
    TODO: Replace with Redis-based implementation for production.
    """
    
    def __init__(self):
        # In-memory storage: {user_id: {endpoint: [(timestamp, count), ...]}}
        self._limits: Dict[str, Dict[str, list]] = {}
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
        elif endpoint in ["analytics"]:
            # Analytics endpoints have higher limits due to dashboard usage
            return self.requests_per_minute * 2
        return self.requests_per_minute
    
    async def check_rate_limit(self, user_id: Optional[int], endpoint: str) -> bool:
        """Check if request is within rate limits.
        
        Args:
            user_id: User ID (None for anonymous users)
            endpoint: Endpoint name
            
        Returns:
            True if request is allowed, raises HTTPException if rate limited
        """
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
    
    async def get_rate_limit_status(self, user_id: Optional[int], endpoint: str) -> Dict[str, int]:
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


# Global rate limiter instance
rate_limiter = RateLimitService()