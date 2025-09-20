import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from keyboards.parser_settings import (
    get_parser_settings_kb,
    get_channel_selection_kb,
    get_back_to_parser_settings_kb,
    get_interval_selection_kb,
)
from database.database import Database
from .states import Form
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()
db = Database()


@router.callback_query(F.data.startswith("settings_"))
async def parser_settings(callback: CallbackQuery, state: FSMContext):
    parser_name = callback.data.split("_")[1]
    await state.update_data(parser_name=parser_name)

    channels = db.get_parser_channels(parser_name)
    text = f"⚙️ Настройки парсера: {parser_name.upper()}\n\n"
    if not channels:
        text += "Каналы для отправки не настроены.\n\n"
    else:
        text += "Каналы для отправки:\n"
        for channel in channels:
            channel_id = channel["channel_id"]
            try:
                chat = await callback.bot.get_chat(channel_id)
                channel_name = f"@{chat.username}" if chat.username else chat.title
            except Exception:
                channel_name = f"ID: {channel_id}"

            keywords = ", ".join(channel['keywords']) if channel['keywords'] else "любые"
            minus_keywords = ", ".join(channel['minus_keywords']) if channel['minus_keywords'] else "нет"
            text += f"  - {channel_name}:\n"
            text += f"    Ключевые слова: {keywords}\n"
            text += f"    Минус-слова: {minus_keywords}\n"
        text += "\n"

    if parser_name in ["kwork", "fl", "guru", "youdo"]:
        settings = db.get_settings(parser_name)
        min_price = settings.get("min_price", None)
        max_price = settings.get("max_price", None)
        price_range_parts = []
        if min_price is not None:
            price_range_parts.append(f"от {min_price}")
        if max_price is not None:
            price_range_parts.append(f"до {max_price}")
        price_range = ' '.join(price_range_parts) if price_range_parts else 'не задан'
        text += f"**Ценовой диапазон:** {price_range}\n"

        global_keywords = ", ".join(settings.get("keywords", [])) if settings.get("keywords") else "не заданы"
        text += f"**Глобальные ключевые слова:** {global_keywords}\n"

    if parser_name == "vk":
        settings = db.get_vk_settings()
        group_ids = ", ".join(settings.get("group_ids", [])) if settings.get("group_ids") else "не заданы"
        text += f"**ID групп:** {group_ids}\n"

    if parser_name == "habr":
        settings = db.get_habr_settings()
        cities = ", ".join(settings.get("cities", [])) if settings.get("cities") else "не заданы"
        text += f"**Города:** {cities}\n"

    await callback.message.edit_text(text, reply_markup=get_parser_settings_kb(parser_name))
    await callback.answer()


@router.callback_query(F.data.startswith("add_channel_"))
async def add_channel(callback: CallbackQuery, state: FSMContext):
    parser_name = callback.data.split("_")[2]
    await state.update_data(parser_name=parser_name)
    
    channels = db.list_channels()
    if not channels:
        await callback.answer("Бот не является администратором ни в одном канале.", show_alert=True)
        return

    display_channels = [{'id': ch[0], 'name': ch[1]} for ch in channels]

    await callback.message.edit_text(
        "Выберите канал, который хотите добавить:",
        reply_markup=get_channel_selection_kb(parser_name, display_channels, "add")
    )


@router.callback_query(F.data.startswith("select_channel_add_"))
async def select_channel_to_add(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    parser_name = parts[3]
    channel_id = int(parts[4])

    message = await callback.message.edit_text("Введите ключевые слова через запятую (или напишите 'нет', чтобы не использовать ключевые слова):")
    await state.update_data(parser_name=parser_name, channel_id=channel_id, prompt_message_id=message.message_id)
    await state.set_state(Form.setting_keywords)


@router.message(Form.setting_keywords)
async def process_keywords(message: Message, state: FSMContext):
    data = await state.get_data()
    prompt_message_id = data.get("prompt_message_id")

    if message.text.lower() == 'нет':
        keywords = []
    else:
        keywords = [kw.strip() for kw in message.text.split(',') if kw.strip()]
    
    new_prompt = await message.answer("Теперь введите минус-слова через запятую (или напишите 'нет', чтобы не использовать минус-слова):")

    await state.update_data(keywords=keywords, prompt_message_id=new_prompt.message_id)
    await state.set_state(Form.setting_minus_keywords)

    try:
        await message.bot.delete_message(message.chat.id, prompt_message_id)
        await message.delete()
    except Exception as e:
        logging.error(f"Failed to delete messages: {e}")


@router.message(Form.setting_minus_keywords)
async def process_minus_keywords(message: Message, state: FSMContext):
    data = await state.get_data()
    prompt_message_id = data.get("prompt_message_id")
    parser_name = data["parser_name"]
    channel_id = data["channel_id"]
    keywords = data["keywords"]
    if message.text.lower() == 'нет':
        minus_keywords = []
    else:
        minus_keywords = [kw.strip() for kw in message.text.split(',') if kw.strip()]

    db.add_parser_channel(parser_name, channel_id, keywords, minus_keywords)

    await message.answer(
        "✅ Канал успешно добавлен!",
        reply_markup=get_back_to_parser_settings_kb(parser_name)
    )
    await state.clear()

    try:
        await message.bot.delete_message(message.chat.id, prompt_message_id)
        await message.delete()
    except Exception as e:
        logging.error(f"Failed to delete messages: {e}")


@router.callback_query(F.data.startswith("remove_channel_"))
async def remove_channel(callback: CallbackQuery, state: FSMContext):
    parser_name = callback.data.split("_")[2]
    await state.update_data(parser_name=parser_name)

    channels = db.get_parser_channels(parser_name)
    if not channels:
        await callback.answer("У этого парсера нет настроенных каналов.", show_alert=True)
        return

    display_channels = []
    for ch in channels:
        try:
            chat = await callback.bot.get_chat(ch['channel_id'])
            name = f"@{chat.username}" if chat.username else chat.title
            display_channels.append({'id': ch['channel_id'], 'name': name})
        except Exception:
            display_channels.append({'id': ch['channel_id'], 'name': f"ID: {ch['channel_id']}"})

    await callback.message.edit_text(
        "Выберите канал, который хотите удалить:",
        reply_markup=get_channel_selection_kb(parser_name, display_channels, "remove")
    )


@router.callback_query(F.data.startswith("select_channel_remove_"))
async def select_channel_to_remove(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    parser_name = parts[3]
    channel_id = int(parts[4])
    
    db.delete_parser_channel(parser_name, channel_id)
    
    await callback.message.edit_text(
        "✅ Канал удален.",
        reply_markup=get_back_to_parser_settings_kb(parser_name)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_channel_"))
async def edit_channel(callback: CallbackQuery, state: FSMContext):
    parser_name = callback.data.split("_")[2]
    await state.update_data(parser_name=parser_name)

    channels = db.get_parser_channels(parser_name)
    if not channels:
        await callback.answer("У этого парсера нет настроенных каналов.", show_alert=True)
        return

    display_channels = []
    for ch in channels:
        try:
            chat = await callback.bot.get_chat(ch['channel_id'])
            name = f"@{chat.username}" if chat.username else chat.title
            display_channels.append({'id': ch['channel_id'], 'name': name})
        except Exception:
            display_channels.append({'id': ch['channel_id'], 'name': f"ID: {ch['channel_id']}"})

    await callback.message.edit_text(
        "Выберите канал, который хотите отредактировать:",
        reply_markup=get_channel_selection_kb(parser_name, display_channels, "edit")
    )


@router.callback_query(F.data.startswith("select_channel_edit_"))
async def select_channel_to_edit(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    parser_name = parts[3]
    channel_id = int(parts[4])

    message = await callback.message.edit_text("Введите новые ключевые слова через запятую (или напишите 'нет', чтобы не использовать ключевые слова):")
    await state.update_data(parser_name=parser_name, channel_id=channel_id, prompt_message_id=message.message_id)
    await state.set_state(Form.editing_keywords)


@router.message(Form.editing_keywords)
async def process_editing_keywords(message: Message, state: FSMContext):
    data = await state.get_data()
    prompt_message_id = data.get("prompt_message_id")

    if message.text.lower() == 'нет':
        keywords = []
    else:
        keywords = [kw.strip() for kw in message.text.split(',') if kw.strip()]

    new_prompt = await message.answer("Теперь введите новые минус-слова через запятую (или напишите 'нет', чтобы не использовать минус-слова):")

    await state.update_data(keywords=keywords, prompt_message_id=new_prompt.message_id)
    await state.set_state(Form.editing_minus_keywords)

    try:
        await message.bot.delete_message(message.chat.id, prompt_message_id)
        await message.delete()
    except Exception as e:
        logging.error(f"Failed to delete messages: {e}")


@router.message(Form.editing_minus_keywords)
async def process_editing_minus_keywords(message: Message, state: FSMContext):
    data = await state.get_data()
    prompt_message_id = data.get("prompt_message_id")
    parser_name = data["parser_name"]
    channel_id = data["channel_id"]
    keywords = data["keywords"]
    if message.text.lower() == 'нет':
        minus_keywords = []
    else:
        minus_keywords = [kw.strip() for kw in message.text.split(',') if kw.strip()]

    db.add_parser_channel(parser_name, channel_id, keywords, minus_keywords)

    await message.answer(
        "✅ Канал успешно обновлен!",
        reply_markup=get_back_to_parser_settings_kb(parser_name)
    )
    await state.clear()

    try:
        await message.bot.delete_message(message.chat.id, prompt_message_id)
        await message.delete()
    except Exception as e:
        logging.error(f"Failed to delete messages: {e}")

@router.callback_query(F.data.startswith("set_") & F.data.endswith("_interval"))
async def set_parser_interval(callback: CallbackQuery, state: FSMContext):
    parser_name = callback.data.replace("set_", "").replace("_interval", "")
    await state.update_data(parser_name=parser_name)
    
    await callback.message.edit_text(
        "⏰ Выберите интервал между сообщениями:",
        reply_markup=get_interval_selection_kb(parser_name)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("set_") & F.data.endswith("_interval_"))
async def select_parser_interval(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split('_')
    parser_name = parts[1]
    interval = int(parts[3])
    
    db.set_parser_interval(parser_name, interval)
    
    await callback.message.edit_text(
        f"✅ Интервал установлен: {interval} секунд",
        reply_markup=get_back_to_parser_settings_kb(parser_name)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("set_") & F.data.endswith("_price"))
async def set_parser_price(callback: CallbackQuery, state: FSMContext):
    parser_name = callback.data.replace("set_", "").replace("_price", "")
    await state.update_data(parser_name=parser_name)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"settings_{parser_name}")]
    ])
    await callback.message.edit_text("Введите минимальную цену:", reply_markup=keyboard)
    await state.set_state(Form.setting_price_min)
    await callback.answer()

@router.message(Form.setting_price_min)
async def process_price_min(message: Message, state: FSMContext):
    try:
        min_price = int(message.text)
        data = await state.get_data()
        parser_name = data["parser_name"]
        await state.update_data(min_price=min_price)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data=f"settings_{parser_name}")]
        ])
        await message.answer("Теперь введите максимальную цену:", reply_markup=keyboard)
        await state.set_state(Form.setting_price_max)
    except ValueError:
        data = await state.get_data()
        parser_name = data["parser_name"]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data=f"settings_{parser_name}")]
        ])
        await message.answer("❌ Введите число!", reply_markup=keyboard)

@router.message(Form.setting_price_max)
async def process_price_max(message: Message, state: FSMContext):
    try:
        max_price = int(message.text)
        data = await state.get_data()
        parser_name = data["parser_name"]
        min_price = data.get("min_price")

        settings = db.get_settings(parser_name)
        db.save_settings(settings.get('keywords', []), min_price, max_price, parser_name)

        await message.answer(f"✅ Ценовой диапазон обновлён: {min_price} - {max_price}")
        await state.clear()
    except ValueError:
        data = await state.get_data()
        parser_name = data["parser_name"]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data=f"settings_{parser_name}")]
        ])
        await message.answer("❌ Введите число!", reply_markup=keyboard)

@router.callback_query(F.data.startswith("set_") & F.data.endswith("_keywords"))
async def set_parser_keywords(callback: CallbackQuery, state: FSMContext):
    parser_name = callback.data.replace("set_", "").replace("_keywords", "")
    await state.update_data(parser_name=parser_name)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"settings_{parser_name}")]
    ])
    await callback.message.edit_text("Введите ключевые слова через запятую:", reply_markup=keyboard)
    await state.set_state(Form.setting_global_keywords)
    await callback.answer()

@router.message(Form.setting_global_keywords)
async def process_global_keywords(message: Message, state: FSMContext):
    keywords = [kw.strip() for kw in message.text.split(',') if kw.strip()]
    data = await state.get_data()
    parser_name = data["parser_name"]

    settings = db.get_settings(parser_name)
    db.save_settings(keywords, settings.get('min_price'), settings.get('max_price'), parser_name)

    await message.answer(f"✅ Глобальные ключевые слова обновлены.")
    await state.clear()

@router.callback_query(F.data == "set_vk_group_ids")
async def set_vk_group_ids(callback: CallbackQuery, state: FSMContext):
    await state.update_data(parser_name="vk")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_vk")]
    ])
    await callback.message.edit_text("Введите ID групп VK через запятую:", reply_markup=keyboard)
    await state.set_state(Form.setting_vk_group_ids)
    await callback.answer()

@router.message(Form.setting_vk_group_ids)
async def process_vk_group_ids(message: Message, state: FSMContext):
    group_ids = [gid.strip() for gid in message.text.split(',') if gid.strip()]
    settings = db.get_vk_settings()
    settings["group_ids"] = group_ids
    db.save_vk_full_settings(settings)
    await message.answer("✅ ID групп VK обновлены.")
    await state.clear()

@router.callback_query(F.data == "set_habr_cities")
async def set_habr_cities(callback: CallbackQuery, state: FSMContext):
    await state.update_data(parser_name="habr")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_habr")]
    ])
    await callback.message.edit_text("Введите города для Habr Career через запятую:", reply_markup=keyboard)
    await state.set_state(Form.setting_habr_cities)
    await callback.answer()

@router.message(Form.setting_habr_cities)
async def process_habr_cities(message: Message, state: FSMContext):
    cities = [city.strip() for city in message.text.split(',') if city.strip()]
    settings = db.get_habr_settings()
    settings["cities"] = cities
    db.save_habr_settings(settings["keywords"], settings["min_salary"], settings["max_salary"], cities, settings["employment_types"])
    await message.answer("✅ Города для Habr Career обновлены.")
    await state.clear()
