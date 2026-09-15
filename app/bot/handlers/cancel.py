"""Global /cancel handler and error handling."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

logger = logging.getLogger(__name__)

router = Router(name="cancel")


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer("❌ Amal bekor qilindi.")
        return
    await state.clear()
    await message.answer("❌ Amal bekor qilindi.")


@router.callback_query(F.data == "cancel")
async def cancel_callback(callback, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Amal bekor qilindi.")
    await callback.answer()
