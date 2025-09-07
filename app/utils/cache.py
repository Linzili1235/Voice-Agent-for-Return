# 缓存工具模块 - 提供 Redis 缓存和幂等性检查功能
import json
from typing import Any, Optional
import redis.asyncio as redis
from redis.asyncio import Redis

from app.config.settings import settings
from app.utils.logging import get_logger


logger = get_logger(__name__)


class CacheManager:
    """Redis cache manager for idempotency and general caching."""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis = redis.from_url(settings.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis:
            return None
        
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("Failed to get from cache", key=key, error=str(e))
            return None
    
    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration."""
        if not self.redis:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            await self.redis.setex(key, expire, serialized_value)
            return True
        except Exception as e:
            logger.error("Failed to set cache", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis:
            return False
        
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error("Failed to delete from cache", key=key, error=str(e))
            return False
    
    async def check_idempotency(self, key: str) -> Optional[Any]:
        """Check if request is idempotent and return cached response."""
        cache_key = f"idempotency:{key}"
        return await self.get(cache_key)
    
    async def store_idempotency(self, key: str, response: Any, expire: int = 3600) -> bool:
        """Store idempotent response in cache."""
        cache_key = f"idempotency:{key}"
        return await self.set(cache_key, response, expire)


# Global cache manager instance
cache_manager = CacheManager()
