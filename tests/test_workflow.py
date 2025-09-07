# 退货流程测试 - 测试完整的退货/退款流程功能
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from server.app.main import app


client = TestClient(app)


def test_return_workflow_amazon_success():
    """Test successful return workflow for Amazon."""
    request_data = {
        "vendor": "amazon",
        "order_id": "123-4567890-1234567",
        "item_sku": "B08N5WRWNW",
        "intent": "return",
        "reason": "damaged",
        "evidence_urls": ["https://example.com/photo1.jpg"],
        "contact_email": "customer@example.com",
        "contact_phone": "+1234567890"
    }
    
    with patch('server.app.services.workflow_service.workflow_service.execute_return_workflow') as mock_workflow:
        mock_workflow.return_value = AsyncMock(
            status="completed",
            message="Return workflow completed successfully",
            data={
                "email_sent": True,
                "sms_sent": True,
                "logged": True,
                "msg_id": "smtp-abc12345",
                "to_email": "returns@amazon.com",
                "subject": "RMA Request - Order 123-4567890-1234567 - Return"
            },
            error=None,
            execution_time=1.5
        )
        
        response = client.post("/workflow/return", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "completed"
        assert data["message"] == "Return workflow completed successfully"
        assert data["data"]["email_sent"] is True
        assert data["data"]["sms_sent"] is True
        assert data["data"]["msg_id"] == "smtp-abc12345"


def test_return_workflow_walmart_without_evidence():
    """Test return workflow for Walmart without evidence."""
    request_data = {
        "vendor": "walmart",
        "order_id": "WM123456789",
        "item_sku": "WM-SKU-123",
        "intent": "refund",
        "reason": "wrong_item",
        "evidence_urls": [],
        "contact_email": "user@example.com",
        "contact_phone": "+1987654321"
    }
    
    with patch('server.app.services.workflow_service.workflow_service.execute_return_workflow') as mock_workflow:
        mock_workflow.return_value = AsyncMock(
            status="completed",
            message="Return workflow completed successfully",
            data={
                "email_sent": True,
                "sms_sent": True,
                "logged": True,
                "msg_id": "smtp-def67890"
            },
            error=None,
            execution_time=2.1
        )
        
        response = client.post("/workflow/return", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "completed"
        assert data["data"]["email_sent"] is True


def test_return_workflow_email_failure_sms_fallback():
    """Test return workflow with email failure and SMS fallback."""
    request_data = {
        "vendor": "target",
        "order_id": "TGT-123456",
        "item_sku": "TGT-SKU-456",
        "intent": "replacement",
        "reason": "not_as_described",
        "evidence_urls": ["https://example.com/photo1.jpg"],
        "contact_email": "customer@example.com",
        "contact_phone": "+1555123456"
    }
    
    with patch('server.app.services.workflow_service.workflow_service.execute_return_workflow') as mock_workflow:
        mock_workflow.return_value = AsyncMock(
            status="completed",
            message="Email failed, sent fallback SMS",
            data={
                "email_sent": False,
                "sms_sent": True,
                "logged": False,
                "msg_id": "sms-stub-12345"
            },
            error=None,
            execution_time=1.8
        )
        
        response = client.post("/workflow/return", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "completed"
        assert data["message"] == "Email failed, sent fallback SMS"
        assert data["data"]["email_sent"] is False
        assert data["data"]["sms_sent"] is True


def test_return_workflow_complete_failure():
    """Test return workflow with complete failure."""
    request_data = {
        "vendor": "amazon",
        "order_id": "123-4567890-1234567",
        "item_sku": "B08N5WRWNW",
        "intent": "return",
        "reason": "damaged",
        "evidence_urls": ["https://example.com/photo1.jpg"],
        "contact_email": "customer@example.com",
        "contact_phone": "+1234567890"
    }
    
    with patch('server.app.services.workflow_service.workflow_service.execute_return_workflow') as mock_workflow:
        mock_workflow.return_value = AsyncMock(
            status="failed",
            message="Return workflow failed",
            data=None,
            error="Email service unavailable",
            execution_time=0.5
        )
        
        response = client.post("/workflow/return", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "failed"
        assert data["message"] == "Return workflow failed"
        assert data["error"] == "Email service unavailable"


def test_return_workflow_invalid_vendor():
    """Test return workflow with invalid vendor."""
    request_data = {
        "vendor": "invalid_vendor",
        "order_id": "TEST-123",
        "item_sku": "SKU-456",
        "intent": "return",
        "reason": "damaged",
        "evidence_urls": [],
        "contact_email": "customer@example.com"
    }
    
    with patch('server.app.services.workflow_service.workflow_service.execute_return_workflow') as mock_workflow:
        mock_workflow.return_value = AsyncMock(
            status="failed",
            message="Failed to generate RMA email",
            data=None,
            error="Vendor not found",
            execution_time=0.2
        )
        
        response = client.post("/workflow/return", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "failed"
        assert "Vendor not found" in data["error"]


def test_return_workflow_missing_required_fields():
    """Test return workflow with missing required fields."""
    request_data = {
        "vendor": "amazon",
        # Missing order_id, item_sku, intent, reason
        "evidence_urls": [],
        "contact_email": "customer@example.com"
    }
    
    response = client.post("/workflow/return", json=request_data)
    
    assert response.status_code == 422  # Validation error


def test_return_workflow_invalid_intent():
    """Test return workflow with invalid intent."""
    request_data = {
        "vendor": "amazon",
        "order_id": "123-4567890-1234567",
        "item_sku": "B08N5WRWNW",
        "intent": "invalid_intent",  # Invalid intent
        "reason": "damaged",
        "evidence_urls": [],
        "contact_email": "customer@example.com"
    }
    
    response = client.post("/workflow/return", json=request_data)
    
    assert response.status_code == 422  # Validation error


def test_return_workflow_invalid_phone():
    """Test return workflow with invalid phone number."""
    request_data = {
        "vendor": "amazon",
        "order_id": "123-4567890-1234567",
        "item_sku": "B08N5WRWNW",
        "intent": "return",
        "reason": "damaged",
        "evidence_urls": [],
        "contact_email": "customer@example.com",
        "contact_phone": "123"  # Invalid phone number
    }
    
    response = client.post("/workflow/return", json=request_data)
    
    assert response.status_code == 422  # Validation error


def test_policy_query_amazon():
    """Test policy query for Amazon."""
    request_data = {
        "vendor": "amazon"
    }
    
    with patch('server.app.services.workflow_service.workflow_service.get_vendor_policy_info') as mock_policy:
        mock_policy.return_value = {
            "return_window": "30天退货窗口",
            "refund_method": "原支付方式退款",
            "shipping": "免费退货标签",
            "condition": "商品需保持原包装"
        }
        
        response = client.post("/workflow/policy", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["vendor"] == "amazon"
        assert "return_window" in data["policies"]
        assert data["policies"]["return_window"] == "30天退货窗口"


def test_policy_query_specific_key():
    """Test policy query for specific key."""
    request_data = {
        "vendor": "walmart",
        "policy_key": "return_window"
    }
    
    with patch('server.app.services.workflow_service.workflow_service.get_vendor_policy_info') as mock_policy:
        mock_policy.return_value = {
            "return_window": "90天退货窗口"
        }
        
        response = client.post("/workflow/policy", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["vendor"] == "walmart"
        assert data["policies"]["return_window"] == "90天退货窗口"


def test_policy_query_invalid_vendor():
    """Test policy query for invalid vendor."""
    request_data = {
        "vendor": "invalid_vendor"
    }
    
    with patch('server.app.services.workflow_service.workflow_service.get_vendor_policy_info') as mock_policy:
        mock_policy.return_value = {}
        
        response = client.post("/workflow/policy", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["vendor"] == "invalid_vendor"
        assert data["policies"] == {}


def test_workflow_status():
    """Test workflow status endpoint."""
    response = client.get("/workflow/status")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "operational"
    assert "max_execution_time" in data
    assert "max_retries" in data
    assert "supported_vendors" in data
    assert "amazon" in data["supported_vendors"]


def test_return_workflow_without_contact_info():
    """Test return workflow without contact email or phone."""
    request_data = {
        "vendor": "amazon",
        "order_id": "123-4567890-1234567",
        "item_sku": "B08N5WRWNW",
        "intent": "return",
        "reason": "damaged",
        "evidence_urls": ["https://example.com/photo1.jpg"]
        # No contact_email or contact_phone
    }
    
    with patch('server.app.services.workflow_service.workflow_service.execute_return_workflow') as mock_workflow:
        mock_workflow.return_value = AsyncMock(
            status="completed",
            message="Return workflow completed successfully",
            data={
                "email_sent": True,
                "sms_sent": False,  # No phone number
                "logged": True,
                "msg_id": "smtp-xyz98765"
            },
            error=None,
            execution_time=1.2
        )
        
        response = client.post("/workflow/return", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "completed"
        assert data["data"]["email_sent"] is True
        assert data["data"]["sms_sent"] is False
