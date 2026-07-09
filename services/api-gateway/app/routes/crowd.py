"""SentinelArena — Crowd Management Routes.

Endpoints for real-time crowd density data, trend analysis,
and crowd advisories.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.core.density_evaluator import DensityReading

logger = structlog.get_logger()
router = APIRouter()


class ZoneDensityResponse(BaseModel):
    """Current density data for a single zone."""

    zone_id: str
    zone_name: str
    current_density_pct: float
    ewma_density_pct: float
    trend_direction: str
    trend_rate_pct_per_min: float
    severity: str
    projected_time_to_threshold_min: float | None
    current_count: int
    capacity: int
    timestamp: str


class CrowdOverviewResponse(BaseModel):
    """Overview of all zone densities."""

    zones: list[ZoneDensityResponse]
    overall_severity: str
    timestamp: str


@router.get("", response_model=CrowdOverviewResponse)
async def get_crowd_overview(request: Request) -> Any:
    """Get current crowd density overview for all zones.

    Returns density data, trend analysis, and severity levels
    for every tracked zone. Data comes from the deterministic
    density evaluator — numbers are never LLM-generated.
    """
    evaluator = request.app.state.density_evaluator
    analyses = evaluator.get_all_zone_analyses()

    # Determine overall severity (highest across all zones)
    severity_order = ["normal", "warning", "critical", "emergency"]
    overall = "normal"
    for a in analyses:
        if severity_order.index(a.severity.value) > severity_order.index(overall):
            overall = a.severity.value

    zones = [
        ZoneDensityResponse(
            zone_id=a.zone_id,
            zone_name=a.zone_name,
            current_density_pct=round(a.current_density_pct, 1),
            ewma_density_pct=round(a.ewma_density_pct, 1),
            trend_direction=a.trend_direction,
            trend_rate_pct_per_min=round(a.trend_rate_pct_per_min, 2),
            severity=a.severity.value,
            projected_time_to_threshold_min=(
                round(a.projected_time_to_threshold_min, 1)
                if a.projected_time_to_threshold_min is not None
                else None
            ),
            current_count=a.current_count,
            capacity=a.capacity,
            timestamp=a.timestamp.isoformat(),
        )
        for a in analyses
    ]

    return CrowdOverviewResponse(
        zones=zones,
        overall_severity=overall,
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.post("/simulate-reading")
async def simulate_reading(
    request: Request,
    zone_id: str = "zone-a",
    count: int = 200,
    capacity: int = 500,
) -> Any:
    """Simulate a crowd density reading for testing.

    This endpoint allows injecting test readings into the density
    evaluator without the Crowd Simulator service running.

    DOCUMENTED AS SIMULATION: This endpoint is for testing only.
    """
    evaluator = request.app.state.density_evaluator

    reading = DensityReading(
        zone_id=zone_id,
        count=count,
        capacity=capacity,
        timestamp=datetime.now(UTC),
    )

    analysis = evaluator.add_reading(reading)

    return analysis.to_dict()


@router.websocket("/ws")
async def crowd_websocket(websocket: WebSocket, request: Request = None) -> None:
    """WebSocket endpoint for real-time crowd density updates.

    Clients connect to receive live density data as it arrives
    from the Crowd Simulator service.
    """
    await websocket.accept()
    logger.info("Crowd WebSocket connected")

    try:
        while True:
            # Wait for client messages (keepalive pings)
            await websocket.receive_text()

            # Return current density overview
            if hasattr(websocket.app, "state"):
                evaluator = websocket.app.state.density_evaluator
                analyses = evaluator.get_all_zone_analyses()
                await websocket.send_json(
                    {
                        "type": "density_update",
                        "zones": [a.to_dict() for a in analyses],
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )

    except WebSocketDisconnect:
        logger.info("Crowd WebSocket disconnected")
