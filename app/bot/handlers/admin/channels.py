"""Admin mandatory channels management."""

import logging
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot.filters.filters import AdminFilter
from app.bot.keyboards.admin import admin_channel_actions_keyboard, admin_channels_keyboard
from app.bot.states.states import ChannelAddStates
from app.database.database import async_session_factory
from app.database.repositories import RequiredChannelRepository, SettingsRepository

logger = logging.getLogger(__name__)

router = Router(name="admin_channels")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())

CHANNEL_ID_PATTERN = re.compile(r"^-?\d+$")


@router.callback_query(F.data == "admin_channels")
async def channels_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text("📢 Majburiy kanallar", reply_markup=admin_channels_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_add_channel")
async def add_channel_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ChannelAddStates.waiting_for_channel_id)
    await callback.message.edit_text(
        "📢 Kanal username yoki ID sini yuboring.\n\n"
        "Masalan:\n@kino_olami\n\nyoki:\n-1001234567890"
    )
    await callback.answer()


@router.message(ChannelAddStates.waiting_for_channel_id)
async def add_channel_id(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    channel_id: int | None = None
    username: str | None = None

    if text.startswith("@"):
        username = text
    elif CHANNEL_ID_PATTERN.match(text):
        channel_id = int(text)
    else:
        await message.answer("❌ Kanal username yoki ID sini yuboring.")
        return

    await state.update_data(channel_id=channel_id, username=username)
    await state.set_state(ChannelAddStates.waiting_for_title)
    await message.answer("📝 Kanal nomini kiriting:")


@router.message(ChannelAddStates.waiting_for_title)
async def add_channel_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(ChannelAddStates.waiting_for_invite_url)
    await message.answer("🔗 Kanal havolasini yuboring:\n\nMasalan:\nhttps://t.me/kino_olami")


@router.message(ChannelAddStates.waiting_for_invite_url)
async def add_channel_url(message: Message, state: FSMContext) -> None:
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("❌ Havola http(s) bilan boshlanishi kerak.")
        return
    data = await state.get_data()
    await state.set_state(ChannelAddStates.confirmation)

    text = (
        "📢 Kanal\n\n"
        f"Nomi: {data.get('title')}\n"
        f"Username: {data.get('username') or '-'}\n"
        f"Havola: {url}\n\n"
        "Saqlansinmi?"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Saqlash", callback_data="channel_save")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="channel_cancel")],
        ]
    )
    await state.update_data(invite_url=url)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "channel_save")
async def channel_save(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    channel_id = data.get("channel_id")
    username = data.get("username")

    # If only username given, resolve the channel id via Telegram.
    if channel_id is None and username:
        try:
            chat = await callback.bot.get_chat(username)
            channel_id = chat.id
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not resolve channel %s: %s", username, exc)
            await callback.answer("❌ Kanal topilmadi. Bot kanalga qo‘shilganmi?", show_alert=True)
            return

    async with async_session_factory() as session:
        repo = RequiredChannelRepository(session)
        await repo.create(
            channel_id=channel_id,
            title=data.get("title"),
            username=username,
            invite_url=data.get("invite_url"),
        )
        await session.commit()

    await state.clear()
    await callback.message.edit_text("✅ Kanal qo‘shildi.")
    await callback.answer()


@router.callback_query(F.data == "channel_cancel")
async def channel_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.answer()


@router.callback_query(F.data == "admin_channel_list")
async def channel_list(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        repo = RequiredChannelRepository(session)
        channels = await repo.list_all()

    if not channels:
        await callback.message.edit_text("📋 Kanallar hozircha bo‘sh.")
        await callback.answer()
        return

    rows = []
    for ch in channels:
        status = "🟢" if ch.is_active else "🔴"
        rows.append(
            [InlineKeyboardButton(text=f"{status} {ch.title}", callback_data=f"admin_channel_view:{ch.id}")]
        )
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_channels")])
    await callback.message.edit_text(
        "📋 Kanallar:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_channel_view:"))
async def channel_view(callback: CallbackQuery) -> None:
    channel_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        repo = RequiredChannelRepository(session)
        ch = await repo.get_by_id(channel_id)
        if ch is None:
            await callback.answer("❌ Kanal topilmadi.", show_alert=True)
            return
    status = "🟢 Faol" if ch.is_active else "🔴 Noaktiv"
    text = (
        f"📢 {ch.title}\n\n"
        f"ID: {ch.channel_id}\n"
        f"Username: {ch.username or '-'}\n"
        f"Havola: {ch.invite_url or '-'}\n"
        f"Holat: {status}"
    )
    await callback.message.edit_text(text, reply_markup=admin_channel_actions_keyboard(channel_id))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_channel_toggle:"))
async def channel_toggle(callback: CallbackQuery) -> None:
    channel_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        repo = RequiredChannelRepository(session)
        ch = await repo.get_by_id(channel_id)
        if ch is None:
            await callback.answer("❌ Kanal topilmadi.", show_alert=True)
            return
        await repo.update(ch, is_active=not ch.is_active)
        await session.commit()
    await callback.answer("✅ Holat o‘zgartirildi.")
    await channel_view(callback)


@router.callback_query(F.data.startswith("admin_channel_delete:"))
async def channel_delete(callback: CallbackQuery) -> None:
    channel_id = int(callback.data.split(":")[1])
    async with async_session_factory() as session:
        repo = RequiredChannelRepository(session)
        ch = await repo.get_by_id(channel_id)
        if ch is None:
            await callback.answer("❌ Kanal topilmadi.", show_alert=True)
            return
        await repo.delete(ch)
        await session.commit()
    await callback.message.edit_text("🗑 Kanal o‘chirildi.")
    await callback.answer()


@router.callback_query(F.data == "admin_toggle_subscription")
async def toggle_subscription(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        repo = SettingsRepository(session)
        current = await repo.get_bool("mandatory_subscription_enabled", default=False)
        await repo.set_bool("mandatory_subscription_enabled", not current)
        await session.commit()
        new_value = not current
    status = "🟢 Yoqilgan" if new_value else "🔴 O‘chirilgan"
    await callback.message.edit_text(f"🔐 Majburiy obuna: {status}")
    await callback.answer()
