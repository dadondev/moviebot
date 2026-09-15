"""User repository."""

from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            language="uz",
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
    ) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = await self.create(telegram_id, username, first_name)
        return user

    async def update_last_active(self, user_id: int) -> None:
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_active_at=datetime.now(UTC))
        )

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return int(result.scalar_one())

    async def count_active(self, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count(User.id)).where(User.last_active_at >= since)
        )
        return int(result.scalar_one())

    async def count_created_since(self, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count(User.id)).where(User.created_at >= since)
        )
        return int(result.scalar_one())

    async def list_all_ids(self) -> list[int]:
        result = await self.session.execute(select(User.id))
        return [row[0] for row in result.all()]

    async def set_blocked(self, user_id: int, blocked: bool) -> None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(is_blocked=blocked)
        )
