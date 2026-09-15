"""Subscription verification handlers."""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.handlers.movie import _show_movie
from app.bot.keyboards.subscription import subscription_keyboard
from app.database.database import async_session_factory
from app.services.movie_service import MovieService
from app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

router = Router(name="subscription")


@router.callback_query(F.data == "check_subscription")
async def check_subscription(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id

    async with async_session_factory() as session:
        sub_service = SubscriptionService(callback.bot, session)
        subscribed, missing = await sub_service.check_all(user_id)

        if not subscribed:
            await sub_service.invalidate_membership_cache(user_id)
            text = (
                "❌ Hali barcha kanallarga obuna bo‘lmagansiz.\n\n"
                "Iltimos, barcha kanallarga obuna bo‘ling."
            )
            await callback.message.edit_text(
                text, reply_markup=subscription_keyboard(missing)
            )
            await callback.answer()
            return

        # Subscribed: continue pending movie request.
        pending_code = await sub_service.get_pending_movie(user_id)
        await sub_service.clear_pending_movie(user_id)

        if pending_code is not None:
            movie_service = MovieService(session)
            movie = await movie_service.get_by_code(pending_code)
            if movie is not None:
                await callback.message.edit_text("✅ Obuna tasdiqlandi!")
                await _show_movie(callback.message, movie, user_id)
                await callback.answer()
                return

    await callback.message.edit_text("✅ Obuna tasdiqlandi!")
    await callback.answer()
