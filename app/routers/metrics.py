# 指标收集路由 - 提供 Prometheus 格式的指标端点
from fastapi import APIRouter, Response
from prometheus_client import (
    Counter, Histogram, Gauge, generate_latest,
    CONTENT_TYPE_LATEST
)

from app.utils.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/metrics", tags=["metrics"])

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

VAPI_CALLS_TOTAL = Counter(
    'vapi_calls_total',
    'Total Vapi calls made',
    ['status']
)

MCP_TOOLS_EXECUTED = Counter(
    'mcp_tools_executed_total',
    'Total MCP tools executed',
    ['tool_name', 'status']
)

CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)


@router.get("/")
async def get_metrics() -> Response:
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus format.
    """
    try:
        metrics_data = generate_latest()
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error("Failed to generate metrics", error=str(e))
        return Response(
            content="# Error generating metrics\n",
            media_type=CONTENT_TYPE_LATEST,
            status_code=500
        )


# Utility functions for updating metrics
def record_request(method: str, endpoint: str, status_code: int, duration: float) -> None:
    """Record HTTP request metrics."""
    REQUEST_COUNT.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code)
    ).inc()
    
    REQUEST_DURATION.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def record_vapi_call(status: str) -> None:
    """Record Vapi call metrics."""
    VAPI_CALLS_TOTAL.labels(status=status).inc()


def record_mcp_tool_execution(tool_name: str, success: bool) -> None:
    """Record MCP tool execution metrics."""
    status = "success" if success else "failure"
    MCP_TOOLS_EXECUTED.labels(tool_name=tool_name, status=status).inc()


def record_cache_hit(cache_type: str) -> None:
    """Record cache hit."""
    CACHE_HITS.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str) -> None:
    """Record cache miss."""
    CACHE_MISSES.labels(cache_type=cache_type).inc()


def set_active_connections(count: int) -> None:
    """Set active connections gauge."""
    ACTIVE_CONNECTIONS.set(count)
