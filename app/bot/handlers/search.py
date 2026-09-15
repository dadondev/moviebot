"""Search handlers."""

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot.states.states import SearchStates
from app.database.database import async_session_factory
from app.services.search_service import SearchService

router = Router(name="search")


async def start_search(message: Message) -> None:
    await message.answer("🔎 Kino nomini yozing:")
    await message.state.set_state(SearchStates.waiting_for_query)


@router.message(SearchStates.waiting_for_query)
async def process_search(message: Message, state: FSMContext) -> None:
    query = message.text.strip()
    if not query:
        await message.answer("❌ Kino nomini yozing.")
        return

    async with async_session_factory() as session:
        search_service = SearchService(session)
        results = await search_service.search(query, limit=10)

    await state.clear()

    if not results:
        await message.answer("❌ Hech narsa topilmadi. Boshqa nom bilan urinib ko‘ring.")
        return

    text = "🔎 Natijalar:\n\n"
    rows = []
    for movie in results:
        year = movie.year if movie.year else "Noma'lum"
        imdb = movie.imdb_rating if movie.imdb_rating else "-"
        text += f"🎬 {movie.title}\n📅 {year} | ⭐ {imdb}\n\n"
        rows.append(
            [InlineKeyboardButton(text=f"🎬 {movie.title}", callback_data=f"movie:{movie.id}")]
        )
    rows.append([InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="main_menu")])
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
