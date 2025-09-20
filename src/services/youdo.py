# services/youdo.py
import asyncio
import aiohttp
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from aiogram import Bot
from database.database import Database
from config_reader import config
from aiogram.exceptions import TelegramRetryAfter

log = logging.getLogger(__name__)

API_URL = "https://youdo.com/api/tasks/tasks"


def render(task: Dict[str, Any]) -> str:
    return (
        f"📌 <b>{task.get('title')}</b>\n"
        f"📍 {task.get('address') or '—'}\n"
        f"💰 {task.get('budget') or '—'}\n"
        f"🕒 {task.get('date') or '—'}\n"
        f"🔗 {task.get('url')}"
    )


class YouDoParserService:
    def __init__(self, bot: Optional[Bot] = None) -> None:
        self.bot = bot
        self.db = Database()
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.lock = asyncio.Lock()

    async def start_parser(self, chat_id: Optional[int] = None) -> None:
        if self.is_running:
            log.info("YouDo parser already running")
            return
        self.is_running = True
        self._task = asyncio.create_task(self._run_loop(chat_id))
        log.info("YouDo parser started")

    async def stop_parser(self) -> None:
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        log.info("YouDo parser stopped")

    async def _run_loop(self, chat_id: Optional[int]) -> None:
        while self.is_running:
            try:
                await self._parse_and_store(chat_id)
                # ⚡️ тянем интервал из БД
                settings = self.db.get_parser_settings("youdo")
                interval = settings["message_interval"] if settings else config.PARSING_INTERVAL
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"YouDo parser error: {e}", exc_info=True)
                await asyncio.sleep(60) # Fallback sleep

    async def _parse_and_store(self, chat_id: Optional[int]) -> None:
        async with self.lock:
            channels = self.db.get_parser_channels("youdo")
            if not channels:
                log.info("Нет настроенных каналов для YouDo.")
                return

            global_settings = self.db.get_youdo_settings()

            json_data = {
                "q": "",
                "status": "opened",
                "radius": None,
                "lat": 55.755864,
                "lng": 37.617698,
                "page": 1,
                "priceMin": "",
                "sortType": 1,
                "categories": ["all"],
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(API_URL, json=json_data) as resp:
                    data = await resp.json()
                    items = data.get("ResultObject", {}).get("Items", [])

                    for channel in channels:
                        new_tasks = []
                        for item in items:
                            task = {
                                "id": item.get("Id"),
                                "title": item.get("Name", ""),
                                "description": item.get("Description", ""),
                                "address": item.get("Address"),
                                "budget": item.get("BudgetDescription"),
                                "date": item.get("DateTimeString"),
                                "url": f"https://youdo.com{item.get('Url')}",
                                "date_create": datetime.utcnow().isoformat(timespec="seconds"),
                                "price": item.get("Budget")
                            }
                            if self._filter_item(task, global_settings, channel):
                                self.db.save_youdo_task(task)
                                new_tasks.append(task)

                        if self.bot and new_tasks:
                            for task in new_tasks:
                                try:
                                    await self.bot.send_message(
                                        channel["channel_id"], render(task),
                                        parse_mode="HTML",
                                        disable_web_page_preview=True
                                    )
                                except TelegramRetryAfter as e:
                                    log.warning(f"Flood control exceeded. Retrying in {e.retry_after} seconds.")
                                    await asyncio.sleep(e.retry_after)
                                    await self.bot.send_message(
                                        channel["channel_id"], render(task),
                                        parse_mode="HTML",
                                        disable_web_page_preview=True
                                    )
                                except Exception as e:
                                    log.error(f"Failed to send message: {e}")
                                await asyncio.sleep(1)

    def _filter_item(self, item: Dict[str, Any], global_settings: dict, channel_settings: dict) -> bool:
        # Сначала применяем глобальные фильтры
        global_keywords = global_settings.get("keywords", [])
        min_price = global_settings.get("min_price")
        max_price = global_settings.get("max_price")

        title_and_desc = (item.get("title", "") + " " + item.get("description", "")).lower()
        if global_keywords:
            if not any(kw.lower() in title_and_desc for kw in global_keywords):
                return False

        price = item.get("price")
        if min_price is not None and (price is None or price < min_price):
            return False
        if max_price is not None and (price is not None and price > max_price):
            return False

        # Затем применяем фильтры для конкретного канала
        channel_keywords = channel_settings.get("keywords", [])
        channel_minus_keywords = channel_settings.get("minus_keywords", [])

        if channel_keywords:
            if not any(kw.lower() in title_and_desc for kw in channel_keywords):
                return False

        if channel_minus_keywords:
            if any(kw.lower() in title_and_desc for kw in channel_minus_keywords):
                return False

        return True
