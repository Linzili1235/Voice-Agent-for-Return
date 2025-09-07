# 知识库服务模块 - 处理 RMA 相关的知识库查询和模板生成
from typing import Dict, Any, Optional
import json

from app.vendors import get_vendor_config, format_rma_email
from app.utils import get_logger


logger = get_logger(__name__)


class KBService:
    """Knowledge base service for RMA processing."""
    
    def __init__(self):
        # RMA reason mappings to human-readable descriptions
        self.reason_descriptions = {
            "damaged": "Item arrived damaged or broken",
            "missing": "Item was missing from the order",
            "wrong_item": "Received wrong item",
            "not_as_described": "Item does not match description",
            "other": "Other reason not listed"
        }
        
        # Intent descriptions
        self.intent_descriptions = {
            "return": "Return the item for a refund",
            "refund": "Request a refund without returning the item",
            "replacement": "Request a replacement item"
        }
    
    def get_reason_description(self, reason: str) -> str:
        """
        Get human-readable description for RMA reason.
        
        Args:
            reason: RMA reason code
            
        Returns:
            Human-readable description
        """
        return self.reason_descriptions.get(reason, reason)
    
    def get_intent_description(self, intent: str) -> str:
        """
        Get human-readable description for RMA intent.
        
        Args:
            intent: RMA intent code
            
        Returns:
            Human-readable description
        """
        return self.intent_descriptions.get(intent, intent)
    
    def generate_rma_email(
        self,
        vendor: str,
        order_id: str,
        item_sku: str,
        intent: str,
        reason: str,
        evidence_urls: list,
        contact_email: Optional[str] = None
    ) -> tuple[str, str, str]:
        """
        Generate RMA email content for a vendor.
        
        Args:
            vendor: Vendor name
            order_id: Order ID
            item_sku: Item SKU
            intent: Intent type (return/refund/replacement)
            reason: Reason for RMA
            evidence_urls: List of evidence URLs
            contact_email: Contact email address
            
        Returns:
            Tuple of (to_email, subject, body)
        """
        try:
            # Get vendor configuration
            vendor_config = get_vendor_config(vendor)
            
            # Format email content
            subject, body = format_rma_email(
                vendor_config=vendor_config,
                order_id=order_id,
                item_sku=item_sku,
                intent=intent,
                reason=reason,
                evidence_urls=evidence_urls,
                contact_email=contact_email
            )
            
            logger.info(
                "RMA email generated",
                vendor=vendor,
                order_id=order_id,
                intent=intent,
                reason=reason
            )
            
            return vendor_config.support_email, subject, body
        
        except Exception as e:
            logger.error(
                "Failed to generate RMA email",
                vendor=vendor,
                order_id=order_id,
                error=str(e)
            )
            raise
    
    def validate_rma_request(
        self,
        vendor: str,
        order_id: str,
        item_sku: str,
        intent: str,
        reason: str,
        evidence_urls: list
    ) -> tuple[bool, Optional[str]]:
        """
        Validate RMA request parameters.
        
        Args:
            vendor: Vendor name
            order_id: Order ID
            item_sku: Item SKU
            intent: Intent type
            reason: Reason for RMA
            evidence_urls: List of evidence URLs
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Get vendor configuration
            vendor_config = get_vendor_config(vendor)
            
            # Check evidence requirements
            if vendor_config.requires_evidence and not evidence_urls:
                return False, f"{vendor} requires evidence for RMA requests"
            
            # Check evidence URL limit
            if len(evidence_urls) > vendor_config.max_evidence_urls:
                return False, f"Too many evidence URLs. Maximum allowed: {vendor_config.max_evidence_urls}"
            
            # Validate evidence URLs format
            for url in evidence_urls:
                if not url.startswith(('http://', 'https://')):
                    return False, f"Invalid evidence URL format: {url}"
            
            return True, None
        
        except Exception as e:
            logger.error(
                "RMA validation error",
                vendor=vendor,
                order_id=order_id,
                error=str(e)
            )
            return False, f"Validation error: {str(e)}"
    
    def get_supported_vendors(self) -> list[str]:
        """
        Get list of supported vendors.
        
        Returns:
            List of supported vendor names
        """
        from app.vendors import get_supported_vendors
        return get_supported_vendors()
    
    def get_vendor_info(self, vendor: str) -> Dict[str, Any]:
        """
        Get vendor information.
        
        Args:
            vendor: Vendor name
            
        Returns:
            Dictionary with vendor information
        """
        try:
            vendor_config = get_vendor_config(vendor)
            return {
                "name": vendor_config.name,
                "support_email": vendor_config.support_email,
                "requires_evidence": vendor_config.requires_evidence,
                "max_evidence_urls": vendor_config.max_evidence_urls,
                "auto_approve_threshold": vendor_config.auto_approve_threshold
            }
        except Exception as e:
            logger.error("Failed to get vendor info", vendor=vendor, error=str(e))
            return {}


# Global knowledge base service instance
kb_service = KBService()
