# handlers/stats.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database.database import Database
from services.kwork import render as render_kwork
from services.guru import render as render_guru
from services.youdo import render as render_youdo
from .services import habr_parser_service

# ✅ вот это обязательно
router = Router()
db = Database()

@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def stats(message: Message) -> None:
    kwork_count = await db.get_total_projects_count()
    habr_count = await db.get_total_habr_vacancies_count()
    fl_count = await db.get_total_fl_projects_count()
    guru_count = await db.get_total_guru_projects_count()
    youdo_count = await db.get_total_youdo_tasks_count()

    text = f"""
📊 Статистика парсеров:
🛠️ Kwork: {kwork_count} проектов
💼 Habr Career: {habr_count} вакансий
💻 FL: {fl_count} проектов
🌐 Guru: {guru_count} проектов
📱 YouDo: {youdo_count} заданий
    """.strip()
    await message.answer(text)
