"""Favorite repository."""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Favorite, Movie


class FavoriteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: int, movie_id: int) -> Favorite | None:
        result = await self.session.execute(
            select(Favorite).where(
                Favorite.user_id == user_id, Favorite.movie_id == movie_id
            )
        )
        return result.scalar_one_or_none()

    async def add(self, user_id: int, movie_id: int) -> Favorite:
        favorite = Favorite(user_id=user_id, movie_id=movie_id)
        self.session.add(favorite)
        await self.session.flush()
        return favorite

    async def remove(self, user_id: int, movie_id: int) -> None:
        await self.session.execute(
            delete(Favorite).where(
                Favorite.user_id == user_id, Favorite.movie_id == movie_id
            )
        )
        await self.session.flush()

    async def list_by_user(self, user_id: int) -> list[Movie]:
        result = await self.session.execute(
            select(Movie)
            .join(Favorite, Favorite.movie_id == Movie.id)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_for_movie(self, movie_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Favorite.id)).where(Favorite.movie_id == movie_id)
        )
        return int(result.scalar_one())

    async def most_favorited(self) -> Movie | None:
        result = await self.session.execute(
            select(Movie)
            .join(Favorite, Favorite.movie_id == Movie.id)
            .group_by(Movie.id)
            .order_by(func.count(Favorite.id).desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
