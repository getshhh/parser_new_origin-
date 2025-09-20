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
                await self._parse_and_send()
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

    async def _parse_and_send(self) -> None:
        async with self.lock:
            channel_configs = self.db.get_parser_channels("vk")
            if not channel_configs:
                log.warning("Каналы для парсера VK не настроены. Пропускаем парсинг.")
                return

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
                        
                        for item in items:
                            if isinstance(item, dict):
                                norm_post = normalize_post(item, group_id)
                                self.db.save_vk_post(norm_post)
                                for config in channel_configs:
                                    if self._filter_post(norm_post, config):
                                        message_text = render_post(norm_post)
                                        try:
                                            await self.bot.send_message(chat_id=config['channel_id'], text=message_text)
                                            new_posts_count += 1
                                        except TelegramRetryAfter as e:
                                            log.warning(f"Flood control exceeded. Retrying in {e.retry_after} seconds.")
                                            await asyncio.sleep(e.retry_after)
                                            await self.bot.send_message(chat_id=config['channel_id'], text=message_text)
                                        except Exception as e:
                                            log.error(f"Не удалось отправить сообщение VK в канал {config['channel_id']}: {e}")
                                        await asyncio.sleep(1)
                        
                        await asyncio.sleep(DELAY_SEC)

                    except Exception as e:
                        log.error(f"Ошибка парсинга VK группы {group_id}: {e}")
                        continue
            
            log.info(f"VK парсинг завершен. Отправлено новых постов: {new_posts_count}")

    def _filter_post(self, post: Dict[str, Any], settings: dict) -> bool:
        keywords = settings.get("keywords", "").split(',') if settings.get("keywords") else []
        minus_words = settings.get("minus_words", "").split(',') if settings.get("minus_words") else []
        min_price = settings.get("min_price")
        max_price = settings.get("max_price")

        title_and_desc = (post.get("title", "") + " " + post.get("description", "")).lower()

        if keywords and keywords[0] != '-':
            if not any(kw.strip().lower() in title_and_desc for kw in keywords):
                return False

        if minus_words and minus_words[0] != '-':
            if any(mw.strip().lower() in title_and_desc for mw in minus_words):
                return False

        price_text = post.get("price", "")
        price_value = None
        if price_text != "Цена не указана":
            price_match = re.search(r'\d+', price_text)
            if price_match:
                price_value = int(price_match.group())

        if min_price is not None and price_value is not None and price_value < min_price:
            return False
        if max_price is not None and price_value is not None and price_value > max_price:
            return False
        
        return True

    async def set_keywords(self, keywords: List[str]) -> None:
        settings = self.db.get_vk_settings()
        self.db.save_vk_settings(keywords, settings.get("min_price"), settings.get("max_price"))
        log.info(f"Установлены ключевые слова VK: {keywords}")

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