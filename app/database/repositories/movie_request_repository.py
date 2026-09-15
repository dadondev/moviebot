"""MovieRequest repository."""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import MovieRequest


class MovieRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_id: int, movie_title: str) -> MovieRequest:
        request = MovieRequest(user_id=user_id, movie_title=movie_title, status="pending")
        self.session.add(request)
        await self.session.flush()
        return request

    async def get_by_id(self, request_id: int) -> MovieRequest | None:
        return await self.session.get(MovieRequest, request_id)

    async def list_by_status(self, status: str, limit: int = 50) -> list[MovieRequest]:
        result = await self.session.execute(
            select(MovieRequest)
            .where(MovieRequest.status == status)
            .order_by(MovieRequest.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_status(self, status: str) -> int:
        result = await self.session.execute(
            select(func.count(MovieRequest.id)).where(MovieRequest.status == status)
        )
        return int(result.scalar_one())

    async def set_status(self, request_id: int, status: str) -> None:
        await self.session.execute(
            update(MovieRequest)
            .where(MovieRequest.id == request_id)
            .values(status=status)
        )
        await self.session.flush()
