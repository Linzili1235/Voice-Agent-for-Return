# 退货流程服务模块 - 处理完整的退货/退款流程
import json
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.schemas import (
    MakeRMAEmailRequest, MakeRMAEmailResponse,
    SendEmailRequest, SendEmailResponse,
    LogSubmissionRequest, LogSubmissionResponse,
    SendSMSRequest, SendSMSResponse
)
from app.services.kb_service import kb_service
from app.services.email_service import email_service
from app.services.sms_service import sms_service
from app.vendors import get_vendor_policy
from app.utils import get_logger, generate_idempotency_key


logger = get_logger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    status: WorkflowStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0


class ReturnWorkflowService:
    """Service for handling return/refund workflow."""
    
    def __init__(self):
        self.max_execution_time = 120  # 2 minutes in seconds
        self.max_retries = 2
        self.workflow_timeout = 120  # 2 minutes timeout
    
    async def execute_return_workflow(
        self,
        vendor: str,
        order_id: str,
        item_sku: str,
        intent: str,
        reason: str,
        evidence_urls: list,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None
    ) -> WorkflowResult:
        """
        Execute complete return/refund workflow.
        
        Args:
            vendor: Vendor name
            order_id: Order ID
            item_sku: Item SKU
            intent: Intent type (return/refund/replacement)
            reason: Reason for RMA
            evidence_urls: List of evidence URLs
            contact_email: Contact email address
            contact_phone: Contact phone number
            
        Returns:
            WorkflowResult with execution status and data
        """
        start_time = time.time()
        
        logger.info(
            "Starting return workflow",
            vendor=vendor,
            order_id=order_id,
            intent=intent,
            reason=reason
        )
        
        try:
            # Step 1: Generate RMA email
            email_result = await self._generate_rma_email(
                vendor=vendor,
                order_id=order_id,
                item_sku=item_sku,
                intent=intent,
                reason=reason,
                evidence_urls=evidence_urls,
                contact_email=contact_email
            )
            
            if not email_result["success"]:
                return WorkflowResult(
                    status=WorkflowStatus.FAILED,
                    message="Failed to generate RMA email",
                    error=email_result["error"],
                    execution_time=time.time() - start_time
                )
            
            # Step 2: Send email
            send_result = await self._send_email(
                to_email=email_result["to_email"],
                subject=email_result["subject"],
                body=email_result["body"]
            )
            
            if not send_result["success"]:
                # Try fallback SMS if email fails
                if contact_phone:
                    sms_result = await self._send_fallback_sms(
                        phone=contact_phone,
                        order_id=order_id,
                        vendor=vendor
                    )
                    if sms_result["success"]:
                        return WorkflowResult(
                            status=WorkflowStatus.COMPLETED,
                            message="Email failed, sent fallback SMS",
                            data={
                                "email_sent": False,
                                "sms_sent": True,
                                "msg_id": sms_result["msg_id"]
                            },
                            execution_time=time.time() - start_time
                        )
                
                return WorkflowResult(
                    status=WorkflowStatus.FAILED,
                    message="Failed to send email and SMS",
                    error=send_result["error"],
                    execution_time=time.time() - start_time
                )
            
            # Step 3: Log submission
            log_result = await self._log_submission(
                vendor=vendor,
                order_id=order_id,
                intent=intent,
                reason=reason,
                msg_id=send_result["msg_id"]
            )
            
            if not log_result["success"]:
                logger.warning(
                    "Failed to log submission",
                    vendor=vendor,
                    order_id=order_id,
                    error=log_result["error"]
                )
            
            # Step 4: Send confirmation SMS
            confirmation_result = await self._send_confirmation_sms(
                phone=contact_phone,
                msg_id=send_result["msg_id"]
            )
            
            if not confirmation_result["success"]:
                logger.warning(
                    "Failed to send confirmation SMS",
                    phone=contact_phone,
                    error=confirmation_result["error"]
                )
            
            execution_time = time.time() - start_time
            
            logger.info(
                "Return workflow completed successfully",
                vendor=vendor,
                order_id=order_id,
                execution_time=execution_time
            )
            
            return WorkflowResult(
                status=WorkflowStatus.COMPLETED,
                message="Return workflow completed successfully",
                data={
                    "email_sent": True,
                    "sms_sent": confirmation_result["success"],
                    "logged": log_result["success"],
                    "msg_id": send_result["msg_id"],
                    "to_email": email_result["to_email"],
                    "subject": email_result["subject"]
                },
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "Return workflow failed",
                vendor=vendor,
                order_id=order_id,
                error=str(e),
                execution_time=execution_time
            )
            
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                message="Return workflow failed",
                error=str(e),
                execution_time=execution_time
            )
    
    async def _generate_rma_email(
        self,
        vendor: str,
        order_id: str,
        item_sku: str,
        intent: str,
        reason: str,
        evidence_urls: list,
        contact_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate RMA email content."""
        try:
            # Validate RMA request
            is_valid, error_msg = kb_service.validate_rma_request(
                vendor=vendor,
                order_id=order_id,
                item_sku=item_sku,
                intent=intent,
                reason=reason,
                evidence_urls=evidence_urls
            )
            
            if not is_valid:
                return {"success": False, "error": error_msg}
            
            # Generate RMA email
            to_email, subject, body = kb_service.generate_rma_email(
                vendor=vendor,
                order_id=order_id,
                item_sku=item_sku,
                intent=intent,
                reason=reason,
                evidence_urls=evidence_urls,
                contact_email=contact_email
            )
            
            return {
                "success": True,
                "to_email": to_email,
                "subject": subject,
                "body": body
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """Send email with retry logic."""
        idempotency_key = generate_idempotency_key()
        
        for attempt in range(self.max_retries):
            try:
                success, msg_id = await email_service.send_email(
                    to=to_email,
                    subject=subject,
                    body=body
                )
                
                if success:
                    return {"success": True, "msg_id": msg_id}
                
                if attempt < self.max_retries - 1:
                    logger.warning(
                        "Email send attempt failed, retrying",
                        attempt=attempt + 1,
                        to_email=to_email
                    )
                    time.sleep(1)  # Wait 1 second before retry
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(
                        "Email send exception, retrying",
                        attempt=attempt + 1,
                        error=str(e)
                    )
                    time.sleep(1)
                else:
                    return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Max retries exceeded"}
    
    async def _log_submission(
        self,
        vendor: str,
        order_id: str,
        intent: str,
        reason: str,
        msg_id: str
    ) -> Dict[str, Any]:
        """Log RMA submission."""
        try:
            # Extract last 4 digits of order ID for logging
            order_id_last4 = order_id[-4:] if len(order_id) >= 4 else order_id
            
            logger.info(
                "RMA submission logged",
                vendor=vendor,
                order_id_last4=order_id_last4,
                intent=intent,
                reason=reason,
                msg_id=msg_id
            )
            
            return {"success": True}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _send_confirmation_sms(
        self,
        phone: Optional[str],
        msg_id: str
    ) -> Dict[str, Any]:
        """Send confirmation SMS to customer."""
        if not phone:
            return {"success": False, "error": "No phone number provided"}
        
        try:
            text = f"您的退货申请已提交，参考号：{msg_id}。我们会在1-2个工作日内处理您的申请。"
            
            success, sms_msg_id = await sms_service.send_sms(
                phone=phone,
                text=text
            )
            
            if success:
                return {"success": True, "msg_id": sms_msg_id}
            else:
                return {"success": False, "error": "SMS send failed"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _send_fallback_sms(
        self,
        phone: str,
        order_id: str,
        vendor: str
    ) -> Dict[str, Any]:
        """Send fallback SMS when email fails."""
        try:
            text = f"您的{vendor}订单{order_id[-4:]}退货申请已提交。由于系统问题，我们将通过其他方式处理您的申请。"
            
            success, msg_id = await sms_service.send_sms(
                phone=phone,
                text=text
            )
            
            if success:
                return {"success": True, "msg_id": msg_id}
            else:
                return {"success": False, "error": "Fallback SMS failed"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_vendor_policy_info(self, vendor: str, policy_key: str = None) -> Dict[str, str]:
        """Get vendor policy information."""
        try:
            return get_vendor_policy(vendor, policy_key)
        except Exception as e:
            logger.error("Failed to get vendor policy", vendor=vendor, error=str(e))
            return {}


# Global workflow service instance
workflow_service = ReturnWorkflowService()

