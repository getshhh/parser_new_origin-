from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def settings_habr_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Изменить ключевые слова", callback_data="set_habr_keywords")],
        [InlineKeyboardButton(text="💰 Изменить зарплатный диапазон", callback_data="set_habr_salary")],
        [InlineKeyboardButton(text="📍 Изменить города", callback_data="set_habr_cities")],
        [InlineKeyboardButton(text="📢 Выбрать канал", callback_data="set_habr_channel")],
        [InlineKeyboardButton(text="⏰ Настроить интервал", callback_data="set_habr_interval")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_settings")]
    ])
