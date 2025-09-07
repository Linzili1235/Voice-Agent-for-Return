# SMS 服务模块 - 处理短信发送功能
import httpx
import uuid
from typing import Optional

from app.config import settings
from app.utils import get_logger


logger = get_logger(__name__)


class SMSService:
    """Service for sending SMS messages."""
    
    def __init__(self):
        self.sms_configured = settings.sms_configured
        self.api_key = settings.sms_api_key
        self.api_url = settings.sms_api_url
    
    async def send_sms(self, phone: str, text: str) -> tuple[bool, Optional[str]]:
        """
        Send SMS message.
        
        Args:
            phone: Phone number
            text: SMS text content
            
        Returns:
            Tuple of (success, message_id)
        """
        if not self.sms_configured:
            logger.warning("SMS not configured, stubbing SMS send", phone=phone)
            return True, f"sms-stub-{uuid.uuid4().hex[:8]}"
        
        try:
            # Prepare request payload
            payload = {
                "to": phone,
                "message": text,
                "api_key": self.api_key
            }
            
            # Send SMS via HTTP API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    timeout=30.0
                )
                
                if response.is_success:
                    # Generate message ID from response or create one
                    message_id = f"sms-{uuid.uuid4().hex[:8]}"
                    
                    logger.info(
                        "SMS sent successfully",
                        phone=phone,
                        message_id=message_id
                    )
                    
                    return True, message_id
                else:
                    logger.error(
                        "SMS API error",
                        phone=phone,
                        status_code=response.status_code,
                        response=response.text
                    )
                    return False, None
        
        except Exception as e:
            logger.error(
                "Failed to send SMS",
                phone=phone,
                error=str(e)
            )
            return False, None
    
    def is_configured(self) -> bool:
        """Check if SMS service is properly configured."""
        return self.sms_configured


# Global SMS service instance
sms_service = SMSService()

