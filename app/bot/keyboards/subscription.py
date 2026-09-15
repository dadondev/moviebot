"""Subscription and rating keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.database.models import RequiredChannel


def subscription_keyboard(channels: list[RequiredChannel]) -> InlineKeyboardMarkup:
    rows = []
    for channel in channels:
        url = channel.invite_url
        if not url and channel.username:
            url = f"https://t.me/{channel.username.lstrip('@')}"
        if url:
            rows.append(
                [InlineKeyboardButton(text=f"📢 {channel.title}", url=url)]
            )
        else:
            rows.append(
                [InlineKeyboardButton(text=f"📢 {channel.title}", callback_data="noop")]
            )
    rows.append(
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def rating_keyboard(movie_id: int) -> InlineKeyboardMarkup:
    rows = []
    for star in range(1, 6):
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{star} ⭐", callback_data=f"rate_set:{movie_id}:{star}"
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"movie:{movie_id}")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
