from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def settings_weblancer_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Настройки каналов", callback_data="channel_settings_weblancer")],
        [InlineKeyboardButton(text="💰 Изменить ценовой диапазон", callback_data="set_weblancer_price")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_settings")]
    ])