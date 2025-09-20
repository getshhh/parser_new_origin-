# handlers/channel_handler.py
from aiogram import Router, F
from aiogram.types import ChatMemberUpdated, Message
from database.database import Database

router = Router()
db = Database()

@router.my_chat_member()
async def handle_chat_member_update(update: ChatMemberUpdated):
    if update.new_chat_member.status in ["administrator", "creator"]:
        # Бот добавлен как администратор
        db.upsert_channel(update.chat.id, update.chat.title)
    elif update.new_chat_member.status in ["left", "kicked"]:
        # Бот удален из канала
        db.delete_channel_entry(update.chat.id)

@router.message(F.chat.type.in_({"channel"}))
async def handle_channel_message(message: Message):
    # Обновляем информацию о канале при получении сообщения
    db.upsert_channel(message.chat.id, message.chat.title)