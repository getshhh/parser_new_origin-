from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from keyboards.settings import settings_root_kb  # ✅

router = Router()

@router.message(Command("settings"))
@router.message(F.text == "⚙️ Настройки")
async def open_settings_menu(message: Message):
    await message.answer("Выберите парсер для настройки:", reply_markup=settings_root_kb())

@router.callback_query(F.data == "back_to_main_settings")
async def back_to_main_settings(callback: CallbackQuery):
    await callback.message.edit_text("Выберите парсер для настройки:", reply_markup=settings_root_kb())
    await callback.answer()
