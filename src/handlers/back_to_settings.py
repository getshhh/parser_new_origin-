# handlers/back_to_settings.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.callback_query(F.data == "back_to_main_settings")
async def back_to_main_settings(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Kwork", callback_data="settings_kwork")],
        [InlineKeyboardButton(text="Habr Career", callback_data="settings_habr")],
        [InlineKeyboardButton(text="FL", callback_data="settings_fl")],
        [InlineKeyboardButton(text="Guru", callback_data="settings_guru")],
        [InlineKeyboardButton(text="YouDo", callback_data="settings_youdo")],
    ])
    await callback.message.edit_text("Выберите парсер для настройки:", reply_markup=keyboard)
    await callback.answer()
