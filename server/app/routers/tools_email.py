# 邮件工具路由 - 处理 RMA 邮件生成和发送相关的 API 端点
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
import time

from app.schemas import (
    MakeRMAEmailRequest, MakeRMAEmailResponse,
    SendEmailRequest, SendEmailResponse
)
from app.services.kb_service import kb_service
from app.services.email_service import email_service
from app.utils import (
    get_logger, redact_sensitive_data, validate_idempotency_key,
    cache_manager
)


logger = get_logger(__name__)
router = APIRouter(prefix="/tools", tags=["email_tools"])


@router.post("/make_rma_email", response_model=MakeRMAEmailResponse)
async def make_rma_email(
    request: MakeRMAEmailRequest,
    http_request: Request
) -> MakeRMAEmailResponse:
    """
    Generate RMA email content for a vendor.
    
    This tool creates a properly formatted email for RMA requests
    based on the vendor's specific requirements and templates.
    """
    start_time = time.time()
    
    # Log incoming request with redacted sensitive data
    log_data = redact_sensitive_data(request.dict())
    logger.info(
        "RMA email generation request",
        method=http_request.method,
        path=http_request.url.path,
        **log_data
    )
    
    try:
        # Validate RMA request
        is_valid, error_msg = kb_service.validate_rma_request(
            vendor=request.vendor,
            order_id=request.order_id,
            item_sku=request.item_sku,
            intent=request.intent,
            reason=request.reason,
            evidence_urls=request.evidence_urls
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Generate RMA email
        to_email, subject, body = kb_service.generate_rma_email(
            vendor=request.vendor,
            order_id=request.order_id,
            item_sku=request.item_sku,
            intent=request.intent,
            reason=request.reason,
            evidence_urls=request.evidence_urls,
            contact_email=request.contact_email
        )
        
        response_time = time.time() - start_time
        logger.info(
            "RMA email generated successfully",
            vendor=request.vendor,
            order_id=request.order_id,
            response_time_ms=round(response_time * 1000, 2)
        )
        
        return MakeRMAEmailResponse(
            to_email=to_email,
            subject=subject,
            body=body
        )
    
    except HTTPException:
        raise
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(
            "Failed to generate RMA email",
            vendor=request.vendor,
            order_id=request.order_id,
            error=str(e),
            response_time_ms=round(response_time * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/send_email", response_model=SendEmailResponse)
async def send_email(
    request: SendEmailRequest,
    http_request: Request
) -> SendEmailResponse:
    """
    Send email via SMTP.
    
    This tool sends emails with idempotency support to prevent
    duplicate sends for the same request.
    """
    start_time = time.time()
    
    # Log incoming request with redacted sensitive data
    log_data = redact_sensitive_data(request.dict())
    logger.info(
        "Email send request",
        method=http_request.method,
        path=http_request.url.path,
        **log_data
    )
    
    try:
        # Handle idempotency if key is provided
        if request.idempotency_key:
            if not validate_idempotency_key(request.idempotency_key):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid idempotency key format"
                )
            
            # Check for existing request
            cached_response = await cache_manager.check_idempotency(request.idempotency_key)
            if cached_response:
                logger.info(
                    "Returning cached email response",
                    idempotency_key=request.idempotency_key
                )
                return SendEmailResponse(**cached_response)
        
        # Send email
        success, msg_id = await email_service.send_email(
            to=request.to,
            subject=request.subject,
            body=request.body
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email"
            )
        
        response = SendEmailResponse(ok=True, msg_id=msg_id)
        
        # Store response in cache for idempotency
        if request.idempotency_key:
            await cache_manager.store_idempotency(
                request.idempotency_key,
                response.dict()
            )
        
        response_time = time.time() - start_time
        logger.info(
            "Email sent successfully",
            to=request.to,
            msg_id=msg_id,
            response_time_ms=round(response_time * 1000, 2)
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(
            "Failed to send email",
            to=request.to,
            error=str(e),
            response_time_ms=round(response_time * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

