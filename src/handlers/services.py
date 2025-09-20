# services.py
import asyncio
from database.database import Database
from aiogram import Bot

from services.kwork import KworkParserService
from services.habr import HabrParserService
from services.fl import FLParserService
from services.guru import GuruParserService
from services.youdo import YouDoParserService
from services.vk import VKParserService
from services.workzilla import WorkZillaParserService
from services.weblancer import WebLancerParserService

db = Database()

class ParserService:
    def __init__(self, name: str, bot: Bot):
        self.name = name
        self.bot = bot
        self.is_running = False

    async def start_parser(self, chat_id: int):
        """Запуск парсера с учётом настроек БД (канал + интервал)."""
        self.is_running = True
        settings = db.get_parser_settings(self.name)

        channel_id = settings["channel_id"] if settings and settings["channel_id"] else chat_id
        interval = settings["message_interval"] if settings else 120

        while self.is_running:
            data = await self.fetch_new_data()
            if data:
                # ⚡️ Можно подключить GPT перед отправкой
                # from services.gpt import process_text
                # data = await process_text(data)

                await self.bot.send_message(channel_id, data)
            await asyncio.sleep(interval)

    async def stop_parser(self):
        self.is_running = False

    async def fetch_new_data(self):
        """Этот метод переопределяется в наследниках (реальный парсинг)."""
        return None


# глобальные переменные для сервисов
kwork_parser_service: KworkParserService | None = None
habr_parser_service: HabrParserService | None = None
fl_parser_service: FLParserService | None = None
guru_parser_service: GuruParserService | None = None
youdo_parser_service: YouDoParserService | None = None
vk_parser_service: VKParserService | None = None
workzilla_parser_service: WorkZillaParserService | None = None
weblancer_parser_service: WebLancerParserService | None = None


def setup_parser_services(
    kwork_service,
    habr_service,
    fl_service,
    guru_service,
    youdo_service,
    vk_service,
    workzilla_service,
    weblancer_service
) -> None:
    """Привязка экземпляров сервисов к глобальным переменным"""
    global kwork_parser_service, habr_parser_service, fl_parser_service
    global guru_parser_service, youdo_parser_service, vk_parser_service
    global workzilla_parser_service, weblancer_parser_service

    kwork_parser_service = kwork_service
    habr_parser_service = habr_service
    fl_parser_service = fl_service
    guru_parser_service = guru_service
    youdo_parser_service = youdo_service
    vk_parser_service = vk_service
    workzilla_parser_service = workzilla_service
    weblancer_parser_service = weblancer_service
