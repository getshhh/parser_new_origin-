# services/habr.py

import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin
import asyncio
import aiohttp
from datetime import datetime
from database.database import Database
from aiogram.exceptions import TelegramRetryAfter

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class HabrParserService:
    def __init__(self, bot=None):
        self.bot = bot
        self.is_running = False
        self.db = Database()
        self.session = None
        
    async def start_parser(self, chat_id=None):
        if self.is_running:
            return
            
        self.is_running = True
        if self.bot and chat_id:
            await self.bot.send_message(chat_id, "✅ Парсер Habr Career включен.")
        
        self.session = aiohttp.ClientSession()
        
        while self.is_running:
            try:
                vacancies = await self.extract_habr_vacancies()
                
                parser_cfg = self.db.get_parser_settings("habr")
                target_channel = parser_cfg["channel_id"] if parser_cfg and parser_cfg.get("channel_id") else chat_id

                new_vacancies = 0
                if self.bot and target_channel and vacancies:
                    for vacancy in vacancies:
                        self.db.save_habr_vacancy(vacancy)
                        new_vacancies += 1
                        message = self.render_vacancy(vacancy)
                        try:
                            await self.bot.send_message(target_channel, message)
                        except TelegramRetryAfter as e:
                            log.warning(f"Flood control exceeded. Retrying in {e.retry_after} seconds.")
                            await asyncio.sleep(e.retry_after)
                            await self.bot.send_message(target_channel, message)
                        except Exception as e:
                            log.error(f"Failed to send message: {e}")
                        await asyncio.sleep(1)
                
                if new_vacancies > 0 and self.bot and target_channel:
                    try:
                        await self.bot.send_message(target_channel, f"✅ Найдено {new_vacancies} новых вакансий на Habr")
                    except TelegramRetryAfter as e:
                        log.warning(f"Flood control exceeded. Retrying in {e.retry_after} seconds.")
                        await asyncio.sleep(e.retry_after)
                        await self.bot.send_message(target_channel, f"✅ Найдено {new_vacancies} новых вакансий на Habr")
                
                # ⚡️ тянем интервал из БД
                settings = self.db.get_parser_settings("habr")
                interval = settings["message_interval"] if settings else 300 # 5 минут по умолчанию
                await asyncio.sleep(interval)
                
            except Exception as e:
                log.error(f"Ошибка в парсере Habr: {e}")
                if self.bot and chat_id:
                    await self.bot.send_message(chat_id, f"❌ Ошибка в парсере Habr: {e}")
                await asyncio.sleep(60)
    
    async def stop_parser(self):
        self.is_running = False
        if self.session:
            await self.session.close()
    
    async def extract_habr_vacancies(self):
        try:
            settings = self.db.get_habr_settings()
            keywords = settings["keywords"]
            min_salary = settings["min_salary"]
            max_salary = settings["max_salary"]
            cities = settings["cities"]
            
            # Формируем URL с учетом фильтров
            base_url = "https://career.habr.com/vacancies"
            params = {
                "q": " ".join(keywords) if keywords else None,
                "type": "all"
            }
            
            # Убираем None значения
            params = {k: v for k, v in params.items() if v is not None}
            
            async with self.session.get(base_url, params=params) as response:
                response.raise_for_status()
                text = await response.text()
                
            soup = BeautifulSoup(text, 'html.parser')
            vacancies = []
            
            vacancy_cards = soup.find_all('div', class_='vacancy-card')
            
            for card in vacancy_cards:
                try:
                    # Заголовок и ссылка
                    title_element = card.find('a', class_='vacancy-card__title-link')
                    title = title_element.get_text(strip=True) if title_element else "No title"
                    link = urljoin('https://career.habr.com', title_element.get('href')) if title_element else None
                    
                    # Компания
                    company_element = card.find('div', class_='vacancy-card__company')
                    company = company_element.get_text(strip=True) if company_element else "Unknown company"
                    
                    # Зарплата
                    salary_element = card.find('div', class_='basic-salary')
                    if not salary_element:
                        salary_element = card.find('div', class_='vacancy-card__salary')
                    salary = salary_element.get_text(strip=True) if salary_element else "Не указана"
                    
                    # Город
                    city = "Не указан"
                    meta_element = card.find('div', class_='vacancy-card__meta')
                    if meta_element:
                        meta_items = meta_element.find_all(['a', 'div'])
                        for item in meta_items:
                            text = item.get_text(strip=True)
                            if (len(text) > 2 and 
                                not any(char.isdigit() for char in text) and
                                text != company and
                                text not in ['Удалённо', 'Офис', 'Гибрид']):
                                city = text
                                break
                    
                    # Теги/навыки
                    tags = []
                    skills_element = card.find('div', class_='vacancy-card__skills')
                    if skills_element:
                        tag_elements = skills_element.find_all('a', class_='link-comp')
                        for tag in tag_elements:
                            tag_text = tag.get_text(strip=True)
                            if tag_text != city:
                                tags.append(tag_text)
                    
                    # Фильтрация по городу
                    if cities and city not in cities and city != "Не указан":
                        continue
                    
                    # Фильтрация по зарплате (если указана)
                    if salary != "Не указана" and min_salary is not None:
                        try:
                            # Пытаемся извлечь числовое значение зарплаты
                            salary_num = int(''.join(filter(str.isdigit, salary.split()[0])))
                            if salary_num < min_salary:
                                continue
                            if max_salary is not None and salary_num > max_salary:
                                continue
                        except:
                            pass
                    
                    vacancies.append({
                        'title': title,
                        'link': link,
                        'company': company,
                        'salary': salary,
                        'city': city,
                        'tags': tags,
                    })
                    
                except Exception as e:
                    log.warning(f"Ошибка при обработке карточки: {e}")
                    continue
            
            return vacancies
            
        except Exception as e:
            log.error(f"Ошибка при извлечении вакансий: {e}")
            return []
    
    def render_vacancy(self, vacancy):
        tags_text = ', '.join(vacancy['tags']) if vacancy['tags'] else 'Нет тегов'
        return f"""
🎯 {vacancy['title']}
🏢 Компания: {vacancy['company']}
💰 Зарплата: {vacancy['salary']}
📍 Город: {vacancy['city']}
🔖 Теги: {tags_text}
🔗 Ссылка: {vacancy['link']}
        """.strip()
    
    async def set_habr_keywords(self, keywords):
        settings = self.db.get_habr_settings()
        self.db.save_habr_settings(
            keywords=keywords,
            min_salary=settings["min_salary"],
            max_salary=settings["max_salary"],
            cities=settings["cities"],
            employment_types=settings["employment_types"]
        )
    
    async def set_habr_salary_range(self, min_salary, max_salary):
        settings = self.db.get_habr_settings()
        self.db.save_habr_settings(
            keywords=settings["keywords"],
            min_salary=min_salary,
            max_salary=max_salary,
            cities=settings["cities"],
            employment_types=settings["employment_types"]
        )
    
    async def set_habr_cities(self, cities):
        settings = self.db.get_habr_settings()
        self.db.save_habr_settings(
            keywords=settings["keywords"],
            min_salary=settings["min_salary"],
            max_salary=settings["max_salary"],
            cities=cities,
            employment_types=settings["employment_types"]
        )