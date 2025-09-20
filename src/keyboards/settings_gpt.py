# src/keyboards/settings_gpt.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def settings_gpt_kb(status: str) -> InlineKeyboardMarkup:
    if status == "running":
        button_text = "Остановить GPT"
        callback_data = "stop_gpt"
    else:
        button_text = "Запустить GPT"
        callback_data = "start_gpt"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=button_text, callback_data=callback_data)],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main_settings")]
    ])
