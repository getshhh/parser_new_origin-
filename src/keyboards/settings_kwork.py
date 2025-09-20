# keyboards/settings_kwork.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def settings_kwork_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Изменить ценовой диапазон", callback_data="set_kwork_price")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_kwork")]
    ])