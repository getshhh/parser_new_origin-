# keyboards/settings_vk.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def settings_vk_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Изменить ценовой диапазон", callback_data="set_vk_price")],
        [InlineKeyboardButton(text="👥 Изменить ID групп", callback_data="set_vk_groups")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_vk")]
    ])