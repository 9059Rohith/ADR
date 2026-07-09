"""SentinelArena — Custom Exception Hierarchy.

Provides domain-specific exceptions that map cleanly to HTTP status codes.
All exceptions are caught by FastAPI's exception handlers and serialized
into consistent, structured JSON error responses.

Exception hierarchy::

    SentinelError (base)
    ├── AuthenticationError       → 401
    ├── AuthorizationError        → 403
    ├── ResourceNotFoundError     → 404
    ├── ResourceConflictError     → 409
    ├── ValidationError           → 422
    ├── ServiceUnavailableError   → 503
    └── ExternalServiceError      → 502

Usage::

    from app.exceptions import ResourceNotFoundError

    raise ResourceNotFoundError("incident", incident_id)
"""

from __future__ import annotations

from typing import Any


class SentinelError(Exception):
    """Base exception for all SentinelArena domain errors.

    Attributes:
        message: Human-readable error description.
        error_code: Machine-readable error code for API consumers.
        status_code: HTTP status code to return.
        details: Optional additional context for debugging.
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "SENTINEL_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize the error for JSON API responses."""
        result: dict[str, Any] = {
            "error": self.error_code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


class AuthenticationError(SentinelError):
    """Raised when authentication fails (invalid credentials, expired token)."""

    def __init__(self, message: str = "Invalid credentials") -> None:
        super().__init__(
            message,
            error_code="AUTHENTICATION_FAILED",
            status_code=401,
        )


class AuthorizationError(SentinelError):
    """Raised when the user lacks permission for the requested action."""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(
            message,
            error_code="AUTHORIZATION_DENIED",
            status_code=403,
        )


class ResourceNotFoundError(SentinelError):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        super().__init__(
            f"{resource_type} not found: {resource_id}",
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class ResourceConflictError(SentinelError):
    """Raised when a resource creation conflicts with existing data."""

    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(
            message,
            error_code="RESOURCE_CONFLICT",
            status_code=409,
        )


class ValidationError(SentinelError):
    """Raised when input validation fails beyond Pydantic's built-in checks."""

    def __init__(self, message: str, *, field: str | None = None) -> None:
        details = {"field": field} if field else {}
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class ServiceUnavailableError(SentinelError):
    """Raised when a required service (e.g., MongoDB) is unavailable."""

    def __init__(self, service: str = "database") -> None:
        super().__init__(
            f"{service} service is currently unavailable",
            error_code="SERVICE_UNAVAILABLE",
            status_code=503,
            details={"service": service},
        )


class ExternalServiceError(SentinelError):
    """Raised when an external API call (e.g., Groq, Weather) fails."""

    def __init__(self, service: str, message: str = "External service error") -> None:
        super().__init__(
            message,
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={"service": service},
        )
