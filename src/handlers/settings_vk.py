from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database.database import Database

from .states import Form
from keyboards.settings_vk import settings_vk_kb
import re

router = Router()
db = Database()

async def settings_vk_menu(callback: CallbackQuery, state: FSMContext):
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
        "⚙️ **Настройки VK (специфичные)**\n\n"
        f"**Ценовой диапазон:** {price_range}\n"
        f"**ID групп:** {', '.join(group_ids) if group_ids else 'Не заданы'}\n\n"
        "Выберите, что хотите изменить."
    )
    await callback.message.edit_text(settings_text, reply_markup=settings_vk_kb(), parse_mode="Markdown")
    await callback.answer()

# -----------------------------
# изменение диапазона цен
# -----------------------------
@router.callback_query(F.data == "set_vk_price")
async def set_vk_price(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите минимальную цену:")
    await state.set_state(Form.vk_price_min)
    await callback.answer()

@router.message(Form.vk_price_min)
async def process_vk_price_min(message: Message, state: FSMContext):
    try:
        min_price = int(message.text)
        await state.update_data(min_price=min_price)
        await message.answer("Теперь введите максимальную цену:")
        await state.set_state(Form.vk_price_max)
    except ValueError:
        await message.answer("❌ Введите число!")

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
        await message.answer("❌ Введите число!")

# -----------------------------
# изменение ID групп
# -----------------------------
@router.callback_query(F.data == "set_vk_groups")
async def set_vk_groups(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите ID групп через запятую (например: -123456, -654321):")
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
        await message.answer(f"❌ Ошибка: {e}")


# -----------------------------
# Настройка интервала для VK
# -----------------------------
@router.callback_query(F.data == "set_vk_interval")
async def set_vk_interval(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите интервал между сообщениями в секундах:")
    await state.set_state(Form.vk_interval)
    await callback.answer()

@router.message(Form.vk_interval)
async def process_vk_interval(message: Message, state: FSMContext):
    try:
        interval = int(message.text)
        if interval <= 0:
            await message.answer("❌ Интервал должен быть положительным числом. Попробуйте еще раз.")
            return

        db.set_parser_interval('vk', interval)
        await message.answer(f"✅ Интервал для VK установлен: {interval} сек.")
        await state.clear()

    except ValueError:
        await message.answer("❌ Введите число!")