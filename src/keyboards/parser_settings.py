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

def get_channel_selection_kb(parser_name: str, channels: list, action: str):
    keyboard = []
    for channel in channels:
        keyboard.append([InlineKeyboardButton(text=f"📢 {channel['name']}", callback_data=f"select_channel_{action}_{parser_name}_{channel['id']}")])
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

def get_back_to_parser_settings_kb(parser_name: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к настройкам", callback_data=f"settings_{parser_name}")]
    ])