import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

# Цвета для терминала
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

URL = "https://www.guru.com/d/jobs/"

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}🎯 {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.END}")

def print_success(text):
    print(f"\n{Colors.BOLD}{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"\n{Colors.BOLD}{Colors.RED}❌ {text}{Colors.END}")

def print_job_header(number):
    print(f"\n{Colors.BOLD}{Colors.PURPLE}🔹 ВАКАНСИЯ #{number}{Colors.END}")
    print(f"{Colors.YELLOW}{'─' * 70}{Colors.END}")

def parse_guru_jobs_beautiful():
    print_header("ПАРСИНГ ВАКАНСИЙ GURU.COM")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем все карточки с вакансиями
        job_cards = soup.find_all('div', class_=lambda x: x and 'job' in str(x).lower())
        
        print(f"{Colors.BOLD}📊 Найдено вакансий: {len(job_cards)}{Colors.END}")
        print(f"{Colors.CYAN}{'=' * 80}{Colors.END}")
        
        for i, card in enumerate(job_cards[:15], 1):
            print_job_header(i)
            
            # Заголовок
            title_elem = card.find(['h2', 'h3', 'h4', 'a'])
            title = title_elem.get_text(strip=True) if title_elem else f"{Colors.RED}Не указано{Colors.END}"
            
            # Ссылка на вакансию
            link = ""
            link_elem = card.find('a', href=True)
            if link_elem and '/jobs/' in link_elem['href']:
                link = urljoin(URL, link_elem['href'])
            
            # Описание
            description = ""
            desc_elem = card.find('p') or card.find('div', class_=lambda x: x and ('desc' in str(x).lower() or 'description' in str(x).lower()))
            if desc_elem:
                description = desc_elem.get_text(strip=True)
                if len(description) > 120:
                    description = description[:120] + "..."
            
            # Цена
            price = f"{Colors.RED}Не указана{Colors.END}"
            price_text = card.get_text()
            price_patterns = [
                r'\$[\d,]+(?:\.[\d]{2})?(?:\s*-\s*\$[\d,]+(?:\.[\d]{2})?)?',
                r'[\d,]+(?:\.\d{2})?\s*USD',
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, price_text, re.IGNORECASE)
                if match:
                    price = f"{Colors.GREEN}{match.group(0)}{Colors.END}"
                    break
            
            # Дополнительная информация
            details = []
            for elem in card.find_all(['span', 'div']):
                text = elem.get_text(strip=True)
                if text and 15 < len(text) < 60 and text not in details:
                    details.append(text)
            
            # Красивый вывод
            print(f"   {Colors.BOLD}🏷️  Заголовок:{Colors.END} {title}")
            
            if link:
                print(f"   {Colors.BOLD}🔗 Ссылка:{Colors.END} {Colors.BLUE}{link}{Colors.END}")
            else:
                print(f"   {Colors.BOLD}🔗 Ссылка:{Colors.END} {Colors.RED}Не найдена{Colors.END}")
            
            print(f"   {Colors.BOLD}💰 Цена:{Colors.END} {price}")
            
            if description:
                print(f"   {Colors.BOLD}📝 Описание:{Colors.END} {Colors.WHITE}{description}{Colors.END}")
            else:
                print(f"   {Colors.BOLD}📝 Описание:{Colors.END} {Colors.RED}Не найдено{Colors.END}")
            
            if details:
                print(f"   {Colors.BOLD}📌 Детали:{Colors.END} {Colors.YELLOW}{', '.join(details[:2])}{Colors.END}")
        
        print_success("Парсинг завершен успешно!")
        
    except Exception as e:
        print_error(f"Ошибка: {e}")

def parse_guru_detailed():
    print_header("ДЕТАЛЬНЫЙ ПАРСИНГ ВАКАНСИЙ")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем все карточки вакансий
        job_cards = soup.find_all('div', class_=lambda x: x and 'job' in str(x).lower())
        
        for i, card in enumerate(job_cards[:12], 1):
            print(f"\n{Colors.BOLD}{Colors.CYAN}🌟 ВАКАНСИЯ #{i}{Colors.END}")
            print(f"{Colors.YELLOW}{'╌' * 65}{Colors.END}")
            
            # Заголовок и ссылка
            title_elem = card.find(['h2', 'h3', 'h4', 'a'])
            title = title_elem.get_text(strip=True) if title_elem else f"{Colors.RED}Не указано{Colors.END}"
            
            link = ""
            link_elem = card.find('a', href=True)
            if link_elem and '/jobs/' in link_elem['href']:
                link = urljoin(URL, link_elem['href'])
            
            # Описание
            description = ""
            # Ищем в различных элементах
            possible_desc_elems = [
                card.find('p'),
                card.find('div', class_=lambda x: x and any(word in str(x).lower() for word in ['desc', 'description', 'text', 'content'])),
                card.find('span', class_=lambda x: x and any(word in str(x).lower() for word in ['desc', 'description']))
            ]
            
            for elem in possible_desc_elems:
                if elem and elem.get_text(strip=True):
                    description = elem.get_text(strip=True)
                    break
            
            # Если не нашли, ищем текст с определенной длиной
            if not description:
                all_texts = [text.strip() for text in card.find_all(string=True) if text.strip()]
                for text in all_texts:
                    if 80 < len(text) < 250:
                        description = text
                        break
            
            if description and len(description) > 100:
                description = description[:100] + "..."
            
            # Цена
            price = f"{Colors.RED}Не указана{Colors.END}"
            price_text = card.get_text()
            price_match = re.search(r'\$[\d,]+(?:\.[\d]{2})?(?:\s*-\s*\$[\d,]+(?:\.[\d]{2})?)?', price_text)
            if price_match:
                price = f"{Colors.GREEN}{price_match.group(0)}{Colors.END}"
            
            # Категория и время
            category = ""
            time_info = ""
            meta_elems = card.find_all(['span', 'div'], class_=lambda x: x and any(word in str(x).lower() for word in ['time', 'date', 'category', 'type']))
            for elem in meta_elems:
                text = elem.get_text(strip=True)
                if text:
                    if any(word in text.lower() for word in ['hrs', 'days', 'ago', 'posted']):
                        time_info = text
                    elif any(word in text.lower() for word in ['development', 'marketing', 'design', 'writing']):
                        category = text
            
            # Вывод
            print(f"   {Colors.BOLD}📛 Должность:{Colors.END} {Colors.WHITE}{title}{Colors.END}")
            
            if link:
                print(f"   {Colors.BOLD}🌐 Ссылка:{Colors.END} {Colors.BLUE}{link}{Colors.END}")
            
            print(f"   {Colors.BOLD}💸 Ставка:{Colors.END} {price}")
            
            if category:
                print(f"   {Colors.BOLD}🏷️  Категория:{Colors.END} {Colors.PURPLE}{category}{Colors.END}")
            
            if time_info:
                print(f"   {Colors.BOLD}⏰ Время:{Colors.END} {Colors.YELLOW}{time_info}{Colors.END}")
            
            if description:
                print(f"   {Colors.BOLD}📄 Описание:{Colors.END}")
                print(f"      {Colors.WHITE}{description}{Colors.END}")
        
        print_success("Детальный парсинг завершен!")
        
    except Exception as e:
        print_error(f"Ошибка: {e}")

def parse_guru_with_preview():
    """Функция с предпросмотром полных описаний"""
    print_header("ПАРСИНГ С ПРЕДПРОСМОТРОМ ОПИСАНИЙ")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем конкретные элементы вакансий
        job_elements = soup.find_all(['article', 'div'], class_=lambda x: x and any(word in str(x).lower() for word in ['job', 'listing', 'card']))
        
        print(f"{Colors.BOLD}📊 Найдено элементов: {len(job_elements)}{Colors.END}")
        
        for i, job in enumerate(job_elements[:10], 1):
            print(f"\n{Colors.BOLD}{Colors.GREEN}✨ ВАКАНСИЯ #{i}{Colors.END}")
            print(f"{Colors.CYAN}{'━' * 60}{Colors.END}")
            
            # Заголовок
            title = "Не указано"
            title_elem = job.find(['h2', 'h3', 'h4', 'a'])
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # Ссылка
            link = ""
            link_elem = job.find('a', href=True)
            if link_elem and '/jobs/' in link_elem['href']:
                link = urljoin(URL, link_elem['href'])
            
            # Полное описание
            full_text = job.get_text()
            sentences = [s.strip() for s in re.split(r'[.!?]', full_text) if s.strip() and len(s.strip()) > 20]
            description = '. '.join(sentences[:3]) + '.' if sentences else "Описание не найдено"
            
            if len(description) > 120:
                description = description[:120] + "..."
            
            # Цена
            price = "Не указана"
            price_match = re.search(r'\$[\d,]+(?:\.[\d]{2})?(?:\s*-\s*\$[\d,]+(?:\.[\d]{2})?)?', full_text)
            if price_match:
                price = price_match.group(0)
            
            # Вывод
            print(f"   {Colors.BOLD}🎯 {title}{Colors.END}")
            print(f"   {Colors.BOLD}🔗 {link if link else 'Ссылка не найдена'}{Colors.END}")
            print(f"   {Colors.BOLD}💰 {price}{Colors.END}")
            print(f"   {Colors.BOLD}📖 {description}{Colors.END}")
        
        print_success("Парсинг с предпросмотром завершен!")
        
    except Exception as e:
        print_error(f"Ошибка: {e}")

# Запуск
if __name__ == "__main__":
    parse_guru_jobs_beautiful()
    print(f"\n{Colors.CYAN}{'=' * 80}{Colors.END}")
    parse_guru_detailed()
    print(f"\n{Colors.CYAN}{'=' * 80}{Colors.END}")
    parse_guru_with_preview()
    print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 ВСЕ ОПЕРАЦИИ ЗАВЕРШЕНЫ!{Colors.END}")