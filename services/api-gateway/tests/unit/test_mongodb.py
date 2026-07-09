"""SentinelArena — Unit Tests for MongoDB Atlas Integration & Schemas."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import User, UserRole, Venue, Zone
from app.seed import seed_mongodb


class TestMongoSchemas:
    """Tests for Pydantic v2 document schemas and ObjectId serialization."""

    def test_user_schema_creation(self) -> None:
        """Test User document validation and defaults."""
        user = User(
            id="user-123",
            email="test@sentinelarena.com",
            hashed_password="hashed_pw_string",
            display_name="Test User",
            role=UserRole.ORGANIZER,
        )
        assert user.email == "test@sentinelarena.com"
        assert user.role == UserRole.ORGANIZER
        assert user.is_active is True
        assert user.created_at is not None

    def test_venue_schema_creation(self) -> None:
        """Test Venue document validation."""
        venue = Venue(
            id="venue-1",
            name="Test Stadium",
            total_capacity=15000,
        )
        assert venue.name == "Test Stadium"
        assert venue.total_capacity == 15000

    def test_zone_schema_creation(self) -> None:
        """Test Zone document validation."""
        zone = Zone(
            id="zone-a",
            venue_id="venue-1",
            code="A",
            name="Main Stand",
            capacity=5000,
            floor_level=1,
        )
        assert zone.code == "A"
        assert zone.capacity == 5000


@pytest.mark.asyncio
class TestMongoDBSeeding:
    """Tests for automated MongoDB Atlas seeding."""

    async def test_seed_when_empty(self) -> None:
        """Test seeding populates collections when empty."""
        mock_db = MagicMock()

        # Setup mocks for empty collections
        for coll_name in ["users", "venues", "zones", "sop_documents", "pois", "edges"]:
            mock_coll = MagicMock()
            mock_coll.count_documents = AsyncMock(return_value=0)
            mock_coll.insert_one = AsyncMock()
            mock_coll.insert_many = AsyncMock()
            setattr(mock_db, coll_name, mock_coll)

        await seed_mongodb(mock_db)

        mock_db.users.insert_many.assert_called_once()
        mock_db.venues.insert_one.assert_called_once()
        mock_db.zones.insert_many.assert_called_once()
        mock_db.sop_documents.insert_many.assert_called_once()
        mock_db.pois.insert_many.assert_called_once()
        mock_db.edges.insert_many.assert_called_once()

    async def test_skip_seed_when_populated(self) -> None:
        """Test seeding skips insertion when collections already have documents."""
        mock_db = MagicMock()

        # Setup mocks for populated collections
        for coll_name in ["users", "venues", "zones", "sop_documents", "pois", "edges"]:
            mock_coll = MagicMock()
            mock_coll.count_documents = AsyncMock(return_value=5)
            mock_coll.insert_one = AsyncMock()
            mock_coll.insert_many = AsyncMock()
            setattr(mock_db, coll_name, mock_coll)

        await seed_mongodb(mock_db)

        mock_db.users.insert_many.assert_not_called()
        mock_db.venues.insert_one.assert_not_called()
        mock_db.zones.insert_many.assert_not_called()
