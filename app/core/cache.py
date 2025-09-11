"""Cache configuration and management."""

import json
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from app.config.settings import settings


class CacheManager:
    """Cache manager using Redis."""
    
    def __init__(self):
        self._redis: Optional[Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis."""
        self._redis = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        # Test connection
        await self._redis.ping()
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._redis:
            return None
        
        value = await self._redis.get(key)
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
        """Set value in cache."""
        if not self._redis:
            return
        
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value, default=str)
        
        await self._redis.set(key, value, ex=expire)
    
    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        if not self._redis:
            return
        
        await self._redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._redis:
            return False
        
        return bool(await self._redis.exists(key))
    
    async def clear(self) -> None:
        """Clear all cache."""
        if not self._redis:
            return
        
        await self._redis.flushdb()


# Global cache instance
cache_manager = CacheManager()