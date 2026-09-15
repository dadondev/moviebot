"""Admin broadcast and movie requests."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.filters.filters import AdminFilter
from app.bot.keyboards.admin import admin_broadcast_keyboard, admin_requests_keyboard
from app.bot.states.states import BroadcastStates
from app.database.database import async_session_factory
from app.services.broadcast_service import BroadcastService
from app.services.request_service import RequestService

logger = logging.getLogger(__name__)

router = Router(name="admin_broadcast")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


# --- Broadcast ---
@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BroadcastStates.waiting_for_message)
    await callback.message.edit_text("📢 Reklama xabarini yuboring:")
    await callback.answer()


@router.message(BroadcastStates.waiting_for_message)
async def broadcast_preview(message: Message, state: FSMContext) -> None:
    await state.update_data(broadcast_message_id=message.message_id)
    await message.answer(
        "📢 Xabar:\n\n...\n\nYuborilsinmi?", reply_markup=admin_broadcast_keyboard()
    )


@router.callback_query(F.data == "broadcast_send")
async def broadcast_send(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    msg_id = data.get("broadcast_message_id")
    if not msg_id:
        await callback.answer("❌ Xabar topilmadi.", show_alert=True)
        return

    async with async_session_factory() as session:
        service = BroadcastService(callback.bot, session)
        result = await service.broadcast(callback.message)

    await state.clear()
    await callback.message.edit_text(
        f"📢 Reklama yuborildi!\n\n"
        f"✅ Yuborildi: {result['sent']}\n"
        f"❌ Xato: {result['failed']}\n"
        f"🚫 Bloklangan: {result['blocked']}"
    )
    await callback.answer()


@router.callback_query(F.data == "broadcast_cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Reklama bekor qilindi.")
    await callback.answer()


# --- Movie requests ---
@router.callback_query(F.data == "admin_requests")
async def requests_menu(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        service = RequestService(session)
        requests = await service.list_pending(limit=20)

    if not requests:
        await callback.message.edit_text("📩 Kino so‘rovlari hozircha yo‘q.")
        await callback.answer()
        return

    await callback.message.edit_text(
        "📩 Kino so‘rovlari:", reply_markup=admin_requests_keyboard(requests)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_request_found:"))
async def request_found(callback: CallbackQuery) -> None:
    request_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        service = RequestService(session)
        await service.set_status(request_id, "found")
        await session.commit()
    await callback.answer("✅ Topildi deb belgilandi.")
    await requests_menu(callback)


@router.callback_query(F.data.startswith("admin_request_reject:"))
async def request_reject(callback: CallbackQuery) -> None:
    request_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        service = RequestService(session)
        await service.set_status(request_id, "rejected")
        await session.commit()
    await callback.answer("❌ Rad etildi.")
    await requests_menu(callback)
