# 退货流程路由 - 处理完整的退货/退款流程 API 端点
from fastapi import APIRouter, HTTPException, status, Request
from typing import Optional, List, Literal
import time
from pydantic import BaseModel, Field, validator

from app.schemas import (
    MakeRMAEmailRequest, MakeRMAEmailResponse,
    SendEmailRequest, SendEmailResponse,
    LogSubmissionRequest, LogSubmissionResponse,
    SendSMSRequest, SendSMSResponse
)
from app.services.workflow_service import workflow_service, WorkflowResult, WorkflowStatus
from app.utils import get_logger, redact_sensitive_data
from app.routers.meta import record_rma_email_generated, record_email_sent, record_sms_sent, record_submission_logged


logger = get_logger(__name__)
router = APIRouter(prefix="/workflow", tags=["workflow"])


class ReturnWorkflowRequest(BaseModel):
    """Request model for return workflow."""
    
    vendor: str = Field(..., description="Vendor name", min_length=1)
    order_id: str = Field(..., description="Order ID", min_length=1)
    item_sku: str = Field(..., description="Item SKU", min_length=1)
    intent: Literal["return", "refund", "replacement"] = Field(..., description="Intent type")
    reason: Literal["damaged", "missing", "wrong_item", "not_as_described", "other"] = Field(..., description="Reason for RMA")
    evidence_urls: List[str] = Field(default_factory=list, description="Evidence URLs")
    contact_email: Optional[str] = Field(default=None, description="Contact email address")
    contact_phone: Optional[str] = Field(default=None, description="Contact phone number")
    
    @validator("contact_email")
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format if provided."""
        if v is not None and "@" not in v:
            raise ValueError("Invalid email format")
        return v
    
    @validator("contact_phone")
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format if provided."""
        if v is not None:
            # Remove all non-digit characters
            digits_only = ''.join(filter(str.isdigit, v))
            if len(digits_only) < 10:
                raise ValueError("Phone number must contain at least 10 digits")
        return v


class ReturnWorkflowResponse(BaseModel):
    """Response model for return workflow."""
    
    status: str = Field(description="Workflow status")
    message: str = Field(description="Response message")
    data: Optional[dict] = Field(default=None, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time: float = Field(description="Execution time in seconds")


class PolicyQueryRequest(BaseModel):
    """Request model for policy query."""
    
    vendor: str = Field(..., description="Vendor name", min_length=1)
    policy_key: Optional[str] = Field(default=None, description="Specific policy key to query")


class PolicyQueryResponse(BaseModel):
    """Response model for policy query."""
    
    vendor: str = Field(description="Vendor name")
    policies: dict = Field(description="Policy information")


@router.post("/return", response_model=ReturnWorkflowResponse)
async def execute_return_workflow(
    request: ReturnWorkflowRequest,
    http_request: Request
) -> ReturnWorkflowResponse:
    """
    Execute complete return/refund workflow.
    
    This endpoint handles the complete workflow:
    1. Generate RMA email
    2. Send email
    3. Log submission
    4. Send confirmation SMS
    
    All operations are idempotent and include retry logic.
    """
    start_time = time.time()
    
    # Log incoming request with redacted sensitive data
    log_data = redact_sensitive_data(request.dict())
    logger.info(
        "Return workflow request",
        method=http_request.method,
        path=http_request.url.path,
        **log_data
    )
    
    try:
        # Execute workflow
        result = await workflow_service.execute_return_workflow(
            vendor=request.vendor,
            order_id=request.order_id,
            item_sku=request.item_sku,
            intent=request.intent,
            reason=request.reason,
            evidence_urls=request.evidence_urls,
            contact_email=request.contact_email,
            contact_phone=request.contact_phone
        )
        
        # Record metrics
        if result.status == WorkflowStatus.COMPLETED:
            record_rma_email_generated(request.vendor, request.intent, request.reason)
            record_email_sent(True)
            if result.data and result.data.get("sms_sent"):
                record_sms_sent(True)
            record_submission_logged(request.vendor, request.intent)
        else:
            record_email_sent(False)
            record_sms_sent(False)
        
        response_time = time.time() - start_time
        logger.info(
            "Return workflow completed",
            vendor=request.vendor,
            order_id=request.order_id,
            status=result.status.value,
            response_time_ms=round(response_time * 1000, 2)
        )
        
        return ReturnWorkflowResponse(
            status=result.status.value,
            message=result.message,
            data=result.data,
            error=result.error,
            execution_time=result.execution_time
        )
    
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(
            "Return workflow failed",
            vendor=request.vendor,
            order_id=request.order_id,
            error=str(e),
            response_time_ms=round(response_time * 1000, 2)
        )
        
        return ReturnWorkflowResponse(
            status=WorkflowStatus.FAILED.value,
            message="Return workflow failed",
            error=str(e),
            execution_time=response_time
        )


@router.post("/policy", response_model=PolicyQueryResponse)
async def query_vendor_policy(
    request: PolicyQueryRequest,
    http_request: Request
) -> PolicyQueryResponse:
    """
    Query vendor policy information.
    
    Returns policy snippets for the specified vendor.
    Only returns existing policy information, no fabricated content.
    """
    start_time = time.time()
    
    # Log incoming request
    log_data = redact_sensitive_data(request.dict())
    logger.info(
        "Policy query request",
        method=http_request.method,
        path=http_request.url.path,
        **log_data
    )
    
    try:
        # Get vendor policy information
        policies = workflow_service.get_vendor_policy_info(
            vendor=request.vendor,
            policy_key=request.policy_key
        )
        
        response_time = time.time() - start_time
        logger.info(
            "Policy query completed",
            vendor=request.vendor,
            policy_key=request.policy_key,
            response_time_ms=round(response_time * 1000, 2)
        )
        
        return PolicyQueryResponse(
            vendor=request.vendor,
            policies=policies
        )
    
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(
            "Policy query failed",
            vendor=request.vendor,
            error=str(e),
            response_time_ms=round(response_time * 1000, 2)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query vendor policy"
        )


@router.get("/status")
async def get_workflow_status() -> dict:
    """
    Get workflow service status.
    
    Returns current status of the workflow service.
    """
    return {
        "status": "operational",
        "max_execution_time": workflow_service.max_execution_time,
        "max_retries": workflow_service.max_retries,
        "supported_vendors": [
            "amazon", "walmart", "target", "bestbuy", "generic"
        ]
    }
