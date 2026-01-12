from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from passlib.context import CryptContext

from src.api.core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """Hash a plaintext password using a secure one-way algorithm."""
    return _pwd_context.hash(password)


# PUBLIC_INTERFACE
def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored hash."""
    return _pwd_context.verify(plain_password, password_hash)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# PUBLIC_INTERFACE
def create_access_token(*, subject: str, role: str) -> tuple[str, int]:
    """
    Create an access JWT.

    Returns: (token, expires_in_seconds)
    """
    expires_in = settings.access_token_expires_minutes * 60
    exp = _utcnow() + timedelta(seconds=expires_in)
    payload: dict[str, Any] = {
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": int(_utcnow().timestamp()),
        "exp": int(exp.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_in


# PUBLIC_INTERFACE
def create_refresh_token(*, subject: str) -> tuple[str, datetime]:
    """
    Create a refresh JWT (stored server-side for revocation).

    Returns: (token, expires_at_datetime_utc)
    """
    expires_at = _utcnow() + timedelta(days=settings.refresh_token_expires_days)
    payload: dict[str, Any] = {
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "sub": subject,
        "type": "refresh",
        "iat": int(_utcnow().timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_at


# PUBLIC_INTERFACE
def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT; raises jwt exceptions on invalid tokens."""
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
    )


# PUBLIC_INTERFACE
def get_token_subject_and_role(token_payload: dict[str, Any]) -> tuple[str, Optional[str]]:
    """Extract subject and role from a token payload."""
    sub = str(token_payload.get("sub", ""))
    role = token_payload.get("role")
    return sub, role
