#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import logging
from typing import Any, Dict, List
from aiogram import Bot

from config_reader import config
from database.database import Database
from aiogram.exceptions import TelegramRetryAfter

log = logging.getLogger(__name__)

API_URL = "https://kwork.ru/projects"
PAGE_CAP = 200
DELAY_SEC = 0.6
TIMEOUT_TOTAL = 30


def normalize_item(raw: Dict[str, Any]) -> Dict[str, Any]:
    title = raw.get("name") or raw.get("title") or ""
    description = raw.get("description") or raw.get("desc") or ""
    price = (
        raw.get("priceLimit")
        or raw.get("price_limit")
        or raw.get("price")
        or raw.get("possiblePriceLimit")
        or raw.get("possible_price")
    )
    pid = raw.get("id")
    link = f"https://kwork.ru/projects/{pid}/view" if pid else ""
    want_dates = raw.get("wantDates") or {}
    date_create = want_dates.get("dateCreate") or raw.get("dateCreate")
    date_active = want_dates.get("dateActive") or raw.get("dateActive")
    date_expire = want_dates.get("dateExpire") or raw.get("dateExpire")
    user = raw.get("user") or {}
    username = user.get("username")
    return {
        "id": pid,
        "title": title,
        "description": description,
        "price": price,
        "url": link,
        "date_create": date_create,
        "date_active": date_active,
        "date_expire": date_expire,
        "username": username,
        "category_id": raw.get("category_id"),
    }


def render(item: Dict[str, Any]) -> str:
    title = item.get("title") or "(без названия)"
    desc = (item.get("description") or "").strip()
    if len(desc) > 300:
        desc = desc[:297] + "..."
    price = item.get("price")
    price_str = f"{price}₽" if price is not None else "—"
    url = item.get("url") or ""
    meta = []
    if item.get("username"):
        meta.append(f"Автор: {item['username']}")
    if item.get("category_id"):
        meta.append(f"Категория: {item['category_id']}")
    meta_line = (" | ".join(meta)) if meta else ""
    lines = [
        f"ID: {item.get('id')}",
        f"Название: {title}",
        f"Цена: {price_str}",
        f"{'(' + meta_line + ')' if meta_line else ''}",
        f"Описание: {desc}",
        f"Ссылка: {url}",
        "-" * 80,
    ]
    return "\n".join(l for l in lines if l is not None)


class KworkParserService:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = Database()
        self.is_running = False
        self.task = None
        self.chat_id = None
        self.lock = asyncio.Lock()

    async def start_parser(self, chat_id: int) -> None:
        if self.is_running:
            return
        self.is_running = True
        self.chat_id = chat_id
        log.info("Парсер Kwork запущен.")
        self.task = asyncio.create_task(self._parsing_loop())

    async def stop_parser(self) -> None:
        if not self.is_running:
            return
        self.is_running = False
        if self.task:
            self.task.cancel()
        log.info("Парсер Kwork остановлен.")

    async def _parsing_loop(self) -> None:
        while self.is_running:
            try:
                await self._parse_and_send()
                # ⚡️ тянем интервал из БД
                settings = self.db.get_parser_settings("kwork")
                interval = settings["message_interval"] if settings else config.PARSING_INTERVAL
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                log.info("Цикл парсинга отменен.")
                break
            except Exception as e:
                log.error(f"Ошибка в цикле парсинга: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _parse_and_send(self) -> None:
        async with self.lock:
            channel_configs = self.db.get_parser_channels("kwork")
            if not channel_configs:
                log.warning("Каналы для парсера Kwork не настроены. Пропускаем парсинг.")
                return

            connector = aiohttp.TCPConnector(limit=8, ssl=False)
            timeout = aiohttp.ClientTimeout(total=TIMEOUT_TOTAL)
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                page = 1
                new_items_count = 0
                while page <= PAGE_CAP:
                    try:
                        url = f"{API_URL}?a=1&page={page}"
                        headers = {
                            "Accept": "application/json, */*;q=0.1",
                            "User-Agent": "Mozilla/5.0 (compatible; KworkPrintAll/1.0)",
                        }
                        async with session.post(url, headers=headers) as resp:
                            if resp.status == 403:
                                raise RuntimeError("403 Forbidden – blocked or missing headers")
                            if resp.status != 200:
                                text = await resp.text()
                                raise RuntimeError(f"HTTP {resp.status}: {text[:200]}")
                            data = await resp.json(content_type=None)
                            if not isinstance(data, dict) or not data.get("success"):
                                raise RuntimeError("Unexpected JSON or success=false")
                            items = data.get("data", {}).get("pagination", {}).get("data")
                            if not isinstance(items, list):
                                items = []

                        for item in items:
                            if isinstance(item, dict):
                                norm_item = normalize_item(item)
                                self.db.save_project(norm_item)
                                for config in channel_configs:
                                    if self._filter_item(norm_item, config):
                                        message_text = render(norm_item)
                                        try:
                                            await self.bot.send_message(chat_id=config['channel_id'], text=message_text)
                                            new_items_count += 1
                                        except TelegramRetryAfter as e:
                                            log.warning(f"Flood control exceeded. Retrying in {e.retry_after} seconds.")
                                            await asyncio.sleep(e.retry_after)
                                            await self.bot.send_message(chat_id=config['channel_id'], text=message_text)
                                        except Exception as e:
                                            log.error(f"Не удалось отправить сообщение в канал {config['channel_id']}: {e}")
                                        await asyncio.sleep(1)

                        if not items:
                            break
                        page += 1
                        await asyncio.sleep(DELAY_SEC)

                    except Exception as e:
                        log.error(f"Ошибка парсинга: {e}")
                        break
            log.info(f"Завершено. Отправлено новых проектов: {new_items_count}")

    def _filter_item(self, item: Dict[str, Any], settings: dict) -> bool:
        keywords = settings.get("keywords", "").split(',') if settings.get("keywords") else []
        minus_words = settings.get("minus_words", "").split(',') if settings.get("minus_words") else []
        min_price = settings.get("min_price")
        max_price = settings.get("max_price")

        title_and_desc = (item.get("title", "") + " " + item.get("description", "")).lower()

        if keywords and keywords[0] != '-':
            if not any(kw.strip().lower() in title_and_desc for kw in keywords):
                return False

        if minus_words and minus_words[0] != '-':
            if any(mw.strip().lower() in title_and_desc for mw in minus_words):
                return False

        price = item.get("price")
        if min_price is not None and price is not None and price < min_price:
            return False
        if max_price is not None and price is not None and price > max_price:
            return False

        return True

    async def set_keywords(self, keywords: List[str]) -> None:
        settings = self.db.get_settings("kwork")
        self.db.save_settings(keywords, settings["min_price"], settings["max_price"], "kwork")
        log.info(f"Установлены ключевые слова: {keywords}")

    async def set_price_range(self, min_price: int, max_price: int) -> None:
        settings = self.db.get_settings("kwork")
        self.db.save_settings(settings["keywords"], min_price, max_price, "kwork")
        log.info(f"Установлен ценовой диапазон: {min_price}-{max_price}")
