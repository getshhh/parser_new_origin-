# keyboards/settings_workzilla.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def settings_workzilla_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Изменить ценовой диапазон", callback_data="set_workzilla_price")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_workzilla")]
    ])