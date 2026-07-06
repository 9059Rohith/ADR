"""SentinelArena — Unit Tests for Authentication."""

from __future__ import annotations

import pytest

from app.core.auth import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    hash_password,
    has_minimum_role,
    verify_access_token,
    verify_password,
)
from app.models import UserRole


class TestPasswordHashing:
    """Tests for Argon2id password hashing."""

    def test_hash_and_verify(self) -> None:
        """Test that hashed passwords can be verified."""
        password = "SecureP@ssw0rd123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_wrong_password(self) -> None:
        """Test that wrong passwords fail verification."""
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_hash_is_argon2id(self) -> None:
        """Test that the hash uses Argon2id."""
        hashed = hash_password("test")
        assert hashed.startswith("$argon2id$")

    def test_different_hashes_for_same_password(self) -> None:
        """Test that same password produces different hashes (salt)."""
        hash1 = hash_password("same_password")
        hash2 = hash_password("same_password")
        assert hash1 != hash2  # Different salts


class TestJWTTokens:
    """Tests for JWT token management."""

    def test_create_and_decode_access_token(self) -> None:
        """Test access token creation and decoding."""
        token = create_access_token("user-123", UserRole.FAN)
        payload = decode_token(token)
        assert payload.sub == "user-123"
        assert payload.role == UserRole.FAN
        assert payload.token_type == "access"

    def test_create_and_decode_refresh_token(self) -> None:
        """Test refresh token creation and decoding."""
        token = create_refresh_token("user-456", UserRole.ORGANIZER)
        payload = decode_token(token)
        assert payload.sub == "user-456"
        assert payload.role == UserRole.ORGANIZER
        assert payload.token_type == "refresh"

    def test_token_pair(self) -> None:
        """Test token pair generation."""
        pair = create_token_pair("user-789", UserRole.VOLUNTEER)
        assert pair.access_token != pair.refresh_token
        assert pair.token_type == "bearer"
        assert pair.expires_in > 0

    def test_verify_access_token(self) -> None:
        """Test access token verification."""
        token = create_access_token("user-123", UserRole.FAN)
        payload = verify_access_token(token)
        assert payload.sub == "user-123"

    def test_verify_refresh_as_access_fails(self) -> None:
        """Test that refresh tokens fail access token verification."""
        from jose import JWTError

        token = create_refresh_token("user-123", UserRole.FAN)
        with pytest.raises(JWTError):
            verify_access_token(token)

    def test_tokens_have_unique_jti(self) -> None:
        """Test that each token gets a unique ID (for revocation)."""
        token1 = create_access_token("user-123", UserRole.FAN)
        token2 = create_access_token("user-123", UserRole.FAN)
        payload1 = decode_token(token1)
        payload2 = decode_token(token2)
        assert payload1.jti != payload2.jti


class TestRBAC:
    """Tests for role-based access control."""

    def test_admin_has_all_roles(self) -> None:
        """Test that admin role satisfies all required roles."""
        assert has_minimum_role(UserRole.ADMIN, UserRole.FAN) is True
        assert has_minimum_role(UserRole.ADMIN, UserRole.VOLUNTEER) is True
        assert has_minimum_role(UserRole.ADMIN, UserRole.ORGANIZER) is True
        assert has_minimum_role(UserRole.ADMIN, UserRole.ADMIN) is True

    def test_fan_only_has_fan_role(self) -> None:
        """Test that fan role only satisfies fan requirement."""
        assert has_minimum_role(UserRole.FAN, UserRole.FAN) is True
        assert has_minimum_role(UserRole.FAN, UserRole.VOLUNTEER) is False
        assert has_minimum_role(UserRole.FAN, UserRole.ORGANIZER) is False
        assert has_minimum_role(UserRole.FAN, UserRole.ADMIN) is False

    def test_role_hierarchy(self) -> None:
        """Test the complete role hierarchy."""
        assert has_minimum_role(UserRole.ORGANIZER, UserRole.VOLUNTEER) is True
        assert has_minimum_role(UserRole.VOLUNTEER, UserRole.ORGANIZER) is False
