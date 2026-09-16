"""Movie request handlers."""

import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.states import RequestStates
from app.config import settings
from app.database.database import async_session_factory
from app.services.request_service import RequestService

logger = logging.getLogger(__name__)

router = Router(name="requests")


async def start_request(message: Message, state: FSMContext) -> None:
    await message.answer("🎬 Qaysi kinoni izlayapsiz?\n\nKino nomini yuboring:")
    await state.set_state(RequestStates.waiting_for_title)


@router.message(RequestStates.waiting_for_title)
async def process_request(message: Message, state: FSMContext) -> None:
    title = message.text.strip()
    if not title:
        await message.answer("❌ Kino nomini yozing.")
        return

    async with async_session_factory() as session:
        request_service = RequestService(session)
        await request_service.create(message.from_user.id, title)
        await session.commit()

    await state.clear()
    await message.answer("✅ So‘rovingiz qabul qilindi. Admin tez orada ko‘rib chiqadi.")

    # Notify admins.
    for admin_id in settings.admin_id_list:
        try:
            await message.bot.send_message(
                admin_id,
                f"📩 Yangi kino so‘rovi!\n\n"
                f"🎬 {title}\n"
                f"👤 @{message.from_user.username or message.from_user.first_name}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not notify admin %s: %s", admin_id, exc)
