from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database.database import Database

from .states import Form
from keyboards.settings_weblancer import settings_weblancer_kb

router = Router()
db = Database()

@router.callback_query(F.data == "settings_weblancer")
async def settings_weblancer(callback: CallbackQuery, state: FSMContext):
    settings = db.get_weblancer_settings()
    min_price = settings.get("min_price", None)
    max_price = settings.get("max_price", None)

    price_range_parts = []
    if min_price is not None:
        price_range_parts.append(f"от {min_price}")
    if max_price is not None:
        price_range_parts.append(f"до {max_price}")
    price_range = ' '.join(price_range_parts) if price_range_parts else 'не задан'

    settings_text = (
        "⚙️ **Настройки Weblancer**\n\n"
        f"**Ценовой диапазон:** {price_range}\n\n"
        "Выберите, что хотите изменить."
    )
    await callback.message.edit_text(settings_text, reply_markup=settings_weblancer_kb(), parse_mode="Markdown")
    await callback.answer()

from .parser_settings import parser_settings as generic_parser_settings

@router.callback_query(F.data == "channel_settings_weblancer")
async def channel_settings_weblancer(callback: CallbackQuery, state: FSMContext):
    callback.data = "settings_weblancer"
    await generic_parser_settings(callback, state)

@router.callback_query(F.data == "set_weblancer_price")
async def set_weblancer_price(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите минимальную цену:")
    await state.set_state(Form.weblancer_price_min)
    await callback.answer()

@router.message(Form.weblancer_price_min)
async def process_weblancer_price_min(message: Message, state: FSMContext):
    try:
        min_price = int(message.text)
        await state.update_data(min_price=min_price)
        await message.answer("Теперь введите максимальную цену:")
        await state.set_state(Form.weblancer_price_max)
    except ValueError:
        await message.answer("❌ Введите число!")

@router.message(Form.weblancer_price_max)
async def process_weblancer_price_max(message: Message, state: FSMContext):
    try:
        max_price = int(message.text)
        data = await state.get_data()
        settings = db.get_weblancer_settings()
        db.save_weblancer_settings(settings.get('keywords'), data.get('min_price'), max_price)
        await message.answer(f"✅ Ценовой диапазон WebLancer обновлён: {data.get('min_price')} - {max_price} руб.")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")


# -----------------------------
# Настройка интервала для Weblancer
# -----------------------------
@router.callback_query(F.data == "set_weblancer_interval")
async def set_weblancer_interval(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите интервал между сообщениями в секундах:")
    await state.set_state(Form.weblancer_interval)
    await callback.answer()

@router.message(Form.weblancer_interval)
async def process_weblancer_interval(message: Message, state: FSMContext):
    try:
        interval = int(message.text)
        if interval <= 0:
            await message.answer("❌ Интервал должен быть положительным числом. Попробуйте еще раз.")
            return

        db.set_parser_interval('weblancer', interval)
        await message.answer(f"✅ Интервал для Weblancer установлен: {interval} сек.")
        await state.clear()

    except ValueError:
        await message.answer("❌ Введите число!")