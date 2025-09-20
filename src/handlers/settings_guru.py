from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database.database import Database

from .states import Form
from keyboards.settings_guru import settings_guru_kb
from .generic_settings import create_generic_handlers, process_keywords, process_minus_words, process_price_min, process_price_max

router = Router()
db = Database()

# -----------------------------
# меню настроек Guru
# -----------------------------
@router.callback_query(F.data == "settings_guru")
async def settings_guru(callback: CallbackQuery, state: FSMContext):
    parser_settings = db.get_parser_settings('guru')
    message_interval = parser_settings.get("message_interval") if parser_settings else None
    interval_text = f"{message_interval} сек." if message_interval is not None else "не задан"

    channels = db.get_parser_channels('guru')

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

    settings_text = (
        "⚙️ **Настройки Guru**\n\n"
        f"**Интервал сообщений:** {interval_text}\n\n"
        "**Подключенные каналы:**\n"
    )
    if channels_info:
        settings_text += "\n\n".join(channels_info)
    else:
        settings_text += "Каналы не подключены."

    await callback.message.edit_text(
        settings_text,
        reply_markup=settings_guru_kb(channels),
        parse_mode="Markdown"
    )
    await callback.answer()

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
