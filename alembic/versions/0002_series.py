"""Add series support: movies.is_series and movie_files.episode_number.

Revision ID: 0002_series
Revises: 0001_initial
Create Date: 2026-09-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_series"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "movies",
        sa.Column("is_series", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_movies_is_series", "movies", ["is_series"])
    op.add_column(
        "movie_files",
        sa.Column("episode_number", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("movie_files", "episode_number")
    op.drop_index("ix_movies_is_series", table_name="movies")
    op.drop_column("movies", "is_series")