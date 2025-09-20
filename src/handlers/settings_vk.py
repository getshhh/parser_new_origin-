from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database.database import Database

from .states import Form
from keyboards.settings_vk import settings_vk_kb
import re

router = Router()
db = Database()

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@router.callback_query(F.data == "settings_vk")
async def settings_vk(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()

    settings = db.get_vk_settings()
    min_price = settings.get("min_price", None)
    max_price = settings.get("max_price", None)
    group_ids = settings.get('group_ids', [])

    price_range_parts = []
    if min_price is not None:
        price_range_parts.append(f"от {min_price}")
    if max_price is not None:
        price_range_parts.append(f"до {max_price}")
    price_range = ' '.join(price_range_parts) if price_range_parts else 'не задан'

    settings_text = (
        "⚙️ **Настройки VK**\n\n"
        f"**Ценовой диапазон:** {price_range}\n"
        f"**ID групп:** {', '.join(group_ids) if group_ids else 'Не заданы'}\n\n"
        "Выберите, что хотите изменить."
    )
    await callback.message.edit_text(settings_text, reply_markup=settings_vk_kb(), parse_mode="Markdown")
    await callback.answer()

# -----------------------------
# изменение диапазона цен
# -----------------------------
from .parser_settings import parser_settings as generic_parser_settings

@router.callback_query(F.data == "channel_settings_vk")
async def channel_settings_vk(callback: CallbackQuery, state: FSMContext):
    callback.data = "settings_vk"
    await generic_parser_settings(callback, state)

@router.callback_query(F.data == "set_vk_price")
async def set_vk_price(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_vk")]
    ])
    await callback.message.edit_text("Введите минимальную цену:", reply_markup=keyboard)
    await state.set_state(Form.vk_price_min)
    await callback.answer()

@router.message(Form.vk_price_min)
async def process_vk_price_min(message: Message, state: FSMContext):
    try:
        min_price = int(message.text)
        await state.update_data(min_price=min_price)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_vk")]
        ])
        await message.answer("Теперь введите максимальную цену:", reply_markup=keyboard)
        await state.set_state(Form.vk_price_max)
    except ValueError:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_vk")]
        ])
        await message.answer("❌ Введите число!", reply_markup=keyboard)

@router.message(Form.vk_price_max)
async def process_vk_price_max(message: Message, state: FSMContext):
    try:
        max_price = int(message.text)
        data = await state.get_data()
        settings = db.get_vk_settings()
        db.save_vk_settings(settings.get('keywords'), data.get('min_price'), max_price)
        await message.answer(f"✅ Ценовой диапазон VK обновлён: {data.get('min_price')} - {max_price} руб.")
        await state.clear()
    except ValueError:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_vk")]
        ])
        await message.answer("❌ Введите число!", reply_markup=keyboard)

# -----------------------------
# изменение ID групп
# -----------------------------
@router.callback_query(F.data == "set_vk_groups")
async def set_vk_groups(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_vk")]
    ])
    await callback.message.edit_text("Введите ID групп через запятую (например: -123456, -654321):", reply_markup=keyboard)
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
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_vk")]
        ])
        await message.answer(f"❌ Ошибка: {e}", reply_markup=keyboard)