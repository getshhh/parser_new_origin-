from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def settings_habr_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Настройки каналов", callback_data="channel_settings_habr")],
        [InlineKeyboardButton(text="💰 Изменить зарплатный диапазон", callback_data="set_habr_salary")],
        [InlineKeyboardButton(text="📍 Изменить города", callback_data="set_habr_cities")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_settings")]
    ])
