"""Search service.

Keeps complex search queries out of Telegram handlers.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Movie
from app.database.repositories import MovieRepository


class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.movie_repo = MovieRepository(session)

    async def search(self, query: str, limit: int = 20) -> list[Movie]:
        query = query.strip()
        if not query:
            return []
        return await self.movie_repo.search(query, limit)
