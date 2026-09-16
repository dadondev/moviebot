"""Fix user_id columns to BigInteger referencing users.telegram_id.

Revision ID: 0003_user_id_bigint
Revises: 0002_series
Create Date: 2026-09-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_user_id_bigint"
down_revision: str | None = "0002_series"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop old FKs referencing users.id.
    op.drop_constraint("favorites_user_id_fkey", "favorites", type_="foreignkey")
    op.drop_constraint("ratings_user_id_fkey", "ratings", type_="foreignkey")
    op.drop_constraint("movie_requests_user_id_fkey", "movie_requests", type_="foreignkey")

    # Change columns to BigInteger.
    op.alter_column("favorites", "user_id", type_=sa.BigInteger(), existing_type=sa.Integer())
    op.alter_column("ratings", "user_id", type_=sa.BigInteger(), existing_type=sa.Integer())
    op.alter_column("movie_requests", "user_id", type_=sa.BigInteger(), existing_type=sa.Integer())

    # Re-add FKs referencing users.telegram_id.
    op.create_foreign_key(
        "favorites_user_id_fkey", "favorites", "users", ["user_id"], ["telegram_id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "ratings_user_id_fkey", "ratings", "users", ["user_id"], ["telegram_id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "movie_requests_user_id_fkey",
        "movie_requests",
        "users",
        ["user_id"],
        ["telegram_id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("favorites_user_id_fkey", "favorites", type_="foreignkey")
    op.drop_constraint("ratings_user_id_fkey", "ratings", type_="foreignkey")
    op.drop_constraint("movie_requests_user_id_fkey", "movie_requests", type_="foreignkey")

    op.alter_column("favorites", "user_id", type_=sa.Integer(), existing_type=sa.BigInteger())
    op.alter_column("ratings", "user_id", type_=sa.Integer(), existing_type=sa.BigInteger())
    op.alter_column("movie_requests", "user_id", type_=sa.Integer(), existing_type=sa.BigInteger())

    op.create_foreign_key(
        "favorites_user_id_fkey", "favorites", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "ratings_user_id_fkey", "ratings", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "movie_requests_user_id_fkey",
        "movie_requests",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )