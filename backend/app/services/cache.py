"""Simple forecast caching service using Redis with fallback."""

import json
import logging
from typing import Any, Optional

from app.core.redis_client import get_redis_client, is_redis_available

logger = logging.getLogger(__name__)


class CacheService:
    """Simple caching service with Redis backend and graceful degradation."""
    
    def __init__(self):
        self.default_ttl = 300  # 5 minutes default TTL
        
    def _make_key(self, prefix: str, identifier: str) -> str:
        """Create a standardized cache key."""
        return f"cache:{prefix}:{identifier}"
    
    async def get_forecast(self, location_id: int) -> Optional[dict[str, Any]]:
        """Get cached forecast data for a location."""
        try:
            if not await is_redis_available():
                logger.debug("Redis unavailable, cache miss")
                return None
                
            client = await get_redis_client()
            if not client:
                return None
                
            key = self._make_key("forecast", str(location_id))
            cached_data = await client.get(key)
            
            if cached_data:
                logger.debug(f"Cache hit for forecast location {location_id}")
                return json.loads(cached_data)
            else:
                logger.debug(f"Cache miss for forecast location {location_id}")
                return None
                
        except Exception as e:
            logger.debug(f"Cache get error for forecast location {location_id}: {e}")
            return None
    
    async def set_forecast(
        self, 
        location_id: int, 
        forecast_data: dict[str, Any], 
        ttl: Optional[int] = None
    ) -> bool:
        """Cache forecast data for a location."""
        try:
            if not await is_redis_available():
                logger.debug("Redis unavailable, skipping cache set")
                return False
                
            client = await get_redis_client()
            if not client:
                return False
                
            key = self._make_key("forecast", str(location_id))
            cached_data = json.dumps(forecast_data)
            
            await client.set(key, cached_data, ex=ttl or self.default_ttl)
            logger.debug(f"Cached forecast for location {location_id} (TTL: {ttl or self.default_ttl}s)")
            return True
            
        except Exception as e:
            logger.debug(f"Cache set error for forecast location {location_id}: {e}")
            return False
    
    async def get_explain_result(self, cache_key: str) -> Optional[dict[str, Any]]:
        """Get cached LLM explanation result."""
        try:
            if not await is_redis_available():
                return None
                
            client = await get_redis_client()
            if not client:
                return None
                
            key = self._make_key("explain", cache_key)
            cached_data = await client.get(key)
            
            if cached_data:
                logger.debug(f"Cache hit for explanation {cache_key}")
                return json.loads(cached_data)
            else:
                logger.debug(f"Cache miss for explanation {cache_key}")
                return None
                
        except Exception as e:
            logger.debug(f"Cache get error for explanation {cache_key}: {e}")
            return None
    
    async def set_explain_result(
        self, 
        cache_key: str, 
        result_data: dict[str, Any], 
        ttl: Optional[int] = None
    ) -> bool:
        """Cache LLM explanation result."""
        try:
            if not await is_redis_available():
                return False
                
            client = await get_redis_client()
            if not client:
                return False
                
            key = self._make_key("explain", cache_key)
            cached_data = json.dumps(result_data)
            
            # Default longer TTL for LLM results (30 minutes)
            await client.set(key, cached_data, ex=ttl or 1800)
            logger.debug(f"Cached explanation result {cache_key} (TTL: {ttl or 1800}s)")
            return True
            
        except Exception as e:
            logger.debug(f"Cache set error for explanation {cache_key}: {e}")
            return False
    
    async def invalidate_location_cache(self, location_id: int) -> bool:
        """Invalidate all cached data for a location."""
        try:
            if not await is_redis_available():
                return False
                
            client = await get_redis_client()
            if not client:
                return False
                
            # Delete forecast cache
            forecast_key = self._make_key("forecast", str(location_id))
            await client.delete(forecast_key)
            
            # Could also delete related explanation caches if they include location_id
            logger.debug(f"Invalidated cache for location {location_id}")
            return True
            
        except Exception as e:
            logger.debug(f"Cache invalidation error for location {location_id}: {e}")
            return False


# Global cache service instance
cache_service = CacheService()