# 应用配置管理模块 - 使用 Pydantic Settings 管理环境变量和配置
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    app_name: str = Field(default="Voice Agent Return Tools", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8787, description="Server port")
    
    # SMTP Configuration (optional)
    smtp_host: Optional[str] = Field(default=None, description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")
    
    # SMS Configuration (optional)
    sms_api_key: Optional[str] = Field(default=None, description="SMS API key")
    sms_api_url: Optional[str] = Field(default=None, description="SMS API URL")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    
    # LLM Configuration
    provider: str = Field(default="stub", description="LLM provider (openai, anthropic, stub)")
    model: str = Field(default="gpt-4o-mini", description="LLM model name")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    
    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.upper()
    
    @validator("provider")
    def validate_provider(cls, v: str) -> str:
        """Validate LLM provider is one of the allowed values."""
        allowed_providers = ["openai", "anthropic", "stub"]
        if v.lower() not in allowed_providers:
            raise ValueError(f"Provider must be one of {allowed_providers}")
        return v.lower()
    
    @property
    def smtp_configured(self) -> bool:
        """Check if SMTP is properly configured."""
        return bool(self.smtp_host and self.smtp_username and self.smtp_password)
    
    @property
    def sms_configured(self) -> bool:
        """Check if SMS is properly configured."""
        return bool(self.sms_api_key and self.sms_api_url)
    
    @property
    def llm_configured(self) -> bool:
        """Check if LLM is properly configured."""
        if self.provider == "stub":
            return True
        elif self.provider == "openai":
            return bool(self.openai_api_key)
        elif self.provider == "anthropic":
            return bool(self.anthropic_api_key)
        return False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

