# Vapi 服务模块 - 处理与 Vapi API 的交互
import time
from typing import Dict, Any, Optional
import httpx
from fastapi import HTTPException, status

from app.config.settings import settings
from app.schemas.vapi import VapiCallRequest, VapiCallResponse, VapiCallStatus
from app.utils.logging import get_logger, log_external_api_call
from app.utils.security import validate_phone_number


logger = get_logger(__name__)


class VapiService:
    """Service for interacting with Vapi API."""
    
    def __init__(self):
        self.base_url = settings.vapi_base_url
        self.api_key = settings.vapi_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_call(self, request: VapiCallRequest) -> VapiCallResponse:
        """
        Create a new Vapi call.
        Validates input and makes idempotent API call to Vapi.
        """
        # Validate phone number
        if not validate_phone_number(request.phone_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number format"
            )
        
        # Prepare request payload
        payload = {
            "phoneNumber": request.phone_number,
            "assistantId": request.assistant_id,
            "customerId": request.customer_id,
            "metadata": request.metadata or {}
        }
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/call",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                response_time = time.time() - start_time
                
                # Log the API call
                log_external_api_call(
                    logger=logger,
                    service="vapi",
                    endpoint="/call",
                    method="POST",
                    status_code=response.status_code,
                    response_time=response_time,
                    error=None if response.is_success else response.text
                )
                
                if response.is_success:
                    data = response.json()
                    return VapiCallResponse(
                        call_id=data["id"],
                        status=data["status"],
                        phone_number=request.phone_number,  # Will be redacted in logging
                        assistant_id=request.assistant_id,
                        created_at=data["createdAt"],
                        estimated_duration=data.get("estimatedDuration")
                    )
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Vapi API error: {response.text}"
                    )
        
        except httpx.TimeoutException:
            response_time = time.time() - start_time
            log_external_api_call(
                logger=logger,
                service="vapi",
                endpoint="/call",
                method="POST",
                status_code=408,
                response_time=response_time,
                error="Request timeout"
            )
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Vapi API request timeout"
            )
        
        except Exception as e:
            response_time = time.time() - start_time
            log_external_api_call(
                logger=logger,
                service="vapi",
                endpoint="/call",
                method="POST",
                status_code=500,
                response_time=response_time,
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal error: {str(e)}"
            )
    
    async def get_call_status(self, call_id: str) -> VapiCallStatus:
        """Get the status of a Vapi call."""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/call/{call_id}",
                    headers=self.headers,
                    timeout=30.0
                )
                
                response_time = time.time() - start_time
                
                log_external_api_call(
                    logger=logger,
                    service="vapi",
                    endpoint=f"/call/{call_id}",
                    method="GET",
                    status_code=response.status_code,
                    response_time=response_time,
                    error=None if response.is_success else response.text
                )
                
                if response.is_success:
                    data = response.json()
                    return VapiCallStatus(
                        call_id=data["id"],
                        status=data["status"],
                        duration=data.get("duration"),
                        transcript=data.get("transcript"),
                        summary=data.get("summary"),
                        ended_at=data.get("endedAt"),
                        metadata=data.get("metadata")
                    )
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Vapi API error: {response.text}"
                    )
        
        except httpx.TimeoutException:
            response_time = time.time() - start_time
            log_external_api_call(
                logger=logger,
                service="vapi",
                endpoint=f"/call/{call_id}",
                method="GET",
                status_code=408,
                response_time=response_time,
                error="Request timeout"
            )
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Vapi API request timeout"
            )
        
        except Exception as e:
            response_time = time.time() - start_time
            log_external_api_call(
                logger=logger,
                service="vapi",
                endpoint=f"/call/{call_id}",
                method="GET",
                status_code=500,
                response_time=response_time,
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal error: {str(e)}"
            )
    
    async def handle_webhook(self, payload: Dict[str, Any]) -> bool:
        """Handle incoming Vapi webhook."""
        try:
            # Process webhook payload
            event_type = payload.get("eventType")
            call_id = payload.get("callId")
            
            logger.info(
                "Received Vapi webhook",
                event_type=event_type,
                call_id=call_id
            )
            
            # Here you would typically:
            # 1. Validate webhook signature
            # 2. Update call status in database
            # 3. Trigger any follow-up actions
            
            return True
        
        except Exception as e:
            logger.error("Failed to process Vapi webhook", error=str(e))
            return False


# Global service instance
vapi_service = VapiService()
