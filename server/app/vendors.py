# 供应商配置模块 - 管理不同供应商的 RMA 处理配置和模板
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class VendorConfig:
    """Vendor configuration for RMA processing."""
    
    name: str
    support_email: str
    rma_email_template: str
    subject_template: str
    requires_evidence: bool = False
    max_evidence_urls: int = 5
    auto_approve_threshold: Optional[int] = None  # Order value threshold for auto-approval
    policy_snippets: Dict[str, str] = None  # Policy information snippets


# Vendor configurations
VENDOR_CONFIGS: Dict[str, VendorConfig] = {
    "amazon": VendorConfig(
        name="Amazon",
        support_email="returns@amazon.com",
        rma_email_template="""
Dear Amazon Customer Service,

I would like to request a {intent} for my recent order.

Order Details:
- Order ID: {order_id}
- Item SKU: {item_sku}
- Reason: {reason}

{evidence_section}

Please let me know the next steps for processing this request.

Best regards,
{contact_info}
        """.strip(),
        subject_template="RMA Request - Order {order_id} - {intent.title()}",
        requires_evidence=True,
        max_evidence_urls=3,
        policy_snippets={
            "return_window": "30天退货窗口",
            "refund_method": "原支付方式退款",
            "shipping": "免费退货标签",
            "condition": "商品需保持原包装"
        }
    ),
    
    "walmart": VendorConfig(
        name="Walmart",
        support_email="customer.service@walmart.com",
        rma_email_template="""
Dear Walmart Customer Service,

I am writing to request a {intent} for my recent purchase.

Purchase Information:
- Order Number: {order_id}
- Product SKU: {item_sku}
- Issue: {reason}

{evidence_section}

I would appreciate your assistance in resolving this matter.

Thank you,
{contact_info}
        """.strip(),
        subject_template="Return Request - Order {order_id}",
        requires_evidence=False,
        max_evidence_urls=5,
        policy_snippets={
            "return_window": "90天退货窗口",
            "refund_method": "原支付方式或礼品卡",
            "shipping": "店内免费退货",
            "condition": "商品需未使用"
        }
    ),
    
    "target": VendorConfig(
        name="Target",
        support_email="guest.service@target.com",
        rma_email_template="""
Dear Target Guest Services,

I need to request a {intent} for my recent order.

Order Information:
- Order ID: {order_id}
- Item: {item_sku}
- Reason for {intent}: {reason}

{evidence_section}

Please advise on the return process.

Sincerely,
{contact_info}
        """.strip(),
        subject_template="Guest Services - {intent.title()} Request - {order_id}",
        requires_evidence=True,
        max_evidence_urls=4,
        policy_snippets={
            "return_window": "90天退货窗口",
            "refund_method": "原支付方式退款",
            "shipping": "免费退货标签",
            "condition": "商品需保持原包装"
        }
    ),
    
    "bestbuy": VendorConfig(
        name="Best Buy",
        support_email="customer.service@bestbuy.com",
        rma_email_template="""
Dear Best Buy Customer Service,

I would like to initiate a {intent} for my recent purchase.

Purchase Details:
- Order ID: {order_id}
- Product SKU: {item_sku}
- Issue Description: {reason}

{evidence_section}

Please provide instructions for the return process.

Best regards,
{contact_info}
        """.strip(),
        subject_template="Customer Service - {intent.title()} - Order {order_id}",
        requires_evidence=True,
        max_evidence_urls=3,
        policy_snippets={
            "return_window": "15天退货窗口",
            "refund_method": "原支付方式退款",
            "shipping": "店内免费退货",
            "condition": "商品需保持原包装和配件"
        }
    ),
    
    "generic": VendorConfig(
        name="Generic Vendor",
        support_email="support@vendor.com",
        rma_email_template="""
Dear Customer Service,

I am requesting a {intent} for my recent order.

Order Information:
- Order ID: {order_id}
- Item SKU: {item_sku}
- Reason: {reason}

{evidence_section}

Please let me know how to proceed with this request.

Thank you,
{contact_info}
        """.strip(),
        subject_template="RMA Request - {order_id} - {intent.title()}",
        requires_evidence=False,
        max_evidence_urls=5,
        policy_snippets={
            "return_window": "30天退货窗口",
            "refund_method": "原支付方式退款",
            "shipping": "联系客服获取退货标签",
            "condition": "商品需保持原包装"
        }
    )
}


def get_vendor_config(vendor_name: str) -> VendorConfig:
    """
    Get vendor configuration by name.
    
    Args:
        vendor_name: Name of the vendor (case-insensitive)
        
    Returns:
        VendorConfig object for the vendor
        
    Raises:
        ValueError: If vendor is not found
    """
    vendor_key = vendor_name.lower().strip()
    
    # Try exact match first
    if vendor_key in VENDOR_CONFIGS:
        return VENDOR_CONFIGS[vendor_key]
    
    # Try partial matches
    for key, config in VENDOR_CONFIGS.items():
        if key in vendor_key or vendor_key in key:
            return config
    
    # Return generic config as fallback
    return VENDOR_CONFIGS["generic"]


def format_rma_email(
    vendor_config: VendorConfig,
    order_id: str,
    item_sku: str,
    intent: str,
    reason: str,
    evidence_urls: list,
    contact_email: Optional[str] = None
) -> tuple[str, str]:
    """
    Format RMA email content using vendor template.
    
    Args:
        vendor_config: Vendor configuration
        order_id: Order ID
        item_sku: Item SKU
        intent: Intent type (return/refund/replacement)
        reason: Reason for RMA
        evidence_urls: List of evidence URLs
        contact_email: Contact email address
        
    Returns:
        Tuple of (subject, body)
    """
    # Format evidence section
    evidence_section = ""
    if evidence_urls:
        evidence_section = "\nEvidence:\n"
        for i, url in enumerate(evidence_urls[:vendor_config.max_evidence_urls], 1):
            evidence_section += f"{i}. {url}\n"
    elif vendor_config.requires_evidence:
        evidence_section = "\nNote: Evidence will be provided upon request.\n"
    
    # Format contact info
    contact_info = contact_email if contact_email else "Customer"
    
    # Format email body
    body = vendor_config.rma_email_template.format(
        intent=intent,
        order_id=order_id,
        item_sku=item_sku,
        reason=reason.replace("_", " ").title(),
        evidence_section=evidence_section,
        contact_info=contact_info
    )
    
    # Format subject
    subject = vendor_config.subject_template.format(
        order_id=order_id,
        intent=intent
    )
    
    return subject, body


def get_supported_vendors() -> list[str]:
    """
    Get list of supported vendor names.
    
    Returns:
        List of supported vendor names
    """
    return list(VENDOR_CONFIGS.keys())


def get_vendor_policy(vendor_name: str, policy_key: str = None) -> Dict[str, str]:
    """
    Get vendor policy information.
    
    Args:
        vendor_name: Name of the vendor
        policy_key: Specific policy key to retrieve (optional)
        
    Returns:
        Dictionary with policy information
    """
    vendor_config = get_vendor_config(vendor_name)
    
    if not vendor_config.policy_snippets:
        return {}
    
    if policy_key:
        return {policy_key: vendor_config.policy_snippets.get(policy_key, "政策信息不可用")}
    
    return vendor_config.policy_snippets.copy()
