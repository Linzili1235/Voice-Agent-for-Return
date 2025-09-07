# 基础数据模式定义 - 包含通用响应和错误处理模式
from typing import Any, Dict, Generic, Optional, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field

T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """Base response model for all API endpoints."""
    
    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="Response message")
    data: Optional[T] = Field(default=None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    success: bool = Field(default=False, description="Always false for errors")
    message: str = Field(description="Error message")
    error_code: str = Field(description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(description="Service status")
    version: str = Field(description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    dependencies: Dict[str, str] = Field(description="Dependency status")


class IdempotencyRequest(BaseModel):
    """Base model for idempotent requests."""
    
    idempotency_key: str = Field(..., description="Unique key for idempotency", min_length=1, max_length=255)
