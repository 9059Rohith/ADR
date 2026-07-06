"""SentinelArena — Authentication Routes.

Endpoints for user registration, login, and token refresh.
Uses Argon2id password hashing and JWT tokens.

When database is not available, these routes will return appropriate
error messages rather than crashing.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    create_token_pair,
    decode_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models import Locale, User, UserRole

logger = structlog.get_logger()
router = APIRouter()


def _check_db(request: Request) -> None:
    """Check if database is available."""
    if not getattr(request.app.state, "db_available", False):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available. Auth requires PostgreSQL.",
        )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Register a new user account.

    Args:
        body: Registration data (email, password, display name, role).
        db: Database session.

    Returns:
        AuthResponse with JWT tokens.

    Raises:
        HTTPException: 409 if email already exists, 503 if DB unavailable.
    """
    _check_db(request)

    # Check for existing user
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user with Argon2id hashed password
    locale_value = body.locale if body.locale in [e.value for e in Locale] else "en"
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        display_name=body.display_name,
        role=body.role,
        locale=Locale(locale_value),
    )
    db.add(user)
    await db.flush()

    # Generate tokens
    tokens = create_token_pair(user.id, user.role)

    logger.info("User registered", user_id=user.id, role=user.role.value)

    return AuthResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role.value,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Authenticate user and return JWT tokens."""
    _check_db(request)

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    tokens = create_token_pair(user.id, user.role)

    logger.info("User logged in", user_id=user.id, role=user.role.value)

    return AuthResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role.value,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: Request,
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Refresh an expired access token using a valid refresh token."""
    _check_db(request)

    try:
        payload = decode_token(body.refresh_token)
        if payload.token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.id == payload.sub))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    tokens = create_token_pair(user.id, user.role)

    return AuthResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role.value,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )
