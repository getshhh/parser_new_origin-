# handlers/parser_commands.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.kwork import ParserService, render as render_kwork
from services.habr import HabrParserService
from services.fl import FLParserService
from services.guru import GuruParserService, render as render_guru
from services.youdo import YouDoParserService, render as render_youdo
from database.database import Database

router = Router()
db = Database()

# ============================
# ГЛОБАЛЬНЫЕ ССЫЛКИ НА СЕРВИСЫ
# ============================
kwork_parser_service: ParserService | None = None
habr_parser_service: HabrParserService | None = None
fl_parser_service: FLParserService | None = None
guru_parser_service: GuruParserService | None = None
youdo_parser_service: YouDoParserService | None = None


def setup_parser_services(
    kwork_service: ParserService,
    habr_service: HabrParserService,
    fl_service: FLParserService,
    guru_service: GuruParserService,
    youdo_service: YouDoParserService,
) -> None:
    """Вызывается из __main__.py — прокидываем инстансы сервисов сюда."""
    global kwork_parser_service, habr_parser_service, fl_parser_service, guru_parser_service, youdo_parser_service
    kwork_parser_service = kwork_service
    habr_parser_service = habr_service
    fl_parser_service = fl_service
    guru_parser_service = guru_service
    youdo_parser_service = youdo_service


# ============================
# СОСТОЯНИЯ FSM ДЛЯ НАСТРОЕК
# ============================
class Form(StatesGroup):
    # Kwork
    setting_keywords = State()
    setting_price_min = State()
    setting_price_max = State()

    # Habr
    setting_habr_keywords = State()
    setting_habr_salary_min = State()
    setting_habr_salary_max = State()
    setting_habr_cities = State()

    # FL
    setting_fl_keywords = State()
    setting_fl_price_min = State()
    setting_fl_price_max = State()

    # Guru
    setting_guru_keywords = State()
    setting_guru_price_min = State()
    setting_guru_price_max = State()

    # YouDo
    setting_youdo_keywords = State()
    setting_youdo_price_min = State()
    setting_youdo_price_max = State()


# ============================
# ВКЛ/ВЫКЛ ПАРСЕРЫ
# ============================

@router.message(Command("enable_parser"))
@router.message(F.text == "▶️ Включить парсер")
async def enable_parser(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Kwork", callback_data="enable_kwork")],
        [InlineKeyboardButton(text="Habr Career", callback_data="enable_habr")],
        [InlineKeyboardButton(text="FL", callback_data="enable_fl")],
        [InlineKeyboardButton(text="Guru", callback_data="enable_guru")],
        [InlineKeyboardButton(text="YouDo", callback_data="enable_youdo")],
        [InlineKeyboardButton(text="Все парсеры", callback_data="enable_all")]
    ])
    await message.answer("Выберите парсер для включения:", reply_markup=keyboard)


@router.callback_query(F.data == "enable_kwork")
async def enable_kwork(callback: CallbackQuery):
    if kwork_parser_service:
        await kwork_parser_service.start_parser(chat_id=callback.message.chat.id)
        await callback.message.edit_text("✅ Парсер Kwork включен.")
    await callback.answer()


@router.callback_query(F.data == "enable_habr")
async def enable_habr(callback: CallbackQuery):
    if habr_parser_service:
        await habr_parser_service.start_parser(chat_id=callback.message.chat.id)
        await callback.message.edit_text("✅ Парсер Habr Career включен.")
    await callback.answer()


@router.callback_query(F.data == "enable_fl")
async def enable_fl(callback: CallbackQuery):
    if fl_parser_service:
        await fl_parser_service.start_parser(chat_id=callback.message.chat.id)
        await callback.message.edit_text("✅ Парсер FL включен.")
    await callback.answer()


@router.callback_query(F.data == "enable_guru")
async def enable_guru(callback: CallbackQuery):
    if guru_parser_service:
        await guru_parser_service.start_parser(chat_id=callback.message.chat.id)
        await callback.message.edit_text("✅ Парсер Guru включен.")
    await callback.answer()


@router.callback_query(F.data == "enable_youdo")
async def enable_youdo(callback: CallbackQuery):
    if youdo_parser_service:
        await youdo_parser_service.start_parser(chat_id=callback.message.chat.id)
        await callback.message.edit_text("✅ Парсер YouDo включен.")
    await callback.answer()


@router.callback_query(F.data == "enable_all")
async def enable_all(callback: CallbackQuery):
    if kwork_parser_service:
        await kwork_parser_service.start_parser(chat_id=callback.message.chat.id)
    if habr_parser_service:
        await habr_parser_service.start_parser(chat_id=callback.message.chat.id)
    if fl_parser_service:
        await fl_parser_service.start_parser(chat_id=callback.message.chat.id)
    if guru_parser_service:
        await guru_parser_service.start_parser(chat_id=callback.message.chat.id)
    if youdo_parser_service:
        await youdo_parser_service.start_parser(chat_id=callback.message.chat.id)
    await callback.message.edit_text("✅ Все парсеры включены.")
    await callback.answer()


@router.message(Command("disable_parser"))
@router.message(F.text == "⏹️ Выключить парсер")
async def disable_parser(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Kwork", callback_data="disable_kwork")],
        [InlineKeyboardButton(text="Habr Career", callback_data="disable_habr")],
        [InlineKeyboardButton(text="FL", callback_data="disable_fl")],
        [InlineKeyboardButton(text="Guru", callback_data="disable_guru")],
        [InlineKeyboardButton(text="YouDo", callback_data="disable_youdo")],
        [InlineKeyboardButton(text="⏹️ Выключить все", callback_data="disable_all")]
    ])
    await message.answer("Выберите парсер для выключения:", reply_markup=keyboard)


@router.callback_query(F.data == "disable_kwork")
async def disable_kwork(callback: CallbackQuery):
    if kwork_parser_service:
        await kwork_parser_service.stop_parser()
        await callback.message.edit_text("🛑 Парсер Kwork выключен.")
    await callback.answer()


@router.callback_query(F.data == "disable_habr")
async def disable_habr(callback: CallbackQuery):
    if habr_parser_service:
        await habr_parser_service.stop_parser()
        await callback.message.edit_text("🛑 Парсер Habr Career выключен.")
    await callback.answer()


@router.callback_query(F.data == "disable_fl")
async def disable_fl(callback: CallbackQuery):
    if fl_parser_service:
        await fl_parser_service.stop_parser()
        await callback.message.edit_text("🛑 Парсер FL выключен.")
    await callback.answer()


@router.callback_query(F.data == "disable_guru")
async def disable_guru(callback: CallbackQuery):
    if guru_parser_service:
        await guru_parser_service.stop_parser()
        await callback.message.edit_text("🛑 Парсер Guru выключен.")
    await callback.answer()


@router.callback_query(F.data == "disable_youdo")
async def disable_youdo(callback: CallbackQuery):
    if youdo_parser_service:
        await youdo_parser_service.stop_parser()
        await callback.message.edit_text("🛑 Парсер YouDo выключен.")
    await callback.answer()


@router.callback_query(F.data == "disable_all")
async def disable_all(callback: CallbackQuery):
    if kwork_parser_service:
        await kwork_parser_service.stop_parser()
    if habr_parser_service:
        await habr_parser_service.stop_parser()
    if fl_parser_service:
        await fl_parser_service.stop_parser()
    if guru_parser_service:
        await guru_parser_service.stop_parser()
    if youdo_parser_service:
        await youdo_parser_service.stop_parser()
    await callback.message.edit_text("🛑 Все парсеры выключены.")
    await callback.answer()


# Доп. обработчик для кнопки из ReplyKeyboardMarkup (главное меню)
@router.message(F.text == "⏹️ Выключить все парсеры")
async def disable_all_from_menu(message: Message):
    if kwork_parser_service:
        await kwork_parser_service.stop_parser()
    if habr_parser_service:
        await habr_parser_service.stop_parser()
    if fl_parser_service:
        await fl_parser_service.stop_parser()
    if guru_parser_service:
        await guru_parser_service.stop_parser()
    if youdo_parser_service:
        await youdo_parser_service.stop_parser()
    await message.answer("🛑 Все парсеры выключены.")


# ============================
# НАСТРОЙКИ
# ============================

@router.message(Command("settings"))
@router.message(F.text == "⚙️ Настройки")
async def settings(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Kwork", callback_data="settings_kwork")],
        [InlineKeyboardButton(text="Habr Career", callback_data="settings_habr")],
        [InlineKeyboardButton(text="FL", callback_data="settings_fl")],
        [InlineKeyboardButton(text="Guru", callback_data="settings_guru")],
        [InlineKeyboardButton(text="YouDo", callback_data="settings_youdo")],
    ])
    await message.answer("Выберите парсер для настройки:", reply_markup=keyboard)


# --- Настройки Kwork ---

@router.callback_query(F.data == "settings_kwork")
async def settings_kwork(callback: CallbackQuery):
    settings = await db.get_settings('kwork')
    text = f"""
⚙️ Настройки Kwork:
🔍 Ключевые слова: {', '.join(settings['keywords']) if settings and settings.get('keywords') else 'Не заданы'}
💰 Мин. цена: {settings.get('min_price') if settings and settings.get('min_price') is not None else 'Не задана'}
💰 Макс. цена: {settings.get('max_price') if settings and settings.get('max_price') is not None else 'Не задана'}
    """.strip()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Изменить ключевые слова", callback_data="set_kwork_keywords")],
        [InlineKeyboardButton(text="💰 Изменить ценовой диапазон", callback_data="set_kwork_price")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_settings")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "set_kwork_keywords")
async def set_kwork_keywords(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите ключевые слова через запятую:")
    await state.set_state(Form.setting_keywords)
    await callback.answer()


@router.message(Form.setting_keywords)
async def process_kwork_keywords(message: Message, state: FSMContext):
    keywords = [kw.strip() for kw in message.text.split(',') if kw.strip()]
    settings = await db.get_settings('kwork')
    min_price = settings.get('min_price') if settings else None
    max_price = settings.get('max_price') if settings else None
    await db.save_settings(keywords, min_price, max_price, 'kwork')
    await message.answer(f"✅ Ключевые слова обновлены: {', '.join(keywords) if keywords else '—'}")
    await state.clear()


@router.callback_query(F.data == "set_kwork_price")
async def set_kwork_price(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите минимальную цену:")
    await state.set_state(Form.setting_price_min)
    await callback.answer()


@router.message(Form.setting_price_min)
async def process_kwork_price_min(message: Message, state: FSMContext):
    try:
        min_price = int(message.text)
        await state.update_data(min_price=min_price)
        await message.answer("Теперь введите максимальную цену:")
        await state.set_state(Form.setting_price_max)
    except ValueError:
        await message.answer("Пожалуйста, введите число:")


@router.message(Form.setting_price_max)
async def process_kwork_price_max(message: Message, state: FSMContext):
    try:
        max_price = int(message.text)
        data = await state.get_data()
        min_price = data.get('min_price')
        settings = await db.get_settings('kwork')
        keywords = settings.get('keywords') if settings else []
        await db.save_settings(keywords, min_price, max_price, 'kwork')
        await message.answer(f"✅ Ценовой диапазон обновлён: {min_price} - {max_price} руб.")
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите число:")


# --- Настройки Habr ---

@router.callback_query(F.data == "settings_habr")
async def settings_habr(callback: CallbackQuery):
    settings = await db.get_habr_settings()
    text = f"""
⚙️ Настройки Habr Career:
🔍 Ключевые слова: {', '.join(settings['keywords']) if settings and settings.get('keywords') else 'Не заданы'}
💰 Мин. зарплата: {settings.get('min_salary') if settings and settings.get('min_salary') is not None else 'Не задана'}
💰 Макс. зарплата: {settings.get('max_salary') if settings and settings.get('max_salary') is not None else 'Не задана'}
📍 Города: {', '.join(settings['cities']) if settings and settings.get('cities') else 'Все города'}
    """.strip()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Изменить ключевые слова", callback_data="set_habr_keywords")],
        [InlineKeyboardButton(text="💰 Изменить зарплатный диапазон", callback_data="set_habr_salary")],
        [InlineKeyboardButton(text="📍 Изменить города", callback_data="set_habr_cities")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_settings")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "set_habr_keywords")
async def set_habr_keywords(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите ключевые слова для поиска вакансий через запятую:")
    await state.set_state(Form.setting_habr_keywords)
    await callback.answer()


@router.message(Form.setting_habr_keywords)
async def process_habr_keywords(message: Message, state: FSMContext):
    keywords = [kw.strip() for kw in message.text.split(',') if kw.strip()]
    await habr_parser_service.set_habr_keywords(keywords)
    await message.answer(f"✅ Ключевые слова обновлены: {', '.join(keywords) if keywords else '—'}")
    await state.clear()


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
        await message.answer("Пожалуйста, введите число:")


@router.message(Form.setting_habr_salary_max)
async def process_habr_salary_max(message: Message, state: FSMContext):
    try:
        max_salary = int(message.text)
        data = await state.get_data()
        min_salary = data.get('min_salary')
        await habr_parser_service.set_habr_salary_range(min_salary, max_salary)
        await message.answer(f"✅ Зарплатный диапазон обновлён: {min_salary} - {max_salary} руб.")
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите число:")


@router.callback_query(F.data == "set_habr_cities")
async def set_habr_cities(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите города для поиска через запятую (оставьте пустым для всех городов):")
    await state.set_state(Form.setting_habr_cities)
    await callback.answer()


@router.message(Form.setting_habr_cities)
async def process_habr_cities(message: Message, state: FSMContext):
    cities = [city.strip() for city in message.text.split(',') if city.strip()]
    await habr_parser_service.set_habr_cities(cities)
    await message.answer(f"✅ Города обновлены: {', '.join(cities) if cities else 'Все города'}")
    await state.clear()


# --- Настройки FL ---

@router.callback_query(F.data == "settings_fl")
async def settings_fl(callback: CallbackQuery):
    settings = await db.get_fl_settings()
    text = f"""
⚙️ Настройки FL:
🔍 Ключевые слова: {', '.join(settings['keywords']) if settings and settings.get('keywords') else 'Не заданы'}
💰 Мин. цена: {settings.get('min_price') if settings and settings.get('min_price') is not None else 'Не задана'}
💰 Макс. цена: {settings.get('max_price') if settings and settings.get('max_price') is not None else 'Не задана'}
    """.strip()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Изменить ключевые слова", callback_data="set_fl_keywords")],
        [InlineKeyboardButton(text="💰 Изменить ценовой диапазон", callback_data="set_fl_price")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_settings")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "set_fl_keywords")
async def set_fl_keywords(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите ключевые слова через запятую:")
    await state.set_state(Form.setting_fl_keywords)
    await callback.answer()


@router.message(Form.setting_fl_keywords)
async def process_fl_keywords(message: Message, state: FSMContext):
    keywords = [kw.strip() for kw in message.text.split(',') if kw.strip()]
    settings = await db.get_fl_settings()
    min_price = settings.get('min_price')
    max_price = settings.get('max_price')
    await db.save_fl_settings(keywords, min_price, max_price)
    await message.answer(f"✅ Ключевые слова для FL обновлены: {', '.join(keywords) if keywords else '—'}")
    await state.clear()


@router.callback_query(F.data == "set_fl_price")
async def set_fl_price(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите минимальную цену:")
    await state.set_state(Form.setting_fl_price_min)
    await callback.answer()


@router.message(Form.setting_fl_price_min)
async def process_fl_price_min(message: Message, state: FSMContext):
    try:
        min_price = int(message.text)
        await state.update_data(min_price=min_price)
        await message.answer("Теперь введите максимальную цену:")
        await state.set_state(Form.setting_fl_price_max)
    except ValueError:
        await message.answer("Пожалуйста, введите число:")


@router.message(Form.setting_fl_price_max)
async def process_fl_price_max(message: Message, state: FSMContext):
    try:
        max_price = int(message.text)
        data = await state.get_data()
        min_price = data.get('min_price')
        settings = await db.get_fl_settings()
        keywords = settings.get('keywords')
        await db.save_fl_settings(keywords, min_price, max_price)
        await message.answer(f"✅ Ценовой диапазон для FL обновлён: {min_price} - {max_price} руб.")
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите число:")


# --- Настройки Guru ---

@router.callback_query(F.data == "settings_guru")
async def settings_guru(callback: CallbackQuery):
    settings = await db.get_guru_settings()
    text = f"""
⚙️ Настройки Guru:
🔍 Ключевые слова: {', '.join(settings['keywords']) if settings.get('keywords') else 'Не заданы'}
💰 Мин. цена: {settings.get('min_price') if settings.get('min_price') is not None else 'Не задана'}
💰 Макс. цена: {settings.get('max_price') if settings.get('max_price') is not None else 'Не задана'}
    """.strip()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Изменить ключевые слова", callback_data="set_guru_keywords")],
        [InlineKeyboardButton(text="💰 Изменить ценовой диапазон", callback_data="set_guru_price")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_settings")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "set_guru_keywords")
async def set_guru_keywords(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите ключевые слова через запятую:")
    await state.set_state(Form.setting_guru_keywords)
    await callback.answer()


@router.message(Form.setting_guru_keywords)
async def process_guru_keywords(message: Message, state: FSMContext):
    keywords = [kw.strip() for kw in message.text.split(',') if kw.strip()]
    settings = await db.get_guru_settings()
    min_price = settings.get('min_price')
    max_price = settings.get('max_price')
    await db.save_guru_settings(keywords, min_price, max_price)
    await message.answer(f"✅ Ключевые слова для Guru обновлены: {', '.join(keywords) if keywords else '—'}")
    await state.clear()


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
        await message.answer("Пожалуйста, введите число:")


@router.message(Form.setting_guru_price_max)
async def process_guru_price_max(message: Message, state: FSMContext):
    try:
        max_price = int(message.text)
        data = await state.get_data()
        min_price = data.get('min_price')
        settings = await db.get_guru_settings()
        keywords = settings.get('keywords')
        await db.save_guru_settings(keywords, min_price, max_price)
        await message.answer(f"✅ Ценовой диапазон для Guru обновлён: {min_price} - {max_price} USD")
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите число:")


# --- Настройки YouDo ---

@router.callback_query(F.data == "settings_youdo")
async def settings_youdo(callback: CallbackQuery):
    settings = await db.get_youdo_settings()
    text = f"""
⚙️ Настройки YouDo:
🔍 Ключевые слова: {', '.join(settings['keywords']) if settings.get('keywords') else 'Не заданы'}
💰 Мин. цена: {settings.get('min_price') if settings.get('min_price') is not None else 'Не задана'}
💰 Макс. цена: {settings.get('max_price') if settings.get('max_price') is not None else 'Не задана'}
    """.strip()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Изменить ключевые слова", callback_data="set_youdo_keywords")],
        [InlineKeyboardButton(text="💰 Изменить ценовой диапазон", callback_data="set_youdo_price")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main_settings")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "set_youdo_keywords")
async def set_youdo_keywords(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите ключевые слова для YouDo через запятую:")
    await state.set_state(Form.setting_youdo_keywords)
    await callback.answer()


@router.message(Form.setting_youdo_keywords)
async def process_youdo_keywords(message: Message, state: FSMContext):
    keywords = [kw.strip() for kw in message.text.split(',') if kw.strip()]
    settings = await db.get_youdo_settings()
    min_price = settings.get('min_price')
    max_price = settings.get('max_price')
    await db.save_youdo_settings(keywords, min_price, max_price)
    await message.answer(f"✅ Ключевые слова для YouDo обновлены: {', '.join(keywords) if keywords else '—'}")
    await state.clear()


@router.callback_query(F.data == "set_youdo_price")
async def set_youdo_price(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите минимальную цену:")
    await state.set_state(Form.setting_youdo_price_min)
    await callback.answer()


@router.message(Form.setting_youdo_price_min)
async def process_youdo_price_min(message: Message, state: FSMContext):
    try:
        min_price = int(message.text)
        await state.update_data(min_price=min_price)
        await message.answer("Теперь введите максимальную цену:")
        await state.set_state(Form.setting_youdo_price_max)
    except ValueError:
        await message.answer("Пожалуйста, введите число:")


@router.message(Form.setting_youdo_price_max)
async def process_youdo_price_max(message: Message, state: FSMContext):
    try:
        max_price = int(message.text)
        data = await state.get_data()
        min_price = data.get('min_price')
        settings = await db.get_youdo_settings()
        keywords = settings.get('keywords')
        await db.save_youdo_settings(keywords, min_price, max_price)
        await message.answer(f"✅ Ценовой диапазон для YouDo обновлён: {min_price} - {max_price} руб.")
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите число:")


# --- Назад к выбору парсера для настроек ---

@router.callback_query(F.data == "back_to_main_settings")
async def back_to_main_settings(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Kwork", callback_data="settings_kwork")],
        [InlineKeyboardButton(text="Habr Career", callback_data="settings_habr")],
        [InlineKeyboardButton(text="FL", callback_data="settings_fl")],
        [InlineKeyboardButton(text="Guru", callback_data="settings_guru")],
        [InlineKeyboardButton(text="YouDo", callback_data="settings_youdo")],
    ])
    await callback.message.edit_text("Выберите парсер для настройки:", reply_markup=keyboard)
    await callback.answer()


# ============================
# СТАТИСТИКА И ПОСЛЕДНИЕ ЗАПИСИ
# ============================

@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def stats(message: Message) -> None:
    kwork_count = await db.get_total_projects_count()
    habr_count = await db.get_total_habr_vacancies_count()
    fl_count = await db.get_total_fl_projects_count()
    guru_count = await db.get_total_guru_projects_count()
    youdo_count = await db.get_total_youdo_tasks_count()

    text = f"""
📊 Статистика парсеров:
🛠️ Kwork: {kwork_count} проектов
💼 Habr Career: {habr_count} вакансий
💻 FL: {fl_count} проектов
🌐 Guru: {guru_count} проектов
📱 YouDo: {youdo_count} заданий
    """.strip()
    await message.answer(text)


@router.message(Command("latest"))
@router.message(F.text == "📝 Последние записи")
@router.message(F.text == "🔍 Последние проекты")
async def latest(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Kwork", callback_data="latest_kwork")],
        [InlineKeyboardButton(text="Habr Career", callback_data="latest_habr")],
        [InlineKeyboardButton(text="FL", callback_data="latest_fl")],
        [InlineKeyboardButton(text="Guru", callback_data="latest_guru")],
        [InlineKeyboardButton(text="YouDo", callback_data="latest_youdo")],
    ])
    await message.answer("Выберите парсер для просмотра последних записей:", reply_markup=keyboard)


@router.callback_query(F.data == "latest_kwork")
async def latest_kwork(callback: CallbackQuery):
    projects = await db.get_latest_projects(5)
    if not projects:
        await callback.message.edit_text("Нет данных о проектах Kwork.")
        await callback.answer()
        return
    messages = [
        render_kwork({
            "id": p[0],
            "title": p[1],
            "description": p[2],
            "price": p[3],
            "url": p[4],
            "date_create": p[5],
            "username": p[6],
            "category_id": p[7]
        }) for p in projects
    ]
    await callback.message.edit_text("\n\n".join(messages))
    await callback.answer()


@router.callback_query(F.data == "latest_habr")
async def latest_habr(callback: CallbackQuery):
    vacancies = await db.get_latest_habr_vacancies(5)
    if not vacancies:
        await callback.message.edit_text("Нет данных о вакансиях Habr.")
        await callback.answer()
        return
    messages = []
    for v in vacancies:
        vacancy_dict = {
            'title': v[1],
            'company': v[2],
            'salary': v[3],
            'city': v[4],
            'tags': v[5].split(",") if v[5] else [],
            'link': v[6]
        }
        messages.append(habr_parser_service.render_vacancy(vacancy_dict))
    await callback.message.edit_text("\n\n".join(messages))
    await callback.answer()


@router.callback_query(F.data == "latest_fl")
async def latest_fl(callback: CallbackQuery):
    projects = await db.get_latest_fl_projects(5)
    if not projects:
        await callback.message.edit_text("Нет данных о проектах FL.")
        await callback.answer()
        return
    messages = [
        render_kwork({
            "id": p[0],
            "title": p[1],
            "description": p[2],
            "price": p[3],
            "url": p[4],
            "date_create": p[5],
            "username": p[6],
            "category_id": p[7]
        }) for p in projects
    ]
    await callback.message.edit_text("\n\n".join(messages))
    await callback.answer()


@router.callback_query(F.data == "latest_guru")
async def latest_guru(callback: CallbackQuery):
    projects = await db.get_latest_guru_projects(5)
    if not projects:
        await callback.message.edit_text("Нет данных о проектах Guru.")
        await callback.answer()
        return
    messages = [
        render_guru({
            "id": p[0],
            "title": p[1],
            "description": p[2],
            "price": p[3],
            "url": p[4],
            "date_create": p[5]
        }) for p in projects
    ]
    await callback.message.edit_text("\n\n".join(messages))
    await callback.answer()


@router.callback_query(F.data == "latest_youdo")
async def latest_youdo(callback: CallbackQuery):
    tasks = await db.get_latest_youdo_tasks(5)
    if not tasks:
        await callback.message.edit_text("Нет данных о заданиях YouDo.")
        await callback.answer()
        return
    messages = [
        render_youdo({
            "id": t[0],
            "title": t[1],
            "description": t[2],
            "address": t[3],
            "budget": t[4],
            "date": t[5],
            "url": t[6],
            "date_create": t[7]
        }) for t in tasks
    ]
    await callback.message.edit_text("\n\n".join(messages))
    await callback.answer()
