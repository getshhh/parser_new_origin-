from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database.database import Database

from .states import Form
from keyboards.settings_guru import settings_guru_kb

router = Router()
db = Database()

# -----------------------------
# меню настроек Guru
# -----------------------------
@router.callback_query(F.data == "settings_guru")
async def settings_guru(callback: CallbackQuery, state: FSMContext = None):
    settings = db.get_guru_settings()
    parser_settings = db.get_parser_settings('guru')

    channel_id = None
    message_interval = None
    if parser_settings:
        channel_id = parser_settings.get("channel_id")
        message_interval = parser_settings.get("message_interval")

    channel_name = "не задан"
    if channel_id:
        try:
            chat = await callback.bot.get_chat(channel_id)
            channel_name = f"@{chat.username}" if chat.username else chat.title
        except Exception:
            channel_name = f"ID: {channel_id} (нет доступа?)"

    interval_text = f"{message_interval} сек." if message_interval is not None else "не задан"

    text = f"""
⚙️ Настройки Guru:
🔍 Ключевые слова: {', '.join(settings['keywords']) if settings['keywords'] else 'Не заданы'}
💰 Мин. цена: {settings['min_price'] if settings['min_price'] else 'Не задана'}
💰 Макс. цена: {settings['max_price'] if settings['max_price'] else 'Не задана'}
📢 Канал для отправки: {channel_name}
⏰ Интервал сообщений: {interval_text}
    """.strip()

    await callback.message.edit_text(text, reply_markup=settings_guru_kb())
    await callback.answer()

# -----------------------------
# изменение ключевых слов
# -----------------------------
@router.callback_query(F.data == "set_guru_keywords")
async def set_guru_keywords(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите ключевые слова через запятую:")
    await state.set_state(Form.setting_guru_keywords)
    await callback.answer()

@router.message(Form.setting_guru_keywords)
async def process_guru_keywords(message: Message, state: FSMContext):
    keywords = [kw.strip() for kw in message.text.split(',') if kw.strip()]
    settings = db.get_guru_settings()
    db.save_guru_settings(keywords, settings.get('min_price'), settings.get('max_price'))
    await message.answer(f"✅ Ключевые слова для Guru обновлены: {', '.join(keywords) if keywords else '—'}")
    await state.clear()

# -----------------------------
# изменение диапазона цен (USD)
# -----------------------------
@router.callback_query(F.data == "set_guru_price")
async def set_guru_price(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите минимальную цену (USD):")
    await state.set_state(Form.setting_guru_price_min)
    await callback.answer()

@router.message(Form.setting_guru_price_min)
async def process_guru_price_min(message: Message, state: FSMContext):
    try:
        min_price = int(message.text)
        await state.update_data(min_price=min_price)
        await message.answer("Теперь введите максимальную цену (USD):")
        await state.set_state(Form.setting_guru_price_max)
    except ValueError:
        await message.answer("❌ Введите число!")

@router.message(Form.setting_guru_price_max)
async def process_guru_price_max(message: Message, state: FSMContext):
    try:
        max_price = int(message.text)
        data = await state.get_data()
        settings = db.get_guru_settings()
        db.save_guru_settings(settings.get('keywords'), data.get('min_price'), max_price)
        await message.answer(f"✅ Ценовой диапазон для Guru обновлён: {data.get('min_price')} - {max_price} USD")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

# -----------------------------
# Выбор канала для Guru
# -----------------------------
@router.callback_query(F.data == "set_guru_channel")
async def set_guru_channel(callback: CallbackQuery):
    channels = db.list_channels()
    if not channels:
        await callback.answer("Бот не является администратором ни в одном канале. Добавьте бота в канал как администратора.", show_alert=True)
        return

    buttons = [
        [InlineKeyboardButton(text=title, callback_data=f"guru_channel_select_{chat_id}")]
        for chat_id, title in channels
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="settings_guru")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text("Выберите канал для отправки уведомлений Guru:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("guru_channel_select_"))
async def process_guru_channel_selection(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split("_")[-1])
    db.set_parser_channel('guru', channel_id)

    await callback.answer("✅ Канал для Guru успешно выбран!")
    await settings_guru(callback, state)

# -----------------------------
# Настройка интервала для Guru
# -----------------------------
@router.callback_query(F.data == "set_guru_interval")
async def set_guru_interval(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите интервал между сообщениями в секундах:")
    await state.set_state(Form.setting_guru_interval)
    await callback.answer()

@router.message(Form.setting_guru_interval)
async def process_guru_interval(message: Message, state: FSMContext):
    try:
        interval = int(message.text)
        if interval <= 0:
            await message.answer("❌ Интервал должен быть положительным числом. Попробуйте еще раз.")
            return

        db.set_parser_interval('guru', interval)
        await message.answer(f"✅ Интервал для Guru установлен: {interval} сек.")
        await state.clear()

    except ValueError:
        await message.answer("❌ Введите число!")
