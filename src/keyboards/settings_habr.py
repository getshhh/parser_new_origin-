from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def settings_habr_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Изменить зарплатный диапазон", callback_data="set_habr_salary")],
        [InlineKeyboardButton(text="📍 Изменить города", callback_data="set_habr_cities")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_habr")]
    ])
