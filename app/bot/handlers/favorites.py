"""Favorites handlers."""

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.database.database import async_session_factory
from app.services.movie_service import MovieService

router = Router(name="favorites")


async def show_favorites(message: Message) -> None:
    async with async_session_factory() as session:
        movie_service = MovieService(session)
        favorites = await movie_service.list_favorites(message.from_user.id)

    if not favorites:
        await message.answer("⭐ Sevimlilarim hozircha bo‘sh.")
        return

    text = "⭐ Sevimlilarim:\n\n"
    rows = []
    for movie in favorites:
        text += f"🎬 {movie.title}\n"
        rows.append(
            [InlineKeyboardButton(text=f"🎬 {movie.title}", callback_data=f"movie:{movie.id}")]
        )
    rows.append([InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="main_menu")])
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data.startswith("toggle_fav:"))
async def toggle_favorite(callback: CallbackQuery) -> None:
    movie_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    async with async_session_factory() as session:
        movie_service = MovieService(session)
        movie = await movie_service.get_by_id(movie_id)
        if movie is None:
            await callback.answer("❌ Kino topilmadi.", show_alert=True)
            return
        is_fav = await movie_service.is_favorite(user_id, movie_id)
        if is_fav:
            await movie_service.remove_favorite(user_id, movie_id)
            msg = "❌ Sevimlilardan olib tashlandi."
        else:
            await movie_service.add_favorite(user_id, movie_id)
            msg = "✅ Sevimlilarga qo‘shildi."
        await session.commit()

    await callback.answer(msg)
    # Refresh the movie info keyboard.
    async with async_session_factory() as session:
        movie_service = MovieService(session)
        is_fav = await movie_service.is_favorite(user_id, movie_id)
        from app.bot.keyboards.movie import movie_info_keyboard

        kb = movie_info_keyboard(movie, user_id, is_fav)
    await callback.message.edit_reply_markup(reply_markup=kb)
