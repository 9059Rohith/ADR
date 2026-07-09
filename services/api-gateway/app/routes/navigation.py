"""SentinelArena — Navigation Routes.

Endpoints for indoor navigation queries using the pathfinding engine
and AI-powered natural language instruction generation.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

logger = structlog.get_logger()
router = APIRouter()


class NavigationRequest(BaseModel):
    """Navigation query request."""

    query: str = Field(
        ..., min_length=1, max_length=500, description="Natural language navigation query"
    )
    from_location_id: str = Field(default="lobby-main", description="Current location node ID")
    to_location_id: str | None = Field(
        default=None, description="Optional specific destination node ID"
    )
    avoid_stairs: bool = Field(default=False)
    wheelchair_accessible: bool = Field(default=False)
    avoid_congestion: bool = Field(default=False)
    locale: str = Field(default="en", pattern="^(en|hi|ta|te|es)$")


class NavigationResponse(BaseModel):
    """Navigation response with route data and instructions."""

    instructions: str
    route_data: dict[str, Any] | None = None
    sources: list[str] = []
    intent: str = "navigation"
    locale: str = "en"


@router.post("", response_model=NavigationResponse)
async def navigate(
    request: Request,
    body: NavigationRequest,
) -> Any:
    """Process a natural-language navigation query.

    Flow:
    1. LLM extracts intent and constraints from the query
    2. Deterministic A* pathfinding computes the optimal route
    3. LLM phrases the route as natural-language instructions
    4. Language Agent translates if needed

    The pathfinding is always deterministic — the LLM only
    interprets queries and phrases results, never invents routes.
    """
    orchestrator = request.app.state.orchestrator

    result = await orchestrator.process_message(
        message=body.query,
        locale=body.locale,
        user_location_id=body.from_location_id,
    )

    return NavigationResponse(
        instructions=result.get("response", ""),
        route_data=result.get("route_data"),
        sources=result.get("sources", []),
        locale=result.get("locale", body.locale),
    )


@router.get("/pois")
async def list_pois(request: Request, poi_type: str | None = None) -> Any:
    """List all points of interest in the venue.

    Args:
        request: FastAPI request with app state.
        poi_type: Optional filter by POI type (e.g., 'restroom', 'gate', 'food_court').

    Returns:
        List of POIs with their locations and metadata.
    """
    venue_graph = request.app.state.venue_graph

    nodes = venue_graph.get_nodes_by_type(poi_type) if poi_type else venue_graph.get_all_nodes()

    return {
        "pois": [
            {
                "id": node.id,
                "name": node.name,
                "type": node.poi_type,
                "floor_level": node.floor_level,
                "x": node.x,
                "y": node.y,
                "is_accessible": node.is_accessible,
                "zone_id": node.zone_id,
            }
            for node in nodes
        ],
        "total": len(nodes),
    }
