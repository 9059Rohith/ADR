"""SentinelArena API Gateway — Database Models.

SQLAlchemy 2.0 async models for the complete data layer:
users, venues, zones, POIs, edges, incidents, SOP documents, audit log, crowd readings.
"""

from __future__ import annotations

import enum
import hashlib
import json
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


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
# User Model
# ============================================================


class User(Base):
    """User account with role-based access control."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.FAN
    )
    locale: Mapped[Locale] = mapped_column(
        Enum(Locale), nullable=False, default=Locale.EN
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    incidents: Mapped[list["Incident"]] = relationship(back_populates="reporter")


# ============================================================
# Venue Models (Graph Structure)
# ============================================================


class Venue(Base):
    """Tournament venue."""

    __tablename__ = "venues"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    address: Mapped[Optional[str]] = mapped_column(String(500))
    total_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=10000)
    map_svg_url: Mapped[Optional[str]] = mapped_column(String(500))
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    zones: Mapped[list["Zone"]] = relationship(back_populates="venue", cascade="all, delete-orphan")
    pois: Mapped[list["POI"]] = relationship(back_populates="venue", cascade="all, delete-orphan")
    edges: Mapped[list["Edge"]] = relationship(back_populates="venue", cascade="all, delete-orphan")


class Zone(Base):
    """Venue zone for crowd density tracking."""

    __tablename__ = "zones"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    venue_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    floor_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    svg_path_id: Mapped[Optional[str]] = mapped_column(String(100))
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)

    # Relationships
    venue: Mapped["Venue"] = relationship(back_populates="zones")
    readings: Mapped[list["CrowdReading"]] = relationship(back_populates="zone")

    __table_args__ = (
        Index("ix_zones_venue_code", "venue_id", "code", unique=True),
    )


class POI(Base):
    """Point of Interest — graph node for navigation."""

    __tablename__ = "pois"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    venue_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False
    )
    zone_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("zones.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    poi_type: Mapped[str] = mapped_column(String(50), nullable=False)
    floor_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    x_coord: Mapped[float] = mapped_column(Float, nullable=False)
    y_coord: Mapped[float] = mapped_column(Float, nullable=False)
    is_accessible: Mapped[bool] = mapped_column(default=True)
    amenities: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)

    # Relationships
    venue: Mapped["Venue"] = relationship(back_populates="pois")

    __table_args__ = (
        Index("ix_pois_venue_type", "venue_id", "poi_type"),
    )


class Edge(Base):
    """Walkable path between POIs — graph edge for navigation."""

    __tablename__ = "edges"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    venue_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False
    )
    from_poi_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("pois.id", ondelete="CASCADE"), nullable=False
    )
    to_poi_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("pois.id", ondelete="CASCADE"), nullable=False
    )
    distance_meters: Mapped[float] = mapped_column(Float, nullable=False)
    accessibility: Mapped[EdgeAccessibility] = mapped_column(
        Enum(EdgeAccessibility), nullable=False, default=EdgeAccessibility.WALKWAY
    )
    is_bidirectional: Mapped[bool] = mapped_column(default=True)
    congestion_weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)

    # Relationships
    venue: Mapped["Venue"] = relationship(back_populates="edges")

    __table_args__ = (
        Index("ix_edges_from_to", "from_poi_id", "to_poi_id"),
    )


# ============================================================
# Incident Model
# ============================================================


class Incident(Base):
    """Incident report filed by volunteers/staff."""

    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    reporter_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )
    venue_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("venues.id"), nullable=False
    )
    zone_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("zones.id")
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity), nullable=False, default=IncidentSeverity.MEDIUM
    )
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus), nullable=False, default=IncidentStatus.REPORTED
    )
    original_locale: Mapped[Locale] = mapped_column(
        Enum(Locale), nullable=False, default=Locale.EN
    )
    ai_triage_summary: Mapped[Optional[str]] = mapped_column(Text)
    ai_suggested_actions: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    reporter: Mapped["User"] = relationship(back_populates="incidents")

    __table_args__ = (
        Index("ix_incidents_status_severity", "status", "severity"),
        Index("ix_incidents_venue_created", "venue_id", "created_at"),
    )


# ============================================================
# SOP Document (RAG Knowledge Base)
# ============================================================


class SOPDocument(Base):
    """Standard Operating Procedure document for RAG retrieval.

    Each row represents a chunk of an SOP document, embedded as a vector
    for similarity search via pgvector.
    """

    __tablename__ = "sop_documents"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    venue_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("venues.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    section: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(384))
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index(
            "ix_sop_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


# ============================================================
# Crowd Reading (Time-Series Data)
# ============================================================


class CrowdReading(Base):
    """Time-series crowd density reading per zone.

    Generated by the Crowd Simulator service (documented as simulated data).
    """

    __tablename__ = "crowd_readings"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    zone_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False
    )
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    density_pct: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    zone: Mapped["Zone"] = relationship(back_populates="readings")

    __table_args__ = (
        Index("ix_crowd_zone_time", "zone_id", "timestamp"),
    )


# ============================================================
# Audit Log (Immutable)
# ============================================================


class AuditLog(Base):
    """Immutable audit trail for organizer decisions.

    Records every approve/reject/broadcast action with actor,
    timestamp, and SHA-256 payload hash for integrity verification.
    """

    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    actor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    decision_status: Mapped[Optional[DecisionStatus]] = mapped_column(Enum(DecisionStatus))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_audit_actor_time", "actor_id", "created_at"),
        Index("ix_audit_resource", "resource_type", "resource_id"),
    )

    @staticmethod
    def compute_payload_hash(payload: dict[str, Any] | None) -> str:
        """Compute SHA-256 hash of the payload for integrity verification."""
        if payload is None:
            return hashlib.sha256(b"null").hexdigest()
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()
