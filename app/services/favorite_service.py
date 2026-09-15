"""Favorite service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Movie
from app.database.repositories import FavoriteRepository


class FavoriteService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = FavoriteRepository(session)

    async def add(self, user_id: int, movie_id: int) -> bool:
        if await self.repo.get(user_id, movie_id) is not None:
            return False
        await self.repo.add(user_id, movie_id)
        return True

    async def remove(self, user_id: int, movie_id: int) -> bool:
        if await self.repo.get(user_id, movie_id) is None:
            return False
        await self.repo.remove(user_id, movie_id)
        return True

    async def list_for_user(self, user_id: int) -> list[Movie]:
        return await self.repo.list_by_user(user_id)
