# keyboards/settings.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def settings_root_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Kwork", callback_data="settings_kwork")],
        [InlineKeyboardButton(text="Habr Career", callback_data="settings_habr")],
        [InlineKeyboardButton(text="FL", callback_data="settings_fl")],
        [InlineKeyboardButton(text="Guru", callback_data="settings_guru")],
        [InlineKeyboardButton(text="YouDo", callback_data="settings_youdo")],
        [InlineKeyboardButton(text="VK", callback_data="settings_vk")],  # ✅ добавлена кнопка VK
        [InlineKeyboardButton(text="Work-Zilla", callback_data="settings_workzilla")],  
        [InlineKeyboardButton(text="WebLancer", callback_data="settings_weblancer")],
        [InlineKeyboardButton(text="GPT", callback_data="settings_gpt")],
    ])