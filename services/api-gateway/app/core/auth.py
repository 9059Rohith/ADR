"""SentinelArena — Authentication & Authorization.

JWT-based authentication with:
- Short-lived access tokens (15 min default)
- Rotating refresh tokens (7 day default)
- Argon2id password hashing (OWASP recommended)
- Role-based access control (RBAC) middleware
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher, Type
from argon2.exceptions import VerificationError
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field

from app.config import get_settings
from app.models import UserRole

# Argon2id hasher with OWASP-recommended parameters
_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MB
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=Type.ID,  # Argon2id
)


# ============================================================
# Password Hashing
# ============================================================


def hash_password(password: str) -> str:
    """Hash a password using Argon2id.

    Args:
        password: Plain-text password.

    Returns:
        Argon2id hash string.
    """
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against an Argon2id hash.

    Args:
        password: Plain-text password to verify.
        hashed: Stored Argon2id hash.

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        return _hasher.verify(hashed, password)
    except VerificationError:
        return False


# ============================================================
# JWT Token Management
# ============================================================


class TokenPayload(BaseModel):
    """Decoded JWT token payload."""

    sub: str  # User ID
    role: UserRole
    token_type: str  # "access" or "refresh"
    exp: int
    iat: int
    jti: str  # Unique token ID for revocation


class TokenPair(BaseModel):
    """Access + refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until access token expires


def create_access_token(user_id: str, role: UserRole) -> str:
    """Create a short-lived JWT access token.

    Args:
        user_id: The user's unique identifier.
        role: The user's role for RBAC.

    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload = {
        "sub": user_id,
        "role": role.value,
        "token_type": "access",
        "exp": int(expires.timestamp()),
        "iat": int(now.timestamp()),
        "jti": secrets.token_urlsafe(16),
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str, role: UserRole) -> str:
    """Create a long-lived JWT refresh token.

    Args:
        user_id: The user's unique identifier.
        role: The user's role for RBAC.

    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    expires = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    payload = {
        "sub": user_id,
        "role": role.value,
        "token_type": "refresh",
        "exp": int(expires.timestamp()),
        "iat": int(now.timestamp()),
        "jti": secrets.token_urlsafe(16),
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_token_pair(user_id: str, role: UserRole) -> TokenPair:
    """Create both access and refresh tokens.

    Args:
        user_id: The user's unique identifier.
        role: The user's role for RBAC.

    Returns:
        TokenPair with both tokens.
    """
    settings = get_settings()
    return TokenPair(
        access_token=create_access_token(user_id, role),
        refresh_token=create_refresh_token(user_id, role),
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token.

    Args:
        token: Encoded JWT string.

    Returns:
        Decoded TokenPayload.

    Raises:
        JWTError: If the token is invalid, expired, or malformed.
    """
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    return TokenPayload(**payload)


def verify_access_token(token: str) -> TokenPayload:
    """Verify an access token specifically.

    Args:
        token: Encoded JWT string.

    Returns:
        Decoded TokenPayload.

    Raises:
        JWTError: If the token is invalid or not an access token.
    """
    payload = decode_token(token)
    if payload.token_type != "access":
        msg = "Not an access token"
        raise JWTError(msg)
    return payload


# ============================================================
# RBAC Helpers
# ============================================================


# Role hierarchy: admin > organizer > volunteer > fan
ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.FAN: 0,
    UserRole.VOLUNTEER: 1,
    UserRole.ORGANIZER: 2,
    UserRole.ADMIN: 3,
}


def has_minimum_role(user_role: UserRole, required_role: UserRole) -> bool:
    """Check if a user's role meets the minimum required role.

    Uses role hierarchy: admin > organizer > volunteer > fan.

    Args:
        user_role: The user's current role.
        required_role: The minimum required role for the action.

    Returns:
        True if the user's role is equal to or higher than required.
    """
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required_role, 0)


# ============================================================
# Pydantic Schemas for Auth Endpoints
# ============================================================


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.FAN
    locale: str = "en"


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class AuthResponse(BaseModel):
    """Authentication response with tokens."""

    user_id: str
    email: str
    display_name: str
    role: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
