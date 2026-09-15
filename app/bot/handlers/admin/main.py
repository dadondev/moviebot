"""Admin main menu and authorization."""

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.filters.filters import AdminFilter
from app.bot.keyboards.admin import admin_menu_keyboard

router = Router(name="admin_main")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())

ADMIN_TEXT = "🛠 Admin panel\n\nKerakli bo‘limni tanlang:"


async def show_admin_menu(message: Message) -> None:
    await message.answer(ADMIN_TEXT, reply_markup=admin_menu_keyboard())


@router.callback_query(F.data == "admin_menu")
async def admin_menu_callback(callback: CallbackQuery) -> None:
    await callback.message.edit_text(ADMIN_TEXT, reply_markup=admin_menu_keyboard())
    await callback.answer()
