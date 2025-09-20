import os
import asyncio
import aiohttp
from dataclasses import dataclass
import re


@dataclass
class Job:
    title: str
    description: str
    price: str
    group_id: str


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


async def fetch_vk_posts(group_id: str):
    token = os.getenv("ROOT__VK__TOKEN", "4374dd104374dd104374dd10fd4057c722443744374dd10245f47e167c547871f98924c")
    url = os.getenv("ROOT__VK__URL_GET", "https://api.vk.com/method/wall.get")

    full_url = f"{url}?owner_id={group_id}&count=5&access_token={token}&v=5.199"

    async with aiohttp.ClientSession() as session:
        async with session.get(full_url) as resp:
            data = await resp.json()

    jobs = []
    for item in data.get("response", {}).get("items", []):
        text = item.get("text", "").strip()
        title = text.split("\n")[0] if text else "Без заголовка"
        description = text.replace(title, "").strip() if text else "Нет описания"
        price = extract_price(text)

        jobs.append(Job(title=title, description=description, price=price, group_id=group_id))

    return jobs


async def main():
    # список групп (отрицательные id = паблики)
    group_ids = ["-1", "-123456", "-654321"]

    for group_id in group_ids:
        jobs = await fetch_vk_posts(group_id)

        print(f"\n=== Посты из группы {group_id} ===\n")
        for job in jobs:
            print("=" * 50)
            print(f"Заголовок: {job.title}")
            print(f"Описание: {job.description}")
            print(f"Цена: {job.price}")
            print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
