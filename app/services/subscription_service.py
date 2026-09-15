"""Subscription service.

Checks user membership in mandatory channels, caches results in Redis,
and manages the pending movie code flow.
"""

import logging

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import RequiredChannel
from app.database.repositories import RequiredChannelRepository, SettingsRepository
from app.services.redis_service import redis_client

logger = logging.getLogger(__name__)

PENDING_MOVIE_PREFIX = "pending_movie:"
SUBSCRIPTION_PREFIX = "subscription:"

# Chat member statuses that count as "subscribed".
_SUBSCRIBED_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.CREATOR,
}


class SubscriptionService:
    def __init__(self, bot: Bot, session: AsyncSession) -> None:
        self.bot = bot
        self.session = session
        self.channel_repo = RequiredChannelRepository(session)
        self.settings_repo = SettingsRepository(session)

    async def is_enabled(self) -> bool:
        return await self.settings_repo.get_bool(
            "mandatory_subscription_enabled", default=False
        )

    async def get_active_channels(self) -> list[RequiredChannel]:
        return await self.channel_repo.list_active()

    async def check_membership(self, user_id: int, channel: RequiredChannel) -> bool:
        """Check a single channel membership with Redis caching."""
        cache_key = f"{SUBSCRIPTION_PREFIX}{user_id}:{channel.channel_id}"
        cached = await redis_client.get(cache_key)
        if cached is not None:
            return cached == "1"

        try:
            member = await self.bot.get_chat_member(
                chat_id=channel.channel_id, user_id=user_id
            )
            subscribed = member.status in _SUBSCRIBED_STATUSES
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            logger.warning(
                "Subscription check failed for user=%s channel=%s: %s",
                user_id,
                channel.channel_id,
                exc,
            )
            subscribed = False

        await redis_client.set(
            cache_key, "1" if subscribed else "0", ex=settings.subscription_cache_ttl
        )
        return subscribed

    async def check_all(self, user_id: int) -> tuple[bool, list[RequiredChannel]]:
        """Check all active channels. Returns (all_subscribed, missing_channels)."""
        channels = await self.get_active_channels()
        missing: list[RequiredChannel] = []
        for channel in channels:
            if not await self.check_membership(user_id, channel):
                missing.append(channel)
        return len(missing) == 0, missing

    # --- Pending movie code helpers ---

    async def set_pending_movie(self, user_id: int, code: int) -> None:
        key = f"{PENDING_MOVIE_PREFIX}{user_id}"
        await redis_client.set(key, str(code), ex=settings.pending_movie_ttl)

    async def get_pending_movie(self, user_id: int) -> int | None:
        key = f"{PENDING_MOVIE_PREFIX}{user_id}"
        value = await redis_client.get(key)
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    async def clear_pending_movie(self, user_id: int) -> None:
        key = f"{PENDING_MOVIE_PREFIX}{user_id}"
        await redis_client.delete(key)

    async def invalidate_membership_cache(self, user_id: int) -> None:
        """Clear cached membership for a user across all channels."""
        channels = await self.get_active_channels()
        keys = [
            f"{SUBSCRIPTION_PREFIX}{user_id}:{channel.channel_id}"
            for channel in channels
        ]
        if keys:
            await redis_client.delete(*keys)
