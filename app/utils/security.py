# 安全工具模块 - 提供身份验证、授权和输入验证功能
import re
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.config.settings import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def generate_idempotency_key() -> str:
    """Generate a unique idempotency key."""
    return secrets.token_urlsafe(32)


def validate_idempotency_key(key: str) -> bool:
    """Validate idempotency key format."""
    if not key or len(key) < 1 or len(key) > 255:
        return False
    # Check for valid characters (alphanumeric, hyphens, underscores)
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', key))


def sanitize_input(data: Any) -> Any:
    """Sanitize input data to prevent injection attacks."""
    if isinstance(data, str):
        # Remove potentially dangerous characters
        return re.sub(r'[<>"\']', '', data)
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    return data


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format."""
    # Remove all non-digit characters
    digits_only = ''.join(filter(str.isdigit, phone))
    return len(digits_only) >= 10 and len(digits_only) <= 15


def create_hmac_signature(data: str, secret: str) -> str:
    """Create HMAC signature for data integrity."""
    return hmac.new(
        secret.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def verify_hmac_signature(data: str, signature: str, secret: str) -> bool:
    """Verify HMAC signature."""
    expected_signature = create_hmac_signature(data, secret)
    return hmac.compare_digest(signature, expected_signature)
