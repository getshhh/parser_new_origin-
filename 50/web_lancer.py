import asyncio
import aiohttp
from bs4 import BeautifulSoup


BASE_URL = "https://www.weblancer.net"


async def fetch_html(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()


async def parse_jobs(url: str):
    html = await fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    projects = soup.find_all("article", class_="bg-white")
    print(f"\n=== Найдено проектов: {len(projects)} ===")

    for p in projects[:5]:  # ограничим 5 для примера
        title_tag = p.find("a", class_="link-style")
        desc_tag = p.find("p", class_="text-gray-600")
        price_tag = p.find("span", class_="text-green-600")

        title = title_tag.get_text(strip=True) if title_tag else "нет"
        link = BASE_URL + title_tag["href"] if title_tag else "нет"
        desc = desc_tag.get_text(strip=True) if desc_tag else "нет"
        price = price_tag.get_text(strip=True) if price_tag else "нет"

        print("\n--- Заказ ---")
        print("Заголовок:", title)
        print("Описание:", desc)
        print("Цена:", price)
        print("Ссылка:", link)


async def main():
    url = "https://www.weblancer.net/jobs/"
    while True:
        try:
            await parse_jobs(url)
        except Exception as e:
            print(f"Ошибка при обработке {url}: {e}")

        await asyncio.sleep(30)  # каждые 30 сек повторяем


if __name__ == "__main__":
    asyncio.run(main())
