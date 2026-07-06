"""SentinelArena — Venue Routes.

Endpoints for venue data: zones, POIs, and map information.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("")
async def get_venue_info(request: Request) -> Any:
    """Get venue overview information."""
    graph = request.app.state.venue_graph
    return {
        "venue": {
            "name": "SentinelArena Stadium",
            "total_capacity": 10000,
            "floors": 3,
            "total_pois": graph.node_count,
            "total_paths": graph.edge_count,
        },
        "zones": [
            {"id": "zone-a", "name": "Zone A — Main Lobby", "capacity": 500, "floor": 0},
            {"id": "zone-b", "name": "Zone B — North Concourse", "capacity": 400, "floor": 0},
            {"id": "zone-c", "name": "Zone C — North Stand", "capacity": 2000, "floor": 1},
            {"id": "zone-d", "name": "Zone D — South Concourse", "capacity": 400, "floor": 0},
            {"id": "zone-e", "name": "Zone E — South Stand", "capacity": 2000, "floor": 1},
            {"id": "zone-f", "name": "Zone F — East Wing", "capacity": 600, "floor": 0},
            {"id": "zone-g", "name": "Zone G — North Gates", "capacity": 300, "floor": 0},
            {"id": "zone-h", "name": "Zone H — South Gates", "capacity": 300, "floor": 0},
            {"id": "zone-i", "name": "Zone I — VIP Area", "capacity": 200, "floor": 0},
            {"id": "zone-j", "name": "Zone J — Level 1 Concourse", "capacity": 1500, "floor": 1},
            {"id": "zone-k", "name": "Zone K — Level 2 Concourse", "capacity": 800, "floor": 2},
            {"id": "zone-l", "name": "Zone L — Press & VIP Level 2", "capacity": 200, "floor": 2},
        ],
    }


@router.get("/map-data")
async def get_map_data(request: Request) -> Any:
    """Get venue map data for SVG rendering.

    Returns all POIs and edges with coordinates for the
    interactive indoor map component.
    """
    graph = request.app.state.venue_graph
    nodes = graph.get_all_nodes()

    return {
        "viewport": {"width": 1000, "height": 600},
        "floors": [0, 1, 2],
        "nodes": [
            {
                "id": n.id,
                "name": n.name,
                "type": n.poi_type,
                "floor": n.floor_level,
                "x": n.x,
                "y": n.y,
                "is_accessible": n.is_accessible,
                "zone_id": n.zone_id,
            }
            for n in nodes
        ],
    }
