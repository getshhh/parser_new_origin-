from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict

def settings_guru_kb(channels: List[Dict]) -> InlineKeyboardMarkup:
    buttons = []
    for channel in channels:
        channel_id = channel['channel_id']
        buttons.extend([
            [
                InlineKeyboardButton(text="🔑 Ключи", callback_data=f"set_guru_keywords_{channel_id}"),
                InlineKeyboardButton(text="⛔️ Минус-слова", callback_data=f"set_guru_minus_words_{channel_id}"),
            ],
            [
                InlineKeyboardButton(text="💰 Цена", callback_data=f"set_guru_price_{channel_id}"),
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"remove_guru_channel_{channel_id}")
            ]
        ])

    buttons.append([InlineKeyboardButton(text="➕ Добавить канал", callback_data="add_guru_channel")])
    buttons.append([InlineKeyboardButton(text="⏰ Настроить интервал", callback_data="set_guru_interval")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_settings")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
