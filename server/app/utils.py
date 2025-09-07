# 工具函数模块 - 提供日志记录、缓存管理和数据脱敏功能
import json
import re
import secrets
from typing import Any, Optional
import redis.asyncio as redis
from redis.asyncio import Redis
import structlog
from structlog.stdlib import LoggerFactory

from app.config import settings


def setup_logging() -> None:
    """Setup structured logging configuration."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def redact_sensitive_data(data: Any) -> Any:
    """
    Redact sensitive information from data for logging.
    Redacts order IDs and phone numbers to show only last 4 digits.
    """
    if isinstance(data, str):
        # Redact order IDs (keep last 4 characters)
        order_id_pattern = r'\b([A-Z0-9]{8,})\b'
        data = re.sub(order_id_pattern, lambda m: '*' * (len(m.group(1)) - 4) + m.group(1)[-4:], data)
        
        # Redact phone numbers (keep last 4 digits)
        phone_pattern = r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        data = re.sub(phone_pattern, r'***-***-\3\4', data)
        
        return data
    
    elif isinstance(data, dict):
        return {key: redact_sensitive_data(value) for key, value in data.items()}
    
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    
    return data


def generate_idempotency_key() -> str:
    """Generate a unique idempotency key."""
    return secrets.token_urlsafe(32)


def validate_idempotency_key(key: str) -> bool:
    """Validate idempotency key format."""
    if not key or len(key) < 1 or len(key) > 255:
        return False
    # Check for valid characters (alphanumeric, hyphens, underscores)
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', key))


class CacheManager:
    """Redis cache manager for idempotency."""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis = redis.from_url(settings.redis_url, decode_responses=True)
            await self.redis.ping()
        except Exception:
            # If Redis is not available, continue without caching
            self.redis = None
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis:
            return None
        
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration."""
        if not self.redis:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            await self.redis.setex(key, expire, serialized_value)
            return True
        except Exception:
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
