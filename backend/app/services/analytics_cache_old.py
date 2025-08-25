"""Simple in-memory cache for analytics queries."""

import time
import hashlib
import json
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class AnalyticsCache:
    """Simple in-memory cache for analytics queries with TTL."""
    
    def __init__(self, default_ttl: int = 15):
        """Initialize cache with default TTL in seconds."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, location_id: int, endpoint: str, **params) -> str:
        """Generate cache key from parameters."""
        # Create a deterministic key from location, endpoint, and params
        key_data = {
            'location_id': location_id,
            'endpoint': endpoint,
            **params
        }
        # Sort keys for consistent hash
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, location_id: int, endpoint: str, **params) -> Optional[Any]:
        """Get cached result if not expired."""
        key = self._generate_key(location_id, endpoint, **params)
        
        if key not in self._cache:
            return None
        
        cache_entry = self._cache[key]
        current_time = time.time()
        
        # Check if expired
        if current_time > cache_entry['expires_at']:
            del self._cache[key]
            logger.debug(f"Cache miss (expired): {key}")
            return None
        
        logger.debug(f"Cache hit: {key}")
        return cache_entry['data']
    
    def set(self, location_id: int, endpoint: str, data: Any, ttl: Optional[int] = None, **params) -> None:
        """Set cached result with TTL."""
        key = self._generate_key(location_id, endpoint, **params)
        expires_at = time.time() + (ttl or self.default_ttl)
        
        self._cache[key] = {
            'data': data,
            'expires_at': expires_at,
            'created_at': time.time()
        }
        
        logger.debug(f"Cache set: {key} (TTL: {ttl or self.default_ttl}s)")
    
    def clear_location(self, location_id: int) -> None:
        """Clear all cache entries for a specific location."""
        keys_to_remove = []
        for key, entry in self._cache.items():
            try:
                # This is a simple approach - in production, we'd store metadata
                if f'"location_id": {location_id}' in key:
                    keys_to_remove.append(key)
            except:
                pass
        
        for key in keys_to_remove:
            del self._cache[key]
        
        logger.debug(f"Cleared cache for location {location_id}: {len(keys_to_remove)} entries")
    
    def clear_expired(self) -> int:
        """Clear all expired entries and return count removed."""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if current_time > entry['expires_at']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        logger.debug(f"Cleared {len(expired_keys)} expired cache entries")
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
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
            'cache_size_mb': sum(len(str(entry)) for entry in self._cache.values()) / (1024 * 1024)
        }


# Global cache instance
analytics_cache = AnalyticsCache(default_ttl=15)  # 15 second TTL for analytics queries