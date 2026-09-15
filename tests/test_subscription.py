"""Subscription service tests (mocked Telegram API)."""

import pytest
from aiogram.enums import ChatMemberStatus

from app.database.repositories import RequiredChannelRepository, SettingsRepository
from app.services.subscription_service import SubscriptionService


class FakeRedis:
    """In-memory stand-in for the async Redis client."""

    def __init__(self):
        self.store: dict[str, str] = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        self.store[key] = value

    async def delete(self, *keys):
        for key in keys:
            self.store.pop(key, None)


@pytest.fixture(autouse=True)
def _mock_redis(monkeypatch):
    import app.services.subscription_service as sub_module

    monkeypatch.setattr(sub_module, "redis_client", FakeRedis())


class FakeBot:
    def __init__(self, memberships: dict[int, str]):
        self.memberships = memberships

    async def get_chat_member(self, chat_id, user_id):
        status = self.memberships.get(chat_id, ChatMemberStatus.LEFT)
        return type("Member", (), {"status": status})()


async def _add_channel(session, channel_id, title="Kino Olami"):
    repo = RequiredChannelRepository(session)
    return await repo.create(channel_id=channel_id, title=title)


@pytest.mark.asyncio
async def test_subscribed_user(session):
    await _add_channel(session, -1001)
    await session.commit()
    bot = FakeBot({-1001: ChatMemberStatus.MEMBER})
    service = SubscriptionService(bot, session)
    subscribed, missing = await service.check_all(1001)
    assert subscribed is True
    assert missing == []


@pytest.mark.asyncio
async def test_unsubscribed_user(session):
    await _add_channel(session, -1001)
    await session.commit()
    bot = FakeBot({-1001: ChatMemberStatus.LEFT})
    service = SubscriptionService(bot, session)
    subscribed, missing = await service.check_all(1002)
    assert subscribed is False
    assert len(missing) == 1


@pytest.mark.asyncio
async def test_multiple_channels(session):
    await _add_channel(session, -1001)
    await _add_channel(session, -1002)
    await _add_channel(session, -1003)
    await session.commit()
    bot = FakeBot({-1001: ChatMemberStatus.MEMBER, -1002: ChatMemberStatus.MEMBER})
    service = SubscriptionService(bot, session)
    subscribed, missing = await service.check_all(1003)
    assert subscribed is False
    assert len(missing) == 1
    assert missing[0].channel_id == -1003


@pytest.mark.asyncio
async def test_disabled_subscription_system(session):
    settings_repo = SettingsRepository(session)
    await settings_repo.set_bool("mandatory_subscription_enabled", False)
    await session.commit()
    service = SubscriptionService(FakeBot({}), session)
    assert await service.is_enabled() is False


@pytest.mark.asyncio
async def test_invalid_channel(session):
    await _add_channel(session, -1001)
    await session.commit()

    class FailingBot(FakeBot):
        async def get_chat_member(self, chat_id, user_id):
            from aiogram.exceptions import TelegramBadRequest

            raise TelegramBadRequest(method="getChatMember", message="chat not found")

    service = SubscriptionService(FailingBot({}), session)
    subscribed, missing = await service.check_all(1004)
    assert subscribed is False
    assert len(missing) == 1
