from loguru import logger
from telethon import TelegramClient
from telethon.errors import PhoneNumberInvalidError
from telethon.tl.types import Message

from pkg import CustomLogger
from src.settings import settings

CustomLogger().add_logger(settings.path.info_log_file, __name__)


class UserBotChecker:
    def __init__(self, api_id: int, api_hash: str, name: str, phone: str) -> None:
        self._client = TelegramClient(name, api_id, api_hash)
        self._phone = phone

    def get_client(self) -> TelegramClient:
        return self._client

    async def start_client(self):
        try:
            await self._client.start(phone=self._phone)
            logger.info("Userbot initialized")
        except PhoneNumberInvalidError:
            logger.error("The phone number is invalid. Check the number and try again.")
            return False
        return True

    async def stop_client(self):
        await self._client.disconnect()

    async def me_get_dialogs(self):
        dialogs = []
        async for dialog in self._client.iter_dialogs():
            dialogs.append(dialog)

        return dialogs

    async def iter_messages(
        self,
        channel_id: int,
        last_processed_id: int,
        limit: int = 50,
    ):
        """
        Получить текстовые сообщения после определенного message_id с лимитом.

        :param channel_id: ID канала/чата
        :param last_processed_id: ID последнего обработанного сообщения
        :param limit: Максимальное количество сообщений для обработки
        """
        entity = await self._client.get_entity(channel_id)
        async for message in self._client.iter_messages(
            entity, min_id=last_processed_id, limit=limit
        ):
            yield message
