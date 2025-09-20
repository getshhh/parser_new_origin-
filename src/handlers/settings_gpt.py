# src/handlers/settings_gpt.py
from aiogram import Router, F
from aiogram.types import CallbackQuery

from typing import Callable
from database.database import Database
from keyboards.settings_gpt import settings_gpt_kb
from keyboards.settings import settings_root_kb

router = Router()
db = Database()

@router.callback_query(F.data == "settings_gpt")
async def open_gpt_settings(callback: CallbackQuery):
    status = db.get_gpt_status()
    await callback.message.edit_text(
        "Настройки GPT",
        reply_markup=settings_gpt_kb(status)
    )
    await callback.answer()

@router.callback_query(F.data == "start_gpt")
async def start_gpt(callback: CallbackQuery, start_gpt_task: Callable):
    db.set_gpt_status("running")
    await start_gpt_task()
    await callback.message.edit_text(
        "GPT запущен",
        reply_markup=settings_gpt_kb("running")
    )
    await callback.answer()

@router.callback_query(F.data == "stop_gpt")
async def stop_gpt(callback: CallbackQuery, stop_gpt_task: Callable):
    db.set_gpt_status("stopped")
    await stop_gpt_task()
    await callback.message.edit_text(
        "GPT остановлен",
        reply_markup=settings_gpt_kb("stopped")
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_main_settings")
async def back_to_main_settings_from_gpt(callback: CallbackQuery):
    await callback.message.edit_text("Выберите парсер для настройки:", reply_markup=settings_root_kb())
    await callback.answer()