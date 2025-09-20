# keyboards/parser_settings.py
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_parser_settings_kb(parser_name: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Изменить ключевые слова", callback_data=f"set_{parser_name}_keywords")],
        [InlineKeyboardButton(text="💰 Изменить ценовой диапазон", callback_data=f"set_{parser_name}_price")],
        [InlineKeyboardButton(text="📢 Выбрать канал", callback_data=f"set_{parser_name}_channel")],
        [InlineKeyboardButton(text="⏰ Настроить интервал", callback_data=f"set_{parser_name}_interval")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_settings")]
    ])

def get_channel_selection_kb(parser_name: str, channels: list):
    keyboard = []
    for chat_id, title in channels:
        keyboard.append([InlineKeyboardButton(text=f"📢 {title}", callback_data=f"select_{parser_name}_channel_{chat_id}")])
    keyboard.append([InlineKeyboardButton(text="❌ Без канала", callback_data=f"remove_{parser_name}_channel")])
    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"settings_{parser_name}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_interval_selection_kb(parser_name: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="30 сек", callback_data=f"set_{parser_name}_interval_30")],
        [InlineKeyboardButton(text="60 сек", callback_data=f"set_{parser_name}_interval_60")],
        [InlineKeyboardButton(text="120 сек", callback_data=f"set_{parser_name}_interval_120")],
        [InlineKeyboardButton(text="300 сек", callback_data=f"set_{parser_name}_interval_300")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"settings_{parser_name}")]
    ])