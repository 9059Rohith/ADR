"""SentinelArena API Gateway — Database Models.

Pydantic v2 document schemas for MongoDB Atlas:
users, venues, zones, POIs, edges, incidents, SOP documents, audit log, crowd readings, decisions.
"""

from __future__ import annotations

import enum
import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Enums
# ============================================================


class UserRole(str, enum.Enum):
    """User roles for RBAC."""

    FAN = "fan"
    VOLUNTEER = "volunteer"
    ORGANIZER = "organizer"
    ADMIN = "admin"


class Locale(str, enum.Enum):
    """Supported locales for multi-language support."""

    EN = "en"
    HI = "hi"
    TA = "ta"
    TE = "te"
    ES = "es"


class ZoneSeverity(str, enum.Enum):
    """Crowd density severity levels."""

    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class IncidentStatus(str, enum.Enum):
    """Incident lifecycle status."""

    REPORTED = "reported"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSeverity(str, enum.Enum):
    """Incident severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionStatus(str, enum.Enum):
    """Decision approval status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"


class EdgeAccessibility(str, enum.Enum):
    """Edge accessibility type."""

    WALKWAY = "walkway"
    STAIRS = "stairs"
    RAMP = "ramp"
    ELEVATOR = "elevator"
    ESCALATOR = "escalator"


# ============================================================
# Base MongoDB Document Model
# ============================================================


class MongoDoc(BaseModel):
    """Base schema for all MongoDB documents."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        from_attributes=True,
    )


# ============================================================
# User Model
# ============================================================


class User(MongoDoc):
    """User account with role-based access control."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    email: str
    hashed_password: str
    display_name: str
    role: UserRole = UserRole.FAN
    locale: Locale = Locale.EN
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================
# Venue Models (Graph Structure)
# ============================================================


class Venue(MongoDoc):
    """Tournament venue."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str | None = None
    address: str | None = None
    total_capacity: int = 10000
    map_svg_url: str | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Zone(MongoDoc):
    """Venue zone for crowd density tracking."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    venue_id: str
    name: str
    code: str
    capacity: int
    floor_level: int = 0
    svg_path_id: str | None = None
    metadata_json: dict[str, Any] | None = None


class POI(MongoDoc):
    """Point of Interest — graph node for navigation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    venue_id: str
    zone_id: str | None = None
    name: str
    poi_type: str
    floor_level: int = 0
    x_coord: float
    y_coord: float
    is_accessible: bool = True
    amenities: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None


class Edge(MongoDoc):
    """Walkable path between POIs — graph edge for navigation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    venue_id: str
    from_poi_id: str
    to_poi_id: str
    distance_meters: float
    accessibility: EdgeAccessibility = EdgeAccessibility.WALKWAY
    is_bidirectional: bool = True
    congestion_weight: float = 1.0
    metadata_json: dict[str, Any] | None = None


# ============================================================
# Incident Model
# ============================================================


class Incident(MongoDoc):
    """Incident report filed by volunteers/staff."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    reporter_id: str
    venue_id: str = "venue-demo"
    zone_id: str | None = None
    title: str
    description: str
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    status: IncidentStatus = IncidentStatus.REPORTED
    original_locale: Locale = Locale.EN
    ai_triage_summary: str | None = None
    ai_suggested_actions: list[str] | dict[str, Any] | None = None
    photo_url: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================
# SOP Document (RAG Knowledge Base)
# ============================================================


class SOPDocument(MongoDoc):
    """Standard Operating Procedure document for RAG retrieval.

    Each document represents a chunk of an SOP document, stored with optional
    vector embedding for similarity search.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    venue_id: str = "venue-demo"
    title: str
    section: str
    content: str
    embedding: list[float] | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================
# Crowd Reading (Time-Series Data)
# ============================================================


class CrowdReading(MongoDoc):
    """Time-series crowd density reading per zone."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    zone_id: str
    count: int
    density_pct: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================
# Audit Log & Decision Models
# ============================================================


class AuditLog(MongoDoc):
    """Immutable audit trail for organizer decisions.

    Records every approve/reject/broadcast action with actor,
    timestamp, and SHA-256 payload hash for integrity verification.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    payload: dict[str, Any] | None = None
    payload_hash: str
    decision_status: DecisionStatus | None = None
    ip_address: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def compute_payload_hash(payload: dict[str, Any] | None) -> str:
        """Compute SHA-256 hash of the payload for integrity verification."""
        if payload is None:
            return hashlib.sha256(b"null").hexdigest()
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


class DecisionDoc(MongoDoc):
    """AI-generated decision recommendation stored in MongoDB."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    query: str
    recommendation: str
    sources: list[str] = []
    status: DecisionStatus = DecisionStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

