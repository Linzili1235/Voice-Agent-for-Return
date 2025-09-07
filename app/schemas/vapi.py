# Vapi API 相关数据模式 - 定义与 Vapi 服务交互的数据结构
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator

from .base import IdempotencyRequest


class VapiCallRequest(IdempotencyRequest):
    """Request model for initiating a Vapi call."""
    
    phone_number: str = Field(..., description="Phone number to call", min_length=10, max_length=15)
    assistant_id: str = Field(..., description="Vapi assistant ID", min_length=1)
    customer_id: Optional[str] = Field(default=None, description="Customer identifier")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional call metadata")
    
    @validator("phone_number")
    def validate_phone_number(cls, v: str) -> str:
        """Validate phone number format."""
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, v))
        if len(digits_only) < 10:
            raise ValueError("Phone number must contain at least 10 digits")
        return digits_only


class VapiCallResponse(BaseModel):
    """Response model for Vapi call creation."""
    
    call_id: str = Field(description="Unique call identifier")
    status: str = Field(description="Call status")
    phone_number: str = Field(description="Called phone number (redacted)")
    assistant_id: str = Field(description="Assistant ID used")
    created_at: datetime = Field(description="Call creation timestamp")
    estimated_duration: Optional[int] = Field(default=None, description="Estimated call duration in seconds")


class VapiCallStatus(BaseModel):
    """Model for Vapi call status information."""
    
    call_id: str = Field(description="Call identifier")
    status: str = Field(description="Current call status")
    duration: Optional[int] = Field(default=None, description="Call duration in seconds")
    transcript: Optional[str] = Field(default=None, description="Call transcript")
    summary: Optional[str] = Field(default=None, description="Call summary")
    ended_at: Optional[datetime] = Field(default=None, description="Call end timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Call metadata")


class VapiWebhookPayload(BaseModel):
    """Model for Vapi webhook payloads."""
    
    event_type: str = Field(description="Type of webhook event")
    call_id: str = Field(description="Call identifier")
    data: Dict[str, Any] = Field(description="Event data")
    timestamp: datetime = Field(description="Event timestamp")
