from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from database.database import Database

router = Router()
db = Database()

@router.message(Command("add_source"))
async def add_source_handler(message: Message):
    try:
        link = message.text.split(" ")[1]
        db.add_source(link)
        await message.answer(f"Источник {link} добавлен.")
    except IndexError:
        await message.answer("Пожалуйста, укажите ссылку после команды /add_source.")
    except Exception as e:
        await message.answer(f"Произошла ошибка при добавлении источника: {e}")