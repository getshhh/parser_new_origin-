from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="▶️ Включить парсер"), KeyboardButton(text="⏹️ Выключить парсер")],
            [KeyboardButton(text="⏹️ Выключить все парсеры")]
        ],
        resize_keyboard=True
    )
