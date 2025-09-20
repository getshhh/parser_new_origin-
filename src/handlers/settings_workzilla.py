from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database.database import Database

from .states import Form
from keyboards.settings_workzilla import settings_workzilla_kb

router = Router()
db = Database()

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@router.callback_query(F.data == "settings_workzilla")
async def settings_workzilla(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()

    settings = db.get_workzilla_settings()
    min_price = settings.get("min_price", None)
    max_price = settings.get("max_price", None)

    price_range_parts = []
    if min_price is not None:
        price_range_parts.append(f"от {min_price}")
    if max_price is not None:
        price_range_parts.append(f"до {max_price}")
    price_range = ' '.join(price_range_parts) if price_range_parts else 'не задан'

    settings_text = (
        "⚙️ **Настройки Work-Zilla**\n\n"
        f"**Ценовой диапазон:** {price_range}\n\n"
        "Выберите, что хотите изменить."
    )
    await callback.message.edit_text(settings_text, reply_markup=settings_workzilla_kb(), parse_mode="Markdown")
    await callback.answer()

from .parser_settings import parser_settings as generic_parser_settings

@router.callback_query(F.data == "channel_settings_workzilla")
async def channel_settings_workzilla(callback: CallbackQuery, state: FSMContext):
    callback.data = "settings_workzilla"
    await generic_parser_settings(callback, state)

@router.callback_query(F.data == "set_workzilla_price")
async def set_workzilla_price(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_workzilla")]
    ])
    await callback.message.edit_text("Введите минимальную цену:", reply_markup=keyboard)
    await state.set_state(Form.workzilla_price_min)
    await callback.answer()

@router.message(Form.workzilla_price_min)
async def process_workzilla_price_min(message: Message, state: FSMContext):
    try:
        min_price = int(message.text)
        await state.update_data(min_price=min_price)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_workzilla")]
        ])
        await message.answer("Теперь введите максимальную цену:", reply_markup=keyboard)
        await state.set_state(Form.workzilla_price_max)
    except ValueError:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_workzilla")]
        ])
        await message.answer("❌ Введите число!", reply_markup=keyboard)

@router.message(Form.workzilla_price_max)
async def process_workzilla_price_max(message: Message, state: FSMContext):
    try:
        max_price = int(message.text)
        data = await state.get_data()
        settings = db.get_workzilla_settings()
        db.save_workzilla_settings(settings.get('keywords'), data.get('min_price'), max_price)
        await message.answer(f"✅ Ценовой диапазон Work-Zilla обновлён: {data.get('min_price')} - {max_price} руб.")
        await state.clear()
    except ValueError:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_workzilla")]
        ])
        await message.answer("❌ Введите число!", reply_markup=keyboard)


# -----------------------------
# Настройка интервала для Work-Zilla
# -----------------------------
@router.callback_query(F.data == "set_workzilla_interval")
async def set_workzilla_interval(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите интервал между сообщениями в секундах:")
    await state.set_state(Form.workzilla_interval)
    await callback.answer()

@router.message(Form.workzilla_interval)
async def process_workzilla_interval(message: Message, state: FSMContext):
    try:
        interval = int(message.text)
        if interval <= 0:
            await message.answer("❌ Интервал должен быть положительным числом. Попробуйте еще раз.")
            return

        db.set_parser_interval('workzilla', interval)
        await message.answer(f"✅ Интервал для Work-Zilla установлен: {interval} сек.")
        await state.clear()

    except ValueError:
        await message.answer("❌ Введите число!")