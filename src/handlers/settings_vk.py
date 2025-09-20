from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database.database import Database

from .states import Form
from keyboards.settings_vk import settings_vk_kb
import re

router = Router()
db = Database()

# -----------------------------
# меню настроек VK
# -----------------------------
@router.callback_query(F.data == "settings_vk")
async def settings_vk(callback: CallbackQuery, state: FSMContext):
    parser_settings = db.get_parser_settings('vk')
    message_interval = parser_settings.get("message_interval") if parser_settings else None
    interval_text = f"{message_interval} сек." if message_interval is not None else "не задан"

    channels = db.get_parser_channels('vk')

    channels_info = []
    if channels:
        for channel in channels:
            try:
                chat = await callback.bot.get_chat(channel["channel_id"])
                channel_name = f"@{chat.username}" if chat.username else chat.title
                keywords = channel['keywords'] if channel['keywords'] else 'нет'
                minus_words = channel['minus_words'] if channel['minus_words'] else 'нет'
                price_range = f"от {channel['min_price']} до {channel['max_price']}" if channel['min_price'] is not None and channel['max_price'] is not None else 'не задан'
                channels_info.append(f"▶️ **{channel_name}**\n   - Ключи: *{keywords}*\n   - Минус-слова: *{minus_words}*\n   - Цена: *{price_range}*")
            except Exception:
                channels_info.append(f"▶️ ID: {channel['channel_id']} (нет доступа?)")
    
    settings = db.get_vk_settings()
    group_ids = settings.get('group_ids', [])

    settings_text = (
        "⚙️ **Настройки VK**\n\n"
        f"**ID групп:** {', '.join(group_ids) if group_ids else 'Не заданы'}\n"
        f"**Интервал сообщений:** {interval_text}\n\n"
        "**Подключенные каналы:**\n"
    )
    if channels_info:
        settings_text += "\n\n".join(channels_info)
    else:
        settings_text += "Каналы не подключены."

    await callback.message.edit_text(
        settings_text,
        reply_markup=settings_vk_kb(channels),
        parse_mode="Markdown"
    )
    await callback.answer()

# -----------------------------
# изменение ключевых слов
# -----------------------------
@router.callback_query(F.data.startswith("set_vk_keywords_"))
async def set_vk_keywords_for_channel(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split("_")[-1])
    await state.update_data(channel_id=channel_id)
    await callback.message.edit_text("Введите ключевые слова через запятую (или '-', если не нужны):")
    await state.set_state(Form.vk_keywords)

@router.message(Form.vk_keywords)
async def process_vk_keywords(message: Message, state: FSMContext):
    data = await state.get_data()
    channel_id = data.get("channel_id")
    settings = db.get_parser_channel_settings('vk', channel_id)
    if settings:
        keywords = message.text if message.text != '-' else ''
        db.update_parser_channel_keywords(settings['id'], keywords)
        await message.answer("✅ Ключевые слова обновлены.")
    await state.clear()

    # Создаем фейковый CallbackQuery для вызова меню
    callback_query = type('obj', (object,), {
        'data': 'settings_vk',
        'message': message,
        'from_user': message.from_user,
        'bot': message.bot,
        'answer': lambda: None
    })
    await settings_vk(callback_query, state)

# -----------------------------
# Настройка минус-слов
# -----------------------------
@router.callback_query(F.data.startswith("set_vk_minus_words_"))
async def set_vk_minus_words_for_channel(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split("_")[-1])
    await state.update_data(channel_id=channel_id)
    await callback.message.edit_text("Введите минус-слова через запятую (или '-', если не нужны):")
    await state.set_state(Form.vk_minus_words)

@router.message(Form.vk_minus_words)
async def process_vk_minus_words(message: Message, state: FSMContext):
    data = await state.get_data()
    channel_id = data.get("channel_id")
    settings = db.get_parser_channel_settings('vk', channel_id)
    if settings:
        minus_words = message.text if message.text != '-' else ''
        db.update_parser_channel_minus_words(settings['id'], minus_words)
        await message.answer("✅ Минус-слова обновлены.")
    await state.clear()

    # Создаем фейковый CallbackQuery для вызова меню
    callback_query = type('obj', (object,), {
        'data': 'settings_vk',
        'message': message,
        'from_user': message.from_user,
        'bot': message.bot,
        'answer': lambda: None
    })
    await settings_vk(callback_query, state)

# -----------------------------
# изменение диапазона цен
# -----------------------------
@router.callback_query(F.data.startswith("set_vk_price_"))
async def set_vk_price(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split("_")[-1])
    await state.update_data(channel_id=channel_id)
    await callback.message.edit_text("Введите минимальную цену:")
    await state.set_state(Form.vk_price_min)

@router.message(Form.vk_price_min)
async def process_vk_price_min(message: Message, state: FSMContext):
    try:
        min_price = int(message.text)
        await state.update_data(min_price=min_price)
        await message.answer("Теперь введите максимальную цену:")
        await state.set_state(Form.vk_price_max)
    except ValueError:
        await message.answer("❌ Введите число!")

@router.message(Form.vk_price_max)
async def process_vk_price_max(message: Message, state: FSMContext):
    try:
        max_price = int(message.text)
        data = await state.get_data()
        channel_id = data.get("channel_id")
        min_price = data.get("min_price")
        settings = db.get_parser_channel_settings('vk', channel_id)
        if settings:
            db.update_parser_channel_price_range(settings['id'], min_price, max_price)
            await message.answer(f"✅ Ценовой диапазон обновлён: {min_price} - {max_price} руб.")
        await state.clear()

        # Создаем фейковый CallbackQuery для вызова меню
        callback_query = type('obj', (object,), {
            'data': 'settings_vk',
            'message': message,
            'from_user': message.from_user,
            'bot': message.bot,
            'answer': lambda: None
        })
        await settings_vk(callback_query, state)
    except ValueError:
        await message.answer("❌ Введите число!")

# -----------------------------
# изменение ID групп
# -----------------------------
@router.callback_query(F.data == "set_vk_groups")
async def set_vk_groups(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите ID групп через запятую (например: -123456, -654321):")
    await state.set_state(Form.vk_groups)
    await callback.answer()

@router.message(Form.vk_groups)
async def process_vk_groups(message: Message, state: FSMContext):
    try:
        # Извлекаем числовые ID из текста
        group_ids = []
        for item in message.text.split(','):
            item = item.strip()
            if item.startswith('-'):
                group_ids.append(item)
            elif item.isdigit():
                group_ids.append(f"-{item}")
        
        # Сохраняем в настройках
        settings = db.get_vk_settings()
        settings['group_ids'] = group_ids
        # Сохраняем полные настройки
        db.save_vk_full_settings(settings)
        
        await message.answer(f"✅ ID групп VK обновлены: {', '.join(group_ids)}")
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# -----------------------------
# Выбор канала для VK
# -----------------------------
@router.callback_query(F.data == "set_vk_channel")
async def set_vk_channel(callback: CallbackQuery):
    channels = db.list_channels()
    if not channels:
        await callback.answer("Бот не является администратором ни в одном канале. Добавьте бота в канал как администратора.", show_alert=True)
        return

    buttons = [
        [InlineKeyboardButton(text=title, callback_data=f"vk_channel_select_{chat_id}")]
        for chat_id, title in channels
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="settings_vk")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text("Выберите канал для отправки уведомлений VK:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("vk_channel_select_"))
async def process_vk_channel_selection(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split("_")[-1])
    db.set_parser_channel('vk', channel_id)

    await callback.answer("✅ Канал для VK успешно выбран!")
    await settings_vk(callback, state)

# -----------------------------
# Настройка интервала для VK
# -----------------------------
@router.callback_query(F.data == "set_vk_interval")
async def set_vk_interval(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите интервал между сообщениями в секундах:")
    await state.set_state(Form.vk_interval)
    await callback.answer()

@router.message(Form.vk_interval)
async def process_vk_interval(message: Message, state: FSMContext):
    try:
        interval = int(message.text)
        if interval <= 0:
            await message.answer("❌ Интервал должен быть положительным числом. Попробуйте еще раз.")
            return

        db.set_parser_interval('vk', interval)
        await message.answer(f"✅ Интервал для VK установлен: {interval} сек.")
        await state.clear()

    except ValueError:
        await message.answer("❌ Введите число!")