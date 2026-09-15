"""MovieFile repository."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import MovieFile


class MovieFileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, file_id: int) -> MovieFile | None:
        return await self.session.get(MovieFile, file_id)

    async def create(
        self,
        *,
        movie_id: int,
        storage_chat_id: int,
        storage_message_id: int,
        telegram_file_id: str,
        telegram_file_unique_id: str,
        quality: str | None = None,
        language: str | None = None,
        episode_number: int | None = None,
    ) -> MovieFile:
        movie_file = MovieFile(
            movie_id=movie_id,
            storage_chat_id=storage_chat_id,
            storage_message_id=storage_message_id,
            telegram_file_id=telegram_file_id,
            telegram_file_unique_id=telegram_file_unique_id,
            quality=quality,
            language=language,
            episode_number=episode_number,
        )
        self.session.add(movie_file)
        await self.session.flush()
        return movie_file

    async def list_by_movie(self, movie_id: int) -> list[MovieFile]:
        result = await self.session.execute(
            select(MovieFile).where(MovieFile.movie_id == movie_id)
        )
        return list(result.scalars().all())

    async def list_episodes(self, movie_id: int) -> list[MovieFile]:
        """Return episode files ordered by episode number."""
        result = await self.session.execute(
            select(MovieFile)
            .where(
                MovieFile.movie_id == movie_id,
                MovieFile.episode_number.is_not(None),
            )
            .order_by(MovieFile.episode_number)
        )
        return list(result.scalars().all())

    async def next_episode_number(self, movie_id: int) -> int:
        """Return the next episode number for a series (max + 1)."""
        result = await self.session.execute(
            select(func.max(MovieFile.episode_number)).where(
                MovieFile.movie_id == movie_id
            )
        )
        max_episode = result.scalar_one()
        return (max_episode or 0) + 1

    async def delete(self, movie_file: MovieFile) -> None:
        await self.session.delete(movie_file)
        await self.session.flush()
