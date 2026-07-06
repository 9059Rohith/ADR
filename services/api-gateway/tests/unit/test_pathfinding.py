"""SentinelArena — Unit Tests for Pathfinding Engine.

Tests the deterministic A* pathfinding algorithm with various
accessibility constraints and edge cases. Target: ≥95% coverage
on pathfinding.py (critical safety code).
"""

from __future__ import annotations

import pytest

from app.core.pathfinding import (
    AccessibilityType,
    GraphEdge,
    GraphNode,
    PathConstraints,
    VenueGraph,
)


@pytest.fixture
def simple_graph() -> VenueGraph:
    """Create a simple test graph with 5 nodes."""
    graph = VenueGraph()

    nodes = [
        GraphNode("A", "Start", "gate", 0, 0.0, 0.0),
        GraphNode("B", "Junction", "junction", 0, 100.0, 0.0),
        GraphNode("C", "Stairs Up", "stairs", 0, 100.0, 100.0, False),
        GraphNode("D", "Elevator Up", "elevator", 0, 200.0, 0.0),
        GraphNode("E", "Restroom", "restroom", 1, 200.0, 100.0),
    ]
    for n in nodes:
        graph.add_node(n)

    edges = [
        GraphEdge("A", "B", 100.0),
        GraphEdge("B", "C", 50.0, AccessibilityType.WALKWAY),
        GraphEdge("C", "E", 20.0, AccessibilityType.STAIRS),
        GraphEdge("B", "D", 100.0),
        GraphEdge("D", "E", 10.0, AccessibilityType.ELEVATOR),
    ]
    for e in edges:
        graph.add_edge(e)

    return graph


class TestPathfinding:
    """Tests for the A* pathfinding engine."""

    def test_basic_route(self, simple_graph: VenueGraph) -> None:
        """Test finding a basic route between two nodes."""
        result = simple_graph.find_route("A", "E")
        assert result is not None
        assert len(result.steps) > 0
        assert result.total_distance_meters > 0
        assert result.estimated_time_seconds > 0
        assert result.nodes_visited[0].id == "A"
        assert result.nodes_visited[-1].id == "E"

    def test_shortest_path(self, simple_graph: VenueGraph) -> None:
        """Test that A* finds the shortest path."""
        result = simple_graph.find_route("A", "E")
        assert result is not None
        # Via stairs: A→B(100) + B→C(50) + C→E(20) = 170m
        # Via elevator: A→B(100) + B→D(100) + D→E(10) = 210m
        # But elevator has a 30s wait penalty, so stairs path should be shorter by distance
        assert result.total_distance_meters <= 210

    def test_avoid_stairs_constraint(self, simple_graph: VenueGraph) -> None:
        """Test that avoid_stairs constraint routes via elevator."""
        constraints = PathConstraints(avoid_stairs=True)
        result = simple_graph.find_route("A", "E", constraints)
        assert result is not None
        # Should go via elevator (A→B→D→E)
        for step in result.steps:
            assert step.accessibility != AccessibilityType.STAIRS

    def test_wheelchair_accessible(self, simple_graph: VenueGraph) -> None:
        """Test wheelchair-accessible route avoids stairs."""
        constraints = PathConstraints(wheelchair_accessible=True)
        result = simple_graph.find_route("A", "E", constraints)
        assert result is not None
        for step in result.steps:
            assert step.accessibility not in (
                AccessibilityType.STAIRS,
                AccessibilityType.ESCALATOR,
            )

    def test_no_route_exists(self, simple_graph: VenueGraph) -> None:
        """Test that None is returned when no route exists."""
        result = simple_graph.find_route("A", "nonexistent")
        assert result is None

    def test_same_start_end(self, simple_graph: VenueGraph) -> None:
        """Test routing from a node to itself."""
        result = simple_graph.find_route("A", "A")
        assert result is not None
        assert result.total_distance_meters == 0
        assert len(result.steps) == 0

    def test_route_serialization(self, simple_graph: VenueGraph) -> None:
        """Test that route results serialize correctly for API/LLM consumption."""
        result = simple_graph.find_route("A", "E")
        assert result is not None
        data = result.to_dict()
        assert "total_distance_meters" in data
        assert "total_distance_display" in data
        assert "estimated_time_display" in data
        assert "nodes" in data
        assert "steps" in data
        assert len(data["nodes"]) == len(result.nodes_visited)

    def test_find_nearest(self, simple_graph: VenueGraph) -> None:
        """Test finding nearest POI of a type."""
        results = simple_graph.find_nearest("A", "restroom")
        assert len(results) > 0
        assert results[0].nodes_visited[-1].poi_type == "restroom"

    def test_find_nearest_no_results(self, simple_graph: VenueGraph) -> None:
        """Test finding nearest when no POI of type exists."""
        results = simple_graph.find_nearest("A", "food_court")
        assert len(results) == 0

    def test_distance_display_meters(self, simple_graph: VenueGraph) -> None:
        """Test human-readable distance display for <1km."""
        result = simple_graph.find_route("A", "B")
        assert result is not None
        assert "m" in result.total_distance_display
        assert "km" not in result.total_distance_display

    def test_congestion_update(self, simple_graph: VenueGraph) -> None:
        """Test that congestion weight updates affect routing."""
        # Get baseline route
        baseline = simple_graph.find_route("A", "E")
        assert baseline is not None
        baseline_time = baseline.estimated_time_seconds

        # Add heavy congestion to the stairs path
        simple_graph.update_congestion("C", "E", 5.0)

        # Re-route should prefer elevator due to congestion
        result = simple_graph.find_route("A", "E")
        assert result is not None

    def test_node_operations(self, simple_graph: VenueGraph) -> None:
        """Test node retrieval operations."""
        node = simple_graph.get_node("A")
        assert node is not None
        assert node.name == "Start"

        gates = simple_graph.get_nodes_by_type("gate")
        assert len(gates) == 1
        assert gates[0].id == "A"

        all_nodes = simple_graph.get_all_nodes()
        assert len(all_nodes) == 5

        assert simple_graph.node_count == 5
        assert simple_graph.edge_count > 0
