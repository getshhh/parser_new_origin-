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
                channels = self.db.get_parser_channels("habr")
                if not channels:
                    log.info("Нет настроенных каналов для Habr. Парсер не будет запущен.")
                    break

                all_vacancies = await self.extract_habr_vacancies()

                unique_new_vacancies = []
                for vacancy in all_vacancies:
                    is_new = False
                    for channel_config in channels:
                        if self._filter_vacancy(vacancy, channel_config):
                            is_new = True
                            break
                    if is_new:
                        unique_new_vacancies.append(vacancy)
                
                for vacancy in unique_new_vacancies:
                    self.db.save_habr_vacancy(vacancy)

                total_new_vacancies = len(unique_new_vacancies)
                for channel_config in channels:
                    target_channel = channel_config["channel_id"]

                    new_vacancies_for_channel = []
                    for vacancy in unique_new_vacancies:
                        if self._filter_vacancy(vacancy, channel_config):
                            new_vacancies_for_channel.append(vacancy)

                    if self.bot and target_channel and new_vacancies_for_channel:
                        for vacancy in new_vacancies_for_channel:
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

                if total_new_vacancies > 0 and self.bot and chat_id: # уведомление в админский чат
                    try:
                        await self.bot.send_message(chat_id, f"✅ Найдено {total_new_vacancies} новых вакансий на Habr и отправлено по каналам.")
                    except TelegramRetryAfter as e:
                        log.warning(f"Flood control exceeded. Retrying in {e.retry_after} seconds.")
                        await asyncio.sleep(e.retry_after)
                        await self.bot.send_message(chat_id, f"✅ Найдено {total_new_vacancies} новых вакансий на Habr и отправлено по каналам.")
                
                settings = self.db.get_parser_settings("habr")
                interval = settings["message_interval"] if settings else 300
                await asyncio.sleep(interval)
                
            except Exception as e:
                log.error(f"Ошибка в парсере Habr: {e}", exc_info=True)
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
            min_salary = settings.get("min_salary")
            max_salary = settings.get("max_salary")
            cities = settings.get("cities")
            
            base_url = "https://career.habr.com/vacancies"
            params = {"type": "all"}
            
            async with self.session.get(base_url, params=params) as response:
                response.raise_for_status()
                text = await response.text()
                
            soup = BeautifulSoup(text, 'html.parser')
            vacancies = []
            
            vacancy_cards = soup.find_all('div', class_='vacancy-card')
            
            for card in vacancy_cards:
                try:
                    title_element = card.find('a', class_='vacancy-card__title-link')
                    title = title_element.get_text(strip=True) if title_element else "No title"
                    link = urljoin('https://career.habr.com', title_element.get('href')) if title_element else None
                    
                    company_element = card.find('div', class_='vacancy-card__company')
                    company = company_element.get_text(strip=True) if company_element else "Unknown company"
                    
                    salary_element = card.find('div', class_='basic-salary') or card.find('div', class_='vacancy-card__salary')
                    salary = salary_element.get_text(strip=True) if salary_element else "Не указана"
                    
                    city = "Не указан"
                    meta_element = card.find('div', class_='vacancy-card__meta')
                    if meta_element:
                        meta_items = meta_element.find_all(['a', 'div'])
                        for item in meta_items:
                            text = item.get_text(strip=True)
                            if (len(text) > 2 and not any(char.isdigit() for char in text) and
                                text != company and text not in ['Удалённо', 'Офис', 'Гибрид']):
                                city = text
                                break
                    
                    tags = []
                    skills_element = card.find('div', class_='vacancy-card__skills')
                    if skills_element:
                        tag_elements = skills_element.find_all('a', class_='link-comp')
                        for tag in tag_elements:
                            tag_text = tag.get_text(strip=True)
                            if tag_text != city:
                                tags.append(tag_text)
                    
                    if cities and city not in cities and city != "Не указан":
                        continue
                    
                    if salary != "Не указана" and min_salary is not None:
                        try:
                            salary_num = int(''.join(filter(str.isdigit, salary.split()[0])))
                            if salary_num < min_salary:
                                continue
                            if max_salary is not None and salary_num > max_salary:
                                continue
                        except:
                            pass
                    
                    vacancies.append({
                        'title': title, 'link': link, 'company': company,
                        'salary': salary, 'city': city, 'tags': tags,
                    })
                    
                except Exception as e:
                    log.warning(f"Ошибка при обработке карточки: {e}")
                    continue
            
            return vacancies
            
        except Exception as e:
            log.error(f"Ошибка при извлечении вакансий: {e}", exc_info=True)
            return []

    def _filter_vacancy(self, vacancy, channel_config):
        keywords = channel_config.get("keywords", [])
        minus_keywords = channel_config.get("minus_keywords", [])

        text_for_filter = (vacancy['title'] + ' ' + ' '.join(vacancy['tags'])).lower()

        if keywords and not any(kw.lower() in text_for_filter for kw in keywords):
            return False

        if minus_keywords and any(kw.lower() in text_for_filter for kw in minus_keywords):
            return False

        return True

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