"""SentinelArena API Gateway — Database Connection.

Async SQLAlchemy 2.0 engine and session factory using asyncpg.
Supports graceful fallback when PostgreSQL is not available.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


def _create_engine():
    """Create the async engine from settings."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.log_level == "debug",
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


engine = _create_engine()

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    Usage::

        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database: create pgvector extension and all tables.

    Raises ConnectionRefusedError or similar if DB is unreachable.
    The caller (lifespan) handles this gracefully.
    """
    from sqlalchemy import text

    async with engine.begin() as conn:
        # pgvector extension — only if available
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception:
            logger.warning("pgvector extension not available — embeddings disabled")
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose of the database engine connection pool."""
    await engine.dispose()
