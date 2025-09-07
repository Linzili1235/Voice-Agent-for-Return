# Vapi API 路由 - 处理语音通话相关的 API 端点
import time
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse

from app.schemas.base import BaseResponse, ErrorResponse
from app.schemas.vapi import VapiCallRequest, VapiCallResponse, VapiCallStatus, VapiWebhookPayload
from app.services.vapi_service import vapi_service
from app.utils.cache import cache_manager
from app.utils.logging import get_logger, log_request, log_response
from app.utils.security import validate_idempotency_key
from app.routers.metrics import record_request, record_vapi_call


logger = get_logger(__name__)
router = APIRouter(prefix="/vapi", tags=["vapi"])


async def validate_idempotency(request: VapiCallRequest) -> None:
    """Validate idempotency key and check for existing request."""
    if not validate_idempotency_key(request.idempotency_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid idempotency key format"
        )
    
    # Check for existing request
    cached_response = await cache_manager.check_idempotency(request.idempotency_key)
    if cached_response:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Request with this idempotency key already exists",
            headers={"X-Cached-Response": "true"}
        )


@router.post("/calls", response_model=BaseResponse[VapiCallResponse])
async def create_call(
    request: VapiCallRequest,
    http_request: Request
) -> BaseResponse[VapiCallResponse]:
    """
    Create a new Vapi call.
    Idempotent operation - duplicate requests with same idempotency key are ignored.
    """
    start_time = time.time()
    
    # Log incoming request
    log_request(
        logger=logger,
        method=http_request.method,
        path=http_request.url.path,
        params=request.dict(),
        user_id=None  # Add user authentication here
    )
    
    try:
        # Validate idempotency
        await validate_idempotency(request)
        
        # Create the call
        call_response = await vapi_service.create_call(request)
        
        # Store response in cache for idempotency
        await cache_manager.store_idempotency(
            request.idempotency_key,
            call_response.dict()
        )
        
        # Record metrics
        record_vapi_call("success")
        
        response_time = time.time() - start_time
        log_response(logger, 200, response_time)
        record_request(http_request.method, http_request.url.path, 200, response_time)
        
        return BaseResponse(
            success=True,
            message="Call created successfully",
            data=call_response
        )
    
    except HTTPException as e:
        response_time = time.time() - start_time
        log_response(logger, e.status_code, response_time, str(e.detail))
        record_request(http_request.method, http_request.url.path, e.status_code, response_time)
        record_vapi_call("error")
        raise e
    
    except Exception as e:
        response_time = time.time() - start_time
        log_response(logger, 500, response_time, str(e))
        record_request(http_request.method, http_request.url.path, 500, response_time)
        record_vapi_call("error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/calls/{call_id}", response_model=BaseResponse[VapiCallStatus])
async def get_call_status(
    call_id: str,
    http_request: Request
) -> BaseResponse[VapiCallStatus]:
    """Get the status of a Vapi call."""
    start_time = time.time()
    
    log_request(
        logger=logger,
        method=http_request.method,
        path=http_request.url.path,
        params={"call_id": call_id}
    )
    
    try:
        call_status = await vapi_service.get_call_status(call_id)
        
        response_time = time.time() - start_time
        log_response(logger, 200, response_time)
        record_request(http_request.method, http_request.url.path, 200, response_time)
        
        return BaseResponse(
            success=True,
            message="Call status retrieved successfully",
            data=call_status
        )
    
    except HTTPException as e:
        response_time = time.time() - start_time
        log_response(logger, e.status_code, response_time, str(e.detail))
        record_request(http_request.method, http_request.url.path, e.status_code, response_time)
        raise e
    
    except Exception as e:
        response_time = time.time() - start_time
        log_response(logger, 500, response_time, str(e))
        record_request(http_request.method, http_request.url.path, 500, response_time)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/webhooks")
async def handle_webhook(
    payload: VapiWebhookPayload,
    http_request: Request
) -> JSONResponse:
    """Handle incoming Vapi webhooks."""
    start_time = time.time()
    
    log_request(
        logger=logger,
        method=http_request.method,
        path=http_request.url.path,
        params=payload.dict()
    )
    
    try:
        success = await vapi_service.handle_webhook(payload.dict())
        
        response_time = time.time() - start_time
        log_response(logger, 200, response_time)
        record_request(http_request.method, http_request.url.path, 200, response_time)
        
        return JSONResponse(
            status_code=200,
            content={"success": success, "message": "Webhook processed"}
        )
    
    except Exception as e:
        response_time = time.time() - start_time
        log_response(logger, 500, response_time, str(e))
        record_request(http_request.method, http_request.url.path, 500, response_time)
        
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Webhook processing failed"}
        )
