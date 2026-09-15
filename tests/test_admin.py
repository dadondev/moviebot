"""Admin authorization tests."""

from app.config import Settings


def test_authorized_admin():
    settings = Settings(
        bot_token="test",
        admin_ids="123,456",
        storage_channel_id=-100,
    )
    assert settings.is_admin(123) is True
    assert settings.is_admin(456) is True


def test_unauthorized_user():
    settings = Settings(
        bot_token="test",
        admin_ids="123,456",
        storage_channel_id=-100,
    )
    assert settings.is_admin(999) is False


def test_empty_admin_list():
    settings = Settings(
        bot_token="test",
        admin_ids="",
        storage_channel_id=-100,
    )
    assert settings.admin_id_list == []
    assert settings.is_admin(1) is False
