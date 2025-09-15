"""Cache configuration and management.

This layer is intentionally tolerant to Redis being unavailable so that
application tests (and even runtime in degraded mode) don't fail hard
when Redis is down. All cache operations become no-ops on connection
errors instead of propagating failures into the business logic.
"""

import json
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from app.config.settings import settings


class CacheManager:
    """Cache manager using Redis."""
    
    def __init__(self):
        self._redis: Optional[Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis. Keeps cache disabled if connection fails."""
        client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        try:
            await client.ping()
        except Exception:
            # Leave self._redis as None so downstream methods short‑circuit
            return
        self._redis = client
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            try:
                await self._redis.aclose()
            except Exception:
                pass
            finally:
                self._redis = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache. Returns None on any connection issue."""
        if not self._redis:
            return None
        try:
            value = await self._redis.get(key)
        except RedisConnectionError:
            return None
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> None:
        """Set value in cache (no-op if disconnected)."""
        if not self._redis:
            return
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value, default=str)
        try:
            await self._redis.set(key, value, ex=expire)
        except RedisConnectionError:
            return
    
    async def delete(self, key: str) -> None:
        """Delete key from cache (safe)."""
        if not self._redis:
            return
        try:
            await self._redis.delete(key)
        except RedisConnectionError:
            return
    
    async def exists(self, key: str) -> bool:
        """Check if key exists (False on error)."""
        if not self._redis:
            return False
        try:
            return bool(await self._redis.exists(key))
        except RedisConnectionError:
            return False
    
    async def clear(self) -> None:
        """Clear all cache (ignored if unavailable)."""
        if not self._redis:
            return
        try:
            await self._redis.flushdb()
        except RedisConnectionError:
            return


# Global cache instance
cache_manager = CacheManager()