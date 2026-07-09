"""SentinelArena — Decision Support Routes.

Endpoints for AI-generated recommendations with human-in-the-loop
approval, rejection, and audit logging persisted to MongoDB Atlas.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.models import AuditLog, DecisionStatus

logger = structlog.get_logger()
router = APIRouter()

# In-memory decision store (fallback when MongoDB is offline)
_pending_decisions: dict[str, dict[str, Any]] = {}


class DecisionRequest(BaseModel):
    """Request for AI decision support."""

    query: str = Field(..., min_length=1, max_length=2000)
    locale: str = Field(default="en")


class DecisionResponse(BaseModel):
    """AI-generated decision recommendation."""

    decision_id: str
    recommendation: str
    sources: list[str]
    status: str = "pending"
    created_at: str


class DecisionAction(BaseModel):
    """Operator action on a decision."""

    action: str = Field(..., pattern="^(approve|reject|edit)$")
    actor_id: str = Field(default="organizer-1")
    notes: str = Field(default="")
    edited_recommendation: str | None = None


@router.post("", response_model=DecisionResponse)
async def request_decision(
    request: Request,
    body: DecisionRequest,
) -> Any:
    """Request AI-generated decision support.

    The Decision Agent synthesizes crowd data, weather, incidents,
    and SOP documents into ranked, cited recommendations.
    All recommendations require organizer approval before any
    broadcast action is taken.
    """
    orchestrator = request.app.state.orchestrator

    result = await orchestrator.process_message(
        message=body.query,
        locale=body.locale,
    )

    decision_id = str(uuid4())
    now = datetime.now(timezone.utc)

    decision = {
        "id": decision_id,
        "recommendation": result.get("response", ""),
        "sources": result.get("sources", []),
        "status": "pending",
        "created_at": now.isoformat(),
        "query": body.query,
    }

    _pending_decisions[decision_id] = decision

    # Persist to MongoDB Atlas if available
    if getattr(request.app.state, "db_available", False):
        try:
            from app.config import get_settings
            from app.database import get_client

            client = get_client()
            db = client[get_settings().mongodb_db_name]
            await db.decisions.insert_one(decision)
        except Exception as exc:
            logger.warning("Failed to save decision to MongoDB", error=str(exc))

    return DecisionResponse(
        decision_id=decision_id,
        recommendation=decision["recommendation"],
        sources=decision["sources"],
        status="pending",
        created_at=now.isoformat(),
    )


@router.get("")
async def list_decisions(request: Request) -> Any:
    """List all pending and recent decisions."""
    if getattr(request.app.state, "db_available", False):
        try:
            from app.config import get_settings
            from app.database import get_client

            client = get_client()
            db = client[get_settings().mongodb_db_name]
            cursor = db.decisions.find({}, {"_id": 0}).sort("created_at", -1).limit(50)
            decisions = [doc async for doc in cursor]
            return {
                "decisions": decisions,
                "total": len(decisions),
            }
        except Exception as exc:
            logger.warning("Failed to fetch decisions from MongoDB", error=str(exc))

    return {
        "decisions": list(_pending_decisions.values()),
        "total": len(_pending_decisions),
    }


@router.post("/{decision_id}/action")
async def action_decision(
    decision_id: str,
    body: DecisionAction,
    request: Request,
) -> Any:
    """Approve, reject, or edit a decision recommendation.

    This is the human-in-the-loop step. Every action is logged
    to the immutable audit trail in MongoDB Atlas when available.

    Args:
        decision_id: ID of the decision to act on.
        body: Action details (approve/reject/edit).
    """
    decision = _pending_decisions.get(decision_id)
    db = None

    if getattr(request.app.state, "db_available", False):
        try:
            from app.config import get_settings
            from app.database import get_client

            client = get_client()
            db = client[get_settings().mongodb_db_name]
            if not decision:
                decision = await db.decisions.find_one({"id": decision_id}, {"_id": 0})
        except Exception as exc:
            logger.warning("Failed to lookup decision in MongoDB", error=str(exc))

    if not decision:
        return {"error": "Decision not found"}

    # Update status
    status_map = {
        "approve": DecisionStatus.APPROVED,
        "reject": DecisionStatus.REJECTED,
        "edit": DecisionStatus.EDITED,
    }
    new_status = status_map[body.action]
    decision["status"] = new_status.value

    if body.edited_recommendation:
        decision["recommendation"] = body.edited_recommendation

    # Audit logging & status update in MongoDB Atlas
    audit_logged = False
    if db is not None:
        try:
            await db.decisions.update_one(
                {"id": decision_id},
                {"$set": {"status": new_status.value, "recommendation": decision.get("recommendation", "")}},
            )

            payload = {
                "decision_id": decision_id,
                "action": body.action,
                "notes": body.notes,
                "original_recommendation": decision.get("recommendation", ""),
            }

            audit_entry = AuditLog(
                actor_id=body.actor_id,
                action=f"decision.{body.action}",
                resource_type="decision",
                resource_id=decision_id,
                payload=payload,
                payload_hash=AuditLog.compute_payload_hash(payload),
                decision_status=new_status,
            )
            await db.audit_log.insert_one(audit_entry.model_dump())
            audit_logged = True
        except Exception as exc:
            logger.warning("Audit log write failed — MongoDB unavailable", error=str(exc))

    logger.info(
        "Decision action recorded",
        decision_id=decision_id,
        action=body.action,
        actor=body.actor_id,
    )

    return {
        "decision_id": decision_id,
        "status": new_status.value,
        "audit_logged": audit_logged,
    }


