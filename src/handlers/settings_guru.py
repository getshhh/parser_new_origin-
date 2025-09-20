from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database.database import Database

from .states import Form
from keyboards.settings_guru import settings_guru_kb

router = Router()
db = Database()

async def settings_guru_menu(callback: CallbackQuery, state: FSMContext):
    settings = db.get_guru_settings()
    min_price = settings.get("min_price", None)
    max_price = settings.get("max_price", None)

    price_range_parts = []
    if min_price is not None:
        price_range_parts.append(f"от {min_price}")
    if max_price is not None:
        price_range_parts.append(f"до {max_price}")
    price_range = ' '.join(price_range_parts) if price_range_parts else 'не задан'

    settings_text = (
        "⚙️ **Настройки Guru (специфичные)**\n\n"
        f"**Ценовой диапазон (USD):** {price_range}\n\n"
        "Выберите, что хотите изменить."
    )
    await callback.message.edit_text(settings_text, reply_markup=settings_guru_kb(), parse_mode="Markdown")
    await callback.answer()

# -----------------------------
# изменение диапазона цен (USD)
# -----------------------------
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
        await message.answer("❌ Введите число!")

@router.message(Form.setting_guru_price_max)
async def process_guru_price_max(message: Message, state: FSMContext):
    try:
        max_price = int(message.text)
        data = await state.get_data()
        settings = db.get_guru_settings()
        db.save_guru_settings(settings.get('keywords'), data.get('min_price'), max_price)
        await message.answer(f"✅ Ценовой диапазон для Guru обновлён: {data.get('min_price')} - {max_price} USD")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")


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
