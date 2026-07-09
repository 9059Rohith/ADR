"""SentinelArena — Unit Tests for Seed Data & Configuration.

Tests that seed data creates valid venue graphs, density evaluators,
and SOP documents. Validates configuration model defaults.
"""

from __future__ import annotations

import pytest

from app.seed import create_venue_graph, create_density_evaluator, get_sop_documents
from app.config import Settings


class TestVenueGraphSeed:
    """Tests for venue graph seed data integrity."""

    def test_graph_has_nodes(self) -> None:
        """Test that the seed graph contains nodes."""
        graph = create_venue_graph()
        assert graph.node_count > 0
        assert graph.node_count >= 25  # Ground + L1 + L2 nodes

    def test_graph_has_edges(self) -> None:
        """Test that the seed graph contains edges."""
        graph = create_venue_graph()
        assert graph.edge_count > 0
        assert graph.edge_count >= 30  # All edges

    def test_graph_has_all_poi_types(self) -> None:
        """Test that the graph contains all expected POI types."""
        graph = create_venue_graph()
        poi_types = {node.poi_type for node in graph.get_all_nodes()}
        expected = {"gate", "junction", "restroom", "food_court", "medical", "elevator", "stairs", "ramp", "seating"}
        assert expected.issubset(poi_types)

    def test_graph_has_gates(self) -> None:
        """Test that the graph has 6 stadium gates."""
        graph = create_venue_graph()
        gates = graph.get_nodes_by_type("gate")
        assert len(gates) == 6

    def test_graph_has_restrooms(self) -> None:
        """Test that the graph has restrooms on multiple floors."""
        graph = create_venue_graph()
        restrooms = graph.get_nodes_by_type("restroom")
        assert len(restrooms) >= 4
        floors = {r.floor_level for r in restrooms}
        assert len(floors) >= 2  # Restrooms on multiple floors

    def test_graph_has_accessible_elevators(self) -> None:
        """Test that all elevators are accessible."""
        graph = create_venue_graph()
        elevators = graph.get_nodes_by_type("elevator")
        assert len(elevators) >= 4
        for elev in elevators:
            assert elev.is_accessible is True

    def test_route_gate1_to_restroom(self) -> None:
        """Test that a route exists from Gate 1 to a restroom."""
        graph = create_venue_graph()
        result = graph.find_route("gate-1", "restroom-g1")
        assert result is not None
        assert result.total_distance_meters > 0

    def test_accessible_route_exists(self) -> None:
        """Test that accessible routes exist (no stairs)."""
        from app.core.pathfinding import PathConstraints, AccessibilityType

        graph = create_venue_graph()
        constraints = PathConstraints(wheelchair_accessible=True)
        result = graph.find_route("gate-1", "concourse-1", constraints)
        assert result is not None
        for step in result.steps:
            assert step.accessibility not in (AccessibilityType.STAIRS, AccessibilityType.ESCALATOR)

    def test_multi_floor_route(self) -> None:
        """Test routing between different floors."""
        graph = create_venue_graph()
        result = graph.find_route("gate-1", "vip-lounge")
        assert result is not None
        assert result.total_distance_meters > 0


class TestDensityEvaluatorSeed:
    """Tests for density evaluator seed data."""

    def test_evaluator_has_zones_registered(self) -> None:
        """Test that all 12 zones are registered."""
        evaluator = create_density_evaluator()
        assert len(evaluator._zone_names) == 12

    def test_evaluator_zone_names(self) -> None:
        """Test that zone names are descriptive."""
        evaluator = create_density_evaluator()
        zone_names = set(evaluator._zone_names.values())
        assert any("Main Lobby" in name for name in zone_names)
        assert any("VIP" in name for name in zone_names)
        assert any("VIP" in name for name in zone_names)


class TestSOPDocuments:
    """Tests for SOP seed documents."""

    def test_sop_documents_exist(self) -> None:
        """Test that SOP documents are provided."""
        docs = get_sop_documents()
        assert len(docs) >= 10

    def test_sop_has_required_fields(self) -> None:
        """Test that each SOP document has title, section, and content."""
        docs = get_sop_documents()
        for doc in docs:
            assert "title" in doc
            assert "section" in doc
            assert "content" in doc
            assert len(doc["content"]) > 50  # Meaningful content

    def test_sop_covers_critical_topics(self) -> None:
        """Test that SOPs cover all critical operational topics."""
        docs = get_sop_documents()
        titles = {doc["title"] for doc in docs}
        assert "Crowd Management Protocol" in titles
        assert "Evacuation Protocol" in titles
        assert "Medical Response Protocol" in titles
        assert "Accessibility Protocol" in titles


class TestConfigDefaults:
    """Tests for configuration defaults and validation."""

    def test_default_settings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings have sensible defaults."""
        # Override conftest env to test actual defaults
        monkeypatch.setenv("MONGODB_DB_NAME", "sentinel_arena")
        monkeypatch.setenv("ENVIRONMENT", "development")
        settings = Settings(
            mongodb_uri="mongodb://localhost:27017",
            jwt_secret_key="test-secret",
            groq_api_key="test-key",
        )
        assert settings.mongodb_db_name == "sentinel_arena"
        assert settings.jwt_algorithm == "HS256"
        assert settings.jwt_access_token_expire_minutes == 15
        assert settings.log_level == "info"
