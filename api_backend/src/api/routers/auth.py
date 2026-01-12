from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    decode_token,
)
from src.api.db.session import get_db
from src.api.models.refresh_token import RefreshToken
from src.api.models.user import User, UserRole
from src.api.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _to_user_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        role=user.role.value if isinstance(user.role, UserRole) else str(user.role),
        created_at=user.created_at,
    )


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account. By default role is 'user'.",
    operation_id="auth_register",
)
def register_user(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> UserPublic:
    """Register a new user account."""
    if not payload.password or len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        id=uuid.uuid4(),
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=UserRole.user,
        created_at=_utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _to_user_public(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Verifies credentials and returns access + refresh tokens.",
    operation_id="auth_login",
)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    """Login and return access and refresh tokens."""
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token, expires_in = create_access_token(subject=str(user.id), role=user.role.value)
    refresh_token, refresh_expires_at = create_refresh_token(subject=str(user.id))

    db.add(
        RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=refresh_expires_at,
            created_at=_utcnow(),
        )
    )
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user=_to_user_public(user),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh tokens",
    description="Exchanges a valid refresh token for a new access token and a rotated refresh token.",
    operation_id="auth_refresh",
)
def refresh(payload: RefreshRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    """Refresh and rotate tokens."""
    # Check token exists in DB (revocation support)
    rt = db.execute(
        select(RefreshToken).where(RefreshToken.token == payload.refresh_token)
    ).scalar_one_or_none()
    if rt is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if rt.expires_at <= _utcnow():
        # Remove expired token proactively.
        db.delete(rt)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    try:
        token_payload = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    sub = token_payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    try:
        user_id = uuid.UUID(str(sub))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Rotate refresh token: delete old, create new
    db.delete(rt)

    access_token, expires_in = create_access_token(subject=str(user.id), role=user.role.value)
    new_refresh_token, new_refresh_expires_at = create_refresh_token(subject=str(user.id))
    db.add(
        RefreshToken(
            user_id=user.id,
            token=new_refresh_token,
            expires_at=new_refresh_expires_at,
            created_at=_utcnow(),
        )
    )
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=expires_in,
        user=_to_user_public(user),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
    description="Revokes a refresh token (if provided).",
    operation_id="auth_logout",
)
def logout(payload: LogoutRequest, db: Annotated[Session, Depends(get_db)]) -> None:
    """Logout by revoking a refresh token (optional)."""
    if payload.refresh_token:
        rt = db.execute(
            select(RefreshToken).where(RefreshToken.token == payload.refresh_token)
        ).scalar_one_or_none()
        if rt is not None:
            db.delete(rt)
            db.commit()
    return None
