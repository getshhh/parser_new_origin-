# keyboards/settings_kwork.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def settings_kwork_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Настройки каналов", callback_data="channel_settings_kwork")],
        [InlineKeyboardButton(text="💰 Изменить ценовой диапазон", callback_data="set_kwork_price")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_settings")]
    ])