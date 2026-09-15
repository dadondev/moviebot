"""Admin users and statistics."""

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.filters.filters import AdminFilter
from app.database.database import async_session_factory
from app.database.repositories import UserRepository
from app.services.statistics_service import StatisticsService

router = Router(name="admin_users")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.callback_query(F.data == "admin_users")
async def users_menu(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        repo = UserRepository(session)
        total = await repo.count_all()
    await callback.message.edit_text(f"👥 Jami foydalanuvchilar: {total:,}")
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def stats_menu(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        stats_service = StatisticsService(session)
        stats = await stats_service.get_summary()

    text = (
        "📊 Statistika\n\n"
        f"👥 Jami foydalanuvchilar: {stats['total_users']:,}\n"
        f"🟢 Faol foydalanuvchilar: {stats['active_users']:,}\n\n"
        f"🎬 Jami kinolar: {stats['total_movies']:,}\n"
        f"👁 Jami ko‘rishlar: {stats['total_views']:,}\n\n"
        f"📩 Kutilayotgan so‘rovlar: {stats['pending_requests']}\n\n"
        f"🆕 Bugungi yangi foydalanuvchilar: {stats['new_users_today']}\n"
        f"🆕 Bugungi yangi kinolar: {stats['new_movies_today']}\n"
    )
    if stats["most_viewed"]:
        text += f"\n🔥 Eng mashhur kino: {stats['most_viewed'].title}"
    if stats["most_rated"]:
        text += f"\n⭐ Eng ko‘p baholangan: {stats['most_rated'].title}"
    if stats["most_favorited"]:
        text += f"\n❤️ Eng ko‘p sevimlida: {stats['most_favorited'].title}"

    await callback.message.edit_text(text)
    await callback.answer()
