"""
DEPRECATED: This module has been moved to infrastructure layer.

Use app.infrastructure.cache.service instead.
This file will be removed in a future version.
"""

import hashlib
import json
import time
from typing import Any

import structlog

from app.core.redis_client import redis_client

logger = structlog.get_logger(__name__)


class CacheHelper:
    """General purpose cache with Redis backend and in-memory fallback."""

    def __init__(self, prefix: str = "cache", default_ttl: int = 300):
        """
        Initialize cache helper.

        Args:
            prefix: Cache key prefix
            default_ttl: Default TTL in seconds
        """
        self.prefix = prefix
        self.default_ttl = default_ttl
        # In-memory fallback cache: {key: {'data': Any, 'expires_at': float}}
        self._fallback_cache: dict[str, dict[str, Any]] = {}

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        # Create a deterministic key from arguments
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())  # Sort for consistency
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{self.prefix}:{key_hash}"

    def _cleanup_expired_fallback(self) -> None:
        """Clean up expired entries from fallback cache."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._fallback_cache.items()
            if current_time > entry['expires_at']
        ]
        for key in expired_keys:
            del self._fallback_cache[key]

    async def get(self, *args, **kwargs) -> Any | None:
        """
        Get cached data.

        Args:
            *args: Positional arguments for key generation
            **kwargs: Keyword arguments for key generation

        Returns:
            Cached data or None if not found/expired
        """
        key = self._generate_key(*args, **kwargs)

        # Try Redis first
        if redis_client.is_connected:
            try:
                cached_data = await redis_client.get(key)
                if cached_data:
                    data = json.loads(cached_data)
                    logger.debug(
                        "Cache hit (Redis)",
                        action="cache.get",
                        key=key,
                        source="redis"
                    )
                    return data
            except (json.JSONDecodeError, Exception) as e:
                logger.debug(
                    "Redis cache get failed",
                    action="cache.get",
                    key=key,
                    error=str(e)
                )

        # Fallback to in-memory cache
        self._cleanup_expired_fallback()

        if key in self._fallback_cache:
            entry = self._fallback_cache[key]
            current_time = time.time()

            if current_time <= entry['expires_at']:
                logger.debug(
                    "Cache hit (fallback)",
                    action="cache.get",
                    key=key,
                    source="memory"
                )
                return entry['data']
            else:
                # Expired
                del self._fallback_cache[key]

        logger.debug(
            "Cache miss",
            action="cache.get",
            key=key
        )
        return None

    async def set(
        self,
        data: Any,
        ttl: int | None = None,
        *args,
        **kwargs
    ) -> bool:
        """
        Set cached data.

        Args:
            data: Data to cache
            ttl: TTL in seconds (uses default if None)
            *args: Positional arguments for key generation
            **kwargs: Keyword arguments for key generation

        Returns:
            True if cached successfully
        """
        key = self._generate_key(*args, **kwargs)
        ttl = ttl or self.default_ttl


        # Try Redis first
        if redis_client.is_connected:
            try:
                cached_data = json.dumps(data, default=str)
                result = await redis_client.set(key, cached_data, ex=ttl)
                if result:
                    logger.debug(
                        "Cache set (Redis)",
                        action="cache.set",
                        key=key,
                        ttl=ttl,
                        target="redis"
                    )
            except Exception as e:
                logger.debug(
                    "Redis cache set failed",
                    action="cache.set",
                    key=key,
                    error=str(e)
                )

        # Always set in fallback cache as well
        expires_at = time.time() + ttl
        self._fallback_cache[key] = {
            'data': data,
            'expires_at': expires_at
        }

        logger.debug(
            "Cache set (fallback)",
            action="cache.set",
            key=key,
            ttl=ttl,
            target="memory"
        )

        # Clean up old entries periodically
        if len(self._fallback_cache) % 100 == 0:
            self._cleanup_expired_fallback()

        return True  # Always return True since fallback succeeded

    async def delete(self, *args, **kwargs) -> bool:
        """
        Delete cached data.

        Args:
            *args: Positional arguments for key generation
            **kwargs: Keyword arguments for key generation

        Returns:
            True if deleted successfully
        """
        key = self._generate_key(*args, **kwargs)

        # Delete from Redis
        if redis_client.is_connected:
            try:
                await redis_client.delete(key)
            except Exception as e:
                logger.debug(
                    "Redis cache delete failed",
                    action="cache.delete",
                    key=key,
                    error=str(e)
                )

        # Delete from fallback cache
        if key in self._fallback_cache:
            del self._fallback_cache[key]

        logger.debug(
            "Cache deleted",
            action="cache.delete",
            key=key
        )
        return True

    async def clear(self) -> bool:
        """Clear all cache entries with this prefix."""
        # Clear fallback cache
        self._fallback_cache.clear()

        # For Redis, we'd need to scan for keys with our prefix
        # This is expensive, so we'll skip it for now
        logger.debug(
            "Cache cleared (fallback only)",
            action="cache.clear",
            prefix=self.prefix
        )
        return True

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        self._cleanup_expired_fallback()

        return {
            "prefix": self.prefix,
            "fallback_entries": len(self._fallback_cache),
            "redis_connected": redis_client.is_connected,
            "fallback_size_mb": sum(
                len(str(entry)) for entry in self._fallback_cache.values()
            ) / (1024 * 1024)
        }


# Pre-configured cache instances
forecast_cache = CacheHelper("forecast", default_ttl=300)  # 5 minutes
observation_cache = CacheHelper("observation", default_ttl=180)  # 3 minutes
analytics_cache = CacheHelper("analytics", default_ttl=60)  # 1 minute
