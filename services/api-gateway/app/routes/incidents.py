"""SentinelArena — Incident Reporting Routes.

Endpoints for creating, listing, and managing incident reports
filed by volunteers and staff, persisted in MongoDB Atlas.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

logger = structlog.get_logger()
router = APIRouter()

# In-memory incident store (fallback when MongoDB is offline)
_incidents: dict[str, dict[str, Any]] = {}


class IncidentCreateRequest(BaseModel):
    """Incident report creation request."""

    title: str = Field(..., min_length=3, max_length=300)
    description: str = Field(..., min_length=10, max_length=5000)
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    zone_id: str = Field(default="zone-a")
    locale: str = Field(default="en", pattern="^(en|hi|ta|te|es)$")
    reporter_id: str = Field(default="volunteer-1")


class IncidentResponse(BaseModel):
    """Incident report response."""

    id: str
    title: str
    description: str
    severity: str
    status: str
    zone_id: str
    ai_triage_summary: str | None = None
    ai_suggested_actions: list[str] = []
    created_at: str


@router.post("", response_model=IncidentResponse, status_code=201)
async def create_incident(
    request: Request,
    body: IncidentCreateRequest,
) -> Any:
    """Create a new incident report.

    The incident is automatically triaged by the AI system,
    which generates a summary and suggested response actions.
    Non-English reports are processed via the Language Agent.
    """
    orchestrator = request.app.state.orchestrator

    # Use Decision Agent for AI triage
    triage_query = (
        f"Triage this incident report and suggest response actions:\n"
        f"Title: {body.title}\n"
        f"Description: {body.description}\n"
        f"Severity: {body.severity}\n"
        f"Zone: {body.zone_id}"
    )

    result = await orchestrator.process_message(
        message=triage_query,
        locale=body.locale,
    )

    incident_id = str(uuid4())
    now = datetime.now(timezone.utc)

    incident = {
        "id": incident_id,
        "title": body.title,
        "description": body.description,
        "severity": body.severity,
        "status": "reported",
        "zone_id": body.zone_id,
        "reporter_id": body.reporter_id,
        "locale": body.locale,
        "ai_triage_summary": result.get("response", ""),
        "ai_suggested_actions": result.get("sources", []),
        "created_at": now.isoformat(),
    }

    _incidents[incident_id] = incident

    # Persist to MongoDB Atlas if available
    if getattr(request.app.state, "db_available", False):
        try:
            from app.config import get_settings
            from app.database import get_client

            client = get_client()
            db = client[get_settings().mongodb_db_name]
            await db.incidents.insert_one(incident)
        except Exception as exc:
            logger.warning("Failed to save incident to MongoDB", error=str(exc))

    logger.info(
        "Incident created",
        incident_id=incident_id,
        severity=body.severity,
        zone=body.zone_id,
    )

    return IncidentResponse(
        id=incident_id,
        title=body.title,
        description=body.description,
        severity=body.severity,
        status="reported",
        zone_id=body.zone_id,
        ai_triage_summary=result.get("response", ""),
        ai_suggested_actions=result.get("sources", []),
        created_at=now.isoformat(),
    )


@router.get("")
async def list_incidents(
    request: Request,
    status: str | None = None,
    severity: str | None = None,
) -> Any:
    """List all incidents, optionally filtered by status or severity."""
    if getattr(request.app.state, "db_available", False):
        try:
            from app.config import get_settings
            from app.database import get_client

            client = get_client()
            db = client[get_settings().mongodb_db_name]
            query: dict[str, Any] = {}
            if status:
                query["status"] = status
            if severity:
                query["severity"] = severity
            cursor = db.incidents.find(query, {"_id": 0}).sort("created_at", -1).limit(100)
            incidents = [doc async for doc in cursor]
            return {
                "incidents": incidents,
                "total": len(incidents),
            }
        except Exception as exc:
            logger.warning("Failed to fetch incidents from MongoDB", error=str(exc))

    incidents_list = list(_incidents.values())

    if status:
        incidents_list = [i for i in incidents_list if i["status"] == status]
    if severity:
        incidents_list = [i for i in incidents_list if i["severity"] == severity]

    return {
        "incidents": incidents_list,
        "total": len(incidents_list),
    }


@router.get("/{incident_id}")
async def get_incident(incident_id: str, request: Request) -> Any:
    """Get a specific incident by ID."""
    if getattr(request.app.state, "db_available", False):
        try:
            from app.config import get_settings
            from app.database import get_client

            client = get_client()
            db = client[get_settings().mongodb_db_name]
            doc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
            if doc:
                return doc
        except Exception as exc:
            logger.warning("Failed to fetch incident from MongoDB", error=str(exc))

    if incident_id not in _incidents:
        return {"error": "Incident not found"}
    return _incidents[incident_id]

