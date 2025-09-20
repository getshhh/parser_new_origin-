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

BASE_URL = "https://work-zilla.com"
DELAY_SEC = 2.0
TIMEOUT_TOTAL = 30

def normalize_vacancy(raw: Dict[str, Any]) -> Dict[str, Any]:
    title = raw.get("title", "Без названия")
    description = raw.get("description", "Нет описания")
    price = raw.get("price", "Цена не указана")
    url = raw.get("url", "")
    
    # Генерируем ID из хэша
    project_id = hash(f"{title}{description}{price}") % 1000000000
    
    return {
        "id": project_id,
        "title": title,
        "description": description,
        "price": price,
        "url": url,
        "date_create": str(time.time())
    }

def render_vacancy(item: Dict[str, Any]) -> str:
    title = item.get("title") or "(без названия)"
    desc = (item.get("description") or "").strip()
    if len(desc) > 300:
        desc = desc[:297] + "..."
    price = item.get("price") or "Цена не указана"
    url = item.get("url") or ""
    
    lines = [
        f"💼 Work-Zilla Вакансия",
        f"ID: {item.get('id')}",
        f"Название: {title}",
        f"Цена: {price}",
        f"Описание: {desc}",
        f"Ссылка: {url}",
        "-"*50,
    ]
    return "\n".join(lines)

class WorkZillaParserService:
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
        log.info("Work-Zilla парсер запущен.")
        self.task = asyncio.create_task(self._parsing_loop())

    async def stop_parser(self) -> None:
        if not self.is_running:
            return
        self.is_running = False
        if self.task:
            self.task.cancel()
        log.info("Work-Zilla парсер остановлен.")

    async def _parsing_loop(self) -> None:
        while self.is_running:
            try:
                await self._parse_and_send()
                # ⚡️ тянем интервал из БД
                settings = self.db.get_parser_settings("workzilla")
                interval = settings["message_interval"] if settings else config.PARSING_INTERVAL
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                log.info("Цикл парсинга Work-Zilla отменен.")
                break
            except Exception as e:
                log.error(f"Ошибка в цикле парсинга Work-Zilla: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _parse_and_send(self) -> None:
        async with self.lock:
            settings = self.db.get_workzilla_settings()
            parser_cfg = self.db.get_parser_settings("workzilla")

            # если канал в настройках — туда, иначе тот чат, где включили
            target_channel = parser_cfg["channel_id"] if parser_cfg and parser_cfg.get("channel_id") else self.chat_id
            
            connector = aiohttp.TCPConnector(limit=8, ssl=False)
            timeout = aiohttp.ClientTimeout(total=TIMEOUT_TOTAL)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                new_vacancies_count = 0
                
                try:
                    url = f"{BASE_URL}/vacancies"
                    
                    async with session.get(url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }) as resp:
                        if resp.status != 200:
                            text = await resp.text()
                            log.error(f"HTTP {resp.status}: {text[:200]}")
                            return
                        
                        html = await resp.text()
                    
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # Селекторы для Work-Zilla
                    vacancies = soup.select(".vacancies-list_item__pOEbS")
                    
                    log.info(f"Найдено вакансий: {len(vacancies)}")
                    
                    new_vacancies = []
                    for v in vacancies:
                        try:
                            blocks = v.select("div.card_content__t4Uk0 > div")
                            
                            title = blocks[0].get_text(strip=True) if len(blocks) > 0 else "—"
                            price = blocks[1].get_text(strip=True) if len(blocks) > 1 else "—"
                            description = blocks[2].get_text(strip=True) if len(blocks) > 2 else "—"
                            
                            # Получаем ссылку
                            link_tag = v.find("a")
                            url = BASE_URL + link_tag["href"] if link_tag and "href" in link_tag.attrs else ""

                            vacancy_data = {
                                "title": title,
                                "description": description,
                                "price": price,
                                "url": url,
                                "date_create": str(time.time())
                            }
                            
                            norm_vacancy = normalize_vacancy(vacancy_data)
                            if self._filter_vacancy(norm_vacancy, settings):
                                self.db.save_workzilla_vacancy(norm_vacancy)
                                new_vacancies.append(norm_vacancy)
                                
                        except Exception as e:
                            log.error(f"Ошибка обработки вакансии: {e}")
                            continue
                    
                    if new_vacancies and target_channel:
                        for vacancy in new_vacancies:
                            message_text = render_vacancy(vacancy)
                            try:
                                await self.bot.send_message(chat_id=target_channel, text=message_text)
                            except TelegramRetryAfter as e:
                                log.warning(f"Flood control exceeded. Retrying in {e.retry_after} seconds.")
                                await asyncio.sleep(e.retry_after)
                                await self.bot.send_message(chat_id=target_channel, text=message_text)
                            except Exception as e:
                                log.error(f"Не удалось отправить сообщение Work-Zilla: {e}")
                            await asyncio.sleep(1)
                    
                    new_vacancies_count = len(new_vacancies)
                    log.info(f"Отфильтровано новых вакансий: {new_vacancies_count}")

                except Exception as e:
                    log.error(f"Ошибка парсинга Work-Zilla: {e}", exc_info=True)
            
            log.info(f"Work-Zilla парсинг завершен. Найдено новых вакансий: {new_vacancies_count}")

    def _filter_vacancy(self, vacancy: Dict[str, Any], settings: dict) -> bool:
        keywords = settings.get("keywords", [])
        min_price = settings.get("min_price")
        max_price = settings.get("max_price")

        # Извлекаем числовое значение цены для фильтрации
        price_text = vacancy.get("price", "")
        price_value = None
        
        # Пытаемся извлечь число из строки с ценой
        if price_text != "Цена не указана" and price_text != "—":
            price_match = re.search(r'\d+', price_text.replace(' ', ''))
            if price_match:
                price_value = int(price_match.group())

        # Фильтрация по ключевым словам
        title_and_desc = (vacancy.get("title", "") + " " + vacancy.get("description", "")).lower()
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
        settings = self.db.get_workzilla_settings()
        self.db.save_workzilla_settings(keywords, settings.get("min_price"), settings.get("max_price"))
        log.info(f"Установлены ключевые слова Work-Zilla: {keywords}")

    async def set_price_range(self, min_price: int, max_price: int) -> None:
        settings = self.db.get_workzilla_settings()
        self.db.save_workzilla_settings(settings.get("keywords", []), min_price, max_price)
        log.info(f"Установлен ценовой диапазон Work-Zilla: {min_price}-{max_price}")