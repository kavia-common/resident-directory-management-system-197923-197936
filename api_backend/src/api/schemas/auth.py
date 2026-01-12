from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserPublic(BaseModel):
    """Public user fields returned to clients."""

    id: UUID = Field(..., description="User id (UUID).")
    email: EmailStr = Field(..., description="User email.")
    role: Literal["admin", "user"] = Field(..., description="User role.")
    created_at: datetime = Field(..., description="Account creation timestamp.")


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email (unique).")
    password: str = Field(..., min_length=8, max_length=128, description="User password (min 8 chars).")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email.")
    password: str = Field(..., description="User password.")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token.")
    refresh_token: str = Field(..., description="Refresh token (stored server-side for revocation).")
    token_type: str = Field("bearer", description="Token type.")
    expires_in: int = Field(..., description="Access token expiration in seconds.")
    user: UserPublic = Field(..., description="Current user.")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token previously issued by /auth/login or /auth/refresh.")


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = Field(None, description="Refresh token to revoke (optional).")
