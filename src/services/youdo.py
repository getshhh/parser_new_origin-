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
            settings = self.db.get_youdo_settings()
            parser_cfg = self.db.get_parser_settings("youdo")

            # если канал в настройках — туда, иначе тот чат, где включили
            target_channel = parser_cfg["channel_id"] if parser_cfg and parser_cfg.get("channel_id") else chat_id

            keywords = set(kw.lower() for kw in (settings.get("keywords") or []))
            min_price = settings.get("min_price")
            max_price = settings.get("max_price")

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

                    new_tasks = []
                    for item in items:
                        title = item.get("Name", "")
                        desc = item.get("Description", "")
                        title_l, desc_l = title.lower(), desc.lower()

                        # фильтр по ключевым словам
                        if keywords and not any(kw in title_l or kw in desc_l for kw in keywords):
                            continue

                        # бюджет
                        budget = item.get("Budget")
                        if min_price is not None and (budget is None or budget < min_price):
                            continue
                        if max_price is not None and (budget is not None and budget > max_price):
                            continue

                        task = {
                            "id": item.get("Id"),
                            "title": title,
                            "description": desc,
                            "address": item.get("Address"),
                            "budget": item.get("BudgetDescription"),
                            "date": item.get("DateTimeString"),
                            "url": f"https://youdo.com{item.get('Url')}",
                            "date_create": datetime.utcnow().isoformat(timespec="seconds"),
                        }

                        self.db.save_youdo_task(task)
                        new_tasks.append(task)

                    if self.bot and target_channel and new_tasks:
                        for task in new_tasks:
                            try:
                                await self.bot.send_message(
                                    target_channel, render(task),
                                    parse_mode="HTML",
                                    disable_web_page_preview=True
                                )
                            except TelegramRetryAfter as e:
                                log.warning(f"Flood control exceeded. Retrying in {e.retry_after} seconds.")
                                await asyncio.sleep(e.retry_after)
                                await self.bot.send_message(
                                    target_channel, render(task),
                                    parse_mode="HTML",
                                    disable_web_page_preview=True
                                )
                            except Exception as e:
                                log.error(f"Failed to send message: {e}")
                            await asyncio.sleep(1)

    # 🔹 Новые методы управления настройками
    async def set_keywords(self, keywords: List[str]) -> None:
        settings = self.db.get_youdo_settings()
        self.db.save_youdo_settings(
            keywords, settings["min_price"], settings["max_price"]
        )
        log.info(f"YouDo keywords set: {keywords}")

    async def set_price_range(self, min_price: int, max_price: int) -> None:
        settings = self.db.get_youdo_settings()
        self.db.save_youdo_settings(
            settings["keywords"], min_price, max_price
        )
        log.info(f"YouDo price range set: {min_price}-{max_price}")
