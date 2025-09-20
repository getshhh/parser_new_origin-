from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database.database import Database

from .states import Form
from keyboards.settings_kwork import settings_kwork_kb

router = Router()
db = Database()

# -----------------------------
# меню настроек Kwork
# -----------------------------
@router.callback_query(F.data == "settings_kwork")
async def settings_kwork(callback: CallbackQuery, state: FSMContext):
    settings = db.get_settings('kwork')
    keywords = settings.get("keywords", [])
    min_price = settings.get("min_price", None)
    max_price = settings.get("max_price", None)

    parser_settings = db.get_parser_settings('kwork')
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

    price_range_parts = []
    if min_price is not None:
        price_range_parts.append(f"от {min_price}")
    if max_price is not None:
        price_range_parts.append(f"до {max_price}")
    price_range = ' '.join(price_range_parts) if price_range_parts else 'не задан'


    settings_text = (
        "⚙️ **Настройки Kwork**\n\n"
        f"**Ключевые слова:** {', '.join(keywords) if keywords else 'не заданы'}\n"
        f"**Ценовой диапазон:** {price_range}\n"
        f"**Канал для отправки:** {channel_name}\n"
        f"**Интервал сообщений:** {interval_text}\n\n"
        "Выберите, что хотите изменить."
    )
    await callback.message.edit_text(settings_text, reply_markup=settings_kwork_kb(), parse_mode="Markdown")
    await callback.answer()

# ... остальной код без изменений ...

# -----------------------------
# изменение ключевых слов
# -----------------------------
@router.callback_query(F.data == "set_kwork_keywords")
async def set_kwork_keywords(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите ключевые слова через запятую:")
    await state.set_state(Form.setting_keywords)
    await callback.answer()

@router.message(Form.setting_keywords)
async def process_kwork_keywords(message: Message, state: FSMContext):
    keywords = [kw.strip() for kw in message.text.split(',') if kw.strip()]
    settings = db.get_settings('kwork')
    db.save_settings(keywords, settings.get('min_price'), settings.get('max_price'), 'kwork')
    await message.answer(f"✅ Ключевые слова обновлены: {', '.join(keywords) if keywords else '—'}")
    await state.clear()

# -----------------------------
# изменение диапазона цен
# -----------------------------
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
        await message.answer("❌ Введите число!")

@router.message(Form.setting_price_max)
async def process_kwork_price_max(message: Message, state: FSMContext):
    try:
        max_price = int(message.text)
        data = await state.get_data()
        settings = db.get_settings('kwork')
        db.save_settings(settings.get('keywords'), data.get('min_price'), max_price, 'kwork')
        await message.answer(f"✅ Ценовой диапазон обновлён: {data.get('min_price')} - {max_price} руб.")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

# -----------------------------
# Выбор канала для Kwork
# -----------------------------
@router.callback_query(F.data == "set_kwork_channel")
async def set_kwork_channel(callback: CallbackQuery):
    channels = db.list_channels()
    if not channels:
        await callback.answer("Бот не является администратором ни в одном канале. Добавьте бота в канал как администратора.", show_alert=True)
        return

    buttons = [
        [InlineKeyboardButton(text=title, callback_data=f"kwork_channel_select_{chat_id}")]
        for chat_id, title in channels
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="settings_kwork")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text("Выберите канал для отправки уведомлений Kwork:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("kwork_channel_select_"))
async def process_kwork_channel_selection(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split("_")[-1])
    db.set_parser_channel('kwork', channel_id)

    await callback.answer("✅ Канал для Kwork успешно выбран!")
    # Возвращаемся в меню настроек, чтобы показать обновленные данные
    await settings_kwork(callback, state)

# -----------------------------
# Настройка интервала для Kwork
# -----------------------------
@router.callback_query(F.data == "set_kwork_interval")
async def set_kwork_interval(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите интервал между сообщениями в секундах:")
    await state.set_state(Form.setting_kwork_interval)
    await callback.answer()

@router.message(Form.setting_kwork_interval)
async def process_kwork_interval(message: Message, state: FSMContext):
    try:
        interval = int(message.text)
        if interval <= 0:
            await message.answer("❌ Интервал должен быть положительным числом. Попробуйте еще раз.")
            return

        db.set_parser_interval('kwork', interval)
        await message.answer(f"✅ Интервал для Kwork установлен: {interval} сек.")
        await state.clear()

    except ValueError:
        await message.answer("❌ Введите число!")
