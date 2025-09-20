#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minimal FL.ru scraper: no params, no bot.
- Iterates pages of https://www.fl.ru/projects/page-N
- Prints each project in a human-readable block
- Stops when an empty page is encountered or after a safe page cap
"""

import asyncio
import aiohttp
import sys
import time
from typing import Dict, List
from bs4 import BeautifulSoup

BASE_URL = "https://www.fl.ru/projects"
PAGE_START = 1
PAGE_CAP = 200          # safety cap to avoid infinite loops
DELAY_SEC = 1.0         # increased delay to avoid rate limiting
TIMEOUT_TOTAL = 30
RETRY_ATTEMPTS = 3      # number of retries for failed requests
RETRY_DELAY = 2.0       # delay between retries

def normalize_item(soup: BeautifulSoup, item) -> Dict[str, str]:
    # Extract title
    title_elem = item.find(class_=["text-h5", "b-post__title", "b-post__grid_title", "p-0", "b-post__pin"]) or \
                 item.find(class_=["text-dark", "text-decoration-none", "link-hover-danger", "cursor-pointer"])
    title = title_elem.get_text(strip=True) if title_elem else "(без названия)"

    # Extract description
    desc_elem = item.find(class_=["b-post__body", "b-post__grid_descript", "b-post__body_overflow_hidden", "b-layuot_width_full"]) or \
                item.find(class_=["b-post__txt", "text-5"])
    description = desc_elem.get_text(strip=True) if desc_elem else ""

    # Truncate description if too long
    if len(description) > 300:
        description = description[:297] + "..."

    # Extract price
    price_elem = item.find(class_=["d-flex", "align-items-center", "b-post__price", "p-0", "ml-lg-16", "b-post__grid_price", "b-post__price_fontsize_15", "b-post__price_bold"]) or \
                 item.find(class_=["text-4", "text-dark", "text-decoration-none"])
    price = price_elem.get_text(strip=True) if price_elem else "Цена не указана"

    # Extract URL
    link_elem = item.find("a", class_=["text-dark", "text-decoration-none", "link-hover-danger", "cursor-pointer"])
    url = f"https://www.fl.ru{link_elem['href']}" if link_elem and link_elem.get('href') else ""

    # Extract project ID from URL if possible
    pid = url.split('/')[-2] if url and '/' in url else ""

    return {
        "id": pid,
        "title": title,
        "description": description,
        "price": price,
        "url": url,
    }

def render(item: Dict[str, str]) -> str:
    title = item.get("title") or "(без названия)"
    desc = item.get("description") or ""
    price = item.get("price") or "Цена не указана"
    url = item.get("url") or ""
    lines = [
        f"ID: {item.get('id')}",
        f"Название: {title}",
        f"Цена: {price}",
        f"Описание: {desc}",
        f"Ссылка: {url}",
        "-"*80,
    ]
    return "\n".join(l for l in lines if l)

async def fetch_page(session: aiohttp.ClientSession, page: int) -> List[Dict[str, str]]:
    url = f"{BASE_URL}/page-{page}"
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.fl.ru/",
        "Connection": "keep-alive",
    }
    for attempt in range(RETRY_ATTEMPTS):
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 403:
                    raise RuntimeError("403 Forbidden – blocked or missing headers")
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"HTTP {resp.status}: {text[:200]}")
                text = await resp.text()
                soup = BeautifulSoup(text, 'html.parser')
                items = soup.find_all(class_="b-post")  # Assuming b-post is the container for each project
                if not items:
                    return []
                return [normalize_item(soup, item) for item in items]
        except Exception as e:
            sys.stderr.write(f"[page {page}, attempt {attempt + 1}] error: {e}\n")
            if attempt < RETRY_ATTEMPTS - 1:
                await asyncio.sleep(RETRY_DELAY)
            continue
    return []  # Return empty list if all retries fail

async def main() -> None:
    connector = aiohttp.TCPConnector(limit=8, ssl=True)  # Enable SSL
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_TOTAL)
    total = 0
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        page = PAGE_START
        while page <= PAGE_CAP:
            items = await fetch_page(session, page)
            if not items:
                sys.stderr.write(f"[page {page}] No items found, stopping\n")
                break
            for item in items:
                print(render(item))
                total += 1
            page += 1
            await asyncio.sleep(DELAY_SEC)
    print(f"Всего проектов выведено: {total}", file=sys.stderr)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.stderr.write("Stopped by user\n")