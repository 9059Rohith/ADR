"""SentinelArena — Dijkstra/A* Pathfinding Engine.

Deterministic pathfinding on the venue graph with accessibility constraints
and live congestion weighting. This is the algorithmic core — no LLM dependency.

The LLM is only used to *phrase* the results, never to compute them.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AccessibilityType(str, Enum):
    """Edge accessibility classification."""

    WALKWAY = "walkway"
    STAIRS = "stairs"
    RAMP = "ramp"
    ELEVATOR = "elevator"
    ESCALATOR = "escalator"


@dataclass(frozen=True)
class GraphNode:
    """A point of interest / junction in the venue graph."""

    id: str
    name: str
    poi_type: str
    floor_level: int
    x: float
    y: float
    is_accessible: bool = True
    zone_id: str | None = None
    amenities: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    """A walkable path between two graph nodes."""

    from_node_id: str
    to_node_id: str
    distance_meters: float
    accessibility: AccessibilityType = AccessibilityType.WALKWAY
    is_bidirectional: bool = True
    congestion_weight: float = 1.0


@dataclass
class RouteStep:
    """A single step in a navigation route."""

    from_node: GraphNode
    to_node: GraphNode
    distance_meters: float
    accessibility: AccessibilityType
    floor_change: int  # positive = up, negative = down, 0 = same


@dataclass
class RouteResult:
    """Complete pathfinding result."""

    steps: list[RouteStep]
    total_distance_meters: float
    estimated_time_seconds: float
    nodes_visited: list[GraphNode]
    is_accessible: bool

    @property
    def total_distance_display(self) -> str:
        """Human-readable distance."""
        if self.total_distance_meters >= 1000:
            return f"{self.total_distance_meters / 1000:.1f} km"
        return f"{self.total_distance_meters:.0f} m"

    @property
    def estimated_time_display(self) -> str:
        """Human-readable estimated time."""
        minutes = int(self.estimated_time_seconds // 60)
        if minutes < 1:
            return "less than 1 min"
        if minutes == 1:
            return "1 min"
        return f"{minutes} min"

    def to_dict(self) -> dict[str, Any]:
        """Serialize route result for API response / LLM consumption."""
        return {
            "total_distance_meters": round(self.total_distance_meters, 1),
            "total_distance_display": self.total_distance_display,
            "estimated_time_seconds": round(self.estimated_time_seconds, 0),
            "estimated_time_display": self.estimated_time_display,
            "is_accessible": self.is_accessible,
            "num_steps": len(self.steps),
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.poi_type,
                    "floor": node.floor_level,
                    "x": node.x,
                    "y": node.y,
                }
                for node in self.nodes_visited
            ],
            "steps": [
                {
                    "from": step.from_node.name,
                    "to": step.to_node.name,
                    "distance_m": round(step.distance_meters, 1),
                    "accessibility": step.accessibility.value,
                    "floor_change": step.floor_change,
                }
                for step in self.steps
            ],
        }


@dataclass(frozen=True)
class PathConstraints:
    """User-specified navigation constraints."""

    avoid_stairs: bool = False
    avoid_escalators: bool = False
    wheelchair_accessible: bool = False
    avoid_congestion: bool = False
    max_congestion_weight: float = 3.0

    def is_edge_allowed(self, edge: GraphEdge) -> bool:
        """Check if an edge satisfies the accessibility constraints."""
        if self.avoid_stairs and edge.accessibility == AccessibilityType.STAIRS:
            return False
        if self.avoid_escalators and edge.accessibility == AccessibilityType.ESCALATOR:
            return False
        if self.wheelchair_accessible and edge.accessibility in (
            AccessibilityType.STAIRS,
            AccessibilityType.ESCALATOR,
        ):
            return False
        if self.avoid_congestion and edge.congestion_weight > self.max_congestion_weight:
            return False
        return True


class VenueGraph:
    """In-memory venue graph for pathfinding.

    Supports Dijkstra and A* algorithms with accessibility constraints
    and live congestion weighting.
    """

    # Average walking speed: 1.4 m/s (about 5 km/h)
    WALKING_SPEED_MS: float = 1.4
    # Elevator wait + travel time penalty in seconds
    ELEVATOR_PENALTY_S: float = 30.0
    # Escalator speed multiplier (slower than walking)
    ESCALATOR_SPEED_MULT: float = 0.7

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._adjacency: dict[str, list[GraphEdge]] = {}

    def add_node(self, node: GraphNode) -> None:
        """Add a node (POI/junction) to the graph."""
        self._nodes[node.id] = node
        if node.id not in self._adjacency:
            self._adjacency[node.id] = []

    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge (walkable path) to the graph."""
        if edge.from_node_id not in self._adjacency:
            self._adjacency[edge.from_node_id] = []
        self._adjacency[edge.from_node_id].append(edge)

        if edge.is_bidirectional:
            reverse = GraphEdge(
                from_node_id=edge.to_node_id,
                to_node_id=edge.from_node_id,
                distance_meters=edge.distance_meters,
                accessibility=edge.accessibility,
                is_bidirectional=False,  # Prevent double-reverse
                congestion_weight=edge.congestion_weight,
            )
            if edge.to_node_id not in self._adjacency:
                self._adjacency[edge.to_node_id] = []
            self._adjacency[edge.to_node_id].append(reverse)

    def update_congestion(self, from_id: str, to_id: str, weight: float) -> None:
        """Update the congestion weight on an edge (called from live density data)."""
        for edge_list in [self._adjacency.get(from_id, [])]:
            for i, edge in enumerate(edge_list):
                if edge.to_node_id == to_id:
                    edge_list[i] = GraphEdge(
                        from_node_id=edge.from_node_id,
                        to_node_id=edge.to_node_id,
                        distance_meters=edge.distance_meters,
                        accessibility=edge.accessibility,
                        is_bidirectional=False,
                        congestion_weight=weight,
                    )

    def get_node(self, node_id: str) -> GraphNode | None:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def get_nodes_by_type(self, poi_type: str) -> list[GraphNode]:
        """Get all nodes of a specific type (e.g., 'restroom', 'gate')."""
        return [n for n in self._nodes.values() if n.poi_type == poi_type]

    def get_all_nodes(self) -> list[GraphNode]:
        """Get all nodes in the graph."""
        return list(self._nodes.values())

    def get_all_edges(self) -> list[GraphEdge]:
        """Get all edges in the graph."""
        return [edge for edges in self._adjacency.values() for edge in edges]

    @property
    def node_count(self) -> int:
        """Number of nodes in the graph."""
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        """Number of edges in the graph (counting each direction separately)."""
        return sum(len(edges) for edges in self._adjacency.values())

    def _heuristic(self, node_a: GraphNode, node_b: GraphNode) -> float:
        """Euclidean distance heuristic for A*."""
        dx = node_a.x - node_b.x
        dy = node_a.y - node_b.y
        # Add floor penalty: 5m per floor difference (approximate)
        dz = abs(node_a.floor_level - node_b.floor_level) * 5.0
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def _edge_cost(self, edge: GraphEdge) -> float:
        """Calculate the traversal cost of an edge in seconds.

        Cost = (distance / speed) * congestion_weight + accessibility_penalty
        """
        base_time = edge.distance_meters / self.WALKING_SPEED_MS

        # Apply congestion weight
        cost = base_time * edge.congestion_weight

        # Accessibility-specific penalties
        if edge.accessibility == AccessibilityType.ELEVATOR:
            cost += self.ELEVATOR_PENALTY_S
        elif edge.accessibility == AccessibilityType.ESCALATOR:
            cost *= (1.0 / self.ESCALATOR_SPEED_MULT)
        elif edge.accessibility == AccessibilityType.STAIRS:
            cost *= 1.3  # Stairs are slower

        return cost

    def find_route(
        self,
        from_id: str,
        to_id: str,
        constraints: PathConstraints | None = None,
    ) -> RouteResult | None:
        """Find the shortest route using A* algorithm.

        Args:
            from_id: Starting node ID.
            to_id: Destination node ID.
            constraints: Optional accessibility constraints.

        Returns:
            RouteResult with the optimal path, or None if no path exists.
        """
        if constraints is None:
            constraints = PathConstraints()

        start = self._nodes.get(from_id)
        goal = self._nodes.get(to_id)

        if start is None or goal is None:
            return None

        # A* with priority queue
        # (f_score, counter, node_id)
        counter = 0
        open_set: list[tuple[float, int, str]] = [(0.0, counter, from_id)]
        came_from: dict[str, tuple[str, GraphEdge]] = {}
        g_score: dict[str, float] = {from_id: 0.0}
        closed_set: set[str] = set()

        while open_set:
            _, _, current_id = heapq.heappop(open_set)

            if current_id in closed_set:
                continue
            closed_set.add(current_id)

            if current_id == to_id:
                return self._reconstruct_route(came_from, from_id, to_id)

            current_node = self._nodes[current_id]

            for edge in self._adjacency.get(current_id, []):
                neighbor_id = edge.to_node_id

                if neighbor_id in closed_set:
                    continue

                if not constraints.is_edge_allowed(edge):
                    continue

                neighbor_node = self._nodes.get(neighbor_id)
                if neighbor_node is None:
                    continue

                tentative_g = g_score[current_id] + self._edge_cost(edge)

                if tentative_g < g_score.get(neighbor_id, float("inf")):
                    came_from[neighbor_id] = (current_id, edge)
                    g_score[neighbor_id] = tentative_g
                    f_score = tentative_g + self._heuristic(neighbor_node, goal)
                    counter += 1
                    heapq.heappush(open_set, (f_score, counter, neighbor_id))

        return None  # No path found

    def find_nearest(
        self,
        from_id: str,
        poi_type: str,
        constraints: PathConstraints | None = None,
        max_results: int = 3,
    ) -> list[RouteResult]:
        """Find the nearest POIs of a given type using Dijkstra's algorithm.

        Args:
            from_id: Starting node ID.
            poi_type: Type of POI to search for (e.g., 'restroom', 'food_court').
            constraints: Optional accessibility constraints.
            max_results: Maximum number of results to return.

        Returns:
            List of RouteResults to the nearest POIs, sorted by distance.
        """
        if constraints is None:
            constraints = PathConstraints()

        targets = [n for n in self._nodes.values() if n.poi_type == poi_type and n.id != from_id]
        if not targets:
            return []

        results: list[RouteResult] = []
        for target in targets:
            route = self.find_route(from_id, target.id, constraints)
            if route is not None:
                results.append(route)

        results.sort(key=lambda r: r.total_distance_meters)
        return results[:max_results]

    def _reconstruct_route(
        self,
        came_from: dict[str, tuple[str, GraphEdge]],
        start_id: str,
        end_id: str,
    ) -> RouteResult:
        """Reconstruct the path from A* came_from map."""
        path_edges: list[GraphEdge] = []
        current = end_id

        while current != start_id:
            prev_id, edge = came_from[current]
            path_edges.append(edge)
            current = prev_id

        path_edges.reverse()

        steps: list[RouteStep] = []
        nodes_visited: list[GraphNode] = [self._nodes[start_id]]
        total_distance = 0.0
        total_time = 0.0
        is_accessible = True

        for edge in path_edges:
            from_node = self._nodes[edge.from_node_id]
            to_node = self._nodes[edge.to_node_id]
            floor_change = to_node.floor_level - from_node.floor_level

            steps.append(
                RouteStep(
                    from_node=from_node,
                    to_node=to_node,
                    distance_meters=edge.distance_meters,
                    accessibility=edge.accessibility,
                    floor_change=floor_change,
                )
            )

            nodes_visited.append(to_node)
            total_distance += edge.distance_meters
            total_time += self._edge_cost(edge)

            if edge.accessibility == AccessibilityType.STAIRS:
                is_accessible = False

        return RouteResult(
            steps=steps,
            total_distance_meters=total_distance,
            estimated_time_seconds=total_time,
            nodes_visited=nodes_visited,
            is_accessible=is_accessible,
        )
