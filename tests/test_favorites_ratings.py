"""Favorites and ratings tests."""

import pytest

from app.database.repositories import (
    FavoriteRepository,
    MovieRepository,
    RatingRepository,
    UserRepository,
)


async def _create_user(session, telegram_id=1):
    repo = UserRepository(session)
    return await repo.create(telegram_id=telegram_id, username="user")


async def _create_movie(session, code=125):
    repo = MovieRepository(session)
    return await repo.create(
        code=code,
        title="Avatar",
        original_title="Avatar",
        description="desc",
        poster_file_id=None,
        year=2009,
        country="AQSh",
        duration=162,
        imdb_rating=7.8,
        age_rating="13+",
        trailer_url=None,
    )


@pytest.mark.asyncio
async def test_favorite_add(session):
    user = await _create_user(session)
    movie = await _create_movie(session)
    await session.commit()
    repo = FavoriteRepository(session)
    await repo.add(user.id, movie.id)
    await session.commit()
    assert await repo.get(user.id, movie.id) is not None


@pytest.mark.asyncio
async def test_favorite_remove(session):
    user = await _create_user(session)
    movie = await _create_movie(session)
    await session.commit()
    repo = FavoriteRepository(session)
    await repo.add(user.id, movie.id)
    await session.commit()
    await repo.remove(user.id, movie.id)
    await session.commit()
    assert await repo.get(user.id, movie.id) is None


@pytest.mark.asyncio
async def test_favorite_duplicate_protection(session):
    user = await _create_user(session)
    movie = await _create_movie(session)
    await session.commit()
    repo = FavoriteRepository(session)
    await repo.add(user.id, movie.id)
    await session.commit()
    # Adding again returns the same single row (unique constraint).
    existing = await repo.get(user.id, movie.id)
    assert existing is not None


@pytest.mark.asyncio
async def test_rating_create(session):
    user = await _create_user(session)
    movie = await _create_movie(session)
    await session.commit()
    repo = RatingRepository(session)
    await repo.upsert(user.id, movie.id, 5)
    await session.commit()
    assert (await repo.get(user.id, movie.id)).rating == 5


@pytest.mark.asyncio
async def test_rating_update(session):
    user = await _create_user(session)
    movie = await _create_movie(session)
    await session.commit()
    repo = RatingRepository(session)
    await repo.upsert(user.id, movie.id, 3)
    await session.commit()
    await repo.upsert(user.id, movie.id, 4)
    await session.commit()
    assert (await repo.get(user.id, movie.id)).rating == 4


@pytest.mark.asyncio
async def test_average_rating(session):
    user1 = await _create_user(session, 1)
    user2 = await _create_user(session, 2)
    movie = await _create_movie(session)
    await session.commit()
    repo = RatingRepository(session)
    await repo.upsert(user1.id, movie.id, 4)
    await repo.upsert(user2.id, movie.id, 5)
    await session.commit()
    avg = await repo.average_for_movie(movie.id)
    assert avg == 4.5
