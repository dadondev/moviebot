"""Broadcast service.

Sends messages to all users with rate limiting and graceful handling of
blocked users.
"""

import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.repositories import UserRepository

logger = logging.getLogger(__name__)


class BroadcastService:
    def __init__(self, bot: Bot, session: AsyncSession) -> None:
        self.bot = bot
        self.session = session
        self.user_repo = UserRepository(session)

    async def broadcast(self, message: Message) -> dict[str, int]:
        """Send a copy of the given message to all users.

        Returns a summary dict with sent/failed counts.
        """
        user_ids = await self.user_repo.list_all_ids()
        sent = 0
        failed = 0
        blocked = 0

        for i in range(0, len(user_ids), settings.broadcast_batch_size):
            batch = user_ids[i : i + settings.broadcast_batch_size]
            for user_id in batch:
                try:
                    await self.bot.copy_message(
                        chat_id=user_id,
                        from_chat_id=message.chat.id,
                        message_id=message.message_id,
                    )
                    sent += 1
                except TelegramForbiddenError:
                    blocked += 1
                    failed += 1
                except TelegramRetryAfter as exc:
                    await asyncio.sleep(exc.retry_after)
                    try:
                        await self.bot.copy_message(
                            chat_id=user_id,
                            from_chat_id=message.chat.id,
                            message_id=message.message_id,
                        )
                        sent += 1
                    except Exception:
                        failed += 1
                except TelegramBadRequest:
                    failed += 1
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Broadcast failed for user %s: %s", user_id, exc)
                    failed += 1
            await asyncio.sleep(settings.broadcast_delay)

        return {"sent": sent, "failed": failed, "blocked": blocked}
