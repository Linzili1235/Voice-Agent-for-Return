# 应用配置管理模块 - 使用 Pydantic Settings 管理环境变量和配置
import re
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    app_name: str = Field(default="Vapi Agent API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of workers")
    
    # Database configuration
    database_url: str = Field(..., description="Database connection URL")
    database_pool_size: int = Field(default=10, description="Database pool size")
    database_max_overflow: int = Field(default=20, description="Database max overflow")
    
    # Security settings
    secret_key: str = Field(..., description="Secret key for JWT tokens")
    access_token_expire_minutes: int = Field(default=30, description="Token expiration time")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    
    # External API configuration
    vapi_api_key: str = Field(..., description="Vapi API key")
    vapi_base_url: str = Field(default="https://api.vapi.ai", description="Vapi base URL")
    mcp_server_url: str = Field(default="http://localhost:3000", description="MCP server URL")
    
    # Redis configuration
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, description="Metrics server port")
    
    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.upper()
    
    @validator("database_url")
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("Database URL must be a PostgreSQL connection string")
        return v
    
    @validator("secret_key")
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key strength."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    @validator("vapi_api_key")
    def validate_vapi_api_key(cls, v: str) -> str:
        """Validate Vapi API key format."""
        if not v or len(v) < 10:
            raise ValueError("Vapi API key must be provided and at least 10 characters long")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
