# 元数据路由 - 处理健康检查和指标监控相关的 API 端点
from fastapi import APIRouter, Response
from prometheus_client import (
    Counter, Histogram, Gauge, generate_latest,
    CONTENT_TYPE_LATEST
)
import time

from app.schemas import HealthResponse
from app.config import settings
from app.utils import get_logger


logger = get_logger(__name__)
router = APIRouter(tags=["meta"])

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

RMA_EMAILS_GENERATED = Counter(
    'rma_emails_generated_total',
    'Total RMA emails generated',
    ['vendor', 'intent', 'reason']
)

EMAILS_SENT = Counter(
    'emails_sent_total',
    'Total emails sent',
    ['status']
)

SMS_SENT = Counter(
    'sms_sent_total',
    'Total SMS messages sent',
    ['status']
)

SUBMISSIONS_LOGGED = Counter(
    'submissions_logged_total',
    'Total RMA submissions logged',
    ['vendor', 'intent']
)


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns the current status of the service.
    """
    return HealthResponse(
        status="ok",
        version=settings.app_version
    )


@router.get("/metrics")
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


def record_rma_email_generated(vendor: str, intent: str, reason: str) -> None:
    """Record RMA email generation metrics."""
    RMA_EMAILS_GENERATED.labels(
        vendor=vendor,
        intent=intent,
        reason=reason
    ).inc()


def record_email_sent(success: bool) -> None:
    """Record email sending metrics."""
    status = "success" if success else "failure"
    EMAILS_SENT.labels(status=status).inc()


def record_sms_sent(success: bool) -> None:
    """Record SMS sending metrics."""
    status = "success" if success else "failure"
    SMS_SENT.labels(status=status).inc()


def record_submission_logged(vendor: str, intent: str) -> None:
    """Record submission logging metrics."""
    SUBMISSIONS_LOGGED.labels(
        vendor=vendor,
        intent=intent
    ).inc()
