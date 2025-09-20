from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database.database import Database

from .states import Form
from keyboards.settings_fl import settings_fl_kb

router = Router()
db = Database()

async def settings_fl_menu(callback: CallbackQuery, state: FSMContext):
    settings = db.get_fl_settings()
    min_price = settings.get("min_price", None)
    max_price = settings.get("max_price", None)

    price_range_parts = []
    if min_price is not None:
        price_range_parts.append(f"от {min_price}")
    if max_price is not None:
        price_range_parts.append(f"до {max_price}")
    price_range = ' '.join(price_range_parts) if price_range_parts else 'не задан'

    settings_text = (
        "⚙️ **Настройки FL (специфичные)**\n\n"
        f"**Ценовой диапазон:** {price_range}\n\n"
        "Выберите, что хотите изменить."
    )
    await callback.message.edit_text(settings_text, reply_markup=settings_fl_kb(), parse_mode="Markdown")
    await callback.answer()

# -----------------------------
# изменение диапазона цен
# -----------------------------
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
        await message.answer("❌ Введите число!")

@router.message(Form.setting_fl_price_max)
async def process_fl_price_max(message: Message, state: FSMContext):
    try:
        max_price = int(message.text)
        data = await state.get_data()
        settings = db.get_fl_settings()
        db.save_fl_settings(settings.get('keywords'), data.get('min_price'), max_price)
        await message.answer(f"✅ Ценовой диапазон для FL обновлён: {data.get('min_price')} - {max_price} руб.")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")


# -----------------------------
# Настройка интервала для FL
# -----------------------------
@router.callback_query(F.data == "set_fl_interval")
async def set_fl_interval(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите интервал между сообщениями в секундах:")
    await state.set_state(Form.setting_fl_interval)
    await callback.answer()

@router.message(Form.setting_fl_interval)
async def process_fl_interval(message: Message, state: FSMContext):
    try:
        interval = int(message.text)
        if interval <= 0:
            await message.answer("❌ Интервал должен быть положительным числом. Попробуйте еще раз.")
            return

        db.set_parser_interval('fl', interval)
        await message.answer(f"✅ Интервал для FL установлен: {interval} сек.")
        await state.clear()

    except ValueError:
        await message.answer("❌ Введите число!")
