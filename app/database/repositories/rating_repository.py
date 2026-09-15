"""Rating repository."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Movie, Rating


class RatingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: int, movie_id: int) -> Rating | None:
        result = await self.session.execute(
            select(Rating).where(
                Rating.user_id == user_id, Rating.movie_id == movie_id
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: int, movie_id: int, rating: int) -> Rating:
        existing = await self.get(user_id, movie_id)
        if existing is not None:
            existing.rating = rating
            await self.session.flush()
            return existing
        new_rating = Rating(user_id=user_id, movie_id=movie_id, rating=rating)
        self.session.add(new_rating)
        await self.session.flush()
        return new_rating

    async def average_for_movie(self, movie_id: int) -> float | None:
        result = await self.session.execute(
            select(func.avg(Rating.rating)).where(Rating.movie_id == movie_id)
        )
        value = result.scalar_one()
        return float(value) if value is not None else None

    async def count_for_movie(self, movie_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Rating.id)).where(Rating.movie_id == movie_id)
        )
        return int(result.scalar_one())

    async def most_rated(self) -> Movie | None:
        result = await self.session.execute(
            select(Movie)
            .join(Rating, Rating.movie_id == Movie.id)
            .group_by(Movie.id)
            .order_by(func.count(Rating.id).desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
