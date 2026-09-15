"""Movie service.

High-level operations over movies, files, favorites and ratings.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Genre, Movie
from app.database.repositories import (
    FavoriteRepository,
    GenreRepository,
    MovieFileRepository,
    MovieRepository,
    RatingRepository,
)

logger = logging.getLogger(__name__)


class MovieService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.movie_repo = MovieRepository(session)
        self.genre_repo = GenreRepository(session)
        self.file_repo = MovieFileRepository(session)
        self.favorite_repo = FavoriteRepository(session)
        self.rating_repo = RatingRepository(session)

    async def get_by_code(self, code: int) -> Movie | None:
        return await self.movie_repo.get_by_code(code)

    async def get_by_id(self, movie_id: int) -> Movie | None:
        return await self.movie_repo.get_by_id(movie_id)

    async def search(self, query: str, limit: int = 20) -> list[Movie]:
        return await self.movie_repo.search(query, limit)

    async def get_popular(self, limit: int = 10, offset: int = 0) -> list[Movie]:
        return await self.movie_repo.get_popular(limit, offset)

    async def get_new(self, limit: int = 10, offset: int = 0) -> list[Movie]:
        return await self.movie_repo.get_new(limit, offset)

    async def get_by_genre(
        self, genre_id: int, limit: int = 10, offset: int = 0
    ) -> list[Movie]:
        return await self.movie_repo.get_by_genre(genre_id, limit, offset)

    async def increment_views(self, movie_id: int) -> None:
        await self.movie_repo.increment_views(movie_id)

    async def get_genres(self) -> list[Genre]:
        return await self.genre_repo.list_all()

    async def get_files(self, movie_id: int):
        return await self.file_repo.list_by_movie(movie_id)

    async def get_episodes(self, movie_id: int):
        return await self.file_repo.list_episodes(movie_id)

    async def next_episode_number(self, movie_id: int) -> int:
        return await self.file_repo.next_episode_number(movie_id)

    async def next_code(self) -> int:
        return await self.movie_repo.next_code()

    async def is_favorite(self, user_id: int, movie_id: int) -> bool:
        return await self.favorite_repo.get(user_id, movie_id) is not None

    async def add_favorite(self, user_id: int, movie_id: int) -> bool:
        if await self.favorite_repo.get(user_id, movie_id) is not None:
            return False
        await self.favorite_repo.add(user_id, movie_id)
        return True

    async def remove_favorite(self, user_id: int, movie_id: int) -> bool:
        if await self.favorite_repo.get(user_id, movie_id) is None:
            return False
        await self.favorite_repo.remove(user_id, movie_id)
        return True

    async def list_favorites(self, user_id: int) -> list[Movie]:
        return await self.favorite_repo.list_by_user(user_id)

    async def rate(self, user_id: int, movie_id: int, rating: int) -> None:
        await self.rating_repo.upsert(user_id, movie_id, rating)

    async def get_average_rating(self, movie_id: int) -> float | None:
        return await self.rating_repo.average_for_movie(movie_id)
