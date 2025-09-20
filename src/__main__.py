# __main__.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from aiogram.types import TelegramObject

from handlers import setup_message_routers, services

# сервисы парсеров
from services.kwork import KworkParserService
from services.habr import HabrParserService
from services.fl import FLParserService
from services.guru import GuruParserService
from services.youdo import YouDoParserService
from services.vk import VKParserService
from services.workzilla import WorkZillaParserService
from services.weblancer import WebLancerParserService


from database.database import Database
from config_reader import config

gpt_task = None


async def stop_gpt_task():
    global gpt_task
    if gpt_task is not None and not gpt_task.done():
        gpt_task.cancel()
        logging.info("GPT task stopped.")

class TaskManagerMiddleware(BaseMiddleware):
    def __init__(self, start_task_func, stop_task_func):
        self.start_task_func = start_task_func
        self.stop_task_func = stop_task_func

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["start_gpt_task"] = self.start_task_func
        data["stop_gpt_task"] = self.stop_task_func
        return await handler(event, data)

async def main() -> None:
    bot_token = config.BOT_TOKEN.get_secret_value()
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # инициализация сервисов парсеров
    kwork_parser = KworkParserService(bot)
    habr_parser = HabrParserService(bot=bot)
    fl_parser = FLParserService(bot=bot)
    guru_parser = GuruParserService(bot=bot)
    youdo_parser = YouDoParserService(bot=bot)
    vk_parser = VKParserService(bot=bot)
    workzilla_parser = WorkZillaParserService(bot=bot)
    weblancer_parser = WebLancerParserService(bot=bot)


    # передаём все парсеры в services
    services.setup_parser_services(
        kwork_parser,
        habr_parser,
        fl_parser,
        guru_parser,
        youdo_parser,
        vk_parser,
        workzilla_parser,
        weblancer_parser
    )

    # настраиваем routers
    message_routers = setup_message_routers()
    dp.include_router(message_routers)

    # инициализация базы данных
    db = Database()

    await bot.delete_webhook(True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass