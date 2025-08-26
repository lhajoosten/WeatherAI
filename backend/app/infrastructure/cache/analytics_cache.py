"""Redis-enhanced analytics cache with in-memory fallback."""

import hashlib
import json
import time
from typing import Any

import structlog

from app.core.config import settings
from app.core.redis_client import redis_client

logger = structlog.get_logger(__name__)


class AnalyticsCache:
    """Redis-based analytics cache with in-memory fallback and TTL."""

    def __init__(self, default_ttl: int = 15, use_redis: bool = True):
        """Initialize cache with default TTL in seconds."""
        self.default_ttl = default_ttl
        self.use_redis = use_redis
        # In-memory fallback cache: {key: {'data': Any, 'expires_at': float}}
        self._cache: dict[str, dict[str, Any]] = {}
        self.redis_prefix = "analytics"

    def _generate_key(self, location_id: int, endpoint: str, **params) -> str:
        """Generate cache key from parameters."""
        # Include all params in key generation for consistency
        key_data = {
            'location_id': location_id,
            'endpoint': endpoint,
            'params': sorted(params.items())  # Sort for consistency
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{self.redis_prefix}:{key_hash}"

    def _cleanup_expired_fallback(self) -> None:
        """Clean up expired entries from fallback cache."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry['expires_at']
        ]
        for key in expired_keys:
            del self._cache[key]

    async def get(self, location_id: int, endpoint: str, **params) -> Any | None:
        """Get cached result if not expired."""
        key = self._generate_key(location_id, endpoint, **params)

        # Try Redis first if enabled and connected
        if self.use_redis and redis_client.is_connected:
            try:
                cached_data = await redis_client.get(key)
                if cached_data:
                    data = json.loads(cached_data)
                    logger.debug(
                        "Analytics cache hit (Redis)",
                        action="analytics_cache.get",
                        key=key,
                        location_id=location_id,
                        endpoint=endpoint,
                        source="redis"
                    )
                    return data
            except (json.JSONDecodeError, Exception) as e:
                logger.debug(
                    "Redis analytics cache get failed",
                    action="analytics_cache.get",
                    key=key,
                    error=str(e)
                )

        # Fallback to in-memory cache
        self._cleanup_expired_fallback()

        if key in self._cache:
            cache_entry = self._cache[key]
            current_time = time.time()

            # Check if expired
            if current_time <= cache_entry['expires_at']:
                logger.debug(
                    "Analytics cache hit (fallback)",
                    action="analytics_cache.get",
                    key=key,
                    location_id=location_id,
                    endpoint=endpoint,
                    source="memory"
                )
                return cache_entry['data']
            else:
                # Expired
                del self._cache[key]

        logger.debug(
            "Analytics cache miss",
            action="analytics_cache.get",
            key=key,
            location_id=location_id,
            endpoint=endpoint
        )
        return None

    async def set(
        self,
        location_id: int,
        endpoint: str,
        data: Any,
        ttl: int | None = None,
        **params
    ) -> None:
        """Set cached result with TTL."""
        key = self._generate_key(location_id, endpoint, **params)
        ttl = ttl or settings.redis_cache_analytics_ttl or self.default_ttl

        # Try Redis first if enabled and connected
        if self.use_redis and redis_client.is_connected:
            try:
                cached_data = json.dumps(data, default=str)
                await redis_client.set(key, cached_data, ex=ttl)
                logger.debug(
                    "Analytics cache set (Redis)",
                    action="analytics_cache.set",
                    key=key,
                    location_id=location_id,
                    endpoint=endpoint,
                    ttl=ttl,
                    target="redis"
                )
            except Exception as e:
                logger.debug(
                    "Redis analytics cache set failed",
                    action="analytics_cache.set",
                    key=key,
                    error=str(e)
                )

        # Always set in fallback cache as well
        expires_at = time.time() + ttl
        self._cache[key] = {
            'data': data,
            'expires_at': expires_at
        }

        logger.debug(
            "Analytics cache set (fallback)",
            action="analytics_cache.set",
            key=key,
            location_id=location_id,
            endpoint=endpoint,
            ttl=ttl,
            target="memory"
        )

        # Clean up old entries periodically
        if len(self._cache) % 50 == 0:
            self._cleanup_expired_fallback()

    async def clear_location(self, location_id: int) -> None:
        """Clear all cache entries for a specific location."""
        # For fallback cache, scan through keys
        keys_to_remove = []
        for key in self._cache.keys():
            if f'"location_id": {location_id}' in key:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._cache[key]

        # For Redis, we'd need to scan for keys, which is expensive
        # Skip for now, let TTL handle it
        logger.debug(
            "Analytics cache cleared for location",
            action="analytics_cache.clear_location",
            location_id=location_id,
            fallback_keys_removed=len(keys_to_remove)
        )

    def clear_expired(self) -> int:
        """Clear all expired entries and return count removed."""
        old_count = len(self._cache)
        self._cleanup_expired_fallback()
        removed_count = old_count - len(self._cache)

        if removed_count > 0:
            logger.debug(
                "Analytics cache expired entries cleared",
                action="analytics_cache.clear_expired",
                removed_count=removed_count
            )

        return removed_count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        self._cleanup_expired_fallback()

        current_time = time.time()
        active_entries = 0
        expired_entries = 0

        for entry in self._cache.values():
            if current_time > entry['expires_at']:
                expired_entries += 1
            else:
                active_entries += 1

        return {
            'total_entries': len(self._cache),
            'active_entries': active_entries,
            'expired_entries': expired_entries,
            'cache_size_mb': sum(len(str(entry)) for entry in self._cache.values()) / (1024 * 1024),
            'redis_enabled': self.use_redis,
            'redis_connected': redis_client.is_connected if self.use_redis else False
        }


# Global cache instance
analytics_cache = AnalyticsCache(default_ttl=15)  # 15 second TTL for analytics queries
