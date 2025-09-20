from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def settings_guru_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Изменить ценовой диапазон", callback_data="set_guru_price")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_guru")]
    ])
