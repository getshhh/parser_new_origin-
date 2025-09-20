# handlers/parser_settings.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from database.database import Database
from .states import Form
from keyboards.parser_settings import get_parser_settings_kb, get_channel_selection_kb, get_interval_selection_kb

router = Router()
db = Database()

@router.callback_query(F.data.startswith("settings_"))
async def parser_settings(callback: CallbackQuery):
    parser_name = callback.data.replace("settings_", "")
    
    settings = await db.get_parser_settings(parser_name)
    channel_info = "Не установлен"
    interval_info = "Не установен"
    
    if settings:
        if settings['channel_id']:
            # Получаем информацию о канал
            channel_dict = dict(channels)
            channel_info = channel_dict.get(settings['channel_id'], f"ID: {settings['channel_id']}")
        if settings['message_interval']:
            interval_info = f"{settings['message_interval']} сек"
    
    text = f"""
⚙️ Настройки {parser_name.upper()}:
📢 Канал: {channel_info}
⏰ Интервал: {interval_info}
    """.strip()

    await callback.message.edit_text(text, reply_markup=get_parser_settings_kb(parser_name))
    await callback.answer()

# handlers/parser_settings.py
# handlers/parser_settings.py
...
@router.callback_query(F.data.startswith("set_") & F.data.endswith("_channel"))
async def set_parser_channel(callback: CallbackQuery, state: FSMContext):
    parser_name = callback.data.split('_')[1]
    
    # channels = await db.list_channels()  <-- This is the problematic line
    channels = db.list_channels() # <-- Corrected line
    
    if not channels:
        await callback.message.answer("Вы еще не добавили бота ни в один канал. Добавьте его как администратора и попробуйте снова.")
        await callback.answer()
        return

    await state.update_data(parser_name=parser_name)
    await callback.message.edit_text(
        "Выберите канал для получения уведомлений:",
        reply_markup=get_channel_selection_kb(parser_name, channels)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("select_") & F.data.endswith("_channel_"))
async def select_parser_channel(callback: CallbackQuery):
    parts = callback.data.split('_')
    parser_name = parts[1]
    channel_id = int(parts[3])
    
    await db.set_parser_channel(parser_name, channel_id)
    
    # Получаем название канала
    channels = await db.list_channels()
    channel_dict = dict(channels)
    channel_name = channel_dict.get(channel_id, f"ID: {channel_id}")
    
    await callback.message.edit_text(
        f"✅ Канал установлен: {channel_name}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад к настройкам", callback_data=f"settings_{parser_name}")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("remove_") & F.data.endswith("_channel"))
async def remove_parser_channel(callback: CallbackQuery):
    parser_name = callback.data.replace("remove_", "").replace("_channel", "")
    
    await db.delete_parser_channel(parser_name)
    
    await callback.message.edit_text(
        "✅ Канал удалён. Сообщения будут отправляться в чат, где был включен парсер.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад к настройкам", callback_data=f"settings_{parser_name}")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("set_") & F.data.endswith("_interval"))
async def set_parser_interval(callback: CallbackQuery):
    parser_name = callback.data.replace("set_", "").replace("_interval", "")
    
    await callback.message.edit_text(
        "⏰ Выберите интервал между сообщениями:",
        reply_markup=get_interval_selection_kb(parser_name)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("set_") & F.data.endswith("_interval_"))
async def select_parser_interval(callback: CallbackQuery):
    parts = callback.data.split('_')
    parser_name = parts[1]
    interval = int(parts[3])
    
    await db.set_parser_interval(parser_name, interval)
    
    await callback.message.edit_text(
        f"✅ Интервал установлен: {interval} секунд",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад к настройкам", callback_data=f"settings_{parser_name}")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("select_") & F.data.contains("_channel_"))
async def set_parser_channel_handler(callback: CallbackQuery, state: FSMContext):
    """
    Handles channel selection for a parser.
    """
    parts = callback.data.split('_')
    parser_name = parts[1]
    channel_id = int(parts[3])

    # Получаем текущие настройки парсера
    settings = db.get_settings(parser_name)

    # Обновляем канал
    settings['channel_id'] = channel_id
    db.save_settings(parser_name, settings)

    await callback.message.edit_text(f"✅ Для парсера **{parser_name.capitalize()}** установлен канал.", parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("set_") & F.data.contains("_interval_"))
async def set_parser_interval_handler(callback: CallbackQuery, state: FSMContext):
    """
    Handles interval selection for a parser.
    """
    parts = callback.data.split('_')
    parser_name = parts[1]
    interval = int(parts[3])

    # Получаем текущие настройки парсера
    settings = db.get_settings(parser_name)

    # Обновляем интервал
    settings['interval'] = interval
    db.save_settings(parser_name, settings)

    await callback.message.edit_text(f"✅ Для парсера **{parser_name.capitalize()}** установлен интервал в **{interval}** сек.", parse_mode="Markdown")
    await callback.answer()