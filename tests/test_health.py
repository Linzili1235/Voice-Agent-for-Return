# 健康检查测试 - 测试系统健康状态和依赖检查功能
import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health/")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "timestamp" in data
    assert "dependencies" in data


def test_readiness_check(client: TestClient):
    """Test readiness check endpoint."""
    response = client.get("/health/ready")
    assert response.status_code in [200, 503]  # May be 503 if Redis is not available
    
    data = response.json()
    assert "status" in data
    assert "timestamp" in data


def test_liveness_check(client: TestClient):
    """Test liveness check endpoint."""
    response = client.get("/health/live")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "running"
