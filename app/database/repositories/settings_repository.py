"""Settings repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Setting


class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, key: str) -> str | None:
        result = await self.session.execute(
            select(Setting).where(Setting.key == key)
        )
        setting = result.scalar_one_or_none()
        return setting.value if setting else None

    async def set(self, key: str, value: str) -> Setting:
        result = await self.session.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()
        if setting is None:
            setting = Setting(key=key, value=value)
            self.session.add(setting)
        else:
            setting.value = value
        await self.session.flush()
        return setting

    async def get_bool(self, key: str, default: bool = False) -> bool:
        value = await self.get(key)
        if value is None:
            return default
        return value.lower() in {"1", "true", "yes", "on"}

    async def set_bool(self, key: str, value: bool) -> None:
        await self.set(key, "1" if value else "0")
