import asyncio
import random
import time
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re


class UpworkHeaderParcer:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        # Категории для замены wordpress
        self.categories = [
            'python', 'video-editing', 'smm', 'marketing', 
            'web-design', 'javascript', 'php', 'graphic-design',
            'seo', 'content-writing', 'data-entry', 'mobile-development',
            'react', 'vue', 'angular', 'nodejs', 'laravel', 'django',
            'flutter', 'react-native', 'ui-ux', 'illustration',
            'wordpress', 'shopify', 'wix', 'squarespace'
        ]
        
        self.base_url = "https://www.upwork.com/freelance-jobs/{}/"

    async def create_stealth_page(self, browser):
        """Создаем stealth страницу"""
        user_agent = random.choice(self.user_agents)
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=user_agent,
            java_script_enabled=True,
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
            }
        )
        
        page = await context.new_page()
        
        # Убираем webdriver detection
        await page.evaluate_on_new_document("""
            () => {
                delete navigator.__proto__.webdriver;
                Object.defineProperty(navigator, 'webdriver', { get: () => false });
            }
        """)
        
        return page, context

    def extract_all_headers(self, soup):
        """Извлекаем ВСЕ заголовки h1-h6 со страницы"""
        headers_data = []
        
        # Ищем все заголовки от h1 до h6
        for level in range(1, 7):
            tag_name = f'h{level}'
            headers = soup.find_all(tag_name)
            
            for header in headers:
                try:
                    text = header.get_text(strip=True)
                    if text and len(text) > 3:  # Отсекаем короткие заголовки
                        # Получаем родительский контекст
                        parent = header.find_parent()
                        parent_class = parent.get('class', []) if parent else []
                        parent_id = parent.get('id', '') if parent else ''
                        
                        # Получаем ссылку если есть
                        link = header.find_parent('a')
                        href = link.get('href', '') if link else ''
                        if href and not href.startswith('http'):
                            href = "https://www.upwork.com" + href
                        
                        headers_data.append({
                            'text': text,
                            'level': level,
                            'tag': tag_name,
                            'parent_class': ' '.join(parent_class) if parent_class else '',
                            'parent_id': parent_id,
                            'link': href,
                            'context': str(header.parent)[:200] + '...' if header.parent else ''
                        })
                except Exception as e:
                    continue
        
        return headers_data

    def extract_jobs_from_headers(self, soup, headers_data, category):
        """Извлекаем вакансии на основе заголовков"""
        jobs = []
        
        for header in headers_data:
            try:
                # Проверяем, похож ли заголовок на вакансию
                text = header['text'].lower()
                
                # Ключевые слова, указывающие на вакансию
                job_keywords = [
                    'developer', 'designer', 'writer', 'manager', 'specialist',
                    'expert', 'engineer', 'assistant', 'consultant', 'analyst',
                    'freelancer', 'remote', 'wanted', 'needed', 'required',
                    'hire', 'looking for', 'job', 'position', 'vacancy'
                ]
                
                is_job = any(keyword in text for keyword in job_keywords)
                
                if is_job and len(text) > 10:
                    # Пытаемся найти описание рядом с заголовком
                    description = ""
                    price = "Цена не указана"
                    
                    # Ищем следующий параграф после заголовка
                    next_sibling = header.find_next_sibling()
                    if next_sibling and next_sibling.name == 'p':
                        description = next_sibling.get_text(strip=True)
                    else:
                        # Ищем любой текст в родительском элементе
                        parent = header.parent
                        if parent:
                            all_text = parent.get_text(' ', strip=True)
                            header_pos = all_text.find(header['text'])
                            if header_pos != -1:
                                description = all_text[header_pos + len(header['text']):].strip()[:200]
                    
                    # Ищем цену вблизи заголовка
                    price_selectors = ['strong', '.price', '.amount', '[class*="budget"]']
                    for selector in price_selectors:
                        price_elem = header.find_next(selector)
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            if price_text and any(char in price_text for char in ['$', '€', '£', '₽']):
                                price = price_text
                                break
                    
                    jobs.append({
                        'title': header['text'],
                        'description': description,
                        'price': price,
                        'link': header['link'],
                        'header_level': header['level'],
                        'header_tag': header['tag'],
                        'category': category
                    })
                    
            except Exception as e:
                continue
        
        return jobs

    async def parse_category(self, page, category):
        """Парсим конкретную категорию"""
        url = self.base_url.format(category)
        print(f"🎯 Парсим категорию: {category}")
        print(f"🌐 URL: {url}")
        
        try:
            await page.goto(url, timeout=30000, wait_until='networkidle')
            await asyncio.sleep(3)
            
            # Получаем контент страницы
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Извлекаем ВСЕ заголовки
            all_headers = self.extract_all_headers(soup)
            print(f"📊 Найдено заголовков: {len(all_headers)}")
            
            # Фильтруем и находим вакансии
            jobs = self.extract_jobs_from_headers(soup, all_headers, category)
            
            # Выводим статистику по заголовкам
            header_stats = {}
            for header in all_headers:
                level = header['level']
                header_stats[level] = header_stats.get(level, 0) + 1
            
            print(f"📈 Статистика заголовков: {header_stats}")
            
            return jobs
            
        except Exception as e:
            print(f"❌ Ошибка при парсинге категории {category}: {e}")
            return []

    async def fetch_upwork(self):
        """Основной метод парсинга"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )
            
            try:
                page, context = await self.create_stealth_page(browser)
                
                all_jobs = []
                
                # Парсим несколько случайных категорий
                categories_to_parse = random.sample(self.categories, 2)  # 2 случайные категории
                
                for category in categories_to_parse:
                    jobs = await self.parse_category(page, category)
                    
                    if jobs:
                        print(f"✅ Найдено вакансий в '{category}': {len(jobs)}")
                        all_jobs.extend(jobs)
                    
                    # Пауза между категориями
                    await asyncio.sleep(random.uniform(2, 4))
                
                await context.close()
                return all_jobs
                
            except Exception as e:
                print(f"🔥 Критическая ошибка: {e}")
                return []
            finally:
                await browser.close()

    def display_results(self, jobs):
        """Красиво выводим результаты"""
        if not jobs:
            print("❌ Вакансии не найдены")
            return
        
        print(f"\n🎯 ВСЕГО НАЙДЕНО ВАКАНСИЙ: {len(jobs)}")
        print("=" * 120)
        
        # Группируем по категориям
        categories = {}
        for job in jobs:
            if job['category'] not in categories:
                categories[job['category']] = []
            categories[job['category']].append(job)
        
        # Выводим по категориям
        for category, category_jobs in categories.items():
            print(f"\n📁 КАТЕГОРИЯ: {category.upper()} ({len(category_jobs)} вакансий)")
            print("-" * 120)
            
            for i, job in enumerate(category_jobs, 1):
                print(f"{i:2d}. [{job['header_tag'].upper()}] {job['title']}")
                print(f"    💰 Цена: {job['price']}")
                print(f"    📝 Описание: {job['description'][:150]}..." if job['description'] else "    📝 Описание: Нет описания")
                if job['link']:
                    print(f"    🔗 Ссылка: {job['link']}")
                print(f"    🏷 Уровень заголовка: h{job['header_level']}")
                print()

    async def main_loop(self):
        """Бесконечный цикл парсинга"""
        print("🚀 Запускаем парсер заголовков Upwork!")
        print("📊 Категории для парсинга:", ', '.join(self.categories))
        print("=" * 120)
        
        session_count = 0
        
        while True:
            session_count += 1
            print(f"\n🔄 СЕССИЯ #{session_count}")
            print("=" * 120)
            
            start_time = time.time()
            
            try:
                jobs = await self.fetch_upwork()
                elapsed_time = time.time() - start_time
                
                self.display_results(jobs)
                print(f"⏱ Время выполнения: {elapsed_time:.2f} сек")
                
            except Exception as e:
                print(f"💥 Ошибка в основной петле: {e}")
            
            # Случайная задержка между сессиями
            delay = random.randint(180, 480)  # 3-8 минут
            print(f"\n💤 Следующая сессия через {delay} секунд ({delay//60} мин)...")
            print("=" * 120)
            
            await asyncio.sleep(delay)


async def main():
    parcer = UpworkHeaderParcer()
    await parcer.main_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Парсер остановлен пользователем")
    except Exception as e:
        print(f"💀 Критический сбой: {e}")