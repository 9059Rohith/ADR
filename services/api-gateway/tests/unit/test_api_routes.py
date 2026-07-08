"""SentinelArena — Unit Tests for API Route Input Validation.

Tests that all Pydantic request models enforce constraints correctly,
ensuring robust input validation at the API boundary.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.routes.chat import ChatRequest
from app.routes.incidents import IncidentCreateRequest
from app.routes.decisions import DecisionRequest, DecisionAction
from app.routes.navigation import NavigationRequest


class TestChatRequestValidation:
    """Tests for ChatRequest input constraints."""

    def test_valid_request(self) -> None:
        """Test a valid chat request."""
        req = ChatRequest(message="Where is the nearest restroom?")
        assert req.message == "Where is the nearest restroom?"
        assert req.locale == "en"
        assert req.user_location_id == "lobby-main"

    def test_empty_message_rejected(self) -> None:
        """Test that empty messages are rejected."""
        with pytest.raises(ValidationError):
            ChatRequest(message="")

    def test_message_too_long_rejected(self) -> None:
        """Test that messages exceeding max length are rejected."""
        with pytest.raises(ValidationError):
            ChatRequest(message="x" * 2001)

    def test_invalid_locale_rejected(self) -> None:
        """Test that invalid locales are rejected."""
        with pytest.raises(ValidationError):
            ChatRequest(message="test", locale="fr")

    def test_valid_locales_accepted(self) -> None:
        """Test all supported locales."""
        for locale in ["en", "hi", "ta", "te", "es"]:
            req = ChatRequest(message="test", locale=locale)
            assert req.locale == locale


class TestIncidentRequestValidation:
    """Tests for IncidentCreateRequest input constraints."""

    def test_valid_incident(self) -> None:
        """Test a valid incident creation request."""
        req = IncidentCreateRequest(
            title="Suspicious package",
            description="Found an unattended bag near Gate 2, black color, no tags visible.",
            severity="high",
            zone_id="zone-b",
        )
        assert req.severity == "high"

    def test_title_too_short_rejected(self) -> None:
        """Test that short titles are rejected."""
        with pytest.raises(ValidationError):
            IncidentCreateRequest(
                title="ab",
                description="This is a valid description.",
            )

    def test_description_too_short_rejected(self) -> None:
        """Test that short descriptions are rejected."""
        with pytest.raises(ValidationError):
            IncidentCreateRequest(
                title="Valid title",
                description="Short",
            )

    def test_invalid_severity_rejected(self) -> None:
        """Test that invalid severity values are rejected."""
        with pytest.raises(ValidationError):
            IncidentCreateRequest(
                title="Valid title",
                description="This is a valid description.",
                severity="extreme",
            )

    def test_all_severities_accepted(self) -> None:
        """Test all valid severity values."""
        for sev in ["low", "medium", "high", "critical"]:
            req = IncidentCreateRequest(
                title="Test incident",
                description="This is a test incident description.",
                severity=sev,
            )
            assert req.severity == sev


class TestDecisionRequestValidation:
    """Tests for decision support request validation."""

    def test_valid_decision_request(self) -> None:
        """Test a valid decision support request."""
        req = DecisionRequest(query="What should we do about Zone C crowd?")
        assert req.locale == "en"

    def test_empty_query_rejected(self) -> None:
        """Test that empty queries are rejected."""
        with pytest.raises(ValidationError):
            DecisionRequest(query="")

    def test_decision_action_valid(self) -> None:
        """Test valid decision actions."""
        for action in ["approve", "reject", "edit"]:
            act = DecisionAction(action=action)
            assert act.action == action

    def test_invalid_action_rejected(self) -> None:
        """Test that invalid actions are rejected."""
        with pytest.raises(ValidationError):
            DecisionAction(action="delete")


class TestNavigationRequestValidation:
    """Tests for navigation query validation."""

    def test_valid_navigation_request(self) -> None:
        """Test a valid navigation request."""
        req = NavigationRequest(query="Navigate to the nearest restroom")
        assert req.from_location_id == "lobby-main"
        assert req.avoid_stairs is False
        assert req.wheelchair_accessible is False

    def test_accessibility_constraints(self) -> None:
        """Test accessibility constraint fields."""
        req = NavigationRequest(
            query="Accessible route to food court",
            wheelchair_accessible=True,
            avoid_stairs=True,
            avoid_congestion=True,
        )
        assert req.wheelchair_accessible is True
        assert req.avoid_stairs is True
        assert req.avoid_congestion is True

    def test_empty_query_rejected(self) -> None:
        """Test that empty navigation queries are rejected."""
        with pytest.raises(ValidationError):
            NavigationRequest(query="")
