"""Initial migration: create all tables.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="uz"),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_active_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "genres",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_genres_slug", "genres", ["slug"])

    op.create_table(
        "movies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("original_title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("poster_file_id", sa.String(length=512), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("country", sa.String(length=255), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("imdb_rating", sa.Float(), nullable=True),
        sa.Column("age_rating", sa.String(length=10), nullable=True),
        sa.Column("trailer_url", sa.String(length=512), nullable=True),
        sa.Column("views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_movies_code", "movies", ["code"])
    op.create_index("ix_movies_title", "movies", ["title"])
    op.create_index("ix_movies_year", "movies", ["year"])
    op.create_index("ix_movies_views", "movies", ["views"])
    op.create_index("ix_movies_created_at", "movies", ["created_at"])

    op.create_table(
        "movie_genres",
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("genre_id", sa.Integer(), sa.ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "movie_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_chat_id", sa.BigInteger(), nullable=False),
        sa.Column("storage_message_id", sa.BigInteger(), nullable=False),
        sa.Column("telegram_file_id", sa.String(length=512), nullable=False),
        sa.Column("telegram_file_unique_id", sa.String(length=512), nullable=False),
        sa.Column("quality", sa.String(length=20), nullable=True),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_movie_files_movie_id", "movie_files", ["movie_id"])

    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "movie_id", name="uq_favorite"),
    )
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"])
    op.create_index("ix_favorites_movie_id", "favorites", ["movie_id"])

    op.create_table(
        "ratings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "movie_id", name="uq_rating"),
    )
    op.create_index("ix_ratings_user_id", "ratings", ["user_id"])
    op.create_index("ix_ratings_movie_id", "ratings", ["movie_id"])

    op.create_table(
        "movie_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movie_title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_movie_requests_user_id", "movie_requests", ["user_id"])
    op.create_index("ix_movie_requests_status", "movie_requests", ["status"])

    op.create_table(
        "required_channels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("invite_url", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("channel_id"),
    )

    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.String(length=512), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_settings_key", "settings", ["key"])


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_table("required_channels")
    op.drop_table("movie_requests")
    op.drop_table("ratings")
    op.drop_table("favorites")
    op.drop_table("movie_files")
    op.drop_table("movie_genres")
    op.drop_table("movies")
    op.drop_table("genres")
    op.drop_table("users")