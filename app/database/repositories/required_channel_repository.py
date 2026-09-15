"""RequiredChannel repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import RequiredChannel


class RequiredChannelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, channel_id: int) -> RequiredChannel | None:
        return await self.session.get(RequiredChannel, channel_id)

    async def get_by_channel_id(self, channel_id: int) -> RequiredChannel | None:
        result = await self.session.execute(
            select(RequiredChannel).where(RequiredChannel.channel_id == channel_id)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[RequiredChannel]:
        result = await self.session.execute(
            select(RequiredChannel)
            .where(RequiredChannel.is_active.is_(True))
            .order_by(RequiredChannel.id)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[RequiredChannel]:
        result = await self.session.execute(
            select(RequiredChannel).order_by(RequiredChannel.id)
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        channel_id: int,
        title: str,
        username: str | None = None,
        invite_url: str | None = None,
    ) -> RequiredChannel:
        channel = RequiredChannel(
            channel_id=channel_id,
            title=title,
            username=username,
            invite_url=invite_url,
            is_active=True,
        )
        self.session.add(channel)
        await self.session.flush()
        return channel

    async def update(self, channel: RequiredChannel, **values: object) -> RequiredChannel:
        for key, value in values.items():
            setattr(channel, key, value)
        await self.session.flush()
        return channel

    async def delete(self, channel: RequiredChannel) -> None:
        await self.session.delete(channel)
        await self.session.flush()
