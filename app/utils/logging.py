# 日志记录工具模块 - 提供结构化日志记录和敏感信息脱敏功能
import sys
import logging
import re
from typing import Any, Dict, Optional
import structlog
from structlog.stdlib import LoggerFactory

from app.config.settings import settings


def redact_sensitive_data(data: Any) -> Any:
    """
    Redact sensitive information from data for logging.
    Redacts phone numbers and IDs to show only last 4 digits.
    """
    if isinstance(data, str):
        # Redact phone numbers (keep last 4 digits)
        phone_pattern = r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        data = re.sub(phone_pattern, r'***-***-\3\4', data)
        
        # Redact IDs (keep last 4 characters)
        id_pattern = r'\b([a-zA-Z0-9]{8,})\b'
        data = re.sub(id_pattern, lambda m: '*' * (len(m.group(1)) - 4) + m.group(1)[-4:], data)
        
        return data
    
    elif isinstance(data, dict):
        return {key: redact_sensitive_data(value) for key, value in data.items()}
    
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    
    return data


def setup_logging() -> None:
    """Setup structured logging configuration."""
    
    # Configure structlog
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
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def log_request(
    logger: structlog.stdlib.BoundLogger,
    method: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
) -> None:
    """Log an incoming request with redacted sensitive data."""
    log_data = {
        "method": method,
        "path": path,
        "params": redact_sensitive_data(params) if params else None,
        "user_id": user_id
    }
    logger.info("Request received", **log_data)


def log_response(
    logger: structlog.stdlib.BoundLogger,
    status_code: int,
    response_time: float,
    error: Optional[str] = None
) -> None:
    """Log a response with timing information."""
    log_data = {
        "status_code": status_code,
        "response_time_ms": round(response_time * 1000, 2),
        "error": error
    }
    logger.info("Response sent", **log_data)


def log_external_api_call(
    logger: structlog.stdlib.BoundLogger,
    service: str,
    endpoint: str,
    method: str,
    status_code: int,
    response_time: float,
    error: Optional[str] = None
) -> None:
    """Log external API calls with timing and error information."""
    log_data = {
        "service": service,
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "response_time_ms": round(response_time * 1000, 2),
        "error": error
    }
    logger.info("External API call", **log_data)
