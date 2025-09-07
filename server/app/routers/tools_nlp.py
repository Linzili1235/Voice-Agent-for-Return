# NLP 工具路由 - 处理自然语言处理和槽位提取相关的 API 端点
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
import time

from app.schemas import (
    SlotExtractionInput, SlotExtractionOutput, Slots
)
from app.services.llm_service import llm_client
from app.utils import (
    get_logger, redact_sensitive_data
)


logger = get_logger(__name__)
router = APIRouter(prefix="/tools", tags=["nlp_tools"])


@router.post("/llm_extract_slots", response_model=SlotExtractionOutput)
async def llm_extract_slots(
    request: SlotExtractionInput,
    http_request: Request
) -> SlotExtractionOutput:
    """
    Extract structured slots from speech transcript using LLM or rule-based fallback.
    
    This tool processes natural language speech transcripts and extracts structured
    information like vendor, order ID, intent, reason, etc. for RMA processing.
    """
    start_time = time.time()
    
    # Log incoming request with redacted sensitive data
    log_data = redact_sensitive_data(request.dict())
    logger.info(
        "LLM slot extraction request",
        method=http_request.method,
        path=http_request.url.path,
        **log_data
    )
    
    try:
        # Extract slots using LLM service
        result = llm_client.extract_slots(request)
        
        response_time = time.time() - start_time
        logger.info(
            "LLM slot extraction completed",
            ok=result.ok,
            language=result.language,
            missing_fields=result.missing_fields,
            response_time_ms=round(response_time * 1000, 2)
        )
        
        return result
    
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(
            "LLM slot extraction failed",
            error=str(e),
            response_time_ms=round(response_time * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/normalize_slots", response_model=Slots)
async def normalize_slots(
    request: Slots,
    http_request: Request
) -> Slots:
    """
    Normalize and clean extracted slots.
    
    This tool applies normalization rules to clean up extracted slot data:
    - Trim whitespace from all string fields
    - Convert order_id to uppercase
    - Map common reason synonyms to enum values
    - Apply vendor alias mapping
    """
    start_time = time.time()
    
    # Log incoming request with redacted sensitive data
    log_data = redact_sensitive_data(request.dict())
    logger.info(
        "Slot normalization request",
        method=http_request.method,
        path=http_request.url.path,
        **log_data
    )
    
    try:
        # Apply normalization rules
        normalized_slots = _normalize_slots_data(request)
        
        response_time = time.time() - start_time
        logger.info(
            "Slot normalization completed",
            vendor=normalized_slots.vendor,
            order_id=normalized_slots.order_id,
            intent=normalized_slots.intent,
            reason=normalized_slots.reason,
            response_time_ms=round(response_time * 1000, 2)
        )
        
        return normalized_slots
    
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(
            "Slot normalization failed",
            error=str(e),
            response_time_ms=round(response_time * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/llm_recap")
async def llm_recap(
    request: dict,
    http_request: Request
) -> dict:
    """
    Generate a recap line from normalized slots.
    
    This tool creates a natural language recap line that can be read back
    to the user to confirm the extracted information.
    """
    start_time = time.time()
    
    # Validate input structure
    try:
        slots_data = request.get("slots", {})
        slots = Slots(**slots_data)
        locale = request.get("locale")
        target_language = request.get("target_language")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input format: {str(e)}"
        )
    
    # Log incoming request with redacted sensitive data
    log_data = redact_sensitive_data(request)
    logger.info(
        "LLM recap generation request",
        method=http_request.method,
        path=http_request.url.path,
        **log_data
    )
    
    try:
        # Generate recap line
        recap_line = _generate_recap_line(slots, locale, target_language)
        
        response_time = time.time() - start_time
        logger.info(
            "LLM recap generation completed",
            recap_line=recap_line,
            response_time_ms=round(response_time * 1000, 2)
        )
        
        return {"recap_line": recap_line}
    
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(
            "LLM recap generation failed",
            error=str(e),
            response_time_ms=round(response_time * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


def _normalize_slots_data(slots: Slots) -> Slots:
    """Apply normalization rules to slots data."""
    
    # Vendor alias mapping
    vendor_aliases = {
        "acme": "AcmeHome",
        "amazon": "amazon",
        "walmart": "walmart", 
        "target": "target",
        "bestbuy": "bestbuy",
        "best buy": "bestbuy",
        "百思买": "bestbuy",
        "亚马逊": "amazon",
        "沃尔玛": "walmart",
        "塔吉特": "target"
    }
    
    # Reason synonym mapping
    reason_synonyms = {
        "broken": "damaged",
        "cracked": "damaged",
        "torn": "damaged",
        "defective": "damaged",
        "faulty": "damaged",
        "not working": "damaged",
        "doesn't work": "damaged",
        "malfunctioning": "damaged",
        "lost": "missing",
        "didn't receive": "missing",
        "never arrived": "missing",
        "not delivered": "missing",
        "incorrect": "wrong_item",
        "wrong product": "wrong_item",
        "different item": "wrong_item",
        "not what I ordered": "wrong_item",
        "not as advertised": "not_as_described",
        "different from description": "not_as_described",
        "doesn't match description": "not_as_described",
        "not what was described": "not_as_described",
        "other": "other",
        "misc": "other",
        "miscellaneous": "other"
    }
    
    # Normalize vendor
    normalized_vendor = None
    if slots.vendor:
        vendor_lower = slots.vendor.lower().strip()
        normalized_vendor = vendor_aliases.get(vendor_lower, slots.vendor.strip())
    
    # Normalize order_id
    normalized_order_id = None
    if slots.order_id:
        normalized_order_id = slots.order_id.strip().upper()
    
    # Normalize item_sku
    normalized_item_sku = None
    if slots.item_sku:
        normalized_item_sku = slots.item_sku.strip()
    
    # Normalize reason
    normalized_reason = slots.reason
    if slots.reason:
        reason_lower = slots.reason.lower().strip()
        normalized_reason = reason_synonyms.get(reason_lower, slots.reason)
    
    return Slots(
        vendor=normalized_vendor,
        order_id=normalized_order_id,
        item_sku=normalized_item_sku,
        intent=slots.intent,
        reason=normalized_reason,
        evidence_urls=slots.evidence_urls
    )


def _generate_recap_line(slots: Slots, locale: str = None, target_language: str = None) -> str:
    """Generate a recap line from normalized slots."""
    
    # Determine language
    language = target_language or locale or "en-US"
    is_chinese = language.startswith("zh")
    
    # Build recap components
    parts = []
    
    if slots.vendor:
        if is_chinese:
            parts.append(f"{slots.vendor}订单")
        else:
            parts.append(f"{slots.vendor} order")
    
    if slots.order_id:
        parts.append(slots.order_id)
    
    if slots.intent:
        intent_text = {
            "return": "退货" if is_chinese else "return",
            "refund": "退款" if is_chinese else "refund", 
            "replacement": "换货" if is_chinese else "replacement"
        }.get(slots.intent, slots.intent)
        parts.append(intent_text)
    
    if slots.reason:
        reason_text = {
            "damaged": "损坏" if is_chinese else "damaged",
            "missing": "缺失" if is_chinese else "missing",
            "wrong_item": "发错货" if is_chinese else "wrong item",
            "not_as_described": "与描述不符" if is_chinese else "not as described",
            "other": "其他原因" if is_chinese else "other reason"
        }.get(slots.reason, slots.reason)
        parts.append(f"由于{reason_text}" if is_chinese else f"due to {reason_text}")
    
    # Generate recap line
    if parts:
        if is_chinese:
            return f"我来帮您处理{' '.join(parts)}的申请。"
        else:
            return f"I'll help you with your {' '.join(parts)} request."
    else:
        if is_chinese:
            return "我来帮您处理退货申请。"
        else:
            return "I'll help you with your return request."
