"""Redis client for caching and rate limiting."""

import asyncio
import logging
from typing import Any, Optional

import redis.asyncio as redis
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)
std_logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client with connection management and fallback handling."""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._connected: bool = False
        self._connection_tested: bool = False
    
    async def initialize(self) -> bool:
        """Initialize Redis connection and test connectivity."""
        try:
            # Create Redis client
            self._client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self._client.ping()
            self._connected = True
            self._connection_tested = True
            
            logger.info(
                "Redis connection established successfully",
                action="redis.initialize",
                status="connected",
                url=settings.redis_url
            )
            return True
            
        except Exception as e:
            self._connected = False
            self._connection_tested = True
            logger.warning(
                "Redis connection failed, will use fallback modes",
                action="redis.initialize",
                status="failed",
                error=str(e),
                url=settings.redis_url
            )
            return False
    
    async def ping(self) -> bool:
        """Test Redis connectivity."""
        if not self._client:
            return False
            
        try:
            await self._client.ping()
            if not self._connected:
                logger.info(
                    "Redis connection restored",
                    action="redis.ping",
                    status="restored"
                )
            self._connected = True
            return True
        except Exception as e:
            if self._connected:
                logger.warning(
                    "Redis connection lost", 
                    action="redis.ping",
                    status="lost",
                    error=str(e)
                )
            self._connected = False
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._connected
    
    @property
    def client(self) -> Optional[redis.Redis]:
        """Get Redis client if connected."""
        return self._client if self._connected else None
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis with fallback handling."""
        if not await self.ping():
            return None
            
        try:
            return await self._client.get(key)
        except Exception as e:
            logger.debug(
                "Redis GET failed",
                action="redis.get", 
                key=key,
                error=str(e)
            )
            self._connected = False
            return None
    
    async def set(
        self, 
        key: str, 
        value: str, 
        ex: Optional[int] = None,
        nx: bool = False
    ) -> bool:
        """Set value in Redis with fallback handling."""
        if not await self.ping():
            return False
            
        try:
            result = await self._client.set(key, value, ex=ex, nx=nx)
            return bool(result)
        except Exception as e:
            logger.debug(
                "Redis SET failed",
                action="redis.set",
                key=key, 
                error=str(e)
            )
            self._connected = False
            return False
    
    async def delete(self, *keys: str) -> int:
        """Delete keys from Redis with fallback handling."""
        if not await self.ping():
            return 0
            
        try:
            return await self._client.delete(*keys)
        except Exception as e:
            logger.debug(
                "Redis DELETE failed",
                action="redis.delete",
                keys=keys,
                error=str(e)
            )
            self._connected = False
            return 0
    
    async def zadd(self, key: str, mapping: dict) -> int:
        """Add to sorted set with fallback handling."""
        if not await self.ping():
            return 0
            
        try:
            return await self._client.zadd(key, mapping)
        except Exception as e:
            logger.debug(
                "Redis ZADD failed",
                action="redis.zadd",
                key=key,
                error=str(e)
            )
            self._connected = False
            return 0
    
    async def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        """Remove from sorted set by score range."""
        if not await self.ping():
            return 0
            
        try:
            return await self._client.zremrangebyscore(key, min_score, max_score)
        except Exception as e:
            logger.debug(
                "Redis ZREMRANGEBYSCORE failed",
                action="redis.zremrangebyscore", 
                key=key,
                error=str(e)
            )
            self._connected = False
            return 0
    
    async def zcard(self, key: str) -> int:
        """Get sorted set cardinality."""
        if not await self.ping():
            return 0
            
        try:
            return await self._client.zcard(key)
        except Exception as e:
            logger.debug(
                "Redis ZCARD failed",
                action="redis.zcard",
                key=key, 
                error=str(e)
            )
            self._connected = False
            return 0
    
    async def expire(self, key: str, time: int) -> bool:
        """Set key expiration."""
        if not await self.ping():
            return False
            
        try:
            return await self._client.expire(key, time)
        except Exception as e:
            logger.debug(
                "Redis EXPIRE failed",
                action="redis.expire",
                key=key,
                error=str(e)
            )
            self._connected = False
            return False
    
    async def close(self):
        """Close Redis connection."""
        if self._client:
            try:
                await self._client.aclose()
                logger.info(
                    "Redis connection closed",
                    action="redis.close",
                    status="closed"
                )
            except Exception as e:
                logger.warning(
                    "Error closing Redis connection",
                    action="redis.close",
                    error=str(e)
                )
            finally:
                self._client = None
                self._connected = False


# Global Redis client instance
redis_client = RedisClient()


async def get_redis_status() -> dict[str, Any]:
    """Get Redis connection status for health checks."""
    if not redis_client._connection_tested:
        await redis_client.initialize()
    
    if redis_client.is_connected:
        try:
            # Get some basic info
            info = await redis_client.client.info("server")
            return {
                "status": "connected",
                "redis_version": info.get("redis_version", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    else:
        return {
            "status": "disconnected",
            "error": "Redis connection not available"
        }