"""SentinelArena API Gateway — Database Connection.

Async MongoDB Atlas client using Motor (motor.motor_asyncio).
Supports connection pooling, health verification, index creation,
and graceful fallback when MongoDB is not available.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config import get_settings

logger = logging.getLogger(__name__)

# Singleton client instance
_client: AsyncIOMotorClient[Any] | None = None


def get_client() -> AsyncIOMotorClient[Any]:
    """Get or create the Motor client singleton."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncIOMotorClient(
            settings.mongodb_uri,
            maxPoolSize=50,
            minPoolSize=5,
            serverSelectionTimeoutMS=5000,
            uuidRepresentation="standard",
        )
    return _client


async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase[Any], None]:
    """FastAPI dependency that yields an async MongoDB database instance.

    Usage::

        @router.get("/items")
        async def get_items(db: AsyncIOMotorDatabase = Depends(get_db)):
            ...
    """
    client = get_client()
    settings = get_settings()
    db = client[settings.mongodb_db_name]
    yield db


async def init_db() -> None:
    """Initialize database: verify MongoDB Atlas connection and create indexes.

    Raises ConnectionFailure or ServerSelectionTimeoutError if DB is unreachable.
    The caller (lifespan) handles this gracefully.
    """
    client = get_client()
    settings = get_settings()
    db = client[settings.mongodb_db_name]

    # Verify connection
    await client.admin.command("ping")
    logger.info("MongoDB Atlas connection verified successfully")

    # Create indexes across collections for top 1% performance
    try:
        # Users collection
        await db.users.create_index("email", unique=True)

        # Venues and Zones
        await db.zones.create_index([("venue_id", 1), ("code", 1)], unique=True)
        await db.pois.create_index([("venue_id", 1), ("poi_type", 1)])
        await db.edges.create_index([("from_poi_id", 1), ("to_poi_id", 1)])

        # Incidents
        await db.incidents.create_index([("status", 1), ("severity", 1)])
        await db.incidents.create_index([("venue_id", 1), ("created_at", -1)])

        # SOP Documents (RAG Knowledge Base)
        await db.sop_documents.create_index([("venue_id", 1)])

        # Decisions
        await db.decisions.create_index([("status", 1), ("created_at", -1)])

        # Time-Series & Audit Log
        await db.crowd_readings.create_index([("zone_id", 1), ("timestamp", -1)])
        await db.audit_log.create_index([("actor_id", 1), ("created_at", -1)])
        await db.audit_log.create_index([("resource_type", 1), ("resource_id", 1)])

        logger.info("MongoDB indexes created/verified successfully")
    except Exception as exc:
        logger.warning("Error creating MongoDB indexes", error=str(exc))


async def close_db() -> None:
    """Close the MongoDB Motor client connection pool."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB connection pool closed")

