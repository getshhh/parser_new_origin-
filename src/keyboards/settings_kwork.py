# keyboards/settings_kwork.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def settings_kwork_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Изменить ключевые слова", callback_data="set_kwork_keywords")],
        [InlineKeyboardButton(text="💰 Изменить ценовой диапазон", callback_data="set_kwork_price")],
        [InlineKeyboardButton(text="📢 Выбрать канал", callback_data="set_kwork_channel")],
        [InlineKeyboardButton(text="⏰ Настроить интервал", callback_data="set_kwork_interval")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_settings")]
    ])