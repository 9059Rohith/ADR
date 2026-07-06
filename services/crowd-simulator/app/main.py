"""SentinelArena — Crowd Simulator Service.

Generates synthetic crowd density data for all venue zones.
Emits readings every 5 seconds simulating realistic match-day patterns.

DOCUMENTED AS SIMULATED DATA: This service generates synthetic IoT sensor
data for demonstration purposes. In production, this would be replaced by
real sensor/camera feeds via the same Redis Streams interface.
"""

from __future__ import annotations

import asyncio
import json
import random
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

logger = structlog.get_logger()

# Zone configurations
ZONES = [
    {"id": "zone-a", "name": "Main Lobby", "capacity": 500, "base_load": 0.4},
    {"id": "zone-b", "name": "North Concourse", "capacity": 400, "base_load": 0.3},
    {"id": "zone-c", "name": "North Stand", "capacity": 2000, "base_load": 0.6},
    {"id": "zone-d", "name": "South Concourse", "capacity": 400, "base_load": 0.3},
    {"id": "zone-e", "name": "South Stand", "capacity": 2000, "base_load": 0.6},
    {"id": "zone-f", "name": "East Wing", "capacity": 600, "base_load": 0.25},
    {"id": "zone-g", "name": "North Gates", "capacity": 300, "base_load": 0.35},
    {"id": "zone-h", "name": "South Gates", "capacity": 300, "base_load": 0.35},
    {"id": "zone-i", "name": "VIP Area", "capacity": 200, "base_load": 0.2},
    {"id": "zone-j", "name": "Level 1 Concourse", "capacity": 1500, "base_load": 0.45},
    {"id": "zone-k", "name": "Level 2 Concourse", "capacity": 800, "base_load": 0.2},
    {"id": "zone-l", "name": "Press & VIP L2", "capacity": 200, "base_load": 0.15},
]

# Simulation state
_simulation_running = False
_latest_readings: dict[str, dict[str, Any]] = {}
_connected_websockets: list[WebSocket] = []
_simulation_time: float = 0.0  # Simulated event time in minutes


def generate_density(zone: dict[str, Any], event_time_min: float) -> dict[str, Any]:
    """Generate a realistic density reading for a zone.

    Models a match-day pattern:
    - 0-30 min: Pre-match entry surge
    - 30-75 min: First half (stable, high in seating)
    - 75-95 min: Halftime (surge in concourse/food/restrooms)
    - 95-140 min: Second half (stable, high in seating)
    - 140-170 min: Post-match egress

    Args:
        zone: Zone configuration dict.
        event_time_min: Current simulated event time in minutes.

    Returns:
        Dict with zone_id, count, capacity, density_pct, timestamp.
    """
    base = zone["base_load"]
    zone_id = zone["id"]

    # Time-based multiplier (match-day pattern)
    if event_time_min < 30:
        # Pre-match: entry surge
        time_mult = 0.3 + (event_time_min / 30) * 0.5
        if zone_id in ("zone-a", "zone-g", "zone-h"):  # Gates and lobby
            time_mult *= 1.5
    elif event_time_min < 75:
        # First half: stable, high in seating
        time_mult = 0.8
        if zone_id in ("zone-c", "zone-e"):  # Seating areas
            time_mult = 1.1
        elif zone_id in ("zone-a", "zone-b", "zone-d"):  # Concourses
            time_mult = 0.4
    elif event_time_min < 95:
        # Halftime: surge in concourses, food, restrooms
        time_mult = 0.6
        if zone_id in ("zone-a", "zone-b", "zone-d", "zone-j"):  # Concourses
            time_mult = 1.3
        elif zone_id in ("zone-c", "zone-e"):  # Seating
            time_mult = 0.5
    elif event_time_min < 140:
        # Second half: stable
        time_mult = 0.75
        if zone_id in ("zone-c", "zone-e"):
            time_mult = 1.05
    else:
        # Post-match: egress
        time_mult = max(0.1, 1.0 - (event_time_min - 140) / 30)
        if zone_id in ("zone-a", "zone-g", "zone-h"):
            time_mult *= 1.4

    # Calculate base density with noise
    density = base * time_mult
    noise = random.gauss(0, 0.05)  # 5% standard deviation noise
    density = max(0.0, min(1.0, density + noise))

    # Simulate occasional spikes (crowd events)
    if random.random() < 0.02:  # 2% chance of spike
        density = min(1.0, density + random.uniform(0.1, 0.25))

    count = int(density * zone["capacity"])
    density_pct = round((count / zone["capacity"]) * 100, 1)

    return {
        "zone_id": zone_id,
        "zone_name": zone["name"],
        "count": count,
        "capacity": zone["capacity"],
        "density_pct": density_pct,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_time_min": round(event_time_min, 1),
    }


async def simulation_loop() -> None:
    """Main simulation loop — generates readings every 5 seconds."""
    global _simulation_running, _simulation_time

    _simulation_running = True
    logger.info("Crowd simulator started")

    while _simulation_running:
        readings = {}
        for zone in ZONES:
            reading = generate_density(zone, _simulation_time)
            readings[zone["id"]] = reading
            _latest_readings[zone["id"]] = reading

        # Broadcast to connected WebSocket clients
        message = json.dumps({
            "type": "crowd_update",
            "readings": list(readings.values()),
            "event_time_min": round(_simulation_time, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        disconnected = []
        for ws in _connected_websockets:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            _connected_websockets.remove(ws)

        # Advance simulation time (5 real seconds = 1 simulated minute)
        _simulation_time += 1.0
        if _simulation_time > 170:
            _simulation_time = 0.0  # Loop back

        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Start the simulation loop on app startup."""
    task = asyncio.create_task(simulation_loop())
    yield
    global _simulation_running
    _simulation_running = False
    task.cancel()


app = FastAPI(
    title="SentinelArena Crowd Simulator",
    description="Synthetic crowd density data generator [SIMULATED DATA]",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check."""
    return {"status": "healthy", "service": "crowd-simulator"}


@app.get("/readings")
async def get_latest_readings() -> Any:
    """Get the latest readings for all zones."""
    return {
        "readings": list(_latest_readings.values()),
        "event_time_min": round(_simulation_time, 1),
        "is_simulated": True,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time crowd density streaming."""
    await websocket.accept()
    _connected_websockets.append(websocket)
    logger.info("Simulator WebSocket connected", total=len(_connected_websockets))

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in _connected_websockets:
            _connected_websockets.remove(websocket)
        logger.info("Simulator WebSocket disconnected")
