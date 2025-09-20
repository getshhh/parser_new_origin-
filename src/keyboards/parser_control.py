from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def enable_parsers_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Kwork", callback_data="enable_kwork")],
        [InlineKeyboardButton(text="Habr Career", callback_data="enable_habr")],
        [InlineKeyboardButton(text="FL", callback_data="enable_fl")],
        [InlineKeyboardButton(text="Guru", callback_data="enable_guru")],
        [InlineKeyboardButton(text="YouDo", callback_data="enable_youdo")],
        [InlineKeyboardButton(text="VK", callback_data="enable_vk")],
        [InlineKeyboardButton(text="WebLancer", callback_data="enable_weblancer")],
        [InlineKeyboardButton(text="Work-Zilla", callback_data="enable_workzilla")],
        [InlineKeyboardButton(text="WebLancer", callback_data="enable_weblancer")],
        [InlineKeyboardButton(text="Включить все", callback_data="enable_all")]
    ])

def disable_parsers_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Kwork", callback_data="disable_kwork")],
        [InlineKeyboardButton(text="Habr Career", callback_data="disable_habr")],
        [InlineKeyboardButton(text="FL", callback_data="disable_fl")],
        [InlineKeyboardButton(text="Guru", callback_data="disable_guru")],
        [InlineKeyboardButton(text="YouDo", callback_data="disable_youdo")],
        [InlineKeyboardButton(text="VK", callback_data="disable_vk")],
        [InlineKeyboardButton(text="WebLancer", callback_data="disable_weblancer")],
        [InlineKeyboardButton(text="Work-Zilla", callback_data="disable_workzilla")], 
        [InlineKeyboardButton(text="WebLancer", callback_data="disable_weblancer")],
        [InlineKeyboardButton(text="Выключить все", callback_data="disable_all")]
    ])