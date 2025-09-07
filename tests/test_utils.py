# 工具函数测试 - 测试安全、缓存和日志记录工具函数
import pytest
from unittest.mock import patch, AsyncMock

from app.utils.security import (
    validate_phone_number,
    validate_idempotency_key,
    generate_idempotency_key,
    sanitize_input,
    create_hmac_signature,
    verify_hmac_signature
)
from app.utils.logging import redact_sensitive_data


class TestSecurityUtils:
    """Test security utility functions."""
    
    def test_validate_phone_number_valid(self):
        """Test phone number validation with valid numbers."""
        assert validate_phone_number("1234567890") is True
        assert validate_phone_number("+1234567890") is True
        assert validate_phone_number("(123) 456-7890") is True
        assert validate_phone_number("123-456-7890") is True
    
    def test_validate_phone_number_invalid(self):
        """Test phone number validation with invalid numbers."""
        assert validate_phone_number("123") is False  # Too short
        assert validate_phone_number("12345678901234567890") is False  # Too long
        assert validate_phone_number("") is False  # Empty
        assert validate_phone_number("abc") is False  # Non-numeric
    
    def test_validate_idempotency_key_valid(self):
        """Test idempotency key validation with valid keys."""
        assert validate_idempotency_key("valid-key-123") is True
        assert validate_idempotency_key("valid_key_123") is True
        assert validate_idempotency_key("validkey123") is True
        assert validate_idempotency_key("a") is True  # Minimum length
    
    def test_validate_idempotency_key_invalid(self):
        """Test idempotency key validation with invalid keys."""
        assert validate_idempotency_key("") is False  # Empty
        assert validate_idempotency_key("a" * 256) is False  # Too long
        assert validate_idempotency_key("invalid key!") is False  # Invalid characters
        assert validate_idempotency_key("invalid@key") is False  # Invalid characters
    
    def test_generate_idempotency_key(self):
        """Test idempotency key generation."""
        key1 = generate_idempotency_key()
        key2 = generate_idempotency_key()
        
        assert len(key1) > 0
        assert len(key2) > 0
        assert key1 != key2  # Should be unique
        assert validate_idempotency_key(key1) is True
        assert validate_idempotency_key(key2) is True
    
    def test_sanitize_input_string(self):
        """Test input sanitization for strings."""
        assert sanitize_input("normal text") == "normal text"
        assert sanitize_input("text with <script>") == "text with script"
        assert sanitize_input("text with \"quotes\"") == "text with quotes"
        assert sanitize_input("text with 'apostrophes'") == "text with apostrophes"
    
    def test_sanitize_input_dict(self):
        """Test input sanitization for dictionaries."""
        input_dict = {
            "normal": "value",
            "dangerous": "<script>alert('xss')</script>",
            "nested": {
                "key": "value with \"quotes\""
            }
        }
        
        sanitized = sanitize_input(input_dict)
        assert sanitized["normal"] == "value"
        assert sanitized["dangerous"] == "scriptalert(xss)/script"
        assert sanitized["nested"]["key"] == "value with quotes"
    
    def test_sanitize_input_list(self):
        """Test input sanitization for lists."""
        input_list = ["normal", "<script>", "text with \"quotes\""]
        sanitized = sanitize_input(input_list)
        
        assert sanitized[0] == "normal"
        assert sanitized[1] == "script"
        assert sanitized[2] == "text with quotes"
    
    def test_hmac_signature(self):
        """Test HMAC signature creation and verification."""
        data = "test data"
        secret = "test secret"
        
        signature = create_hmac_signature(data, secret)
        assert len(signature) == 64  # SHA256 hex length
        
        assert verify_hmac_signature(data, signature, secret) is True
        assert verify_hmac_signature(data, "invalid", secret) is False
        assert verify_hmac_signature("different data", signature, secret) is False


class TestLoggingUtils:
    """Test logging utility functions."""
    
    def test_redact_sensitive_data_phone_numbers(self):
        """Test phone number redaction in logs."""
        # Test various phone number formats
        test_cases = [
            ("Call 1234567890", "Call ***-***-7890"),
            ("Call +1234567890", "Call ***-***-7890"),
            ("Call (123) 456-7890", "Call ***-***-7890"),
            ("Call 123-456-7890", "Call ***-***-7890"),
        ]
        
        for input_text, expected in test_cases:
            result = redact_sensitive_data(input_text)
            assert result == expected
    
    def test_redact_sensitive_data_ids(self):
        """Test ID redaction in logs."""
        # Test various ID formats
        test_cases = [
            ("ID: abcdefgh1234", "ID: ********1234"),
            ("ID: 1234567890abcdef", "ID: ************cdef"),
            ("Short ID: abc", "Short ID: abc"),  # Should not redact short IDs
        ]
        
        for input_text, expected in test_cases:
            result = redact_sensitive_data(input_text)
            assert result == expected
    
    def test_redact_sensitive_data_dict(self):
        """Test redaction in dictionary data."""
        input_dict = {
            "phone": "1234567890",
            "id": "abcdefgh1234",
            "normal": "value",
            "nested": {
                "phone": "9876543210",
                "id": "xyz1234567890"
            }
        }
        
        result = redact_sensitive_data(input_dict)
        
        assert result["phone"] == "***-***-7890"
        assert result["id"] == "********1234"
        assert result["normal"] == "value"
        assert result["nested"]["phone"] == "***-***-3210"
        assert result["nested"]["id"] == "**********7890"
    
    def test_redact_sensitive_data_list(self):
        """Test redaction in list data."""
        input_list = [
            "Call 1234567890",
            {"phone": "9876543210"},
            "Normal text"
        ]
        
        result = redact_sensitive_data(input_list)
        
        assert result[0] == "Call ***-***-7890"
        assert result[1]["phone"] == "***-***-3210"
        assert result[2] == "Normal text"
