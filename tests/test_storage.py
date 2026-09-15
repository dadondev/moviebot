"""Storage service tests (mocked Telegram API)."""

import pytest

from app.services.storage_service import StorageService


class FakeBot:
    def __init__(self):
        self.copied = []

    async def copy_message(self, chat_id, from_chat_id, message_id):
        self.copied.append((chat_id, from_chat_id, message_id))
        return type("Copied", (), {"message_id": 874})()

    async def delete_message(self, chat_id, message_id):
        return True

    async def get_chat(self, chat_id):
        return type("Chat", (), {"id": chat_id})()


@pytest.mark.asyncio
async def test_storage_message_creation():
    bot = FakeBot()
    service = StorageService(bot)
    # Override storage chat id for test.
    service.storage_chat_id = -1001234567890
    chat_id, msg_id = await service.copy_to_storage_by_ids(123, 456)
    assert chat_id == -1001234567890
    assert msg_id == 874
    assert bot.copied == [(-1001234567890, 123, 456)]


@pytest.mark.asyncio
async def test_storage_message_lookup():
    bot = FakeBot()
    service = StorageService(bot)
    service.storage_chat_id = -1001234567890
    result = await service.copy_to_user(999, -1001234567890, 874)
    assert result.message_id == 874


@pytest.mark.asyncio
async def test_delivery_failure():
    class FailingBot(FakeBot):
        async def copy_message(self, chat_id, from_chat_id, message_id):
            raise RuntimeError("message not found")

    bot = FailingBot()
    service = StorageService(bot)
    with pytest.raises(RuntimeError):
        await service.copy_to_user(999, -1001234567890, 99999)


@pytest.mark.asyncio
async def test_missing_storage_message():
    class MissingBot(FakeBot):
        async def copy_message(self, chat_id, from_chat_id, message_id):
            raise RuntimeError("message not found")

    bot = MissingBot()
    service = StorageService(bot)
    with pytest.raises(RuntimeError):
        await service.copy_to_user(999, -1001234567890, 99999)
