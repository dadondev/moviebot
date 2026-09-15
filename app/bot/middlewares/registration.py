"""User registration middleware.

Registers the user in the database on every incoming message/callback.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.database.database import async_session_factory
from app.database.repositories import UserRepository

logger = logging.getLogger(__name__)


class UserRegistrationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is not None and not user.is_bot:
            async with async_session_factory() as session:
                repo = UserRepository(session)
                db_user = await repo.get_or_create(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                )
                await repo.update_last_active(db_user.id)
                await session.commit()
                data["db_user"] = db_user
        return await handler(event, data)
