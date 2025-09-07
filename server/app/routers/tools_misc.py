# 其他工具路由 - 处理日志记录和短信发送相关的 API 端点
from fastapi import APIRouter, HTTPException, status, Request
import time

from app.schemas import (
    LogSubmissionRequest, LogSubmissionResponse,
    SendSMSRequest, SendSMSResponse
)
from app.services.sms_service import sms_service
from app.utils import get_logger, redact_sensitive_data


logger = get_logger(__name__)
router = APIRouter(prefix="/tools", tags=["misc_tools"])


@router.post("/log_submission", response_model=LogSubmissionResponse)
async def log_submission(
    request: LogSubmissionRequest,
    http_request: Request
) -> LogSubmissionResponse:
    """
    Log RMA submission for tracking and analytics.
    
    This tool logs RMA submissions with masked order IDs for privacy.
    """
    start_time = time.time()
    
    # Log incoming request with redacted sensitive data
    log_data = redact_sensitive_data(request.dict())
    logger.info(
        "RMA submission log request",
        method=http_request.method,
        path=http_request.url.path,
        **log_data
    )
    
    try:
        # Log the submission with structured data
        submission_data = {
            "vendor": request.vendor,
            "order_id_last4": request.order_id_last4,
            "intent": request.intent,
            "reason": request.reason,
            "msg_id": request.msg_id,
            "timestamp": time.time()
        }
        
        logger.info(
            "RMA submission logged",
            vendor=request.vendor,
            order_id_last4=request.order_id_last4,
            intent=request.intent,
            reason=request.reason,
            msg_id=request.msg_id
        )
        
        # Here you could also store in a database or send to analytics service
        # For now, we just log it
        
        response_time = time.time() - start_time
        logger.info(
            "Submission logging completed",
            response_time_ms=round(response_time * 1000, 2)
        )
        
        return LogSubmissionResponse(ok=True)
    
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(
            "Failed to log submission",
            vendor=request.vendor,
            order_id_last4=request.order_id_last4,
            error=str(e),
            response_time_ms=round(response_time * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/send_sms", response_model=SendSMSResponse)
async def send_sms(
    request: SendSMSRequest,
    http_request: Request
) -> SendSMSResponse:
    """
    Send SMS message.
    
    This tool sends SMS messages via configured SMS service.
    """
    start_time = time.time()
    
    # Log incoming request with redacted sensitive data
    log_data = redact_sensitive_data(request.dict())
    logger.info(
        "SMS send request",
        method=http_request.method,
        path=http_request.url.path,
        **log_data
    )
    
    try:
        # Send SMS
        success, msg_id = await sms_service.send_sms(
            phone=request.phone,
            text=request.text
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send SMS"
            )
        
        response_time = time.time() - start_time
        logger.info(
            "SMS sent successfully",
            phone=request.phone,
            msg_id=msg_id,
            response_time_ms=round(response_time * 1000, 2)
        )
        
        return SendSMSResponse(ok=True)
    
    except HTTPException:
        raise
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(
            "Failed to send SMS",
            phone=request.phone,
            error=str(e),
            response_time_ms=round(response_time * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
