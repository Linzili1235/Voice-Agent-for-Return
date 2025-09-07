# Vapi API 测试 - 测试语音通话相关的 API 端点
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.schemas.vapi import VapiCallResponse, VapiCallStatus


def test_create_call_invalid_phone(client: TestClient, sample_vapi_call_request):
    """Test creating a call with invalid phone number."""
    # Test with invalid phone number
    invalid_request = sample_vapi_call_request.copy()
    invalid_request["phone_number"] = "123"  # Too short
    
    response = client.post("/vapi/calls", json=invalid_request)
    assert response.status_code == 422  # Validation error


def test_create_call_invalid_idempotency_key(client: TestClient, sample_vapi_call_request):
    """Test creating a call with invalid idempotency key."""
    invalid_request = sample_vapi_call_request.copy()
    invalid_request["idempotency_key"] = ""  # Empty key
    
    response = client.post("/vapi/calls", json=invalid_request)
    assert response.status_code == 422  # Validation error


@patch('app.services.vapi_service.vapi_service.create_call')
def test_create_call_success(mock_create_call, client: TestClient, sample_vapi_call_request):
    """Test successful call creation."""
    # Mock the service response
    mock_response = VapiCallResponse(
        call_id="call-123",
        status="initiated",
        phone_number="1234567890",
        assistant_id="assistant-123",
        created_at="2023-01-01T00:00:00Z",
        estimated_duration=300
    )
    mock_create_call.return_value = mock_response
    
    response = client.post("/vapi/calls", json=sample_vapi_call_request)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Call created successfully"
    assert data["data"]["call_id"] == "call-123"


@patch('app.services.vapi_service.vapi_service.get_call_status')
def test_get_call_status_success(mock_get_status, client: TestClient):
    """Test successful call status retrieval."""
    # Mock the service response
    mock_response = VapiCallStatus(
        call_id="call-123",
        status="completed",
        duration=300,
        transcript="Test transcript",
        summary="Test summary",
        ended_at="2023-01-01T00:05:00Z",
        metadata={"test": True}
    )
    mock_get_status.return_value = mock_response
    
    response = client.get("/vapi/calls/call-123")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Call status retrieved successfully"
    assert data["data"]["call_id"] == "call-123"
    assert data["data"]["status"] == "completed"


@patch('app.services.vapi_service.vapi_service.handle_webhook')
def test_webhook_handling(mock_handle_webhook, client: TestClient):
    """Test webhook handling."""
    mock_handle_webhook.return_value = True
    
    webhook_payload = {
        "event_type": "call.ended",
        "call_id": "call-123",
        "data": {"duration": 300},
        "timestamp": "2023-01-01T00:05:00Z"
    }
    
    response = client.post("/vapi/webhooks", json=webhook_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Webhook processed"
