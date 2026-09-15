"""Admin keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.database.models import Genre, Movie


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Kino qo‘shish", callback_data="admin_add_movie")],
            [InlineKeyboardButton(text="🎬 Kinolar", callback_data="admin_movies")],
            [InlineKeyboardButton(text="📢 Majburiy kanallar", callback_data="admin_channels")],
            [InlineKeyboardButton(text="🎭 Janrlar", callback_data="admin_genres")],
            [InlineKeyboardButton(text="📩 Kino so‘rovlari", callback_data="admin_requests")],
            [InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users")],
            [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📢 Reklama", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="admin_settings")],
        ]
    )


def admin_movies_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔎 Kino qidirish", callback_data="admin_movie_search")],
            [InlineKeyboardButton(text="📋 Barcha kinolar", callback_data="admin_movie_list:1")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_menu")],
        ]
    )


def admin_movie_actions_keyboard(movie_id: int, is_series: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"admin_edit:{movie_id}")],
        [InlineKeyboardButton(text="🗑 O‘chirish", callback_data=f"admin_delete:{movie_id}")],
    ]
    if is_series:
        rows.insert(
            1,
            [InlineKeyboardButton(text="➕ Qism qo‘shish", callback_data=f"admin_add_episode:{movie_id}")],
        )
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_movies")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_edit_keyboard(movie_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Nomi", callback_data=f"edit_field:{movie_id}:title")],
            [InlineKeyboardButton(text="🌍 Original nomi", callback_data=f"edit_field:{movie_id}:original_title")],
            [InlineKeyboardButton(text="🔢 Kod", callback_data=f"edit_field:{movie_id}:code")],
            [InlineKeyboardButton(text="📝 Tavsif", callback_data=f"edit_field:{movie_id}:description")],
            [InlineKeyboardButton(text="📅 Yil", callback_data=f"edit_field:{movie_id}:year")],
            [InlineKeyboardButton(text="🎭 Janrlar", callback_data=f"edit_field:{movie_id}:genres")],
            [InlineKeyboardButton(text="🌍 Davlat", callback_data=f"edit_field:{movie_id}:country")],
            [InlineKeyboardButton(text="⏱ Davomiylik", callback_data=f"edit_field:{movie_id}:duration")],
            [InlineKeyboardButton(text="⭐ IMDb", callback_data=f"edit_field:{movie_id}:imdb_rating")],
            [InlineKeyboardButton(text="🔞 Yosh chegarasi", callback_data=f"edit_field:{movie_id}:age_rating")],
            [InlineKeyboardButton(text="🖼 Poster", callback_data=f"edit_field:{movie_id}:poster")],
            [InlineKeyboardButton(text="🎞 Treyler", callback_data=f"edit_field:{movie_id}:trailer_url")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"admin_view:{movie_id}")],
        ]
    )


def admin_channels_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Kanal qo‘shish", callback_data="admin_add_channel")],
            [InlineKeyboardButton(text="📋 Kanallar", callback_data="admin_channel_list")],
            [InlineKeyboardButton(text="🔐 Majburiy obuna", callback_data="admin_toggle_subscription")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_menu")],
        ]
    )


def admin_channel_actions_keyboard(channel_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"admin_channel_edit:{channel_id}")],
            [InlineKeyboardButton(text="🗑 O‘chirish", callback_data=f"admin_channel_delete:{channel_id}")],
            [InlineKeyboardButton(text="🟢/🔴 Faollashtirish", callback_data=f"admin_channel_toggle:{channel_id}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_channel_list")],
        ]
    )


def admin_genres_keyboard(genres: list[Genre]) -> InlineKeyboardMarkup:
    rows = []
    for genre in genres:
        rows.append(
            [InlineKeyboardButton(text=f"🗑 {genre.name}", callback_data=f"admin_genre_delete:{genre.id}")]
        )
    rows.append([InlineKeyboardButton(text="➕ Janr qo‘shish", callback_data="admin_genre_add")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_requests_keyboard(requests) -> InlineKeyboardMarkup:
    rows = []
    for req in requests:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"✅ {req.movie_title}",
                    callback_data=f"admin_request_found:{req.id}",
                ),
                InlineKeyboardButton(
                    text=f"❌ {req.movie_title}",
                    callback_data=f"admin_request_reject:{req.id}",
                ),
            ]
        )
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_broadcast_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Yuborish", callback_data="broadcast_send")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="broadcast_cancel")],
        ]
    )


def admin_settings_keyboard(mandatory_enabled: bool) -> InlineKeyboardMarkup:
    status = "🟢 Yoqilgan" if mandatory_enabled else "🔴 O‘chirilgan"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🔐 Majburiy obuna: {status}",
                    callback_data="admin_toggle_subscription",
                )
            ],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_menu")],
        ]
    )


def admin_movie_list_keyboard(movies: list[Movie], page: int, total_pages: int) -> InlineKeyboardMarkup:
    rows = []
    for movie in movies:
        rows.append(
            [InlineKeyboardButton(text=f"🎬 {movie.title}", callback_data=f"admin_view:{movie.id}")]
        )
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_movie_list:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_movie_list:{page + 1}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_movies")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
