"""Movie repository tests."""

import pytest

from app.database.repositories import GenreRepository, MovieRepository


async def _create_genre(session, name="Drama"):
    repo = GenreRepository(session)
    return await repo.create(name, name.lower())


async def _create_movie(session, code=125, title="Avatar", **kwargs):
    repo = MovieRepository(session)
    return await repo.create(
        code=code,
        title=title,
        original_title=kwargs.get("original_title", title),
        description=kwargs.get("description", "Test description"),
        poster_file_id=None,
        year=kwargs.get("year", 2009),
        country=kwargs.get("country", "AQSh"),
        duration=kwargs.get("duration", 162),
        imdb_rating=kwargs.get("imdb_rating", 7.8),
        age_rating=kwargs.get("age_rating", "13+"),
        trailer_url=None,
    )


@pytest.mark.asyncio
async def test_create_movie(session):
    movie = await _create_movie(session)
    await session.commit()
    assert movie.id is not None
    assert movie.code == 125
    assert movie.title == "Avatar"


@pytest.mark.asyncio
async def test_find_by_code(session):
    await _create_movie(session)
    await session.commit()
    repo = MovieRepository(session)
    found = await repo.get_by_code(125)
    assert found is not None
    assert found.title == "Avatar"


@pytest.mark.asyncio
async def test_find_by_code_not_found(session):
    repo = MovieRepository(session)
    assert await repo.get_by_code(999) is None


@pytest.mark.asyncio
async def test_search(session):
    await _create_movie(session, code=125, title="Avatar")
    await _create_movie(session, code=126, title="Avatar: The Way of Water")
    await session.commit()
    repo = MovieRepository(session)
    results = await repo.search("avatar")
    assert len(results) == 2


@pytest.mark.asyncio
async def test_update_movie(session):
    movie = await _create_movie(session)
    await session.commit()
    repo = MovieRepository(session)
    await repo.update(movie, title="Avatar 2")
    await session.commit()
    assert movie.title == "Avatar 2"


@pytest.mark.asyncio
async def test_delete_movie(session):
    movie = await _create_movie(session)
    await session.commit()
    repo = MovieRepository(session)
    await repo.delete(movie)
    await session.commit()
    assert await repo.get_by_code(125) is None


@pytest.mark.asyncio
async def test_code_exists(session):
    await _create_movie(session)
    await session.commit()
    repo = MovieRepository(session)
    assert await repo.code_exists(125) is True
    assert await repo.code_exists(999) is False


@pytest.mark.asyncio
async def test_increment_views(session):
    movie = await _create_movie(session)
    await session.commit()
    repo = MovieRepository(session)
    await repo.increment_views(movie.id)
    await session.commit()
    refreshed = await repo.get_by_id(movie.id)
    assert refreshed.views == 1
