# 指标测试 - 测试 Prometheus 指标端点和指标收集功能
import pytest
from fastapi.testclient import TestClient


def test_metrics_endpoint(client: TestClient):
    """Test metrics endpoint returns Prometheus format."""
    response = client.get("/metrics/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
    
    # Check that response contains Prometheus metrics format
    content = response.text
    assert "# HELP" in content or "# TYPE" in content


def test_metrics_after_request(client: TestClient):
    """Test that metrics are recorded after making requests."""
    # Make a request to generate metrics
    client.get("/health/")
    
    # Check metrics endpoint
    response = client.get("/metrics/")
    assert response.status_code == 200
    
    content = response.text
    # Should contain HTTP request metrics
    assert "http_requests_total" in content or "http_request_duration_seconds" in content
