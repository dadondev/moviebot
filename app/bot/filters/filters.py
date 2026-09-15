"""Custom filters."""

from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.config import settings


class AdminFilter(BaseFilter):
    """Filter that passes only for configured admin Telegram IDs."""

    async def __call__(self, message: Message) -> bool:
        if message.from_user is None:
            return False
        return settings.is_admin(message.from_user.id)


class IsMovieMessageFilter(BaseFilter):
    """Filter that passes for video or document messages that look like a movie."""

    async def __call__(self, message: Message) -> bool:
        return message.video is not None or message.document is not None
