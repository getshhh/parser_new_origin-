import os
import asyncio
import aiohttp
import logging
import re
from typing import Dict, Any, List
from aiogram import Bot
from datetime import datetime

from database.database import Database
from config_reader import config
from aiogram.exceptions import TelegramRetryAfter

log = logging.getLogger(__name__)

API_URL = "https://api.vk.com/method/wall.get"
DELAY_SEC = 1.0
TIMEOUT_TOTAL = 30

def extract_price(text: str) -> str:
    """
    Ищем цену в тексте: 1000₽, 2000 руб, $50 и т.п.
    """
    patterns = [
        r"\d+\s?₽",
        r"\d+\s?руб",
        r"\$\s?\d+",
        r"\d+\s?USD",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group()
    return "Цена не указана"

def normalize_post(raw: Dict[str, Any], group_id: str) -> Dict[str, Any]:
    text = raw.get("text", "").strip()
    title = text.split("\n")[0] if text else "Без заголовка"
    description = text.replace(title, "").strip() if text else "Нет описания"
    price = extract_price(text)
    
    # Преобразуем дату из Unix timestamp
    date = raw.get("date", 0)
    date_create = datetime.fromtimestamp(date).isoformat() if date else datetime.now().isoformat()
    
    return {
        "id": raw.get("id"),
        "group_id": group_id,
        "title": title,
        "description": description,
        "price": price,
        "date_create": date_create
    }

def render_post(item: Dict[str, Any]) -> str:
    title = item.get("title") or "(без названия)"
    desc = (item.get("description") or "").strip()
    if len(desc) > 300:
        desc = desc[:297] + "..."
    price = item.get("price") or "Цена не указана"
    
    lines = [
        f"Группа: {item.get('group_id')}",
        f"ID поста: {item.get('id')}",
        f"Заголовок: {title}",
        f"Цена: {price}",
        f"Описание: {desc}",
        f"Дата: {item.get('date_create', '')}",
        "-"*50,
    ]
    return "\n".join(lines)

class VKParserService:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = Database()
        self.is_running = False
        self.task = None
        self.chat_id = None
        self.lock = asyncio.Lock()
        self.token = os.getenv("ROOT__VK__TOKEN", "4374dd104374dd104374dd10fd4057c722443744374dd10245f47e167c547871f98924c")

    async def start_parser(self, chat_id: int) -> None:
        if self.is_running:
            return
        self.is_running = True
        self.chat_id = chat_id
        log.info("VK парсер запущен.")
        self.task = asyncio.create_task(self._parsing_loop())

    async def stop_parser(self) -> None:
        if not self.is_running:
            return
        self.is_running = False
        if self.task:
            self.task.cancel()
        log.info("VK парсер остановлен.")

    async def _parsing_loop(self) -> None:
        while self.is_running:
            try:
                channels = self.db.get_parser_channels("vk")
                if not channels:
                    log.info("Нет настроенных каналов для VK. Парсер не будет запущен.")
                    return

                await self._parse_and_send(channels)
                # ⚡️ тянем интервал из БД
                settings = self.db.get_parser_settings("vk")
                interval = settings["message_interval"] if settings else config.PARSING_INTERVAL
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                log.info("Цикл парсинга VK отменен.")
                break
            except Exception as e:
                log.error(f"Ошибка в цикле парсинга VK: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _parse_and_send(self, channels: List[Dict]) -> None:
        async with self.lock:
            settings = self.db.get_vk_settings()
            group_ids = settings.get("group_ids", [])
            
            if not group_ids:
                log.warning("Не заданы ID групп для парсинга VK")
                return

            connector = aiohttp.TCPConnector(limit=8, ssl=False)
            timeout = aiohttp.ClientTimeout(total=TIMEOUT_TOTAL)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                new_posts_count = 0
                
                for group_id in group_ids:
                    try:
                        url = f"{API_URL}?owner_id={group_id}&count=10&access_token={self.token}&v=5.199"
                        
                        async with session.get(url) as resp:
                            if resp.status != 200:
                                text = await resp.text()
                                raise RuntimeError(f"HTTP {resp.status}: {text[:200]}")
                            
                            data = await resp.json()
                            items = data.get("response", {}).get("items", [])
                        
                        all_posts = [normalize_post(item, group_id) for item in items if isinstance(item, dict)]
                        
                        unique_new_posts = []
                        for post in all_posts:
                            is_new = False
                            for channel_config in channels:
                                if self._filter_post(post, settings, channel_config):
                                    is_new = True
                                    break
                            if is_new:
                                unique_new_posts.append(post)

                        for post in unique_new_posts:
                            self.db.save_vk_post(post)

                        for channel_config in channels:
                            new_posts_for_channel = []
                            for post in unique_new_posts:
                                if self._filter_post(post, settings, channel_config):
                                    new_posts_for_channel.append(post)

                            if new_posts_for_channel and channel_config["channel_id"]:
                                for post in new_posts_for_channel:
                                    message_text = render_post(post)
                                    try:
                                        await self.bot.send_message(chat_id=channel_config["channel_id"], text=message_text)
                                    except TelegramRetryAfter as e:
                                        log.warning(f"Flood control exceeded. Retrying in {e.retry_after} seconds.")
                                        await asyncio.sleep(e.retry_after)
                                        await self.bot.send_message(chat_id=channel_config["channel_id"], text=message_text)
                                    except Exception as e:
                                        log.error(f"Не удалось отправить сообщение VK: {e}")
                                    await asyncio.sleep(1)
                        
                        new_posts_count += len(unique_new_posts)
                        await asyncio.sleep(DELAY_SEC)

                    except Exception as e:
                        log.error(f"Ошибка парсинга VK группы {group_id}: {e}")
                        continue
            
            log.info(f"VK парсинг завершен. Найдено новых постов: {new_posts_count}")

    def _filter_post(self, post: Dict[str, Any], settings: dict, channel_config: dict) -> bool:
        keywords = channel_config.get("keywords", [])
        minus_keywords = channel_config.get("minus_keywords", [])
        min_price = settings.get("min_price")
        max_price = settings.get("max_price")

        price_text = post.get("price", "")
        price_value = None
        
        if price_text != "Цена не указана":
            price_match = re.search(r'\d+', price_text)
            if price_match:
                price_value = int(price_match.group())

        title_and_desc = (post.get("title", "") + " " + post.get("description", "")).lower()
        if keywords and not any(kw.lower() in title_and_desc for kw in keywords):
            return False

        if minus_keywords and any(kw.lower() in title_and_desc for kw in minus_keywords):
            return False
        
        if min_price is not None and price_value is not None and price_value < min_price:
            return False
        if max_price is not None and price_value is not None and price_value > max_price:
            return False
        
        return True

    async def set_price_range(self, min_price: int, max_price: int) -> None:
        settings = self.db.get_vk_settings()
        self.db.save_vk_settings(settings.get("keywords", []), min_price, max_price)
        log.info(f"Установлен ценовой диапазон VK: {min_price}-{max_price}")

    def set_group_ids(self, group_ids: List[str]) -> None:
        settings = self.db.get_vk_settings()
        # Сохраняем group_ids в настройках
        settings["group_ids"] = group_ids
        # Здесь нужно добавить метод в Database для сохранения полных настроек VK
        self._save_vk_full_settings(settings)
        log.info(f"Установлены ID групп VK: {group_ids}")

    def _save_vk_full_settings(self, settings: dict) -> None:
        self.db.save_vk_full_settings(settings)