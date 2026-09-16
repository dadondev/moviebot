"""Admin movie management: upload FSM, preview, save, edit, delete."""

import logging
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot.filters.filters import AdminFilter
from app.bot.keyboards.admin import (
    admin_edit_keyboard,
    admin_movie_actions_keyboard,
    admin_movie_list_keyboard,
    admin_movies_keyboard,
)
from app.bot.states.states import EpisodeAddStates, MovieEditStates, MovieUploadStates
from app.database.database import async_session_factory
from app.database.repositories import GenreRepository, MovieRepository
from app.services.movie_service import MovieService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

router = Router(name="admin_movies")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())

CODE_PATTERN = re.compile(r"^\d+$")
YEAR_PATTERN = re.compile(r"^\d{4}$")
DURATION_PATTERN = re.compile(r"^\d+$")
IMDB_PATTERN = re.compile(r"^\d+(\.\d+)?$")

DEFAULT_GENRES = [
    "Drama",
    "Komediya",
    "Jangari",
    "Qo‘rqinchli",
    "Romantik",
    "Fantastika",
    "Fantasy",
    "Detektiv",
    "Triller",
    "Oilaviy",
    "Multfilm",
    "Tarixiy",
]


async def _ensure_default_genres(session) -> None:
    repo = GenreRepository(session)
    existing = {g.slug for g in await repo.list_all()}
    for name in DEFAULT_GENRES:
        slug = name.lower().replace(" ", "-")
        if slug not in existing:
            await repo.create(name, slug)
    await session.commit()


# --- Entry: admin clicks "➕ Kino qo‘shish" ---
@router.callback_query(F.data == "admin_add_movie")
async def admin_add_movie(callback: CallbackQuery, state: FSMContext) -> None:
    # Clear any previous upload state so we start fresh.
    await state.clear()
    await state.set_state(MovieUploadStates.waiting_for_file)
    await callback.message.edit_text(
        "🎬 Kinoni yuboring (video yoki hujjat).\n\n"
        "Masalan: Avatar.mp4\n\n"
        "Bekor qilish uchun: /cancel"
    )
    await callback.answer()


# --- Detect movie upload (video/document) ---
# Only fires when the admin is in the movie-upload flow (waiting_for_file),
# so it never hijacks the episode-add flow or normal chats.
@router.message(MovieUploadStates.waiting_for_file, F.video | F.document)
async def receive_movie_file(message: Message, state: FSMContext) -> None:
    file_id = None
    file_unique_id = None
    if message.video:
        file_id = message.video.file_id
        file_unique_id = message.video.file_unique_id
    elif message.document:
        file_id = message.document.file_id
        file_unique_id = message.document.file_unique_id

    await state.update_data(
        telegram_file_id=file_id,
        telegram_file_unique_id=file_unique_id,
        source_message_id=message.message_id,
        source_chat_id=message.chat.id,
    )
    await state.set_state(MovieUploadStates.waiting_for_title)
    await message.answer("🎬 Kino nomini kiriting:")


# --- Title ---
@router.message(MovieUploadStates.waiting_for_title)
async def ask_original_title(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    edit_field = data.get("edit_field")

    # If we're editing a specific field during the upload preview, handle it.
    if edit_field:
        await _apply_upload_edit(message, state, edit_field)
        return

    await state.update_data(title=message.text.strip())
    await state.set_state(MovieUploadStates.waiting_for_original_title)
    await message.answer("🌍 Original nomini kiriting:")


async def _apply_upload_edit(message: Message, state: FSMContext, field: str) -> None:
    """Apply an edit to a single field during the upload flow, then return to preview."""
    text = message.text.strip() if message.text else ""

    if field == "code":
        if text.lower() == "/skip":
            async with async_session_factory() as session:
                repo = MovieRepository(session)
                code = await repo.next_code()
            await state.update_data(code=code)
        elif not CODE_PATTERN.match(text):
            await message.answer("❌ Kod faqat raqamlardan iborat bo‘lishi kerak.")
            return
        else:
            code = int(text)
            async with async_session_factory() as session:
                repo = MovieRepository(session)
                if await repo.code_exists(code):
                    await message.answer("❌ Bu kod allaqachon mavjud.")
                    return
            await state.update_data(code=code)
    elif field == "year":
        if not YEAR_PATTERN.match(text):
            await message.answer("❌ Yil 4 xonali raqam bo‘lishi kerak.")
            return
        await state.update_data(year=int(text))
    elif field == "duration":
        match = DURATION_PATTERN.search(text)
        if not match:
            await message.answer("❌ Davomiylik raqam bo‘lishi kerak.")
            return
        await state.update_data(duration=int(match.group()))
    elif field == "imdb_rating":
        if not IMDB_PATTERN.match(text):
            await message.answer("❌ IMDb reytingi raqam bo‘lishi kerak.")
            return
        await state.update_data(imdb_rating=float(text))
    elif field == "poster":
        if message.photo:
            await state.update_data(poster_file_id=message.photo[-1].file_id)
        elif text.lower() == "/skip":
            await state.update_data(poster_file_id=None)
        else:
            await message.answer("🖼 Iltimos, rasm yuboring yoki /skip bosing.")
            return
    elif field == "trailer_url":
        if text.lower() == "/skip":
            await state.update_data(trailer_url=None)
        elif text.startswith("http"):
            await state.update_data(trailer_url=text)
        else:
            await message.answer("🎞 Havola http(s) bilan boshlanishi kerak yoki /skip bosing.")
            return
    elif field == "genres":
        # Genre editing is handled via callbacks; this branch is a fallback.
        await message.answer("🎭 Janrlarni tanlash uchun quyidagi tugmalardan foydalaning.")
        return
    else:
        await state.update_data(**{field: text})

    # Clear the edit flag and return to the preview.
    await state.update_data(edit_field=None)
    await state.set_state(MovieUploadStates.confirmation)
    data = await state.get_data()
    await _render_preview(message, data)


# --- Original title ---
@router.message(MovieUploadStates.waiting_for_original_title)
async def ask_code(message: Message, state: FSMContext) -> None:
    await state.update_data(original_title=message.text.strip())
    await state.set_state(MovieUploadStates.waiting_for_code)
    # Suggest the next available code.
    async with async_session_factory() as session:
        repo = MovieRepository(session)
        next_code = await repo.next_code()
    await message.answer(
        f"🔢 Kino kodini kiriting:\n\n"
        f"💡 Tavsiya etilgan kod: {next_code}\n\n"
        f"Masalan: {next_code}\n\n"
        f"Tavsiya etilgan kodni qabul qilish uchun /skip bosing."
    )


# --- Code ---
@router.message(MovieUploadStates.waiting_for_code)
async def ask_description(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text.lower() == "/skip":
        async with async_session_factory() as session:
            repo = MovieRepository(session)
            code = await repo.next_code()
        await state.update_data(code=code)
        await state.set_state(MovieUploadStates.waiting_for_description)
        await message.answer("📝 Kino haqida qisqacha ma'lumot kiriting:")
        return
    if not CODE_PATTERN.match(text):
        await message.answer("❌ Kod faqat raqamlardan iborat bo‘lishi kerak.\n\nBoshqa kod kiriting:")
        return
    code = int(text)
    async with async_session_factory() as session:
        repo = MovieRepository(session)
        if await repo.code_exists(code):
            next_code = await repo.next_code()
            await message.answer(
                f"❌ Bu kino kodi allaqachon mavjud.\n\n"
                f"💡 Tavsiya etilgan kod: {next_code}\n\n"
                f"Boshqa kod kiriting yoki /skip bosing:"
            )
            return
    await state.update_data(code=code)
    await state.set_state(MovieUploadStates.waiting_for_description)
    await message.answer("📝 Kino haqida qisqacha ma'lumot kiriting:")


# --- Description ---
@router.message(MovieUploadStates.waiting_for_description)
async def ask_year(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text.strip())
    await state.set_state(MovieUploadStates.waiting_for_year)
    await message.answer("📅 Kino chiqarilgan yilni kiriting:\n\nMasalan: 2009")


# --- Year ---
@router.message(MovieUploadStates.waiting_for_year)
async def ask_genres(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not YEAR_PATTERN.match(text):
        await message.answer("❌ Yil 4 xonali raqam bo‘lishi kerak.\n\nMasalan: 2009")
        return
    await state.update_data(year=int(text))
    await state.set_state(MovieUploadStates.waiting_for_genres)
    await _show_genre_selection(message, state)


async def _show_genre_selection(message: Message, state: FSMContext | None = None) -> None:
    selected: set[int] = set()
    if state is not None:
        data = await state.get_data()
        selected = set(data.get("selected_genres", []))

    async with async_session_factory() as session:
        await _ensure_default_genres(session)
        repo = GenreRepository(session)
        genres = await repo.list_all()
    rows = []
    for genre in genres:
        mark = "☑" if genre.id in selected else "☐"
        rows.append(
            [InlineKeyboardButton(text=f"{mark} {genre.name}", callback_data=f"upload_genre:{genre.id}")]
        )
    rows.append([InlineKeyboardButton(text="✅ Tayyor", callback_data="upload_genres_done")])
    await message.answer(
        "🎭 Janrlarni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@router.callback_query(MovieUploadStates.waiting_for_genres, F.data.startswith("upload_genre:"))
async def toggle_upload_genre(callback: CallbackQuery, state: FSMContext) -> None:
    genre_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    selected = set(data.get("selected_genres", []))
    if genre_id in selected:
        selected.discard(genre_id)
    else:
        selected.add(genre_id)
    await state.update_data(selected_genres=list(selected))

    async with async_session_factory() as session:
        repo = GenreRepository(session)
        genres = await repo.list_all()
    rows = []
    for genre in genres:
        mark = "☑" if genre.id in selected else "☐"
        rows.append(
            [InlineKeyboardButton(text=f"{mark} {genre.name}", callback_data=f"upload_genre:{genre.id}")]
        )
    rows.append([InlineKeyboardButton(text="✅ Tayyor", callback_data="upload_genres_done")])
    # Use edit_text (not edit_reply_markup) so the buttons reliably refresh.
    await callback.message.edit_text(
        "🎭 Janrlarni tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await callback.answer()


@router.callback_query(MovieUploadStates.waiting_for_genres, F.data == "upload_genres_done")
async def genres_done(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected = data.get("selected_genres", [])
    if not selected:
        await callback.answer("❌ Kamida bitta janr tanlang.", show_alert=True)
        return

    # If we were editing genres during the preview, return to the preview.
    if data.get("edit_field") == "genres":
        await state.update_data(edit_field=None)
        await state.set_state(MovieUploadStates.confirmation)
        await _render_preview(callback.message, data)
        await callback.answer()
        return

    await state.set_state(MovieUploadStates.waiting_for_country)
    await callback.message.edit_text("🌍 Davlatni kiriting:\n\nMasalan: AQSh")
    await callback.answer()


# --- Country ---
@router.message(MovieUploadStates.waiting_for_country)
async def ask_duration(message: Message, state: FSMContext) -> None:
    await state.update_data(country=message.text.strip())
    await state.set_state(MovieUploadStates.waiting_for_duration)
    await message.answer("⏱ Davomiyligini kiriting:\n\nMasalan:\n162 daqiqa")


# --- Duration ---
@router.message(MovieUploadStates.waiting_for_duration)
async def ask_imdb(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    match = DURATION_PATTERN.search(text)
    if not match:
        await message.answer("❌ Davomiylik daqiqada raqam bo‘lishi kerak.\n\nMasalan: 162")
        return
    await state.update_data(duration=int(match.group()))
    await state.set_state(MovieUploadStates.waiting_for_imdb)
    await message.answer("⭐ IMDb reytingini kiriting:\n\nMasalan:\n7.8")


# --- IMDb ---
@router.message(MovieUploadStates.waiting_for_imdb)
async def ask_age_rating(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not IMDB_PATTERN.match(text):
        await message.answer("❌ IMDb reytingi raqam bo‘lishi kerak.\n\nMasalan: 7.8")
        return
    await state.update_data(imdb_rating=float(text))
    await state.set_state(MovieUploadStates.waiting_for_age_rating)
    await message.answer("🔞 Yosh chegarasini kiriting:\n\nMasalan:\n13+")


# --- Age rating ---
@router.message(MovieUploadStates.waiting_for_age_rating)
async def ask_poster(message: Message, state: FSMContext) -> None:
    await state.update_data(age_rating=message.text.strip())
    await state.set_state(MovieUploadStates.waiting_for_poster)
    await message.answer("🖼 Kino posterini yuboring.\n\nAgar poster bo‘lmasa:\n/skip")


# --- Poster ---
@router.message(MovieUploadStates.waiting_for_poster)
async def ask_trailer(message: Message, state: FSMContext) -> None:
    if message.photo:
        await state.update_data(poster_file_id=message.photo[-1].file_id)
    elif message.text and message.text.strip().lower() == "/skip":
        await state.update_data(poster_file_id=None)
    else:
        await message.answer("🖼 Iltimos, rasm yuboring yoki /skip bosing.")
        return
    await state.set_state(MovieUploadStates.waiting_for_trailer)
    await message.answer("🎞 Treyler havolasini yuboring.\n\nAgar treyler bo‘lmasa:\n/skip")


# --- Trailer ---
@router.message(MovieUploadStates.waiting_for_trailer)
async def show_preview(message: Message, state: FSMContext) -> None:
    text = message.text.strip() if message.text else ""
    if text.lower() == "/skip":
        await state.update_data(trailer_url=None)
    elif text.startswith("http"):
        await state.update_data(trailer_url=text)
    else:
        await message.answer("🎞 Havola http(s) bilan boshlanishi kerak yoki /skip bosing.")
        return

    # Ask whether this is a movie or a series.
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Film", callback_data="upload_type:movie")],
            [InlineKeyboardButton(text="📺 Serial", callback_data="upload_type:series")],
        ]
    )
    await state.set_state(MovieUploadStates.waiting_for_series)
    await message.answer("Bu nima?", reply_markup=kb)


@router.callback_query(F.data.startswith("upload_type:"))
async def upload_type_selected(callback: CallbackQuery, state: FSMContext) -> None:
    movie_type = callback.data.split(":")[1]
    is_series = movie_type == "series"
    await state.update_data(is_series=is_series)
    await state.set_state(MovieUploadStates.confirmation)
    data = await state.get_data()
    await _render_preview(callback.message, data)
    await callback.answer()


async def _render_preview(message: Message, data: dict) -> None:
    async with async_session_factory() as session:
        repo = GenreRepository(session)
        genres = []
        for gid in data.get("selected_genres", []):
            g = await repo.get_by_id(gid)
            if g:
                genres.append(g.name)

    text = (
        "🎬 KINO MA'LUMOTLARI\n\n"
        f"🎬 Nomi: {data.get('title')}\n"
        f"🌍 Original nomi: {data.get('original_title')}\n"
        f"🔢 Kodi: {data.get('code')}\n"
        f"📺 Turi: {'Serial' if data.get('is_series') else 'Film'}\n\n"
        f"📅 Yil: {data.get('year')}\n"
        f"🎭 Janr: {', '.join(genres)}\n"
        f"🌍 Davlat: {data.get('country')}\n"
        f"⏱ Davomiyligi: {data.get('duration')} daqiqa\n"
        f"⭐ IMDb: {data.get('imdb_rating')}\n"
        f"🔞 Yosh chegarasi: {data.get('age_rating')}\n\n"
        f"📝 Tavsif:\n{data.get('description')}\n\n"
        "Ma'lumotlar to'g'rimi?"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Saqlash", callback_data="upload_save")],
            [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data="upload_edit")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="upload_cancel")],
        ]
    )
    await message.answer(text, reply_markup=kb)


# --- Save ---
@router.callback_query(F.data == "upload_save")
async def save_movie(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    code = data.get("code")
    telegram_file_id = data.get("telegram_file_id")

    if not telegram_file_id:
        await callback.answer("❌ Video fayl topilmadi.", show_alert=True)
        return

    async with async_session_factory() as session:
        movie_repo = MovieRepository(session)
        genre_repo = GenreRepository(session)

        # Re-validate code uniqueness inside the transaction.
        if await movie_repo.code_exists(code):
            await callback.answer("❌ Bu kino kodi allaqachon mavjud.", show_alert=True)
            return

        genres = []
        for gid in data.get("selected_genres", []):
            g = await genre_repo.get_by_id(gid)
            if g:
                genres.append(g)

        movie = await movie_repo.create(
            code=code,
            title=data.get("title"),
            original_title=data.get("original_title"),
            description=data.get("description"),
            poster_file_id=data.get("poster_file_id"),
            year=data.get("year"),
            country=data.get("country"),
            duration=data.get("duration"),
            imdb_rating=data.get("imdb_rating"),
            age_rating=data.get("age_rating"),
            trailer_url=data.get("trailer_url"),
            is_series=bool(data.get("is_series")),
            genres=genres,
        )

        # Copy the uploaded movie to the private storage channel.
        storage = StorageService(callback.bot)
        try:
            storage_chat_id, storage_message_id = await storage.copy_to_storage_by_ids(
                from_chat_id=data.get("source_chat_id"),
                message_id=data.get("source_message_id"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Storage copy failed for movie %s: %s", code, exc)
            await session.rollback()
            await callback.answer("⚠️ Saqlashda xatolik yuz berdi.", show_alert=True)
            return

        from app.database.repositories import MovieFileRepository

        file_repo = MovieFileRepository(session)
        await file_repo.create(
            movie_id=movie.id,
            storage_chat_id=storage_chat_id,
            storage_message_id=storage_message_id,
            telegram_file_id=telegram_file_id,
            telegram_file_unique_id=data.get("telegram_file_unique_id", ""),
            quality="1080p",
            language="Uzbek",
        )
        await session.commit()

    await state.clear()
    await callback.message.edit_text(f"✅ Kino saqlandi!\n\n🎬 {data.get('title')} (kod: {code})")
    await callback.answer()


@router.callback_query(F.data == "upload_edit")
async def upload_edit(callback: CallbackQuery, state: FSMContext) -> None:
    """Show a menu of fields the admin can edit before saving."""
    await state.set_state(MovieUploadStates.confirmation)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Nomi", callback_data="upload_edit_field:title")],
            [InlineKeyboardButton(text="🌍 Original nomi", callback_data="upload_edit_field:original_title")],
            [InlineKeyboardButton(text="🔢 Kod", callback_data="upload_edit_field:code")],
            [InlineKeyboardButton(text="📝 Tavsif", callback_data="upload_edit_field:description")],
            [InlineKeyboardButton(text="📅 Yil", callback_data="upload_edit_field:year")],
            [InlineKeyboardButton(text="🎭 Janrlar", callback_data="upload_edit_field:genres")],
            [InlineKeyboardButton(text="🌍 Davlat", callback_data="upload_edit_field:country")],
            [InlineKeyboardButton(text="⏱ Davomiylik", callback_data="upload_edit_field:duration")],
            [InlineKeyboardButton(text="⭐ IMDb", callback_data="upload_edit_field:imdb_rating")],
            [InlineKeyboardButton(text="🔞 Yosh chegarasi", callback_data="upload_edit_field:age_rating")],
            [InlineKeyboardButton(text="🖼 Poster", callback_data="upload_edit_field:poster")],
            [InlineKeyboardButton(text="🎞 Treyler", callback_data="upload_edit_field:trailer_url")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="upload_back_to_preview")],
        ]
    )
    await callback.message.edit_text("✏️ Qaysi maydonni tahrirlash kerak?", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "upload_back_to_preview")
async def upload_back_to_preview(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await _render_preview(callback.message, data)
    await callback.answer()


@router.callback_query(F.data.startswith("upload_edit_field:"))
async def upload_edit_field(callback: CallbackQuery, state: FSMContext) -> None:
    field = callback.data.split(":")[1]
    await state.update_data(edit_field=field)

    if field == "genres":
        # Show genre selection directly.
        await state.set_state(MovieUploadStates.waiting_for_genres)
        await _show_genre_selection(callback.message, state)
        await callback.answer()
        return

    prompts = {
        "title": "🎬 Yangi nomni kiriting:",
        "original_title": "🌍 Yangi original nomni kiriting:",
        "code": "🔢 Yangi kodni kiriting:",
        "description": "📝 Yangi tavsifni kiriting:",
        "year": "📅 Yangi yilni kiriting:",
        "country": "🌍 Yangi davlatni kiriting:",
        "duration": "⏱ Yangi davomiylikni kiriting:",
        "imdb_rating": "⭐ Yangi IMDb reytingini kiriting:",
        "age_rating": "🔞 Yangi yosh chegarasini kiriting:",
        "poster": "🖼 Yangi poster yuboring yoki /skip:",
        "trailer_url": "🎞 Yangi treyler havolasini kiriting yoki /skip:",
    }
    await state.set_state(MovieUploadStates.waiting_for_title)
    await callback.message.edit_text(prompts.get(field, "Qiymatni kiriting:"))
    await callback.answer()


@router.callback_query(F.data == "upload_cancel")
async def upload_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Amal bekor qilindi.")
    await callback.answer()


# --- Admin movie list / view / edit / delete ---
@router.callback_query(F.data == "admin_movies")
async def admin_movies_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text("🎬 Kinolar", reply_markup=admin_movies_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("admin_movie_list:"))
async def admin_movie_list(callback: CallbackQuery) -> None:
    page = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        repo = MovieRepository(session)
        movies = await repo.list_all(limit=10, offset=(page - 1) * 10)
        total = await repo.count_all()
    total_pages = max(1, (total + 9) // 10)
    await callback.message.edit_text(
        "📋 Barcha kinolar:", reply_markup=admin_movie_list_keyboard(movies, page, total_pages)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_view:"))
async def admin_view_movie(callback: CallbackQuery) -> None:
    movie_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        movie_service = MovieService(session)
        movie = await movie_service.get_by_id(movie_id)
        if movie is None:
            await callback.answer("❌ Kino topilmadi.", show_alert=True)
            return
        files = await movie_service.get_files(movie_id)
        avg = await movie_service.get_average_rating(movie_id)
        fav_count = await movie_service.favorite_repo.count_for_movie(movie_id)

    movie_type = "📺 Serial" if movie.is_series else "🎬 Film"
    text = (
        f"🎬 {movie.title}\n\n"
        f"🔢 Kod: {movie.code}\n"
        f"{movie_type}\n"
        f"👁 Ko‘rishlar: {movie.views:,}\n"
        f"⭐ Reyting: {avg if avg is not None else '-'}\n"
        f"❤️ Sevimlilar: {fav_count}\n"
        f"🎥 Fayllar: {len(files)}"
    )
    await callback.message.edit_text(
        text, reply_markup=admin_movie_actions_keyboard(movie_id, movie.is_series)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit:"))
async def admin_edit_menu(callback: CallbackQuery) -> None:
    movie_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        "✏️ Tahrirlash uchun maydonni tanlang:", reply_markup=admin_edit_keyboard(movie_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field:"))
async def edit_field(callback: CallbackQuery, state: FSMContext) -> None:
    _, movie_id, field = callback.data.split(":")
    await state.update_data(edit_movie_id=int(movie_id), edit_field=field)
    await state.set_state(MovieEditStates.waiting_for_field)
    prompts = {
        "title": "🎬 Yangi nomni kiriting:",
        "original_title": "🌍 Yangi original nomni kiriting:",
        "code": "🔢 Yangi kodni kiriting:",
        "description": "📝 Yangi tavsifni kiriting:",
        "year": "📅 Yangi yilni kiriting:",
        "genres": "🎭 Janrlarni tanlang:",
        "country": "🌍 Yangi davlatni kiriting:",
        "duration": "⏱ Yangi davomiylikni kiriting:",
        "imdb_rating": "⭐ Yangi IMDb reytingini kiriting:",
        "age_rating": "🔞 Yangi yosh chegarasini kiriting:",
        "poster": "🖼 Yangi poster yuboring yoki /skip:",
        "trailer_url": "🎞 Yangi treyler havolasini kiriting yoki /skip:",
    }
    await callback.message.edit_text(prompts.get(field, "Qiymatni kiriting:"))
    await callback.answer()


@router.message(MovieEditStates.waiting_for_field)
async def process_edit(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    movie_id = data.get("edit_movie_id")
    field = data.get("edit_field")
    value = message.text.strip() if message.text else None

    if field == "poster":
        if message.photo:
            value = message.photo[-1].file_id
        elif value and value.lower() == "/skip":
            value = None
        else:
            await message.answer("🖼 Iltimos, rasm yuboring yoki /skip bosing.")
            return
    elif field == "trailer_url":
        if value and value.lower() == "/skip":
            value = None
        elif value and not value.startswith("http"):
            await message.answer("🎞 Havola http(s) bilan boshlanishi kerak.")
            return

    async with async_session_factory() as session:
        repo = MovieRepository(session)
        movie = await repo.get_by_id(movie_id)
        if movie is None:
            await message.answer("❌ Kino topilmadi.")
            await state.clear()
            return

        if field == "code":
            if not CODE_PATTERN.match(value):
                await message.answer("❌ Kod faqat raqamlardan iborat bo‘lishi kerak.")
                return
            new_code = int(value)
            if await repo.code_exists(new_code, exclude_id=movie_id):
                await message.answer("❌ Bu kod allaqachon mavjud.")
                return
            await repo.update(movie, code=new_code)
        elif field == "year":
            if not YEAR_PATTERN.match(value):
                await message.answer("❌ Yil 4 xonali raqam bo‘lishi kerak.")
                return
            await repo.update(movie, year=int(value))
        elif field == "duration":
            match = DURATION_PATTERN.search(value)
            if not match:
                await message.answer("❌ Davomiylik raqam bo‘lishi kerak.")
                return
            await repo.update(movie, duration=int(match.group()))
        elif field == "imdb_rating":
            if not IMDB_PATTERN.match(value):
                await message.answer("❌ IMDb reytingi raqam bo‘lishi kerak.")
                return
            await repo.update(movie, imdb_rating=float(value))
        else:
            await repo.update(movie, **{field: value})
        await session.commit()

    await state.clear()
    await message.answer("✅ Yangilandi.")
    await message.answer("🎬 Kinolar", reply_markup=admin_movies_keyboard())


@router.callback_query(F.data.startswith("admin_delete:"))
async def admin_delete_confirm(callback: CallbackQuery) -> None:
    movie_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        repo = MovieRepository(session)
        movie = await repo.get_by_id(movie_id)
        if movie is None:
            await callback.answer("❌ Kino topilmadi.", show_alert=True)
            return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Ha, o‘chirish", callback_data=f"admin_delete_confirm:{movie_id}")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"admin_view:{movie_id}")],
        ]
    )
    await callback.message.edit_text(
        f"⚠️ Ushbu kinoni o‘chirmoqchimisiz?\n\n🎬 {movie.title}\n🔢 {movie.code}",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_delete_confirm:"))
async def admin_delete_execute(callback: CallbackQuery) -> None:
    movie_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        repo = MovieRepository(session)
        movie = await repo.get_by_id(movie_id)
        if movie is None:
            await callback.answer("❌ Kino topilmadi.", show_alert=True)
            return
        files = await repo.get_files(movie_id)
        storage = StorageService(callback.bot)
        for f in files:
            await storage.delete_storage_message(f.storage_chat_id, f.storage_message_id)
        await repo.delete(movie)
        await session.commit()
    await callback.message.edit_text(f"🗑 Kino o‘chirildi: {movie.title}")
    await callback.answer()


# --- Add episode to a series ---
@router.callback_query(F.data.startswith("admin_add_episode:"))
async def admin_add_episode(callback: CallbackQuery, state: FSMContext) -> None:
    movie_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        movie_service = MovieService(session)
        movie = await movie_service.get_by_id(movie_id)
        if movie is None:
            await callback.answer("❌ Kino topilmadi.", show_alert=True)
            return
        next_ep = await movie_service.next_episode_number(movie_id)

    await state.update_data(episode_movie_id=movie_id, episode_number=next_ep)
    await state.set_state(EpisodeAddStates.waiting_for_file)
    await callback.message.edit_text(
        f"📺 {movie.title}\n\n"
        f"🎬 Qism {next_ep} uchun video yuboring.\n\n"
        "Bekor qilish uchun: /cancel"
    )
    await callback.answer()


@router.message(EpisodeAddStates.waiting_for_file)
async def episode_file_received(message: Message, state: FSMContext) -> None:
    file_id = None
    file_unique_id = None
    if message.video:
        file_id = message.video.file_id
        file_unique_id = message.video.file_unique_id
    elif message.document:
        file_id = message.document.file_id
        file_unique_id = message.document.file_unique_id
    else:
        await message.answer("❌ Video yoki hujjat yuboring.")
        return

    await state.update_data(
        episode_file_id=file_id,
        episode_file_unique_id=file_unique_id,
        episode_source_message_id=message.message_id,
        episode_source_chat_id=message.chat.id,
    )
    await state.set_state(EpisodeAddStates.waiting_for_episode_number)
    data = await state.get_data()
    await message.answer(
        f"🎬 Qism raqamini kiriting:\n\n"
        f"💡 Tavsiya: {data.get('episode_number')}\n\n"
        f"Tavsiyani qabul qilish uchun /skip bosing."
    )


@router.message(EpisodeAddStates.waiting_for_episode_number)
async def episode_number_received(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text.lower() == "/skip":
        episode_number = (await state.get_data()).get("episode_number")
    elif CODE_PATTERN.match(text):
        episode_number = int(text)
    else:
        await message.answer("❌ Qism raqami faqat raqamlardan iborat bo‘lishi kerak.")
        return

    await state.update_data(episode_number=episode_number)
    await state.set_state(EpisodeAddStates.confirmation)
    data = await state.get_data()

    async with async_session_factory() as session:
        movie_service = MovieService(session)
        movie = await movie_service.get_by_id(data.get("episode_movie_id"))

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Saqlash", callback_data="episode_save")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="episode_cancel")],
        ]
    )
    await message.answer(
        f"📺 {movie.title if movie else ''}\n\n"
        f"🎬 Qism: {episode_number}\n\n"
        "Saqlansinmi?",
        reply_markup=kb,
    )


@router.callback_query(F.data == "episode_save")
async def episode_save(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    movie_id = data.get("episode_movie_id")
    episode_number = data.get("episode_number")
    file_id = data.get("episode_file_id")

    if not file_id:
        await callback.answer("❌ Video fayl topilmadi.", show_alert=True)
        return

    async with async_session_factory() as session:
        movie_service = MovieService(session)
        movie = await movie_service.get_by_id(movie_id)
        if movie is None:
            await callback.answer("❌ Kino topilmadi.", show_alert=True)
            return

        storage = StorageService(callback.bot)
        try:
            storage_chat_id, storage_message_id = await storage.copy_to_storage_by_ids(
                from_chat_id=data.get("episode_source_chat_id"),
                message_id=data.get("episode_source_message_id"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Episode storage copy failed movie=%s: %s", movie_id, exc)
            await callback.answer("⚠️ Saqlashda xatolik yuz berdi.", show_alert=True)
            return

        await movie_service.file_repo.create(
            movie_id=movie_id,
            storage_chat_id=storage_chat_id,
            storage_message_id=storage_message_id,
            telegram_file_id=file_id,
            telegram_file_unique_id=data.get("episode_file_unique_id", ""),
            quality="1080p",
            language="Uzbek",
            episode_number=episode_number,
        )
        await session.commit()

    await state.clear()
    await callback.message.edit_text(
        f"✅ Qism saqlandi!\n\n📺 {movie.title} — 🎬 Qism {episode_number}"
    )
    await callback.answer()


@router.callback_query(F.data == "episode_cancel")
async def episode_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Amal bekor qilindi.")
    await callback.answer()
