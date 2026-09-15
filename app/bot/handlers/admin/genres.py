"""Admin genres management."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.filters.filters import AdminFilter
from app.bot.keyboards.admin import admin_genres_keyboard
from app.bot.states.states import GenreAddStates
from app.database.database import async_session_factory
from app.database.repositories import GenreRepository

router = Router(name="admin_genres")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.callback_query(F.data == "admin_genres")
async def genres_menu(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        repo = GenreRepository(session)
        genres = await repo.list_all()
    await callback.message.edit_text(
        "🎭 Janrlar", reply_markup=admin_genres_keyboard(genres)
    )
    await callback.answer()


@router.callback_query(F.data == "admin_genre_add")
async def genre_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(GenreAddStates.waiting_for_name)
    await callback.message.edit_text("🎭 Yangi janr nomini kiriting:")
    await callback.answer()


@router.message(GenreAddStates.waiting_for_name)
async def genre_add_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not name:
        await message.answer("❌ Janr nomini kiriting.")
        return
    slug = name.lower().replace(" ", "-")
    async with async_session_factory() as session:
        repo = GenreRepository(session)
        if await repo.get_by_slug(slug) is not None:
            await message.answer("❌ Bu janr allaqachon mavjud.")
            return
        await repo.create(name, slug)
        await session.commit()
    await state.clear()
    await message.answer(f"✅ Janr qo‘shildi: {name}")


@router.callback_query(F.data.startswith("admin_genre_delete:"))
async def genre_delete(callback: CallbackQuery) -> None:
    genre_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        repo = GenreRepository(session)
        genre = await repo.get_by_id(genre_id)
        if genre is None:
            await callback.answer("❌ Janr topilmadi.", show_alert=True)
            return
        await repo.delete(genre)
        await session.commit()
    await callback.answer("🗑 Janr o‘chirildi.")
    await genres_menu(callback)
