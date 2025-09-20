# services/guru.py
import asyncio
import aiohttp
import logging
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from aiogram import Bot
from urllib.parse import urljoin

from config_reader import config
from database.database import Database
from aiogram.exceptions import TelegramRetryAfter

log = logging.getLogger(__name__)

BASE_URL = "https://www.guru.com"
LIST_URL = f"{BASE_URL}/d/jobs/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

PAGE_CAP = max(1, int(getattr(config, "MAX_PAGES", 5)))


def _text(el) -> str:
    return el.get_text(strip=True) if el else ""


def _price_from_text(text: str) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"\$([\d,]+)", text)
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except Exception:
        return None


def render(item: Dict[str, Any]) -> str:
    title = item.get("title") or "(no title)"
    desc = (item.get("description") or "").strip()
    if len(desc) > 500:
        desc = desc[:497] + "..."
    price = item.get("price")
    price_str = f"${price}" if price is not None else "—"
    url = item.get("url") or ""
    return (
        f"🌐 <b>{title}</b>\n"
        f"💰 Бюджет: {price_str}\n"
        f"{desc}\n"
        f"{url}"
    )


class GuruParserService:
    def __init__(self, bot: Optional[Bot] = None) -> None:
        self.bot = bot
        self.db = Database()
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.lock = asyncio.Lock()

    async def start_parser(self, chat_id: Optional[int] = None) -> None:
        if self.is_running:
            log.info("Guru parser already running")
            return
        self.is_running = True
        self._task = asyncio.create_task(self._run_loop(chat_id))
        log.info("Guru parser started")

    async def stop_parser(self) -> None:
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        log.info("Guru parser stopped")

    async def _run_loop(self, chat_id: Optional[int]) -> None:
        channels = self.db.get_parser_channels("guru")
        if not channels:
            log.info("Нет настроенных каналов для Guru. Парсер не будет запущен.")
            if self.bot and chat_id:
                await self.bot.send_message(chat_id, "Нет настроенных каналов для Guru. Парсер не будет запущен.")
            self.is_running = False
            return

        while self.is_running:
            try:
                await self._parse_and_store(channels)
                # ⚡️ тянем интервал из БД
                settings = self.db.get_parser_settings("guru")
                interval = settings["message_interval"] if settings else config.PARSING_INTERVAL
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Guru parser error: {e}", exc_info=True)
                await asyncio.sleep(60) # Fallback sleep

    async def _parse_and_store(self, channels: List[Dict]) -> int:
        async with self.lock:
            connector = aiohttp.TCPConnector(limit=8, ssl=False)
            timeout = aiohttp.ClientTimeout(total=40)
            async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers=HEADERS) as session:
                page = 1
                settings = self.db.get_guru_settings()
                min_price = settings.get("min_price")
                max_price = settings.get("max_price")

                while page <= PAGE_CAP:
                    items = await self._fetch_page(session, page)
                    if not items:
                        break

                    for channel_config in channels:
                        target_channel = channel_config["channel_id"]
                        keywords = set(kw.lower() for kw in (channel_config.get("keywords") or []))
                        minus_keywords = set(kw.lower() for kw in (channel_config.get("minus_keywords") or []))

                        new_items = []
                        for it in items:
                            title_l = (it.get("title") or "").lower()
                            desc_l = (it.get("description") or "").lower()
                            text_for_filter = title_l + " " + desc_l

                            if keywords and not any(kw in text_for_filter for kw in keywords):
                                continue

                            if minus_keywords and any(kw in text_for_filter for kw in minus_keywords):
                                continue

                            price = it.get("price")
                            if min_price is not None and (price is None or price < min_price):
                                continue
                            if max_price is not None and (price is not None and price > max_price):
                                continue

                            self.db.save_guru_project(it)
                            new_items.append(it)

                        if self.bot and target_channel and new_items:
                            for item in new_items:
                                try:
                                    await self.bot.send_message(
                                        target_channel,
                                        render(item),
                                        parse_mode="HTML",
                                        disable_web_page_preview=True,
                                    )
                                except TelegramRetryAfter as e:
                                    log.warning(f"Flood control exceeded. Retrying in {e.retry_after} seconds.")
                                    await asyncio.sleep(e.retry_after)
                                    await self.bot.send_message(
                                        target_channel,
                                        render(item),
                                        parse_mode="HTML",
                                        disable_web_page_preview=True,
                                    )
                                except Exception as e:
                                    log.error(f"Failed to send message: {e}")
                                await asyncio.sleep(1)
                    page += 1
                    await asyncio.sleep(1)
                return 0

    async def _fetch_page(self, session: aiohttp.ClientSession, page: int) -> List[Dict[str, Any]]:
        url = LIST_URL if page == 1 else f"{LIST_URL}?page={page}"
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return []
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                cards = soup.find_all("div", class_=lambda x: x and "job" in str(x).lower())
                return [self._normalize_card(c) for c in cards]
        except Exception as e:
            log.warning(f"[Guru page {page}] {e}")
        return []

    def _normalize_card(self, node) -> Dict[str, Any]:
        title_el = node.find(["h2", "h3", "a"])
        title = _text(title_el)
        url = ""
        link_el = node.find("a", href=True)
        if link_el and "/jobs/" in link_el["href"]:
            url = urljoin(BASE_URL, link_el["href"])
        desc_el = node.find("p") or node.find("div", class_=lambda x: x and "desc" in str(x).lower())
        description = _text(desc_el)
        price = _price_from_text(node.get_text())
        now_iso = datetime.utcnow().isoformat(timespec="seconds")
        proj_id = abs(hash((title, url))) % (10**9)
        return {
            "id": proj_id,
            "title": title,
            "description": description,
            "price": price,
            "url": url,
            "date_create": now_iso,
            "username": None,
            "category_id": None,
            "source": "guru",
        }
