"""Rate limiting middleware."""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.services.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, rate_limiter: RateLimiter) -> None:
        self.rate_limiter = rate_limiter

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is not None:
            allowed = await self.rate_limiter.check(f"user:{user.id}")
            if not allowed:
                if isinstance(event, Message):
                    await event.answer("⚠️ Juda ko‘p so‘rov yubordingiz. Biroz kuting.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("Juda tez, biroz kuting.", show_alert=True)
                return None
        return await handler(event, data)
