"""Rating handlers."""

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.keyboards.subscription import rating_keyboard
from app.database.database import async_session_factory
from app.services.movie_service import MovieService

router = Router(name="rating")


@router.callback_query(F.data.startswith("rate:"))
async def show_rating(callback: CallbackQuery) -> None:
    movie_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        "⭐ Filmni baholang:", reply_markup=rating_keyboard(movie_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rate_set:"))
async def set_rating(callback: CallbackQuery) -> None:
    _, movie_id, value = callback.data.split(":")
    movie_id = int(movie_id)
    rating = int(value)

    async with async_session_factory() as session:
        movie_service = MovieService(session)
        await movie_service.rate(callback.from_user.id, movie_id, rating)
        await session.commit()

    await callback.answer(f"✅ Bahoyingiz: {rating} ⭐")
    await callback.message.edit_text(f"✅ Filmga {rating} ⭐ baho berdingiz. Rahmat!")
