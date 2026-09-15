"""Movie repository."""

from datetime import datetime

from sqlalchemy import String, cast, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Genre, Movie, MovieFile


class MovieRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, movie_id: int) -> Movie | None:
        return await self.session.get(Movie, movie_id)

    async def get_by_code(self, code: int) -> Movie | None:
        result = await self.session.execute(
            select(Movie)
            .where(Movie.code == code)
            .options(selectinload(Movie.genres), selectinload(Movie.files))
        )
        return result.scalar_one_or_none()

    async def get_by_code_without_relations(self, code: int) -> Movie | None:
        result = await self.session.execute(select(Movie).where(Movie.code == code))
        return result.scalar_one_or_none()

    async def code_exists(self, code: int, exclude_id: int | None = None) -> bool:
        stmt = select(Movie.id).where(Movie.code == code)
        if exclude_id is not None:
            stmt = stmt.where(Movie.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def next_code(self) -> int:
        """Return the next available movie code (max code + 1)."""
        result = await self.session.execute(select(func.max(Movie.code)))
        max_code = result.scalar_one()
        return (max_code or 0) + 1

    async def create(
        self,
        *,
        code: int,
        title: str,
        original_title: str | None,
        description: str | None,
        poster_file_id: str | None,
        year: int | None,
        country: str | None,
        duration: int | None,
        imdb_rating: float | None,
        age_rating: str | None,
        trailer_url: str | None,
        is_series: bool = False,
        genres: list[Genre] | None = None,
    ) -> Movie:
        movie = Movie(
            code=code,
            title=title,
            original_title=original_title,
            description=description,
            poster_file_id=poster_file_id,
            year=year,
            country=country,
            duration=duration,
            imdb_rating=imdb_rating,
            age_rating=age_rating,
            trailer_url=trailer_url,
            is_series=is_series,
            views=0,
        )
        if genres:
            movie.genres = genres
        self.session.add(movie)
        await self.session.flush()
        return movie

    async def update(self, movie: Movie, **values: object) -> Movie:
        for key, value in values.items():
            setattr(movie, key, value)
        await self.session.flush()
        return movie

    async def delete(self, movie: Movie) -> None:
        await self.session.delete(movie)
        await self.session.flush()

    async def increment_views(self, movie_id: int) -> None:
        await self.session.execute(
            update(Movie)
            .where(Movie.id == movie_id)
            .values(views=Movie.views + 1)
        )

    async def search(self, query: str, limit: int = 20) -> list[Movie]:
        """Case-insensitive partial search on title, original title and code."""
        pattern = f"%{query}%"
        stmt = (
            select(Movie)
            .where(
                Movie.title.ilike(pattern)
                | Movie.original_title.ilike(pattern)
                | cast(Movie.code, String).ilike(pattern)
            )
            .order_by(Movie.views.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_popular(self, limit: int = 10, offset: int = 0) -> list[Movie]:
        result = await self.session.execute(
            select(Movie)
            .order_by(Movie.views.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_new(self, limit: int = 10, offset: int = 0) -> list[Movie]:
        result = await self.session.execute(
            select(Movie)
            .order_by(Movie.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_genre(
        self, genre_id: int, limit: int = 10, offset: int = 0
    ) -> list[Movie]:
        result = await self.session.execute(
            select(Movie)
            .join(Movie.genres)
            .where(Genre.id == genre_id)
            .order_by(Movie.views.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count(Movie.id)))
        return int(result.scalar_one())

    async def count_created_since(self, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count(Movie.id)).where(Movie.created_at >= since)
        )
        return int(result.scalar_one())

    async def total_views(self) -> int:
        result = await self.session.execute(select(func.coalesce(func.sum(Movie.views), 0)))
        return int(result.scalar_one())

    async def most_viewed(self) -> Movie | None:
        result = await self.session.execute(
            select(Movie).order_by(Movie.views.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[Movie]:
        result = await self.session.execute(
            select(Movie).order_by(Movie.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def get_files(self, movie_id: int) -> list[MovieFile]:
        result = await self.session.execute(
            select(MovieFile).where(MovieFile.movie_id == movie_id)
        )
        return list(result.scalars().all())
