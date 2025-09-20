from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def settings_youdo_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Настройки каналов", callback_data="channel_settings_youdo")],
        [InlineKeyboardButton(text="💰 Изменить ценовой диапазон", callback_data="set_youdo_price")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_settings")]
    ])
