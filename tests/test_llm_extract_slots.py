# LLM 槽位提取测试 - 测试 llm_extract_slots 工具的核心功能
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from server.app.main import app


client = TestClient(app)


def test_llm_extract_slots_messy_mixed_sentence():
    """Test slot extraction from messy mixed sentence with all information present."""
    request_data = {
        "transcript": "I need to return my Amazon order 123-4567890-1234567, the item B08N5WRWNW is damaged and broken",
        "locale": "en-US",
        "target_language": None
    }
    
    with patch('server.app.services.llm_service.llm_client.extract_slots') as mock_extract:
        mock_extract.return_value = AsyncMock(
            ok=True,
            language="en-US",
            slots={
                "vendor": "amazon",
                "order_id": "123-4567890-1234567",
                "item_sku": "B08N5WRWNW",
                "intent": "return",
                "reason": "damaged",
                "evidence_urls": []
            },
            missing_fields=[],
            clarify_question=None,
            recap_line="I'll help you with your amazon order 123-4567890-1234567 return request due to damaged.",
            notes="Rule-based extraction using keyword matching"
        )
        
        response = client.post("/tools/llm_extract_slots", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert data["ok"] is True
        assert data["language"] == "en-US"
        assert "slots" in data
        assert "missing_fields" in data
        assert "clarify_question" in data
        assert "recap_line" in data
        assert "notes" in data
        
        # Check extracted slots
        slots = data["slots"]
        assert slots["vendor"] == "amazon"
        assert slots["order_id"] == "123-4567890-1234567"
        assert slots["item_sku"] == "B08N5WRWNW"
        assert slots["intent"] == "return"
        assert slots["reason"] == "damaged"
        assert slots["evidence_urls"] == []
        
        # Check that no fields are missing
        assert data["missing_fields"] == []
        assert data["clarify_question"] is None


def test_llm_extract_slots_missing_order_id():
    """Test slot extraction when order_id is missing."""
    request_data = {
        "transcript": "I want to return something from Amazon, the item is damaged",
        "locale": "en-US",
        "target_language": None
    }
    
    with patch('server.app.services.llm_service.llm_client.extract_slots') as mock_extract:
        mock_extract.return_value = AsyncMock(
            ok=True,
            language="en-US",
            slots={
                "vendor": "amazon",
                "order_id": None,
                "item_sku": None,
                "intent": "return",
                "reason": "damaged",
                "evidence_urls": []
            },
            missing_fields=["order_id", "item_sku"],
            clarify_question="What is your order number?",
            recap_line="I'll help you with your amazon order return request due to damaged.",
            notes="Rule-based extraction using keyword matching"
        )
        
        response = client.post("/tools/llm_extract_slots", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert data["ok"] is True
        assert data["language"] == "en-US"
        
        # Check extracted slots
        slots = data["slots"]
        assert slots["vendor"] == "amazon"
        assert slots["order_id"] is None
        assert slots["item_sku"] is None
        assert slots["intent"] == "return"
        assert slots["reason"] == "damaged"
        
        # Check missing fields and clarification
        assert "order_id" in data["missing_fields"]
        assert "item_sku" in data["missing_fields"]
        assert data["clarify_question"] is not None
        assert "order number" in data["clarify_question"].lower()


def test_llm_extract_slots_correction_phrase():
    """Test slot extraction with correction phrase (更正：...)."""
    request_data = {
        "transcript": "I want to return my Walmart order WM123456789. 更正：Actually it's Target order TGT-123456, the item is wrong",
        "locale": "en-US",
        "target_language": None
    }
    
    with patch('server.app.services.llm_service.llm_client.extract_slots') as mock_extract:
        mock_extract.return_value = AsyncMock(
            ok=True,
            language="en-US",
            slots={
                "vendor": "target",
                "order_id": "TGT-123456",
                "item_sku": None,
                "intent": "return",
                "reason": "wrong_item",
                "evidence_urls": []
            },
            missing_fields=["item_sku"],
            clarify_question="What is the SKU or product name of the wrong item you received?",
            recap_line="I'll help you with your target order TGT-123456 return request due to wrong_item.",
            notes="User corrected vendor from Walmart to Target, final values used"
        )
        
        response = client.post("/tools/llm_extract_slots", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert data["ok"] is True
        assert data["language"] == "en-US"
        
        # Check that corrected values are used
        slots = data["slots"]
        assert slots["vendor"] == "target"  # Corrected value
        assert slots["order_id"] == "TGT-123456"  # Corrected value
        assert slots["intent"] == "return"
        assert slots["reason"] == "wrong_item"
        
        # Check missing fields
        assert data["missing_fields"] == ["item_sku"]
        assert data["clarify_question"] is not None


def test_llm_extract_slots_chinese_transcript():
    """Test slot extraction with Chinese transcript."""
    request_data = {
        "transcript": "我的亚马逊订单123-4567890-1234567中的商品B08N5WRWNW有损坏，我想退货",
        "locale": "zh-CN",
        "target_language": None
    }
    
    with patch('server.app.services.llm_service.llm_client.extract_slots') as mock_extract:
        mock_extract.return_value = AsyncMock(
            ok=True,
            language="zh-CN",
            slots={
                "vendor": "amazon",
                "order_id": "123-4567890-1234567",
                "item_sku": "B08N5WRWNW",
                "intent": "return",
                "reason": "damaged",
                "evidence_urls": []
            },
            missing_fields=[],
            clarify_question=None,
            recap_line="我来帮您处理亚马逊订单123-4567890-1234567中损坏商品B08N5WRWNW的退货申请。",
            notes="Complete information provided in single Chinese sentence"
        )
        
        response = client.post("/tools/llm_extract_slots", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert data["ok"] is True
        assert data["language"] == "zh-CN"
        
        # Check extracted slots
        slots = data["slots"]
        assert slots["vendor"] == "amazon"
        assert slots["order_id"] == "123-4567890-1234567"
        assert slots["item_sku"] == "B08N5WRWNW"
        assert slots["intent"] == "return"
        assert slots["reason"] == "damaged"
        
        # Check that no fields are missing
        assert data["missing_fields"] == []
        assert data["clarify_question"] is None


def test_llm_extract_slots_invalid_input():
    """Test slot extraction with invalid input format."""
    request_data = {
        "transcript": "",  # Empty transcript
        "locale": "en-US"
    }
    
    with patch('server.app.services.llm_service.llm_client.extract_slots') as mock_extract:
        mock_extract.return_value = AsyncMock(
            ok=False,
            language=None,
            slots={
                "vendor": None,
                "order_id": None,
                "item_sku": None,
                "intent": None,
                "reason": None,
                "evidence_urls": []
            },
            missing_fields=["unknown"],
            clarify_question=None,
            recap_line=None,
            notes="Error: Empty transcript provided"
        )
        
        response = client.post("/tools/llm_extract_slots", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check error response
        assert data["ok"] is False
        assert data["missing_fields"] == ["unknown"]
        assert data["clarify_question"] is None
        assert data["recap_line"] is None


def test_llm_extract_slots_service_error():
    """Test slot extraction when LLM service fails."""
    request_data = {
        "transcript": "I want to return my Amazon order",
        "locale": "en-US"
    }
    
    with patch('server.app.services.llm_service.llm_client.extract_slots') as mock_extract:
        mock_extract.side_effect = Exception("LLM service unavailable")
        
        response = client.post("/tools/llm_extract_slots", json=request_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "Internal server error" in data["detail"]


def test_llm_extract_slots_missing_required_fields():
    """Test slot extraction with missing required fields."""
    request_data = {
        "locale": "en-US"
        # Missing transcript field
    }
    
    response = client.post("/tools/llm_extract_slots", json=request_data)
    
    assert response.status_code == 422  # Validation error


def test_llm_extract_slots_with_evidence_urls():
    """Test slot extraction with evidence URLs."""
    request_data = {
        "transcript": "I want to return my Amazon order 123-4567890-1234567, the item is damaged. Here's the photo: https://example.com/photo1.jpg",
        "locale": "en-US"
    }
    
    with patch('server.app.services.llm_service.llm_client.extract_slots') as mock_extract:
        mock_extract.return_value = AsyncMock(
            ok=True,
            language="en-US",
            slots={
                "vendor": "amazon",
                "order_id": "123-4567890-1234567",
                "item_sku": None,
                "intent": "return",
                "reason": "damaged",
                "evidence_urls": ["https://example.com/photo1.jpg"]
            },
            missing_fields=["item_sku"],
            clarify_question="What is the SKU or product name of the item you want to return?",
            recap_line="I'll help you with your amazon order 123-4567890-1234567 return request due to damaged.",
            notes="Rule-based extraction using keyword matching"
        )
        
        response = client.post("/tools/llm_extract_slots", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check evidence URLs are extracted
        slots = data["slots"]
        assert slots["evidence_urls"] == ["https://example.com/photo1.jpg"]
