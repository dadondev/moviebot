"""Main menu and common keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardMarkup

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔎 Kino izlash"),
            KeyboardButton(text="🔢 Kod orqali izlash"),
        ],
        [
            KeyboardButton(text="🎭 Janrlar"),
            KeyboardButton(text="🔥 Mashhur kinolar"),
        ],
        [
            KeyboardButton(text="🆕 Yangi kinolar"),
            KeyboardButton(text="⭐ Sevimlilarim"),
        ],
        [KeyboardButton(text="📩 Kino so‘rash")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Kerakli bo'limni tanlang...",
)


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")]
        ]
    )


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="main_menu")]
        ]
    )
