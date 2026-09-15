"""Storage service.

Responsible for copying movies to/from the private storage channel using
Telegram's copyMessage API. The storage channel is never exposed to users.
"""

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import Message

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Handles Telegram copy operations for the private storage channel."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.storage_chat_id = settings.storage_channel_id

    async def copy_to_storage(self, message: Message) -> tuple[int, int]:
        """Copy a message to the private storage channel.

        Returns (storage_chat_id, storage_message_id).
        """
        copied = await self.bot.copy_message(
            chat_id=self.storage_chat_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
        return self.storage_chat_id, copied.message_id

    async def copy_to_storage_by_ids(
        self, from_chat_id: int, message_id: int
    ) -> tuple[int, int]:
        """Copy a message (identified by chat + message id) to the storage channel."""
        copied = await self.bot.copy_message(
            chat_id=self.storage_chat_id,
            from_chat_id=from_chat_id,
            message_id=message_id,
        )
        return self.storage_chat_id, copied.message_id

    async def copy_to_user(
        self, chat_id: int, storage_chat_id: int, storage_message_id: int
    ) -> Message:
        """Copy a stored movie message to a user.

        Returns the resulting message in the user's chat.
        """
        return await self.bot.copy_message(
            chat_id=chat_id,
            from_chat_id=storage_chat_id,
            message_id=storage_message_id,
        )

    async def delete_storage_message(
        self, storage_chat_id: int, storage_message_id: int
    ) -> bool:
        """Delete a message from the storage channel. Returns success."""
        try:
            await self.bot.delete_message(
                chat_id=storage_chat_id, message_id=storage_message_id
            )
            return True
        except (TelegramBadRequest, TelegramForbiddenError):
            logger.warning(
                "Could not delete storage message chat=%s msg=%s",
                storage_chat_id,
                storage_message_id,
            )
            return False

    async def validate_storage_channel(self) -> bool:
        """Check the bot can access the storage channel."""
        try:
            await self.bot.get_chat(self.storage_chat_id)
            return True
        except (TelegramBadRequest, TelegramForbiddenError):
            logger.error("Bot cannot access storage channel %s", self.storage_chat_id)
            return False
