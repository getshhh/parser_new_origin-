# keyboards/settings_vk.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def settings_vk_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Изменить ключевые слова", callback_data="set_vk_keywords")],
        [InlineKeyboardButton(text="💰 Изменить ценовой диапазон", callback_data="set_vk_price")],
        [InlineKeyboardButton(text="👥 Изменить ID групп", callback_data="set_vk_groups")],
        [InlineKeyboardButton(text="📢 Выбрать канал", callback_data="set_vk_channel")],
        [InlineKeyboardButton(text="⏰ Настроить интервал", callback_data="set_vk_interval")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_settings")]
    ])