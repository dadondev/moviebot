"""Rating service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories import RatingRepository


class RatingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = RatingRepository(session)

    async def rate(self, user_id: int, movie_id: int, rating: int) -> None:
        await self.repo.upsert(user_id, movie_id, rating)

    async def average(self, movie_id: int) -> float | None:
        return await self.repo.average_for_movie(movie_id)
