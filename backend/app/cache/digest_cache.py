"""Digest-specific caching wrapper around Redis client.

This module provides async caching functionality specifically for digest responses,
with proper TTL management and JSON serialization.
"""

import json
import hashlib
from typing import Optional

import structlog

from app.core.redis_client import redis_client

logger = structlog.get_logger(__name__)


class DigestCache:
    """Async wrapper around Redis client for digest-specific caching."""
    
    def __init__(self, key_prefix: str = "digest"):
        """Initialize digest cache with optional key prefix.
        
        Args:
            key_prefix: Prefix for all cache keys (default: "digest")
        """
        self.key_prefix = key_prefix
    
    def _generate_cache_key(self, user_id: str, date: str, forecast_sig: str, prefs_hash: str) -> str:
        """Generate cache key for digest.
        
        Args:
            user_id: User identifier
            date: Date string (YYYY-MM-DD)
            forecast_sig: Forecast signature/hash
            prefs_hash: User preferences hash
            
        Returns:
            Formatted cache key
        """
        return f"{self.key_prefix}:morning:{user_id}:{date}:{forecast_sig}:{prefs_hash}"
    
    async def get_digest(self, user_id: str, date: str, forecast_sig: str, prefs_hash: str) -> Optional[str]:
        """Get cached digest JSON string.
        
        Args:
            user_id: User identifier
            date: Date string (YYYY-MM-DD)
            forecast_sig: Forecast signature/hash
            prefs_hash: User preferences hash
            
        Returns:
            Cached digest JSON string or None if not found/expired
        """
        key = self._generate_cache_key(user_id, date, forecast_sig, prefs_hash)
        
        try:
            result = await redis_client.get(key)
            if result:
                logger.debug(
                    "Digest cache hit",
                    action="digest_cache.get",
                    key=key,
                    user_id=user_id,
                    date=date
                )
                return result
            else:
                logger.debug(
                    "Digest cache miss",
                    action="digest_cache.get",
                    key=key,
                    user_id=user_id,
                    date=date
                )
                return None
        except Exception as e:
            logger.warning(
                "Digest cache get failed",
                action="digest_cache.get",
                key=key,
                error=str(e)
            )
            return None
    
    async def set_digest(self, user_id: str, date: str, forecast_sig: str, 
                        prefs_hash: str, digest_json: str, ttl_seconds: int) -> None:
        """Set cached digest with TTL.
        
        Args:
            user_id: User identifier
            date: Date string (YYYY-MM-DD)
            forecast_sig: Forecast signature/hash
            prefs_hash: User preferences hash
            digest_json: Digest response as JSON string
            ttl_seconds: Time to live in seconds
        """
        key = self._generate_cache_key(user_id, date, forecast_sig, prefs_hash)
        
        try:
            await redis_client.set(key, digest_json, ex=ttl_seconds)
            logger.debug(
                "Digest cached successfully",
                action="digest_cache.set",
                key=key,
                user_id=user_id,
                date=date,
                ttl_seconds=ttl_seconds
            )
        except Exception as e:
            logger.warning(
                "Digest cache set failed",
                action="digest_cache.set",
                key=key,
                error=str(e)
            )
    
    async def get_ttl(self, user_id: str, date: str, forecast_sig: str, prefs_hash: str) -> Optional[int]:
        """Get remaining TTL for cached digest.
        
        Args:
            user_id: User identifier
            date: Date string (YYYY-MM-DD)
            forecast_sig: Forecast signature/hash
            prefs_hash: User preferences hash
            
        Returns:
            Remaining TTL in seconds, or None if key doesn't exist
        """
        key = self._generate_cache_key(user_id, date, forecast_sig, prefs_hash)
        
        try:
            ttl = await redis_client.ttl(key)
            return ttl if ttl > 0 else None
        except Exception as e:
            logger.warning(
                "Digest cache TTL check failed",
                action="digest_cache.ttl",
                key=key,
                error=str(e)
            )
            return None


def generate_forecast_signature(forecast_data: dict) -> str:
    """Generate a signature/hash for forecast data to detect changes.
    
    Args:
        forecast_data: Forecast data dictionary
        
    Returns:
        SHA256 hash of relevant forecast data
    """
    # Extract key fields that would affect digest generation
    signature_data = {
        'hourly_count': len(forecast_data.get('hourly', [])),
        'last_updated': forecast_data.get('last_updated'),
        'location_id': forecast_data.get('location_id')
    }
    
    # Include sample of hourly data (first and last few hours)
    hourly = forecast_data.get('hourly', [])
    if hourly:
        # Take first 6 and last 6 hours for signature
        sample_hours = hourly[:6] + hourly[-6:] if len(hourly) > 12 else hourly
        signature_data['sample_hours'] = [
            {
                'temp': h.get('temperature'),
                'precip': h.get('precipitation'),
                'wind': h.get('wind_speed')
            }
            for h in sample_hours
        ]
    
    # Generate hash
    json_str = json.dumps(signature_data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()[:16]  # Use first 16 chars


def generate_preferences_hash(preferences: dict) -> str:
    """Generate a hash for user preferences to detect changes.
    
    Args:
        preferences: User preferences dictionary
        
    Returns:
        SHA256 hash of preferences
    """
    # Include only preferences that affect digest generation
    relevant_prefs = {
        'outdoor_activities': preferences.get('outdoor_activities', True),
        'temperature_tolerance': preferences.get('temperature_tolerance', 'normal'),
        'rain_tolerance': preferences.get('rain_tolerance', 'low'),
        'units_system': preferences.get('units_system', 'metric')
    }
    
    json_str = json.dumps(relevant_prefs, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()[:12]  # Use first 12 chars


# Global cache instance
digest_cache = DigestCache()