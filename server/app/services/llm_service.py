# LLM 服务模块 - 处理大语言模型调用和槽位提取功能
import json
import re
import os
from typing import Dict, List, Optional
import httpx

from app.config import settings
from app.schemas import SlotExtractionInput, SlotExtractionOutput, Slots
from app.utils import get_logger, redact_sensitive_data
from app.vendors import get_supported_vendors


logger = get_logger(__name__)


class LLMClient:
    """Client for LLM-based slot extraction."""
    
    def __init__(self):
        self.provider = settings.provider
        self.model = settings.model
        self.openai_api_key = settings.openai_api_key
        self.anthropic_api_key = settings.anthropic_api_key
        
        # Load system prompt from file
        self.system_prompt = self._load_system_prompt()
        
        # Keyword mappings for stub mode
        self.intent_keywords = {
            "return": ["return", "退货", "退回", "寄回"],
            "refund": ["refund", "退款", "退钱", "退费"],
            "replacement": ["replacement", "换货", "更换", "替换"]
        }
        
        self.reason_keywords = {
            "damaged": ["damaged", "broken", "损坏", "破损", "坏了"],
            "missing": ["missing", "lost", "缺失", "丢失", "没收到"],
            "wrong_item": ["wrong", "incorrect", "错误", "发错了", "不对"],
            "not_as_described": ["not as described", "different", "不符", "不一样", "描述不符"],
            "other": ["other", "其他", "别的原因", "其他原因"]
        }
        
        self.vendor_keywords = {
            "amazon": ["amazon", "亚马逊"],
            "walmart": ["walmart", "沃尔玛"],
            "target": ["target", "塔吉特"],
            "bestbuy": ["best buy", "bestbuy", "百思买"],
            "generic": ["generic", "其他", "别的"]
        }
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from file."""
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "slot_extract.md")
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error("Failed to load system prompt", error=str(e))
            return "Extract structured information from speech transcript. Return JSON only."
    
    def extract_slots(self, payload: SlotExtractionInput) -> SlotExtractionOutput:
        """
        Extract slots from speech transcript using LLM or rule-based fallback.
        
        Args:
            payload: Input containing transcript and optional locale/target_language
            
        Returns:
            SlotExtractionOutput with extracted slots and metadata
        """
        # Log incoming request with redacted sensitive data
        log_data = redact_sensitive_data(payload.dict())
        logger.info(
            "Slot extraction request",
            provider=self.provider,
            model=self.model,
            **log_data
        )
        
        try:
            if self.provider == "stub":
                return self._extract_slots_stub(payload)
            elif self.provider == "openai":
                return self._extract_slots_openai(payload)
            elif self.provider == "anthropic":
                return self._extract_slots_anthropic(payload)
            else:
                logger.error("Unknown LLM provider", provider=self.provider)
                return self._create_error_response("Unknown provider")
        
        except Exception as e:
            logger.error(
                "Slot extraction failed",
                provider=self.provider,
                error=str(e)
            )
            return self._create_error_response(str(e))
    
    def _extract_slots_stub(self, payload: SlotExtractionInput) -> SlotExtractionOutput:
        """Rule-based slot extraction fallback."""
        transcript = payload.transcript.lower()
        
        # Extract order ID using regex
        order_id_match = re.search(r'[A-Za-z0-9-]{4,}', payload.transcript)
        order_id = order_id_match.group(0) if order_id_match else None
        
        # Extract vendor from allowlist
        vendor = None
        for vendor_key, keywords in self.vendor_keywords.items():
            if any(keyword in transcript for keyword in keywords):
                vendor = vendor_key
                break
        
        # Extract intent from keywords
        intent = None
        for intent_key, keywords in self.intent_keywords.items():
            if any(keyword in transcript for keyword in keywords):
                intent = intent_key
                break
        
        # Extract reason from keywords
        reason = None
        for reason_key, keywords in self.reason_keywords.items():
            if any(keyword in transcript for keyword in keywords):
                reason = reason_key
                break
        
        # Extract SKU (look for patterns like B08N5WRWNW, SKU-123, etc.)
        sku_match = re.search(r'\b[A-Z0-9]{6,}\b', payload.transcript)
        item_sku = sku_match.group(0) if sku_match else None
        
        # Extract URLs
        url_pattern = r'https?://[^\s]+'
        evidence_urls = re.findall(url_pattern, payload.transcript)
        
        # Determine missing fields
        missing_fields = []
        if not vendor:
            missing_fields.append("vendor")
        if not order_id:
            missing_fields.append("order_id")
        if not item_sku:
            missing_fields.append("item_sku")
        if not intent:
            missing_fields.append("intent")
        if not reason:
            missing_fields.append("reason")
        
        # Generate clarify question
        clarify_question = None
        if missing_fields:
            if "order_id" in missing_fields:
                clarify_question = "What is your order number?"
            elif "vendor" in missing_fields:
                clarify_question = "Which store or website did you purchase from?"
            elif "intent" in missing_fields:
                clarify_question = "Do you want to return, refund, or replace the item?"
            elif "reason" in missing_fields:
                clarify_question = "What is the reason for your request?"
            elif "item_sku" in missing_fields:
                clarify_question = "What is the product SKU or name?"
        
        # Generate recap line
        recap_line = self._generate_recap_line(vendor, order_id, intent, reason, payload.locale)
        
        # Detect language
        language = self._detect_language(payload.transcript, payload.locale)
        
        slots = Slots(
            vendor=vendor,
            order_id=order_id,
            item_sku=item_sku,
            intent=intent,
            reason=reason,
            evidence_urls=evidence_urls
        )
        
        logger.info(
            "Stub slot extraction completed",
            vendor=vendor,
            order_id=order_id,
            intent=intent,
            reason=reason,
            missing_fields=missing_fields
        )
        
        return SlotExtractionOutput(
            ok=True,
            language=language,
            slots=slots,
            missing_fields=missing_fields,
            clarify_question=clarify_question,
            recap_line=recap_line,
            notes="Rule-based extraction using keyword matching"
        )
    
    def _extract_slots_openai(self, payload: SlotExtractionInput) -> SlotExtractionOutput:
        """Extract slots using OpenAI API."""
        if not self.openai_api_key:
            logger.error("OpenAI API key not configured")
            return self._create_error_response("OpenAI API key not configured")
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user", 
                "content": f"Transcript: {payload.transcript}\n\nPlease extract slots and return JSON matching the SlotExtractionOutput schema."
            }
        ]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0,
                        "max_tokens": 500
                    },
                    timeout=30.0
                )
                
                if response.is_success:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    return self._parse_llm_response(content)
                else:
                    logger.error(
                        "OpenAI API error",
                        status_code=response.status_code,
                        response=response.text
                    )
                    return self._create_error_response("OpenAI API error")
        
        except Exception as e:
            logger.error("OpenAI API request failed", error=str(e))
            return self._create_error_response(str(e))
    
    def _extract_slots_anthropic(self, payload: SlotExtractionInput) -> SlotExtractionOutput:
        """Extract slots using Anthropic API."""
        if not self.anthropic_api_key:
            logger.error("Anthropic API key not configured")
            return self._create_error_response("Anthropic API key not configured")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.anthropic_api_key,
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 500,
                        "temperature": 0,
                        "system": self.system_prompt,
                        "messages": [
                            {
                                "role": "user",
                                "content": f"Transcript: {payload.transcript}\n\nPlease extract slots and return JSON matching the SlotExtractionOutput schema."
                            }
                        ]
                    },
                    timeout=30.0
                )
                
                if response.is_success:
                    result = response.json()
                    content = result["content"][0]["text"]
                    return self._parse_llm_response(content)
                else:
                    logger.error(
                        "Anthropic API error",
                        status_code=response.status_code,
                        response=response.text
                    )
                    return self._create_error_response("Anthropic API error")
        
        except Exception as e:
            logger.error("Anthropic API request failed", error=str(e))
            return self._create_error_response(str(e))
    
    def _parse_llm_response(self, content: str) -> SlotExtractionOutput:
        """Parse LLM response and validate against schema."""
        try:
            # Extract JSON from response (handle cases where LLM adds extra text)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                logger.error("No JSON found in LLM response", content=content[:200])
                return self._create_error_response("No JSON found in response")
            
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # Validate against schema
            return SlotExtractionOutput(**data)
        
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM JSON response", error=str(e), content=content[:200])
            return self._create_error_response("Invalid JSON response")
        except Exception as e:
            logger.error("Failed to validate LLM response", error=str(e))
            return self._create_error_response("Response validation failed")
    
    def _generate_recap_line(self, vendor: Optional[str], order_id: Optional[str], 
                           intent: Optional[str], reason: Optional[str], locale: Optional[str]) -> Optional[str]:
        """Generate a recap line based on extracted information."""
        if not any([vendor, order_id, intent, reason]):
            return None
        
        # Simple recap generation
        parts = []
        if vendor:
            parts.append(f"{vendor} order")
        if order_id:
            parts.append(f"{order_id}")
        if intent:
            parts.append(f"{intent} request")
        if reason:
            parts.append(f"due to {reason}")
        
        if parts:
            return f"I'll help you with your {' '.join(parts)}."
        return None
    
    def _detect_language(self, transcript: str, locale: Optional[str]) -> Optional[str]:
        """Detect language from transcript or use provided locale."""
        if locale:
            return locale
        
        # Simple language detection based on character patterns
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', transcript))
        total_chars = len(transcript)
        
        if chinese_chars > total_chars * 0.3:
            return "zh-CN"
        else:
            return "en-US"
    
    def _create_error_response(self, error_msg: str) -> SlotExtractionOutput:
        """Create error response with missing_fields=["unknown"]."""
        return SlotExtractionOutput(
            ok=False,
            language=None,
            slots=Slots(),
            missing_fields=["unknown"],
            clarify_question=None,
            recap_line=None,
            notes=f"Error: {error_msg}"
        )


# Global LLM client instance
llm_client = LLMClient()
