from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database.database import Database

from .states import Form
from keyboards.settings_weblancer import settings_weblancer_kb

router = Router()
db = Database()

@router.callback_query(F.data == "settings_weblancer")
async def settings_weblancer(callback: CallbackQuery, state: FSMContext = None):
    settings = db.get_weblancer_settings()
    parser_settings = db.get_parser_settings('weblancer')

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
⚙️ Настройки WebLancer:
🔍 Ключевые слова: {', '.join(settings['keywords']) if settings['keywords'] else 'Не заданы'}
💰 Мин. цена: {settings['min_price'] if settings['min_price'] else 'Не задана'}
💰 Макс. цена: {settings['max_price'] if settings['max_price'] else 'Не задана'}
📢 Канал для отправки: {channel_name}
⏰ Интервал сообщений: {interval_text}
    """.strip()

    await callback.message.edit_text(text, reply_markup=settings_weblancer_kb())
    await callback.answer()

@router.callback_query(F.data == "set_weblancer_keywords")
async def set_weblancer_keywords(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите ключевые слова через запятую:")
    await state.set_state(Form.weblancer_keywords)
    await callback.answer()

@router.message(Form.weblancer_keywords)
async def process_weblancer_keywords(message: Message, state: FSMContext):
    keywords = [kw.strip() for kw in message.text.split(',') if kw.strip()]
    settings = db.get_weblancer_settings()
    db.save_weblancer_settings(keywords, settings.get('min_price'), settings.get('max_price'))
    await message.answer(f"✅ Ключевые слова WebLancer обновлены: {', '.join(keywords) if keywords else '—'}")
    await state.clear()

@router.callback_query(F.data == "set_weblancer_price")
async def set_weblancer_price(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите минимальную цену:")
    await state.set_state(Form.weblancer_price_min)
    await callback.answer()

@router.message(Form.weblancer_price_min)
async def process_weblancer_price_min(message: Message, state: FSMContext):
    try:
        min_price = int(message.text)
        await state.update_data(min_price=min_price)
        await message.answer("Теперь введите максимальную цену:")
        await state.set_state(Form.weblancer_price_max)
    except ValueError:
        await message.answer("❌ Введите число!")

@router.message(Form.weblancer_price_max)
async def process_weblancer_price_max(message: Message, state: FSMContext):
    try:
        max_price = int(message.text)
        data = await state.get_data()
        settings = db.get_weblancer_settings()
        db.save_weblancer_settings(settings.get('keywords'), data.get('min_price'), max_price)
        await message.answer(f"✅ Ценовой диапазон WebLancer обновлён: {data.get('min_price')} - {max_price} руб.")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

# -----------------------------
# Выбор канала для Weblancer
# -----------------------------
@router.callback_query(F.data == "set_weblancer_channel")
async def set_weblancer_channel(callback: CallbackQuery):
    channels = db.list_channels()
    if not channels:
        await callback.answer("Бот не является администратором ни в одном канале. Добавьте бота в канал как администратора.", show_alert=True)
        return

    buttons = [
        [InlineKeyboardButton(text=title, callback_data=f"weblancer_channel_select_{chat_id}")]
        for chat_id, title in channels
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="settings_weblancer")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text("Выберите канал для отправки уведомлений Weblancer:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("weblancer_channel_select_"))
async def process_weblancer_channel_selection(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split("_")[-1])
    db.set_parser_channel('weblancer', channel_id)

    await callback.answer("✅ Канал для Weblancer успешно выбран!")
    await settings_weblancer(callback, state)

# -----------------------------
# Настройка интервала для Weblancer
# -----------------------------
@router.callback_query(F.data == "set_weblancer_interval")
async def set_weblancer_interval(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите интервал между сообщениями в секундах:")
    await state.set_state(Form.weblancer_interval)
    await callback.answer()

@router.message(Form.weblancer_interval)
async def process_weblancer_interval(message: Message, state: FSMContext):
    try:
        interval = int(message.text)
        if interval <= 0:
            await message.answer("❌ Интервал должен быть положительным числом. Попробуйте еще раз.")
            return

        db.set_parser_interval('weblancer', interval)
        await message.answer(f"✅ Интервал для Weblancer установлен: {interval} сек.")
        await state.clear()

    except ValueError:
        await message.answer("❌ Введите число!")