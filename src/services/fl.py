# services/fl.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import logging
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from aiogram import Bot

from config_reader import config
from database.database import Database
from aiogram.exceptions import TelegramRetryAfter

log = logging.getLogger(__name__)

BASE_URL = "https://www.fl.ru"
LIST_URL = f"{BASE_URL}/projects/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

PAGE_CAP = max(1, int(getattr(config, "MAX_PAGES", 5)))
TIMEOUT_TOTAL = 40
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2.0


def _text(el) -> str:
    return el.get_text(strip=True) if el else ""


def _price_from_text(text: str) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"(\d[\d\s]{0,12})", text.replace("\xa0", " "))
    if not m:
        return None
    try:
        return int(m.group(1).replace(" ", ""))
    except Exception:
        return None


def render(item: Dict[str, Any]) -> str:
    title = item.get("title") or "(без названия)"
    desc = (item.get("description") or "").strip()
    if len(desc) > 500:
        desc = desc[:497] + "..."
    price = item.get("price")
    price_str = f"{price} ₽" if price is not None else "—"
    url = item.get("url") or ""
    who = item.get("username") or "—"
    return (
        f"💼 <b>{title}</b>\n"
        f"Автор: {who}\n"
        f"Бюджет: {price_str}\n"
        f"{desc}\n"
        f"{url}"
    )


class FLParserService:
    def __init__(self, bot: Optional[Bot] = None) -> None:
        self.bot = bot
        self.db = Database()
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.lock = asyncio.Lock()

    async def start_parser(self, chat_id: Optional[int] = None) -> None:
        if self.is_running:
            log.info("FL parser already running")
            return
        self.is_running = True
        self._task = asyncio.create_task(self._run_loop(chat_id))
        log.info("FL parser started")

    async def stop_parser(self) -> None:
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        log.info("FL parser stopped")

    async def _run_loop(self, chat_id: Optional[int]) -> None:
        while self.is_running:
            try:
                channels = self.db.get_parser_channels("fl")
                if not channels:
                    log.info("Нет настроенных каналов для FL. Парсер не будет запущен.")
                    return

                await self._parse_and_store(channels)
                # ⚡️ тянем интервал из БД
                settings = self.db.get_parser_settings("fl")
                interval = settings["message_interval"] if settings else config.PARSING_INTERVAL
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Ошибка в FL-парсере: {e}", exc_info=True)
                await asyncio.sleep(60) # Fallback sleep

    async def _parse_and_store(self, channels: List[Dict]) -> int:
        async with self.lock:
            connector = aiohttp.TCPConnector(limit=8, ssl=False)
            timeout = aiohttp.ClientTimeout(total=TIMEOUT_TOTAL)
            async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers=HEADERS) as session:
                page = 1
                # ✅ берём именно FL-настройки
                settings = self.db.get_fl_settings()
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

                            # фильтрация по ключевым словам
                            if keywords and not any(kw in text_for_filter for kw in keywords):
                                continue

                            if minus_keywords and any(kw in text_for_filter for kw in minus_keywords):
                                continue

                            # фильтрация по цене
                            price = it.get("price")
                            if min_price is not None and (price is None or price < min_price):
                                continue
                            if max_price is not None and (price is not None and price > max_price):
                                continue

                            # сохраняем в БД
                            self.db.save_fl_project(it)
                            new_items.append(it)

                        # отправляем уведомление
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
                                await asyncio.sleep(1) # небольшой перерыв между сообщениями

                    page += 1
                    await asyncio.sleep(0.8)
                return 0

    async def _fetch_page(self, session: aiohttp.ClientSession, page: int) -> List[Dict[str, Any]]:
        url = LIST_URL if page == 1 else f"{LIST_URL}?page={page}"
        for attempt in range(RETRY_ATTEMPTS):
            try:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        continue
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    cards = self._extract_cards(soup)
                    return [self._normalize_card(c) for c in cards]
            except Exception as e:
                log.warning(f"[FL page {page}, attempt {attempt+1}] {e}")
                if attempt < RETRY_ATTEMPTS - 1:
                    await asyncio.sleep(RETRY_DELAY)
        return []

    def _extract_cards(self, soup: BeautifulSoup) -> List:
        cards = soup.select(".b-post")
        if cards:
            return cards
        return soup.select(".projects-list .project")

    def _normalize_card(self, node) -> Dict[str, Any]:
        title_el = node.select_one("h2 a, .b-post__title a, .title a")
        title = _text(title_el)
        url = title_el.get("href") if title_el else None
        if url and url.startswith("/"):
            url = BASE_URL + url
        user_el = node.select_one(".b-post__txt a[href*='/users/'], .author a, .username a")
        username = _text(user_el)
        desc_el = node.select_one(".b-post__txt, .text, .content, .b-post__description")
        description = _text(desc_el)
        price_el = node.select_one(".b-post__price, .price, .budget, .cost")
        price = _price_from_text(_text(price_el)) or _price_from_text(description)
        now_iso = datetime.utcnow().isoformat(timespec="seconds")
        proj_id = abs(hash((title, url))) % (10**9)
        return {
            "id": proj_id,
            "title": title,
            "description": description,
            "price": price,
            "url": url,
            "date_create": now_iso,
            "username": username or None,
            "category_id": None,
            "source": "fl",
        }
