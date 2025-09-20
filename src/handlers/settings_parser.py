# handlers/settings_parser.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database.database import Database
from keyboards.settings_parser import choose_channel_kb
from .states import Form

router = Router()
db = Database()

# -----------------------------
# Меню настроек канала
# -----------------------------
@router.callback_query(F.data.startswith("settings_channel:"))
async def settings_channel(callback: CallbackQuery):
    parser_name = callback.data.split(":")[1]
    channels = db.list_channels()

    if not channels:
        await callback.message.edit_text(
            "❌ Нет доступных каналов. Добавьте бота в канал и сделайте его админом."
        )
    else:
        await callback.message.edit_text(
            f"Выберите канал для {parser_name}:",
            reply_markup=choose_channel_kb(parser_name, channels)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("set_channel:"))
async def set_channel(callback: CallbackQuery):
    _, parser_name, chat_id = callback.data.split(":")
    db.set_parser_channel(parser_name, int(chat_id))
    await callback.message.edit_text(
        f"✅ Канал для {parser_name} установлен: {chat_id}"
    )
    await callback.answer()

# -----------------------------
# Настройка интервала
# -----------------------------
@router.callback_query(F.data.startswith("settings_interval:"))
async def settings_interval(callback: CallbackQuery, state: FSMContext):
    parser_name = callback.data.split(":")[1]
    await callback.message.edit_text(
        f"Введите интервал для {parser_name} (в секундах):"
    )
    await state.set_state(Form.setting_interval)
    await state.update_data(parser=parser_name)
    await callback.answer()


@router.message(Form.setting_interval)
async def process_interval(message: Message, state: FSMContext):
    try:
        seconds = int(message.text)
        data = await state.get_data()
        parser = data["parser"]
        db.set_parser_interval(parser, seconds)
        await message.answer(
            f"✅ Интервал для {parser} установлен: {seconds} секунд."
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")
