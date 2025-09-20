import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
from typing import Dict, Any, List
from aiogram import Bot
import re
import time

from database.database import Database
from config_reader import config
from aiogram.exceptions import TelegramRetryAfter

log = logging.getLogger(__name__)

BASE_URL = "https://www.weblancer.net"
DELAY_SEC = 2.0
TIMEOUT_TOTAL = 30

def normalize_project(raw: Dict[str, Any]) -> Dict[str, Any]:
    title = raw.get("title", "Без названия")
    description = raw.get("description", "Нет описания")
    price = raw.get("price", "Цена не указана")
    url = raw.get("url", "")
    username = raw.get("username", "Неизвестен")
    
    # Генерируем ID из хэша
    project_id = hash(f"{title}{description}{price}") % 1000000000
    
    return {
        "id": project_id,
        "title": title,
        "description": description,
        "price": price,
        "url": url,
        "date_create": str(time.time()),
        "username": username
    }

def render_project(item: Dict[str, Any]) -> str:
    title = item.get("title") or "(без названия)"
    desc = (item.get("description") or "").strip()
    if len(desc) > 300:
        desc = desc[:297] + "..."
    price = item.get("price") or "Цена не указана"
    url = item.get("url") or ""
    
    lines = [
        f"🏗️ WebLancer Проект",
        f"ID: {item.get('id')}",
        f"Название: {title}",
        f"Цена: {price}",
        f"Автор: {item.get('username', 'Неизвестен')}",
        f"Описание: {desc}",
        f"Ссылка: {url}",
        "-"*50,
    ]
    return "\n".join(lines)

class WebLancerParserService:
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
        log.info("WebLancer парсер запущен.")
        self.task = asyncio.create_task(self._parsing_loop())

    async def stop_parser(self) -> None:
        if not self.is_running:
            return
        self.is_running = False
        if self.task:
            self.task.cancel()
        log.info("WebLancer парсер остановлен.")

    async def _parsing_loop(self) -> None:
        while self.is_running:
            try:
                await self._parse_and_send()
                # ⚡️ тянем интервал из БД
                settings = self.db.get_parser_settings("weblancer")
                interval = settings["message_interval"] if settings else config.PARSING_INTERVAL
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                log.info("Цикл парсинга WebLancer отменен.")
                break
            except Exception as e:
                log.error(f"Ошибка в цикле парсинга WebLancer: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _parse_and_send(self) -> None:
        async with self.lock:
            settings = self.db.get_weblancer_settings()
            parser_cfg = self.db.get_parser_settings("weblancer")

            # если канал в настройках — туда, иначе тот чат, где включили
            target_channel = parser_cfg["channel_id"] if parser_cfg and parser_cfg.get("channel_id") else self.chat_id
            
            connector = aiohttp.TCPConnector(limit=8, ssl=False)
            timeout = aiohttp.ClientTimeout(total=TIMEOUT_TOTAL)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                new_projects_count = 0
                
                try:
                    url = f"{BASE_URL}/jobs/"
                    
                    async with session.get(url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }) as resp:
                        if resp.status != 200:
                            text = await resp.text()
                            log.error(f"HTTP {resp.status}: {text[:200]}")
                            return
                        
                        html = await resp.text()
                    
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # Селекторы для WebLancer
                    projects = soup.find_all("article", class_="bg-white")

                    
                    log.info(f"Найдено проектов: {len(projects)}")
                    
                    new_projects = []
                    for p in projects:
                        try:
                            # Ищем элементы с проектами
                            title_tag = p.find("a", class_="link-style")

                            if not title_tag:
                                continue
                                
                            price_tag = p.find("span", class_="text-green-600")

                            desc_tag = p.find("p", class_="text-gray-600")

                            user_tag = p.find("a", href=lambda x: x and "/users/" in x)


                            title = title_tag.get_text(strip=True) if title_tag else "Без названия"
                            link = BASE_URL + title_tag["href"] if title_tag and "href" in title_tag.attrs else ""
                            description = desc_tag.get_text(strip=True) if desc_tag else "Нет описания"
                            price = price_tag.get_text(strip=True) if price_tag else "Цена не указана"
                            username = user_tag.get_text(strip=True) if user_tag else "Неизвестен"

                            project_data = {
                                "title": title,
                                "description": description,
                                "price": price,
                                "url": link,
                                "username": username,
                                "date_create": str(time.time())
                            }
                            
                            norm_project = normalize_project(project_data)
                            if self._filter_project(norm_project, settings):
                                self.db.save_weblancer_project(norm_project)
                                new_projects.append(norm_project)
                                
                        except Exception as e:
                            log.error(f"Ошибка обработки проекта: {e}")
                            continue
                    
                    if new_projects and target_channel:
                        for project in new_projects:
                            message_text = render_project(project)
                            try:
                                await self.bot.send_message(chat_id=target_channel, text=message_text)
                            except TelegramRetryAfter as e:
                                log.warning(f"Flood control exceeded. Retrying in {e.retry_after} seconds.")
                                await asyncio.sleep(e.retry_after)
                                await self.bot.send_message(chat_id=target_channel, text=message_text)
                            except Exception as e:
                                log.error(f"Не удалось отправить сообщение WebLancer: {e}")
                            await asyncio.sleep(1)
                    
                    new_projects_count = len(new_projects)
                    log.info(f"Отфильтровано новых проектов: {new_projects_count}")

                except Exception as e:
                    log.error(f"Ошибка парсинга WebLancer: {e}", exc_info=True)
            
            log.info(f"WebLancer парсинг завершен. Найдено новых проектов: {new_projects_count}")

    def _filter_project(self, project: Dict[str, Any], settings: dict) -> bool:
        keywords = settings.get("keywords", [])
        min_price = settings.get("min_price")
        max_price = settings.get("max_price")

        # Извлекаем числовое значение цены для фильтрации
        price_text = project.get("price", "")
        price_value = None
        
        # Пытаемся извлечь число из строки с ценой
        if price_text != "Цена не указана" and price_text != "нет":
            price_match = re.search(r'\d+', price_text.replace(' ', ''))
            if price_match:
                price_value = int(price_match.group())

        # Фильтрация по ключевым словам
        title_and_desc = (project.get("title", "") + " " + project.get("description", "")).lower()
        if keywords:
            if not any(kw.lower() in title_and_desc for kw in keywords):
                return False
        
        # Фильтрация по цене
        if min_price is not None and price_value is not None and price_value < min_price:
            return False
        if max_price is not None and price_value is not None and price_value > max_price:
            return False
        
        return True

    async def set_keywords(self, keywords: List[str]) -> None:
        settings = self.db.get_weblancer_settings()
        self.db.save_weblancer_settings(keywords, settings.get("min_price"), settings.get("max_price"))
        log.info(f"Установлены ключевые слова WebLancer: {keywords}")

    async def set_price_range(self, min_price: int, max_price: int) -> None:
        settings = self.db.get_weblancer_settings()
        self.db.save_weblancer_settings(settings.get("keywords", []), min_price, max_price)
        log.info(f"Установлен ценовой диапазон WebLancer: {min_price}-{max_price}")