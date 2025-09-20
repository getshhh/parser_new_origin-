from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database.database import Database

from .states import Form
from keyboards.settings_habr import settings_habr_kb
from .services import habr_parser_service

router = Router()
db = Database()

# -----------------------------
# меню настроек Habr
# -----------------------------
@router.callback_query(F.data == "settings_habr")
async def settings_habr(callback: CallbackQuery, state: FSMContext = None):
    settings = db.get_habr_settings()
    parser_settings = db.get_parser_settings('habr')

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
⚙️ Настройки Habr Career:
🔍 Ключевые слова: {', '.join(settings['keywords']) if settings['keywords'] else 'Не заданы'}
💰 Мин. зарплата: {settings['min_salary'] if settings['min_salary'] else 'Не задана'}
💰 Макс. зарплата: {settings['max_salary'] if settings['max_salary'] else 'Не задана'}
📍 Города: {', '.join(settings['cities']) if settings['cities'] else 'Все города'}
📢 Канал для отправки: {channel_name}
⏰ Интервал сообщений: {interval_text}
    """.strip()

    await callback.message.edit_text(text, reply_markup=settings_habr_kb())
    await callback.answer()

# -----------------------------
# изменение ключевых слов
# -----------------------------
@router.callback_query(F.data == "set_habr_keywords")
async def set_habr_keywords(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите ключевые слова через запятую:")
    await state.set_state(Form.setting_habr_keywords)
    await callback.answer()

@router.message(Form.setting_habr_keywords)
async def process_habr_keywords(message: Message, state: FSMContext):
    keywords = [kw.strip() for kw in message.text.split(',') if kw.strip()]
    await habr_parser_service.set_habr_keywords(keywords)
    await message.answer(f"✅ Ключевые слова обновлены: {', '.join(keywords) if keywords else '—'}")
    await state.clear()

# -----------------------------
# изменение зарплаты
# -----------------------------
@router.callback_query(F.data == "set_habr_salary")
async def set_habr_salary(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите минимальную зарплату:")
    await state.set_state(Form.setting_habr_salary_min)
    await callback.answer()

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
        await habr_parser_service.set_habr_salary_range(data.get('min_salary'), max_salary)
        await message.answer(f"✅ Зарплатный диапазон обновлён: {data.get('min_salary')} - {max_salary} руб.")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

# -----------------------------
# изменение городов
# -----------------------------
@router.callback_query(F.data == "set_habr_cities")
async def set_habr_cities(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите города через запятую (оставьте пустым для всех):")
    await state.set_state(Form.setting_habr_cities)
    await callback.answer()

@router.message(Form.setting_habr_cities)
async def process_habr_cities(message: Message, state: FSMContext):
    cities = [c.strip() for c in message.text.split(',') if c.strip()]
    await habr_parser_service.set_habr_cities(cities)
    await message.answer(f"✅ Города обновлены: {', '.join(cities) if cities else 'Все города'}")
    await state.clear()

# -----------------------------
# Выбор канала для Habr
# -----------------------------
@router.callback_query(F.data == "set_habr_channel")
async def set_habr_channel(callback: CallbackQuery):
    channels = db.list_channels()
    if not channels:
        await callback.answer("Бот не является администратором ни в одном канале. Добавьте бота в канал как администратора.", show_alert=True)
        return

    buttons = [
        [InlineKeyboardButton(text=title, callback_data=f"habr_channel_select_{chat_id}")]
        for chat_id, title in channels
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="settings_habr")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text("Выберите канал для отправки уведомлений Habr:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("habr_channel_select_"))
async def process_habr_channel_selection(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split("_")[-1])
    db.set_parser_channel('habr', channel_id)

    await callback.answer("✅ Канал для Habr успешно выбран!")
    await settings_habr(callback, state)

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
