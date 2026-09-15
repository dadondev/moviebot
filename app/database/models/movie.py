"""Movie, Genre and MovieFile models."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base

# Association table for the many-to-many movie <-> genre relationship.
movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column(
        "movie_id",
        Integer,
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "genre_id",
        Integer,
        ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    movies: Mapped[list["Movie"]] = relationship(  # noqa: F821
        secondary=movie_genres, back_populates="genres"
    )


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    original_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    poster_file_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    country: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    imdb_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    age_rating: Mapped[str | None] = mapped_column(String(10), nullable=True)
    trailer_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    views: Mapped[int] = mapped_column(Integer, default=0, index=True)
    is_series: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    genres: Mapped[list[Genre]] = relationship(
        secondary=movie_genres, back_populates="movies"
    )
    files: Mapped[list["MovieFile"]] = relationship(  # noqa: F821
        back_populates="movie", cascade="all, delete-orphan"
    )
    favorites: Mapped[list["Favorite"]] = relationship(  # noqa: F821
        back_populates="movie", cascade="all, delete-orphan"
    )
    ratings: Mapped[list["Rating"]] = relationship(  # noqa: F821
        back_populates="movie", cascade="all, delete-orphan"
    )


class MovieFile(Base):
    __tablename__ = "movie_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), index=True
    )
    storage_chat_id: Mapped[int] = mapped_column(BigInteger)
    storage_message_id: Mapped[int] = mapped_column(BigInteger)
    telegram_file_id: Mapped[str] = mapped_column(String(512))
    telegram_file_unique_id: Mapped[str] = mapped_column(String(512))
    quality: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    episode_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    movie: Mapped[Movie] = relationship(back_populates="files")
