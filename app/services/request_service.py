"""Movie request service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import MovieRequest
from app.database.repositories import MovieRequestRepository


class RequestService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = MovieRequestRepository(session)

    async def create(self, user_id: int, movie_title: str) -> MovieRequest:
        return await self.repo.create(user_id, movie_title)

    async def list_pending(self, limit: int = 50) -> list[MovieRequest]:
        return await self.repo.list_by_status("pending", limit)

    async def count_pending(self) -> int:
        return await self.repo.count_by_status("pending")

    async def set_status(self, request_id: int, status: str) -> None:
        await self.repo.set_status(request_id, status)
