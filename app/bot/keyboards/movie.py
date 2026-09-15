"""Movie-related keyboards (info, delivery, pagination)."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.database.models import Movie, MovieFile


def movie_info_keyboard(movie: Movie, user_id: int, is_favorite: bool) -> InlineKeyboardMarkup:
    fav_text = "❌ Sevimlilardan olib tashlash" if is_favorite else "⭐ Sevimlilarga qo‘shish"
    rows = [
        [InlineKeyboardButton(text="▶️ Filmni olish", callback_data=f"get_movie:{movie.id}")],
        [InlineKeyboardButton(text=fav_text, callback_data=f"toggle_fav:{movie.id}")],
    ]
    if movie.trailer_url:
        rows.append(
            [InlineKeyboardButton(text="🎞 Treyler", url=movie.trailer_url)]
        )
    rows.append(
        [InlineKeyboardButton(text="⭐ Baholash", callback_data=f"rate:{movie.id}")]
    )
    rows.append(
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def movie_files_keyboard(movie_id: int, files: list[MovieFile]) -> InlineKeyboardMarkup:
    rows = []
    for f in files:
        quality = f.quality if f.quality else "Noma'lum"
        label = f"🎥 {quality}"
        if f.language:
            label += f" {f.language}"
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"deliver:{movie_id}:{f.id}")]
        )
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"movie:{movie_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def series_episodes_keyboard(movie_id: int, episodes: list[MovieFile]) -> InlineKeyboardMarkup:
    """Keyboard listing a series' episodes for the user to pick."""
    rows = []
    for ep in episodes:
        label = f"🎬 Qism {ep.episode_number}"
        if ep.language:
            label += f" ({ep.language})"
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"deliver:{movie_id}:{ep.id}")]
        )
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"movie:{movie_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def pagination_keyboard(
    prefix: str, page: int, total_pages: int, movie_ids: list[int]
) -> InlineKeyboardMarkup:
    rows = []
    for movie_id in movie_ids:
        rows.append(
            [InlineKeyboardButton(text="🎬 Ko‘rish", callback_data=f"movie:{movie_id}")]
        )
    nav = []
    if page > 1:
        nav.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"{prefix}:{page - 1}")
        )
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"{prefix}:{page + 1}")
        )
    rows.append(nav)
    rows.append([InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
