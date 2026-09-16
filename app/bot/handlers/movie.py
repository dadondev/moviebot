"""Movie handlers: code detection, info display, delivery, popular/new."""

import logging
import re

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from app.bot.keyboards.movie import (
    movie_files_keyboard,
    movie_info_keyboard,
    pagination_keyboard,
    series_episodes_keyboard,
)
from app.bot.keyboards.subscription import subscription_keyboard
from app.config import settings
from app.database.database import async_session_factory
from app.database.models import Movie
from app.services.movie_service import MovieService
from app.services.storage_service import StorageService
from app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

router = Router(name="movie")

PAGE_SIZE = 10

CODE_PATTERN = re.compile(r"^\d+$")


def format_movie_info(movie: Movie) -> str:
    lines = [f"🎬 {movie.title}"]
    if movie.year:
        lines.append(f"📅 Yil: {movie.year}")
    if movie.genres:
        lines.append(f"🎭 Janr: {', '.join(g.name for g in movie.genres)}")
    if movie.country:
        lines.append(f"🌍 Davlat: {movie.country}")
    if movie.duration:
        lines.append(f"⏱ Davomiyligi: {movie.duration} daqiqa")
    if movie.imdb_rating:
        lines.append(f"⭐ IMDb: {movie.imdb_rating}")
    if movie.age_rating:
        lines.append(f"🔞 Yosh chegarasi: {movie.age_rating}")
    if movie.description:
        lines.append(f"\n📝 Tavsif:\n{movie.description}")
    return "\n".join(lines)


async def _handle_movie_code(message: Message, code: int) -> None:
    async with async_session_factory() as session:
        movie_service = MovieService(session)
        movie = await movie_service.get_by_code(code)
        if movie is None:
            await message.answer(
                "❌ Bunday kino topilmadi.\n\n🔢 Kino kodini tekshirib, qayta yuboring."
            )
            return

        bot = message.bot
        sub_service = SubscriptionService(bot, session)
        enabled = await sub_service.is_enabled()

        if enabled:
            subscribed, missing = await sub_service.check_all(message.from_user.id)
            if not subscribed:
                await sub_service.set_pending_movie(message.from_user.id, code)
                text = (
                    "📢 Filmni olish uchun quyidagi kanallarga\n"
                    "obuna bo‘ling:\n\n"
                )
                for i, ch in enumerate(missing, 1):
                    text += f"{i}️⃣ 📢 {ch.title}\n"
                text += (
                    "\nObuna bo‘lganingizdan keyin\n"
                    '"✅ Tekshirish" tugmasini bosing.'
                )
                await message.answer(text, reply_markup=subscription_keyboard(missing))
                return

        await _show_movie(message, movie, message.from_user.id)


async def _show_movie(
    message: Message, movie: Movie, user_id: int, edit: bool = False
) -> None:
    async with async_session_factory() as session:
        movie_service = MovieService(session)
        is_fav = await movie_service.is_favorite(user_id, movie.id)
        kb = movie_info_keyboard(movie, user_id, is_fav)

    text = format_movie_info(movie)
    if movie.poster_file_id:
        if edit:
            await message.edit_media(
                media=InputMediaPhoto(media=movie.poster_file_id, caption=text),
                reply_markup=kb,
            )
        else:
            await message.answer_photo(
                photo=movie.poster_file_id, caption=text, reply_markup=kb
            )
    else:
        if edit:
            await message.edit_text(text, reply_markup=kb)
        else:
            await message.answer(text, reply_markup=kb)


@router.message(StateFilter(None), F.text.regexp(CODE_PATTERN))
async def on_movie_code(message: Message) -> None:
    code = int(message.text)
    await _handle_movie_code(message, code)


@router.callback_query(F.data.startswith("movie:"))
async def show_movie_callback(callback: CallbackQuery) -> None:
    movie_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        movie_service = MovieService(session)
        movie = await movie_service.get_by_id(movie_id)
        if movie is None:
            await callback.answer("❌ Kino topilmadi.", show_alert=True)
            return
        is_fav = await movie_service.is_favorite(callback.from_user.id, movie.id)
        kb = movie_info_keyboard(movie, callback.from_user.id, is_fav)
    text = format_movie_info(movie)
    if movie.poster_file_id:
        await callback.message.edit_media(
            media=InputMediaPhoto(media=movie.poster_file_id, caption=text),
            reply_markup=kb,
        )
    else:
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("get_movie:"))
async def get_movie(callback: CallbackQuery) -> None:
    movie_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        movie_service = MovieService(session)
        movie = await movie_service.get_by_id(movie_id)
        if movie is None:
            await callback.answer("❌ Kino topilmadi.", show_alert=True)
            return
        files = await movie_service.get_files(movie_id)

    if not files:
        await callback.answer("⚠️ Film fayli hozircha mavjud emas.", show_alert=True)
        return

    if movie.is_series:
        # Show episode list for series.
        episodes = [f for f in files if f.episode_number is not None]
        if not episodes:
            await callback.answer("⚠️ Qismlar hozircha mavjud emas.", show_alert=True)
            return
        await callback.message.edit_text(
            f"📺 {movie.title}\n\nQismlarni tanlang:",
            reply_markup=series_episodes_keyboard(movie_id, episodes),
        )
    elif len(files) == 1:
        await _deliver_file(callback, movie_id, files[0].id)
    else:
        await callback.message.edit_text(
            f"🎬 {movie.title}\n\nMavjud versiyalar:", reply_markup=movie_files_keyboard(movie_id, files)
        )
    await callback.answer()


async def _deliver_file(callback: CallbackQuery, movie_id: int, file_id: int) -> None:
    async with async_session_factory() as session:
        movie_service = MovieService(session)
        movie = await movie_service.get_by_id(movie_id)
        files = await movie_service.get_files(movie_id)
        target = next((f for f in files if f.id == file_id), None)
        if movie is None or target is None:
            await callback.answer("❌ Fayl topilmadi.", show_alert=True)
            return

        storage = StorageService(callback.bot)
        try:
            await storage.copy_to_user(
                chat_id=callback.from_user.id,
                storage_chat_id=target.storage_chat_id,
                storage_message_id=target.storage_message_id,
            )
            await movie_service.increment_views(movie_id)
            await session.commit()
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Delivery failed movie=%s code=%s chat=%s msg=%s: %s",
                movie_id,
                movie.code,
                target.storage_chat_id,
                target.storage_message_id,
                exc,
            )
            await callback.answer(
                "⚠️ Film fayli hozircha mavjud emas.\n\nAdministratorga xabar berildi.",
                show_alert=True,
            )
            await _notify_admin_broken(callback, movie, target)
            return
    await callback.answer("✅ Film yuborildi!")


async def _notify_admin_broken(callback: CallbackQuery, movie: Movie, target) -> None:
    for admin_id in settings.admin_id_list:
        try:
            await callback.bot.send_message(
                admin_id,
                f"⚠️ Film fayli mavjud emas!\n\n"
                f"🎬 {movie.title}\n🔢 Kod: {movie.code}\n"
                f"📦 Storage chat: {target.storage_chat_id}\n"
                f"📦 Storage msg: {target.storage_message_id}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not notify admin %s: %s", admin_id, exc)


@router.callback_query(F.data.startswith("deliver:"))
async def deliver_callback(callback: CallbackQuery) -> None:
    _, movie_id, file_id = callback.data.split(":")
    await _deliver_file(callback, int(movie_id), int(file_id))


@router.callback_query(F.data.startswith("popular:"))
async def show_popular_callback(callback: CallbackQuery) -> None:
    page = int(callback.data.split(":")[1])
    await _show_list(callback, "popular", page)


@router.callback_query(F.data.startswith("new:"))
async def show_new_callback(callback: CallbackQuery) -> None:
    page = int(callback.data.split(":")[1])
    await _show_list(callback, "new", page)


async def _show_list(callback: CallbackQuery, kind: str, page: int) -> None:
    async with async_session_factory() as session:
        movie_service = MovieService(session)
        if kind == "popular":
            movies = await movie_service.get_popular(PAGE_SIZE, (page - 1) * PAGE_SIZE)
            total = len(movies)
        else:
            movies = await movie_service.get_new(PAGE_SIZE, (page - 1) * PAGE_SIZE)
            total = len(movies)

    if not movies:
        await callback.answer("❌ Kinolar topilmadi.", show_alert=True)
        return

    text = "🔥 Mashhur kinolar\n\n" if kind == "popular" else "🆕 Yangi kinolar\n\n"
    for i, movie in enumerate(movies, 1):
        text += f"{i}. 🎬 {movie.title}\n"
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    kb = pagination_keyboard(kind, page, total_pages, [m.id for m in movies])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


async def show_popular(message: Message) -> None:
    async with async_session_factory() as session:
        movie_service = MovieService(session)
        movies = await movie_service.get_popular(PAGE_SIZE, 0)
    if not movies:
        await message.answer("❌ Kinolar topilmadi.")
        return
    text = "🔥 Mashhur kinolar\n\n"
    for i, movie in enumerate(movies, 1):
        text += f"{i}. 🎬 {movie.title}\n"
    kb = pagination_keyboard("popular", 1, 1, [m.id for m in movies])
    await message.answer(text, reply_markup=kb)


async def show_new(message: Message) -> None:
    async with async_session_factory() as session:
        movie_service = MovieService(session)
        movies = await movie_service.get_new(PAGE_SIZE, 0)
    if not movies:
        await message.answer("❌ Kinolar topilmadi.")
        return
    text = "🆕 Yangi kinolar\n\n"
    for i, movie in enumerate(movies, 1):
        text += f"{i}. 🎬 {movie.title}\n"
    kb = pagination_keyboard("new", 1, 1, [m.id for m in movies])
    await message.answer(text, reply_markup=kb)
