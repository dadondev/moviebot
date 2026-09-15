"""Genre repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Genre


class GenreRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, genre_id: int) -> Genre | None:
        return await self.session.get(Genre, genre_id)

    async def get_by_slug(self, slug: str) -> Genre | None:
        result = await self.session.execute(select(Genre).where(Genre.slug == slug))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Genre]:
        result = await self.session.execute(select(Genre).order_by(Genre.name))
        return list(result.scalars().all())

    async def create(self, name: str, slug: str) -> Genre:
        genre = Genre(name=name, slug=slug)
        self.session.add(genre)
        await self.session.flush()
        return genre

    async def delete(self, genre: Genre) -> None:
        await self.session.delete(genre)
        await self.session.flush()
