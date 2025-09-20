from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database.database import Database

from .states import Form

db = Database()

def create_generic_handlers(parser_name: str, settings_callback: str):
    router = Router()

    @router.callback_query(F.data == f"add_{parser_name}_channel")
    async def add_channel(callback: CallbackQuery):
        channels = db.list_channels()
        if not channels:
            await callback.answer("Бот не является администратором ни в одном канале.", show_alert=True)
            return

        buttons = [
            [InlineKeyboardButton(text=title, callback_data=f"{parser_name}_select_channel_{chat_id}")]
            for chat_id, title in channels
        ]
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=settings_callback)])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text("Выберите канал для добавления:", reply_markup=keyboard)

    @router.callback_query(F.data.startswith(f"{parser_name}_select_channel_"))
    async def select_channel(callback: CallbackQuery, state: FSMContext):
        channel_id = int(callback.data.split("_")[-1])
        try:
            db.add_parser_channel(parser_name, channel_id)
            await callback.answer("✅ Канал добавлен!")
        except Exception as e:
            await callback.answer(f"❗️ Ошибка при добавлении канала: {e}", show_alert=True)

        callback.data = settings_callback
        await globals()[f"settings_{parser_name}"](callback, state)

    @router.callback_query(F.data.startswith(f"remove_{parser_name}_channel_"))
    async def remove_channel(callback: CallbackQuery, state: FSMContext):
        channel_id = int(callback.data.split("_")[-1])
        db.delete_parser_channel(parser_name, channel_id)
        await callback.answer("✅ Канал удален!")
        callback.data = settings_callback
        await globals()[f"settings_{parser_name}"](callback, state)

    @router.callback_query(F.data.startswith(f"set_{parser_name}_keywords_"))
    async def set_keywords_for_channel(callback: CallbackQuery, state: FSMContext):
        channel_id = int(callback.data.split("_")[-1])
        await state.update_data(channel_id=channel_id, parser_name=parser_name, settings_callback=settings_callback)
        await callback.message.edit_text("Введите ключевые слова через запятую (или '-', если не нужны):")
        await state.set_state(Form.setting_keywords)

    @router.callback_query(F.data.startswith(f"set_{parser_name}_minus_words_"))
    async def set_minus_words_for_channel(callback: CallbackQuery, state: FSMContext):
        channel_id = int(callback.data.split("_")[-1])
        await state.update_data(channel_id=channel_id, parser_name=parser_name, settings_callback=settings_callback)
        await callback.message.edit_text("Введите минус-слова через запятую (или '-', если не нужны):")
        await state.set_state(Form.setting_minus_words)

    @router.callback_query(F.data.startswith(f"set_{parser_name}_price_"))
    async def set_price(callback: CallbackQuery, state: FSMContext):
        channel_id = int(callback.data.split("_")[-1])
        await state.update_data(channel_id=channel_id, parser_name=parser_name, settings_callback=settings_callback)
        await callback.message.edit_text("Введите минимальную цену:")
        await state.set_state(Form.setting_price_min)

    return router

@F.state == Form.setting_keywords
async def process_keywords(message: Message, state: FSMContext):
    data = await state.get_data()
    channel_id = data.get("channel_id")
    parser_name = data.get("parser_name")
    settings_callback = data.get("settings_callback")

    settings = db.get_parser_channel_settings(parser_name, channel_id)
    if settings:
        keywords = message.text if message.text != '-' else ''
        db.update_parser_channel_keywords(settings['id'], keywords)
        await message.answer("✅ Ключевые слова обновлены.")
    await state.clear()

    callback_query = type('obj', (object,), {
        'data': settings_callback,
        'message': message,
        'from_user': message.from_user,
        'bot': message.bot,
        'answer': lambda: None
    })
    await globals()[f"settings_{parser_name}"](callback_query, state)

@F.state == Form.setting_minus_words
async def process_minus_words(message: Message, state: FSMContext):
    data = await state.get_data()
    channel_id = data.get("channel_id")
    parser_name = data.get("parser_name")
    settings_callback = data.get("settings_callback")

    settings = db.get_parser_channel_settings(parser_name, channel_id)
    if settings:
        minus_words = message.text if message.text != '-' else ''
        db.update_parser_channel_minus_words(settings['id'], minus_words)
        await message.answer("✅ Минус-слова обновлены.")
    await state.clear()

    callback_query = type('obj', (object,), {
        'data': settings_callback,
        'message': message,
        'from_user': message.from_user,
        'bot': message.bot,
        'answer': lambda: None
    })
    await globals()[f"settings_{parser_name}"](callback_query, state)

@F.state == Form.setting_price_min
async def process_price_min(message: Message, state: FSMContext):
    try:
        min_price = int(message.text)
        await state.update_data(min_price=min_price)
        await message.answer("Теперь введите максимальную цену:")
        await state.set_state(Form.setting_price_max)
    except ValueError:
        await message.answer("❌ Введите число!")

@F.state == Form.setting_price_max
async def process_price_max(message: Message, state: FSMContext):
    try:
        max_price = int(message.text)
        data = await state.get_data()
        channel_id = data.get("channel_id")
        parser_name = data.get("parser_name")
        settings_callback = data.get("settings_callback")
        min_price = data.get("min_price")

        settings = db.get_parser_channel_settings(parser_name, channel_id)
        if settings:
            db.update_parser_channel_price_range(settings['id'], min_price, max_price)
            await message.answer(f"✅ Ценовой диапазон обновлён: {min_price} - {max_price} руб.")
        await state.clear()

        callback_query = type('obj', (object,), {
            'data': settings_callback,
            'message': message,
            'from_user': message.from_user,
            'bot': message.bot,
            'answer': lambda: None
        })
        await globals()[f"settings_{parser_name}"](callback_query, state)
    except ValueError:
        await message.answer("❌ Введите число!")
