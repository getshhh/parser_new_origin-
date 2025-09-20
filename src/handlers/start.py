from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from database.database import Database

from keyboards.main_menu import main_menu_kb  # ✅ импортируем клавиатуру

router = Router()
db = Database()

@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "Добро пожаловать в панель управления парсером! Выберите действие:",
        reply_markup=main_menu_kb()
    )

@router.message(Command("help"))
async def help_me(message: Message) -> None:
    help_text = """
📋 Команды парсера:

/start - Запуск бота
/help - Помощь по командам

🎛️ Кнопки меню:
📊 Статистика - Показать статистику
⚙️ Настройки - Изменить параметры парсинга
▶️ Включить парсер - Запуск парсера
⏹️ Выключить парсер - Остановка парсера
⏹️ Выключить все парсеры - Остановить все парсеры
"""
    await message.answer(help_text, reply_markup=main_menu_kb())
