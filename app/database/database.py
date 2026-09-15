"""Database engine and session management (async SQLAlchemy)."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return the application engine, creating it lazily on first use."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the session factory, creating it lazily on first use."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


def async_session_factory() -> AsyncSession:
    """Return a new async session from the lazily-created factory."""
    return get_session_factory()()


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI-style dependency yielding an async session."""
    async with get_session_factory()() as session:
        yield session


async def init_models() -> None:
    """Create all tables (used for tests / non-migration setups)."""
    # Import models so they register on the metadata.
    from app.database import models  # noqa: F401

    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
