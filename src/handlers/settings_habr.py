from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database.database import Database

from .states import Form
from keyboards.settings_habr import settings_habr_kb

router = Router()
db = Database()

async def settings_habr_menu(callback: CallbackQuery, state: FSMContext):
    settings = db.get_habr_settings()
    min_salary = settings.get("min_salary", None)
    max_salary = settings.get("max_salary", None)
    cities = settings.get("cities", [])

    salary_range_parts = []
    if min_salary is not None:
        salary_range_parts.append(f"от {min_salary}")
    if max_salary is not None:
        salary_range_parts.append(f"до {max_salary}")
    salary_range = ' '.join(salary_range_parts) if salary_range_parts else 'не задан'

    settings_text = (
        "⚙️ **Настройки Habr (специфичные)**\n\n"
        f"**Зарплатный диапазон:** {salary_range}\n"
        f"**Города:** {', '.join(cities) if cities else 'Все города'}\n\n"
        "Выберите, что хотите изменить."
    )
    await callback.message.edit_text(settings_text, reply_markup=settings_habr_kb(), parse_mode="Markdown")
    await callback.answer()

# -----------------------------
# изменение зарплаты
# -----------------------------
@router.callback_query(F.data == "set_habr_salary")
async def set_habr_salary(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите минимальную зарплату:")
    await state.set_state(Form.setting_habr_salary_min)
    await callback.answer()

@router.message(Form.setting_habr_salary_min)
async def process_habr_salary_min(message: Message, state: FSMContext):
    try:
        min_salary = int(message.text)
        await state.update_data(min_salary=min_salary)
        await message.answer("Теперь введите максимальную зарплату:")
        await state.set_state(Form.setting_habr_salary_max)
    except ValueError:
        await message.answer("❌ Введите число!")

@router.message(Form.setting_habr_salary_max)
async def process_habr_salary_max(message: Message, state: FSMContext):
    try:
        max_salary = int(message.text)
        data = await state.get_data()
        settings = db.get_habr_settings()
        db.save_habr_settings(
            keywords=settings.get("keywords", []),
            min_salary=data.get('min_salary'),
            max_salary=max_salary,
            cities=settings.get("cities", []),
            employment_types=settings.get("employment_types", [])
        )
        await message.answer(f"✅ Зарплатный диапазон обновлён: {data.get('min_salary')} - {max_salary} руб.")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

# -----------------------------
# изменение городов
# -----------------------------
@router.callback_query(F.data == "set_habr_cities")
async def set_habr_cities(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите города через запятую (оставьте пустым для всех):")
    await state.set_state(Form.setting_habr_cities)
    await callback.answer()

@router.message(Form.setting_habr_cities)
async def process_habr_cities(message: Message, state: FSMContext):
    cities = [c.strip() for c in message.text.split(',') if c.strip()]
    settings = db.get_habr_settings()
    db.save_habr_settings(
        keywords=settings.get("keywords", []),
        min_salary=settings.get("min_salary"),
        max_salary=settings.get("max_salary"),
        cities=cities,
        employment_types=settings.get("employment_types", [])
    )
    await message.answer(f"✅ Города обновлены: {', '.join(cities) if cities else 'Все города'}")
    await state.clear()


# -----------------------------
# Настройка интервала для Habr
# -----------------------------
@router.callback_query(F.data == "set_habr_interval")
async def set_habr_interval(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите интервал между сообщениями в секундах:")
    await state.set_state(Form.setting_habr_interval)
    await callback.answer()

@router.message(Form.setting_habr_interval)
async def process_habr_interval(message: Message, state: FSMContext):
    try:
        interval = int(message.text)
        if interval <= 0:
            await message.answer("❌ Интервал должен быть положительным числом. Попробуйте еще раз.")
            return

        db.set_parser_interval('habr', interval)
        await message.answer(f"✅ Интервал для Habr установлен: {interval} сек.")
        await state.clear()

    except ValueError:
        await message.answer("❌ Введите число!")
