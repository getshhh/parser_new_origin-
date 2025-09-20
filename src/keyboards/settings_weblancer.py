from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def settings_weblancer_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Изменить ключевые слова", callback_data="set_weblancer_keywords")],
        [InlineKeyboardButton(text="💰 Изменить ценовой диапазон", callback_data="set_weblancer_price")],
        [InlineKeyboardButton(text="📢 Выбрать канал", callback_data="set_weblancer_channel")],
        [InlineKeyboardButton(text="⏰ Настроить интервал", callback_data="set_weblancer_interval")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_settings")]
    ])