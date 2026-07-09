"""SentinelArena — Authentication Routes.

Endpoints for user registration, login, and token refresh.
Uses Argon2id password hashing and JWT tokens with JTI claims
for stateless session management.

Security measures:
    - Argon2id with OWASP-recommended parameters (64 MB memory, 3 iterations)
    - Short-lived access tokens (15 min) + rotating refresh tokens (7 days)
    - Constant-time password comparison (via argon2-cffi)
    - Generic error messages to prevent user enumeration
    - Database availability check before auth operations

When database is not available, these routes will return HTTP 503
rather than exposing internal errors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status

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
from app.models import Locale, User

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase

logger = structlog.get_logger()
router = APIRouter()


def _check_db(request: Request) -> None:
    """Verify database availability before auth operations.

    Args:
        request: FastAPI request object with app state.

    Raises:
        HTTPException: 503 if MongoDB Atlas is not available.
    """
    if not getattr(request.app.state, "db_available", False):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available. Auth requires MongoDB Atlas.",
        )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncIOMotorDatabase[Any] = Depends(get_db),
) -> Any:
    """Register a new user account.

    Creates a new user with Argon2id-hashed password and returns
    a JWT token pair (access + refresh) for immediate authentication.

    Args:
        request: FastAPI request with app state.
        body: Registration data including email, password, display name, and role.
        db: MongoDB database instance (injected via FastAPI dependency).

    Returns:
        AuthResponse containing user info and JWT token pair.

    Raises:
        HTTPException: 409 if email already exists.
        HTTPException: 503 if database is unavailable.
    """
    _check_db(request)

    # Check for existing user in MongoDB (prevent duplicates)
    existing = await db.users.find_one({"email": body.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Validate and normalize locale
    locale_value = body.locale if body.locale in [e.value for e in Locale] else "en"

    # Create user document with Argon2id-hashed password
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        display_name=body.display_name,
        role=body.role,
        locale=Locale(locale_value),
    )

    await db.users.insert_one(user.model_dump())

    # Generate JWT token pair
    tokens = create_token_pair(user.id, user.role)

    logger.info(
        "User registered successfully",
        user_id=user.id,
        role=user.role.value,
        event="user_registered",
    )

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
    db: AsyncIOMotorDatabase[Any] = Depends(get_db),
) -> Any:
    """Authenticate user and return JWT tokens.

    Performs constant-time password verification using Argon2id.
    Returns generic error messages to prevent user enumeration attacks.

    Args:
        request: FastAPI request with app state.
        body: Login credentials (email + password).
        db: MongoDB database instance.

    Returns:
        AuthResponse with JWT token pair on successful authentication.

    Raises:
        HTTPException: 401 if credentials are invalid.
        HTTPException: 403 if account is deactivated.
        HTTPException: 503 if database is unavailable.
    """
    _check_db(request)

    # Lookup user by email (indexed query)
    user_doc = await db.users.find_one({"email": body.email})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user = User.model_validate(user_doc)

    # Constant-time password verification (Argon2id)
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Check account status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    tokens = create_token_pair(user.id, user.role)

    logger.info(
        "User authenticated successfully",
        user_id=user.id,
        role=user.role.value,
        event="user_login",
    )

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
    db: AsyncIOMotorDatabase[Any] = Depends(get_db),
) -> Any:
    """Refresh an expired access token using a valid refresh token.

    Validates the refresh token, verifies the user still exists and
    is active, then issues a new token pair. The old refresh token
    is implicitly invalidated by the new pair.

    Args:
        request: FastAPI request with app state.
        body: Refresh token to validate.
        db: MongoDB database instance.

    Returns:
        AuthResponse with a new JWT token pair.

    Raises:
        HTTPException: 401 if refresh token is invalid or user not found.
        HTTPException: 503 if database is unavailable.
    """
    _check_db(request)

    try:
        payload = decode_token(body.refresh_token)
        if payload.token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type — expected refresh token",
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from None

    # Verify user still exists and is active in MongoDB
    user_doc = await db.users.find_one({"id": payload.sub})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    user = User.model_validate(user_doc)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    tokens = create_token_pair(user.id, user.role)

    logger.info(
        "Token refreshed successfully",
        user_id=user.id,
        event="token_refresh",
    )

    return AuthResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role.value,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )
