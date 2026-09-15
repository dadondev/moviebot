"""Pytest fixtures and configuration."""

import asyncio
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import models  # noqa: F401
from app.database.database import Base


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(engine) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory


@pytest_asyncio.fixture
async def session(session_factory) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session
