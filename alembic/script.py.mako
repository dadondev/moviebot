"""Alembic migration script template."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "{{ revision }}"
down_revision: str | None = "{{ down_revision }}"
branch_labels: str | Sequence[str] | None = "{{ branch_labels }}"
depends_on: str | Sequence[str] | None = "{{ depends_on }}"


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass