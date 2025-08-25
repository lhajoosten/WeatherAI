"""Redis client initialization and utilities."""

import logging
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Optional[Redis] = None
_redis_available: bool = False


async def get_redis_client() -> Optional[Redis]:
    """Get Redis client instance with connection verification."""
    global _redis_client, _redis_available
    
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await _redis_client.ping()
            _redis_available = True
            logger.info(f"Redis connection established: {settings.redis_url}")
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            _redis_available = False
            _redis_client = None
            
    return _redis_client


async def is_redis_available() -> bool:
    """Check if Redis is available."""
    global _redis_available
    
    if not _redis_available:
        # Try to reconnect
        client = await get_redis_client()
        return client is not None
        
    return _redis_available


async def ping_redis() -> bool:
    """Ping Redis to check connectivity."""
    try:
        client = await get_redis_client()
        if client:
            await client.ping()
            return True
    except Exception as e:
        logger.debug(f"Redis ping failed: {e}")
        global _redis_available
        _redis_available = False
        
    return False


async def redis_get(key: str) -> Optional[str]:
    """Get value from Redis with fallback handling."""
    try:
        client = await get_redis_client()
        if client:
            return await client.get(key)
    except Exception as e:
        logger.debug(f"Redis GET failed for key {key}: {e}")
        
    return None


async def redis_set(key: str, value: str, ex: Optional[int] = None) -> bool:
    """Set value in Redis with fallback handling."""
    try:
        client = await get_redis_client()
        if client:
            await client.set(key, value, ex=ex)
            return True
    except Exception as e:
        logger.debug(f"Redis SET failed for key {key}: {e}")
        
    return False


async def redis_delete(key: str) -> bool:
    """Delete key from Redis with fallback handling."""
    try:
        client = await get_redis_client()
        if client:
            await client.delete(key)
            return True
    except Exception as e:
        logger.debug(f"Redis DELETE failed for key {key}: {e}")
        
    return False


async def close_redis():
    """Close Redis connection gracefully."""
    global _redis_client, _redis_available
    
    if _redis_client:
        try:
            await _redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.warning(f"Error closing Redis connection: {e}")
        finally:
            _redis_client = None
            _redis_available = False