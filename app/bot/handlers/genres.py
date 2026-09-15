"""Genres handlers."""

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.database.database import async_session_factory
from app.services.movie_service import MovieService

router = Router(name="genres")


async def show_genres(message: Message) -> None:
    async with async_session_factory() as session:
        movie_service = MovieService(session)
        genres = await movie_service.get_genres()

    if not genres:
        await message.answer("❌ Janrlar hozircha mavjud emas.")
        return

    rows = []
    for genre in genres:
        rows.append(
            [InlineKeyboardButton(text=f"🎭 {genre.name}", callback_data=f"genre:{genre.id}:1")]
        )
    rows.append([InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="main_menu")])
    await message.answer("🎭 Janrlarni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data.startswith("genre:"))
async def genre_movies(callback: CallbackQuery) -> None:
    _, genre_id, page = callback.data.split(":")
    genre_id = int(genre_id)
    page = int(page)

    async with async_session_factory() as session:
        movie_service = MovieService(session)
        movies = await movie_service.get_by_genre(genre_id, limit=10, offset=(page - 1) * 10)

    if not movies:
        await callback.answer("❌ Bu janrda kinolar yo‘q.", show_alert=True)
        return

    text = "🎭 Janr bo‘yicha kinolar:\n\n"
    rows = []
    for movie in movies:
        text += f"🎬 {movie.title}\n"
        rows.append(
            [InlineKeyboardButton(text=f"🎬 {movie.title}", callback_data=f"movie:{movie.id}")]
        )
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await callback.answer()
