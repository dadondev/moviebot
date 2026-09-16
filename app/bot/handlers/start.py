"""Start and main menu handlers."""

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.common import MAIN_MENU
from app.config import settings

router = Router(name="start")

WELCOME_TEXT = (
    "🎬 Kino Bot'ga xush kelibsiz!\n\n"
    "Bu bot orqali sevimli kinolaringizni\n"
    "tez va oson topishingiz mumkin."
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=MAIN_MENU)


@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: CallbackQuery) -> None:
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=MAIN_MENU)
    await callback.answer()


@router.message(F.text == "🔎 Kino izlash")
async def search_button(message: Message, state: FSMContext) -> None:
    from app.bot.handlers.search import start_search

    await start_search(message, state)


@router.message(F.text == "🔢 Kod orqali izlash")
async def code_button(message: Message) -> None:
    await message.answer("🔢 Kino kodini yuboring:\n\nMasalan: 125")


@router.message(F.text == "🎭 Janrlar")
async def genres_button(message: Message) -> None:
    from app.bot.handlers.genres import show_genres

    await show_genres(message)


@router.message(F.text == "🔥 Mashhur kinolar")
async def popular_button(message: Message) -> None:
    from app.bot.handlers.movie import show_popular

    await show_popular(message)


@router.message(F.text == "🆕 Yangi kinolar")
async def new_button(message: Message) -> None:
    from app.bot.handlers.movie import show_new

    await show_new(message)


@router.message(F.text == "⭐ Sevimlilarim")
async def favorites_button(message: Message) -> None:
    from app.bot.handlers.favorites import show_favorites

    await show_favorites(message)


@router.message(F.text == "📩 Kino so‘rash")
async def request_button(message: Message, state: FSMContext) -> None:
    from app.bot.handlers.requests import start_request

    await start_request(message, state)


@router.message(F.text == "/admin")
async def admin_command(message: Message) -> None:
    if settings.is_admin(message.from_user.id):
        from app.bot.handlers.admin.main import show_admin_menu

        await show_admin_menu(message)
    else:
        await message.answer("❌ Sizda admin huquqi yo‘q.")
