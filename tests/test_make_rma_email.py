# RMA 邮件生成测试 - 测试 make_rma_email 工具的核心功能
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from server.app.main import app


client = TestClient(app)


def test_make_rma_email_amazon():
    """Test RMA email generation for Amazon."""
    request_data = {
        "vendor": "amazon",
        "order_id": "123-4567890-1234567",
        "item_sku": "B08N5WRWNW",
        "intent": "return",
        "reason": "damaged",
        "evidence_urls": ["https://example.com/photo1.jpg"],
        "contact_email": "customer@example.com"
    }
    
    response = client.post("/tools/make_rma_email", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "to_email" in data
    assert "subject" in data
    assert "body" in data
    
    # Check email content
    assert data["to_email"] == "returns@amazon.com"
    assert "123-4567890-1234567" in data["subject"]
    assert "Return" in data["subject"]
    assert "123-4567890-1234567" in data["body"]
    assert "B08N5WRWNW" in data["body"]
    assert "Damaged" in data["body"]
    assert "customer@example.com" in data["body"]


def test_make_rma_email_walmart():
    """Test RMA email generation for Walmart."""
    request_data = {
        "vendor": "walmart",
        "order_id": "WM123456789",
        "item_sku": "WM-SKU-123",
        "intent": "refund",
        "reason": "wrong_item",
        "evidence_urls": [],
        "contact_email": "user@example.com"
    }
    
    response = client.post("/tools/make_rma_email", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["to_email"] == "customer.service@walmart.com"
    assert "WM123456789" in data["subject"]
    assert "Refund" in data["subject"]
    assert "WM123456789" in data["body"]
    assert "WM-SKU-123" in data["body"]
    assert "Wrong Item" in data["body"]


def test_make_rma_email_target():
    """Test RMA email generation for Target."""
    request_data = {
        "vendor": "target",
        "order_id": "TGT-123456",
        "item_sku": "TGT-SKU-456",
        "intent": "replacement",
        "reason": "not_as_described",
        "evidence_urls": [
            "https://example.com/photo1.jpg",
            "https://example.com/photo2.jpg"
        ],
        "contact_email": "customer@example.com"
    }
    
    response = client.post("/tools/make_rma_email", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["to_email"] == "guest.service@target.com"
    assert "TGT-123456" in data["subject"]
    assert "Replacement" in data["subject"]
    assert "TGT-123456" in data["body"]
    assert "TGT-SKU-456" in data["body"]
    assert "Not As Described" in data["body"]


def test_make_rma_email_generic_vendor():
    """Test RMA email generation for unknown vendor (should use generic template)."""
    request_data = {
        "vendor": "unknown_vendor",
        "order_id": "UNK-123456",
        "item_sku": "UNK-SKU-789",
        "intent": "return",
        "reason": "other",
        "evidence_urls": [],
        "contact_email": "customer@example.com"
    }
    
    response = client.post("/tools/make_rma_email", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    
    # Should use generic vendor config
    assert data["to_email"] == "support@vendor.com"
    assert "UNK-123456" in data["subject"]
    assert "UNK-123456" in data["body"]
    assert "UNK-SKU-789" in data["body"]


def test_make_rma_email_missing_evidence_for_amazon():
    """Test that Amazon requires evidence and fails without it."""
    request_data = {
        "vendor": "amazon",
        "order_id": "123-4567890-1234567",
        "item_sku": "B08N5WRWNW",
        "intent": "return",
        "reason": "damaged",
        "evidence_urls": [],  # No evidence provided
        "contact_email": "customer@example.com"
    }
    
    response = client.post("/tools/make_rma_email", json=request_data)
    
    assert response.status_code == 400
    data = response.json()
    assert "requires evidence" in data["detail"].lower()


def test_make_rma_email_too_many_evidence_urls():
    """Test validation for too many evidence URLs."""
    request_data = {
        "vendor": "amazon",
        "order_id": "123-4567890-1234567",
        "item_sku": "B08N5WRWNW",
        "intent": "return",
        "reason": "damaged",
        "evidence_urls": [
            "https://example.com/photo1.jpg",
            "https://example.com/photo2.jpg",
            "https://example.com/photo3.jpg",
            "https://example.com/photo4.jpg"  # Too many for Amazon (max 3)
        ],
        "contact_email": "customer@example.com"
    }
    
    response = client.post("/tools/make_rma_email", json=request_data)
    
    assert response.status_code == 400
    data = response.json()
    assert "too many evidence" in data["detail"].lower()


def test_make_rma_email_invalid_evidence_url():
    """Test validation for invalid evidence URL format."""
    request_data = {
        "vendor": "amazon",
        "order_id": "123-4567890-1234567",
        "item_sku": "B08N5WRWNW",
        "intent": "return",
        "reason": "damaged",
        "evidence_urls": ["invalid-url"],  # Invalid URL format
        "contact_email": "customer@example.com"
    }
    
    response = client.post("/tools/make_rma_email", json=request_data)
    
    assert response.status_code == 400
    data = response.json()
    assert "invalid evidence url" in data["detail"].lower()


def test_make_rma_email_invalid_intent():
    """Test validation for invalid intent value."""
    request_data = {
        "vendor": "amazon",
        "order_id": "123-4567890-1234567",
        "item_sku": "B08N5WRWNW",
        "intent": "invalid_intent",  # Invalid intent
        "reason": "damaged",
        "evidence_urls": ["https://example.com/photo1.jpg"],
        "contact_email": "customer@example.com"
    }
    
    response = client.post("/tools/make_rma_email", json=request_data)
    
    assert response.status_code == 422  # Validation error


def test_make_rma_email_invalid_reason():
    """Test validation for invalid reason value."""
    request_data = {
        "vendor": "amazon",
        "order_id": "123-4567890-1234567",
        "item_sku": "B08N5WRWNW",
        "intent": "return",
        "reason": "invalid_reason",  # Invalid reason
        "evidence_urls": ["https://example.com/photo1.jpg"],
        "contact_email": "customer@example.com"
    }
    
    response = client.post("/tools/make_rma_email", json=request_data)
    
    assert response.status_code == 422  # Validation error


def test_make_rma_email_missing_required_fields():
    """Test validation for missing required fields."""
    request_data = {
        "vendor": "amazon",
        # Missing order_id, item_sku, intent, reason
        "evidence_urls": [],
        "contact_email": "customer@example.com"
    }
    
    response = client.post("/tools/make_rma_email", json=request_data)
    
    assert response.status_code == 422  # Validation error


def test_make_rma_email_without_contact_email():
    """Test RMA email generation without contact email (should use default)."""
    request_data = {
        "vendor": "walmart",
        "order_id": "WM123456789",
        "item_sku": "WM-SKU-123",
        "intent": "return",
        "reason": "damaged",
        "evidence_urls": []
        # No contact_email provided
    }
    
    response = client.post("/tools/make_rma_email", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "Customer" in data["body"]  # Should use default "Customer"

