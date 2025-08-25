"""Redis client for caching, rate limiting, and health checks (unified implementation).

This module provides a single RedisClient class that manages connection state
(lazy async init, ping, close) plus thin functional wrappers that preserve the
public API expected by existing services & tests (get_redis_client,
is_redis_available, etc.).

Design goals (PR #11 intent):
- Lazy, single shared async client instance.
- Structured logging with action / status fields.
- Clear separation between connection state and helper operations.
- Graceful fallback: if Redis is down, callers get None / False instead of exceptions.
- Health status function returns minimal server info when available.
- Compatible with rate_limit and tests that patch get_redis_client / is_redis_available.
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional

import redis.asyncio as redis
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class RedisClient:  # pragma: no cover - behaviour covered via wrappers/tests
    """Async Redis client manager with lazy initialization and health helpers.

    Public usage should go through the module-level helper coroutines to allow
    easy mocking in tests (e.g. patch('app.services.rate_limit.get_redis_client')).
    """

    def __init__(self) -> None:
        self._client: Optional[redis.Redis] = None
        self._connected: bool = False
        self._connection_tested: bool = False
        self._lock = asyncio.Lock()  # prevent concurrent connection races
        self._last_error: Optional[str] = None

    async def initialize(self) -> bool:
        """Ensure a connected Redis client (lazy). Returns True if connected.
        Never raises to callers; errors are logged and reflected in state.
        """
        if self._connected:
            return True
        # Only one coroutine attempts a real connection
        async with self._lock:
            if self._connected:  # double-checked
                return True
            try:
                logger.debug(
                    "Attempting Redis connection",
                    action="redis.initialize",
                    status="attempting",
                    url=settings.redis_url,
                )
                self._client = redis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                # Ping to validate connection
                await self._client.ping()
                self._connected = True
                self._connection_tested = True
                self._last_error = None
                logger.info(
                    "Redis connection established",
                    action="redis.initialize",
                    status="connected",
                    url=settings.redis_url,
                )
            except Exception as e:  # noqa: BLE001
                self._connected = False
                self._connection_tested = True
                self._last_error = str(e)
                self._client = None
                logger.warning(
                    "Redis connection failed, using fallback",
                    action="redis.initialize",
                    status="failed",
                    error=str(e),
                    url=settings.redis_url,
                )
        return self._connected

    async def ping(self) -> bool:
        """Ping Redis; update connectivity state.
        Returns True if connected after ping.
        """
        if not self._client:
            return False
        try:
            await self._client.ping()
            if not self._connected:
                logger.info(
                    "Redis connection restored",
                    action="redis.ping",
                    status="restored",
                )
            self._connected = True
            return True
        except Exception as e:  # noqa: BLE001
            if self._connected:
                logger.warning(
                    "Redis connection lost",
                    action="redis.ping",
                    status="lost",
                    error=str(e),
                )
            self._connected = False
            self._last_error = str(e)
            return False

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def client(self) -> Optional[redis.Redis]:
        return self._client if self._connected else None

    async def close(self) -> None:
        if self._client:
            try:
                await self._client.aclose()
                logger.info(
                    "Redis connection closed",
                    action="redis.close",
                    status="closed",
                )
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "Error closing Redis connection",
                    action="redis.close",
                    error=str(e),
                )
            finally:
                self._client = None
                self._connected = False

    # Convenience data helpers (guard with ping & connection) -----------------
    async def get(self, key: str) -> Optional[str]:
        if not await self.ping():
            return None
        try:
            return await self._client.get(key)  # type: ignore[union-attr]
        except Exception as e:  # noqa: BLE001
            logger.debug(
                "Redis GET failed",
                action="redis.get",
                key=key,
                error=str(e),
            )
            self._connected = False
            return None

    async def set(self, key: str, value: str, ex: Optional[int] = None, nx: bool = False) -> bool:
        if not await self.ping():
            return False
        try:
            result = await self._client.set(key, value, ex=ex, nx=nx)  # type: ignore[union-attr]
            return bool(result)
        except Exception as e:  # noqa: BLE001
            logger.debug(
                "Redis SET failed",
                action="redis.set",
                key=key,
                error=str(e),
            )
            self._connected = False
            return False

    async def delete(self, *keys: str) -> int:
        if not await self.ping():
            return 0
        try:
            return await self._client.delete(*keys)  # type: ignore[union-attr]
        except Exception as e:  # noqa: BLE001
            logger.debug(
                "Redis DELETE failed",
                action="redis.delete",
                keys=keys,
                error=str(e),
            )
            self._connected = False
            return 0

    async def zadd(self, key: str, mapping: dict[str, float]) -> int:
        if not await self.ping():
            return 0
        try:
            return await self._client.zadd(key, mapping)  # type: ignore[union-attr]
        except Exception as e:  # noqa: BLE001
            logger.debug(
                "Redis ZADD failed",
                action="redis.zadd",
                key=key,
                error=str(e),
            )
            self._connected = False
            return 0

    async def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        if not await self.ping():
            return 0
        try:
            return await self._client.zremrangebyscore(key, min_score, max_score)  # type: ignore[union-attr]
        except Exception as e:  # noqa: BLE001
            logger.debug(
                "Redis ZREMRANGEBYSCORE failed",
                action="redis.zremrangebyscore",
                key=key,
                error=str(e),
            )
            self._connected = False
            return 0

    async def zcard(self, key: str) -> int:
        if not await self.ping():
            return 0
        try:
            return await self._client.zcard(key)  # type: ignore[union-attr]
        except Exception as e:  # noqa: BLE001
            logger.debug(
                "Redis ZCARD failed",
                action="redis.zcard",
                key=key,
                error=str(e),
            )
            self._connected = False
            return 0

    async def expire(self, key: str, seconds: int) -> bool:
        if not await self.ping():
            return False
        try:
            return bool(await self._client.expire(key, seconds))  # type: ignore[union-attr]
        except Exception as e:  # noqa: BLE001
            logger.debug(
                "Redis EXPIRE failed",
                action="redis.expire",
                key=key,
                error=str(e),
            )
            self._connected = False
            return False


# Single shared instance
redis_client = RedisClient()


# Module-level helper API (compat layer for services & tests) -----------------
async def get_redis_client() -> Optional[redis.Redis]:
    """Return the raw Redis client if connected (after lazy init), else None.
    Rate limiting code expects the raw client to call pipeline(), zadd(), etc.
    """
    await redis_client.initialize()
    return redis_client.client


async def is_redis_available() -> bool:
    await redis_client.initialize()
    return redis_client.is_connected


async def ping_redis() -> bool:
    return await redis_client.ping()


async def redis_get(key: str) -> Optional[str]:
    return await redis_client.get(key)


async def redis_set(key: str, value: str, ex: Optional[int] = None, nx: bool = False) -> bool:
    return await redis_client.set(key, value, ex=ex, nx=nx)


async def redis_delete(key: str) -> int:
    return await redis_client.delete(key)


async def close_redis() -> None:
    await redis_client.close()


async def get_redis_status() -> dict[str, Any]:
    """Return structured health information for /health endpoint.
    { status: connected|disconnected|error, redis_version?, uptime_seconds?, error? }
    """
    # Ensure at least one initialization attempt
    await redis_client.initialize()
    if not redis_client.is_connected:
        return {
            "status": "disconnected",
            "error": redis_client._last_error or "Redis connection not available",
        }
    try:
        info = await redis_client.client.info("server")  # type: ignore[union-attr]
        return {
            "status": "connected",
            "redis_version": info.get("redis_version", "unknown"),
            "uptime_seconds": info.get("uptime_in_seconds", 0),
        }
    except Exception as e:  # noqa: BLE001
        return {
            "status": "error",
            "error": str(e),
        }