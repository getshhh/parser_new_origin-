from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database.database import Database

from .states import Form
from keyboards.settings_habr import settings_habr_kb

router = Router()
db = Database()

# -----------------------------
# меню настроек Habr
# -----------------------------
@router.callback_query(F.data == "settings_habr")
async def settings_habr(callback: CallbackQuery, state: FSMContext):
    parser_settings = db.get_parser_settings('habr')
    message_interval = parser_settings.get("message_interval") if parser_settings else None
    interval_text = f"{message_interval} сек." if message_interval is not None else "не задан"

    channels = db.get_parser_channels('habr')

    channels_info = []
    if channels:
        for channel in channels:
            try:
                chat = await callback.bot.get_chat(channel["channel_id"])
                channel_name = f"@{chat.username}" if chat.username else chat.title
                keywords = channel['keywords'] if channel['keywords'] else 'нет'
                minus_words = channel['minus_words'] if channel['minus_words'] else 'нет'
                price_range = f"от {channel['min_price']} до {channel['max_price']}" if channel['min_price'] is not None and channel['max_price'] is not None else 'не задан'
                channels_info.append(f"▶️ **{channel_name}**\n   - Ключи: *{keywords}*\n   - Минус-слова: *{minus_words}*\n   - Зарплата: *{price_range}*")
            except Exception:
                channels_info.append(f"▶️ ID: {channel['channel_id']} (нет доступа?)")

    settings_text = (
        "⚙️ **Настройки Habr Career**\n\n"
        f"**Интервал сообщений:** {interval_text}\n\n"
        "**Подключенные каналы:**\n"
    )
    if channels_info:
        settings_text += "\n\n".join(channels_info)
    else:
        settings_text += "Каналы не подключены."

    await callback.message.edit_text(
        settings_text,
        reply_markup=settings_habr_kb(channels),
        parse_mode="Markdown"
    )
    await callback.answer()

# -----------------------------
# Добавление канала
# -----------------------------
@router.callback_query(F.data == "add_habr_channel")
async def add_habr_channel(callback: CallbackQuery):
    channels = db.list_channels()
    if not channels:
        await callback.answer("Бот не является администратором ни в одном канале.", show_alert=True)
        return

    buttons = [
        [InlineKeyboardButton(text=title, callback_data=f"habr_select_channel_{chat_id}")]
        for chat_id, title in channels
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="settings_habr")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("Выберите канал для добавления:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("habr_select_channel_"))
async def select_habr_channel(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split("_")[-1])
    try:
        db.add_parser_channel('habr', channel_id)
        await callback.answer("✅ Канал добавлен!")
    except Exception as e:
        await callback.answer(f"❗️ Ошибка при добавлении канала: {e}", show_alert=True)
    await settings_habr(callback, state)

# -----------------------------
# Удаление канала
# -----------------------------
@router.callback_query(F.data.startswith("remove_habr_channel_"))
async def remove_habr_channel(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split("_")[-1])
    db.delete_parser_channel('habr', channel_id)
    await callback.answer("✅ Канал удален!")
    await settings_habr(callback, state)

# -----------------------------
# Настройка ключевых слов
# -----------------------------
@router.callback_query(F.data.startswith("set_habr_keywords_"))
async def set_habr_keywords_for_channel(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split("_")[-1])
    await state.update_data(channel_id=channel_id)
    await callback.message.edit_text("Введите ключевые слова через запятую (или '-', если не нужны):")
    await state.set_state(Form.setting_habr_keywords)

@router.message(Form.setting_habr_keywords)
async def process_habr_keywords(message: Message, state: FSMContext):
    data = await state.get_data()
    channel_id = data.get("channel_id")
    settings = db.get_parser_channel_settings('habr', channel_id)
    if settings:
        keywords = message.text if message.text != '-' else ''
        db.update_parser_channel_keywords(settings['id'], keywords)
        await message.answer("✅ Ключевые слова обновлены.")
    await state.clear()

    # Создаем фейковый CallbackQuery для вызова меню
    callback_query = type('obj', (object,), {
        'data': 'settings_habr',
        'message': message,
        'from_user': message.from_user,
        'bot': message.bot,
        'answer': lambda: None
    })
    await settings_habr(callback_query, state)

# -----------------------------
# Настройка минус-слов
# -----------------------------
@router.callback_query(F.data.startswith("set_habr_minus_words_"))
async def set_habr_minus_words_for_channel(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split("_")[-1])
    await state.update_data(channel_id=channel_id)
    await callback.message.edit_text("Введите минус-слова через запятую (или '-', если не нужны):")
    await state.set_state(Form.setting_habr_minus_words)

@router.message(Form.setting_habr_minus_words)
async def process_habr_minus_words(message: Message, state: FSMContext):
    data = await state.get_data()
    channel_id = data.get("channel_id")
    settings = db.get_parser_channel_settings('habr', channel_id)
    if settings:
        minus_words = message.text if message.text != '-' else ''
        db.update_parser_channel_minus_words(settings['id'], minus_words)
        await message.answer("✅ Минус-слова обновлены.")
    await state.clear()

    # Создаем фейковый CallbackQuery для вызова меню
    callback_query = type('obj', (object,), {
        'data': 'settings_habr',
        'message': message,
        'from_user': message.from_user,
        'bot': message.bot,
        'answer': lambda: None
    })
    await settings_habr(callback_query, state)

# -----------------------------
# изменение диапазона зарплат
# -----------------------------
@router.callback_query(F.data.startswith("set_habr_salary_"))
async def set_habr_salary(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split("_")[-1])
    await state.update_data(channel_id=channel_id)
    await callback.message.edit_text("Введите минимальную зарплату:")
    await state.set_state(Form.setting_habr_salary_min)

@router.message(Form.setting_habr_salary_min)
async def process_habr_salary_min(message: Message, state: FSMContext):
    try:
        min_salary = int(message.text)
        await state.update_data(min_salary=min_salary)
        await message.answer("Теперь введите максимальную зарплату:")
        await state.set_state(Form.setting_habr_salary_max)
    except ValueError:
        await message.answer("❌ Введите число!")

@router.message(Form.setting_habr_salary_max)
async def process_habr_salary_max(message: Message, state: FSMContext):
    try:
        max_salary = int(message.text)
        data = await state.get_data()
        channel_id = data.get("channel_id")
        min_salary = data.get("min_salary")
        settings = db.get_parser_channel_settings('habr', channel_id)
        if settings:
            db.update_parser_channel_price_range(settings['id'], min_salary, max_salary)
            await message.answer(f"✅ Зарплатный диапазон обновлён: {min_salary} - {max_salary} руб.")
        await state.clear()

        # Создаем фейковый CallbackQuery для вызова меню
        callback_query = type('obj', (object,), {
            'data': 'settings_habr',
            'message': message,
            'from_user': message.from_user,
            'bot': message.bot,
            'answer': lambda: None
        })
        await settings_habr(callback_query, state)
    except ValueError:
        await message.answer("❌ Введите число!")

# -----------------------------
# Настройка интервала для Habr
# -----------------------------
@router.callback_query(F.data == "set_habr_interval")
async def set_habr_interval(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите интервал между сообщениями в секундах:")
    await state.set_state(Form.setting_habr_interval)
    await callback.answer()

@router.message(Form.setting_habr_interval)
async def process_habr_interval(message: Message, state: FSMContext):
    try:
        interval = int(message.text)
        if interval <= 0:
            await message.answer("❌ Интервал должен быть положительным числом. Попробуйте еще раз.")
            return

        db.set_parser_interval('habr', interval)
        await message.answer(f"✅ Интервал для Habr установлен: {interval} сек.")
        await state.clear()

    except ValueError:
        await message.answer("❌ Введите число!")
