from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database.database import Database

from .states import Form
from keyboards.settings_fl import settings_fl_kb

router = Router()
db = Database()

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@router.callback_query(F.data == "settings_fl")
async def settings_fl(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()

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
        "⚙️ **Настройки FL**\n\n"
        f"**Ценовой диапазон:** {price_range}\n\n"
        "Выберите, что хотите изменить."
    )
    await callback.message.edit_text(settings_text, reply_markup=settings_fl_kb(), parse_mode="Markdown")
    await callback.answer()

# -----------------------------
# изменение диапазона цен
# -----------------------------
from .parser_settings import parser_settings as generic_parser_settings

@router.callback_query(F.data == "channel_settings_fl")
async def channel_settings_fl(callback: CallbackQuery, state: FSMContext):
    callback.data = "settings_fl"
    await generic_parser_settings(callback, state)

@router.callback_query(F.data == "set_fl_price")
async def set_fl_price(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_fl")]
    ])
    await callback.message.edit_text("Введите минимальную цену:", reply_markup=keyboard)
    await state.set_state(Form.setting_fl_price_min)
    await callback.answer()

@router.message(Form.setting_fl_price_min)
async def process_fl_price_min(message: Message, state: FSMContext):
    try:
        min_price = int(message.text)
        await state.update_data(min_price=min_price)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_fl")]
        ])
        await message.answer("Теперь введите максимальную цену:", reply_markup=keyboard)
        await state.set_state(Form.setting_fl_price_max)
    except ValueError:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_fl")]
        ])
        await message.answer("❌ Введите число!", reply_markup=keyboard)

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
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_fl")]
        ])
        await message.answer("❌ Введите число!", reply_markup=keyboard)
