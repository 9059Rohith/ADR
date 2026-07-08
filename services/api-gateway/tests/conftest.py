"""SentinelArena — Pytest Configuration.

Provides fixtures used across all test modules:
- Event loop configuration for async tests
- Settings overrides for test environment
- Shared mock factories
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _mock_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Override settings with test values to prevent accidental production access."""
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DB_NAME", "sentinel_test")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-unit-tests-only")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-api-key")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DEBUG", "true")
