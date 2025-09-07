# 健康检查和监控路由 - 提供系统状态和指标端点
import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
import httpx

from app.schemas.base import HealthCheckResponse
from app.config.settings import settings
from app.utils.cache import cache_manager
from app.utils.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


async def check_database() -> str:
    """Check database connectivity."""
    try:
        # Here you would check your database connection
        # For now, we'll assume it's healthy
        return "healthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return "unhealthy"


async def check_redis() -> str:
    """Check Redis connectivity."""
    try:
        if cache_manager.redis:
            await cache_manager.redis.ping()
            return "healthy"
        return "unhealthy"
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        return "unhealthy"


async def check_vapi_api() -> str:
    """Check Vapi API connectivity."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.vapi_base_url}/health",
                headers={"Authorization": f"Bearer {settings.vapi_api_key}"},
                timeout=5.0
            )
            return "healthy" if response.is_success else "unhealthy"
    except Exception as e:
        logger.error("Vapi API health check failed", error=str(e))
        return "unhealthy"


async def check_mcp_server() -> str:
    """Check MCP server connectivity."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.mcp_server_url}/health",
                timeout=5.0
            )
            return "healthy" if response.is_success else "unhealthy"
    except Exception as e:
        logger.error("MCP server health check failed", error=str(e))
        return "unhealthy"


@router.get("/", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    Comprehensive health check endpoint.
    Checks all system dependencies and returns overall status.
    """
    start_time = time.time()
    
    # Check all dependencies
    dependencies = {
        "database": await check_database(),
        "redis": await check_redis(),
        "vapi_api": await check_vapi_api(),
        "mcp_server": await check_mcp_server()
    }
    
    # Determine overall status
    overall_status = "healthy" if all(
        status == "healthy" for status in dependencies.values()
    ) else "unhealthy"
    
    response_time = time.time() - start_time
    
    logger.info(
        "Health check completed",
        status=overall_status,
        response_time_ms=round(response_time * 1000, 2),
        dependencies=dependencies
    )
    
    return HealthCheckResponse(
        status=overall_status,
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        dependencies=dependencies
    )


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Kubernetes readiness probe endpoint.
    Returns 200 if service is ready to accept traffic.
    """
    # Check critical dependencies only
    redis_status = await check_redis()
    
    if redis_status != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )
    
    return {"status": "ready", "timestamp": datetime.utcnow()}


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes liveness probe endpoint.
    Returns 200 if service is alive.
    """
    return {"status": "alive", "timestamp": datetime.utcnow()}
