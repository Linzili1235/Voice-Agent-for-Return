# 数据模式定义模块 - 包含所有 API 请求和响应的数据模型
from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, validator


# RMA Email Tool Schemas
class MakeRMAEmailRequest(BaseModel):
    """Request model for making RMA email."""
    
    vendor: str = Field(..., description="Vendor name", min_length=1)
    order_id: str = Field(..., description="Order ID", min_length=1)
    item_sku: str = Field(..., description="Item SKU", min_length=1)
    intent: Literal["return", "refund", "replacement"] = Field(..., description="Intent type")
    reason: Literal["damaged", "missing", "wrong_item", "not_as_described", "other"] = Field(..., description="Reason for RMA")
    evidence_urls: List[str] = Field(default_factory=list, description="Evidence URLs")
    contact_email: Optional[str] = Field(default=None, description="Contact email address")
    
    @validator("contact_email")
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format if provided."""
        if v is not None and "@" not in v:
            raise ValueError("Invalid email format")
        return v


class MakeRMAEmailResponse(BaseModel):
    """Response model for making RMA email."""
    
    to_email: str = Field(description="Recipient email address")
    subject: str = Field(description="Email subject")
    body: str = Field(description="Email body content")


# Email Service Schemas
class SendEmailRequest(BaseModel):
    """Request model for sending email."""
    
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    idempotency_key: Optional[str] = Field(default=None, description="Idempotency key for duplicate prevention")
    
    @validator("to")
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v


class SendEmailResponse(BaseModel):
    """Response model for sending email."""
    
    ok: bool = Field(description="Whether email was sent successfully")
    msg_id: Optional[str] = Field(default=None, description="Message ID if successful")


# Log Submission Schemas
class LogSubmissionRequest(BaseModel):
    """Request model for logging submission."""
    
    vendor: str = Field(..., description="Vendor name")
    order_id_last4: str = Field(..., description="Last 4 digits of order ID", min_length=4, max_length=4)
    intent: Literal["return", "refund", "replacement"] = Field(..., description="Intent type")
    reason: Literal["damaged", "missing", "wrong_item", "not_as_described", "other"] = Field(..., description="Reason for RMA")
    msg_id: Optional[str] = Field(default=None, description="Message ID from email sending")


class LogSubmissionResponse(BaseModel):
    """Response model for logging submission."""
    
    ok: bool = Field(description="Whether logging was successful")


# SMS Service Schemas
class SendSMSRequest(BaseModel):
    """Request model for sending SMS."""
    
    phone: str = Field(..., description="Phone number")
    text: str = Field(..., description="SMS text content")
    
    @validator("phone")
    def validate_phone(cls, v: str) -> str:
        """Validate phone number format."""
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, v))
        if len(digits_only) < 10:
            raise ValueError("Phone number must contain at least 10 digits")
        return digits_only


class SendSMSResponse(BaseModel):
    """Response model for sending SMS."""
    
    ok: bool = Field(description="Whether SMS was sent successfully")


# Health Check Schemas
class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field(description="Application version")


# Error Response Schema
class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(description="Error message")
    detail: Optional[str] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
