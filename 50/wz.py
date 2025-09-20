import asyncio
import aiohttp
from bs4 import BeautifulSoup

URL = "https://work-zilla.com/vacancies"

async def fetch_html(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()

async def main():
    html = await fetch_html(URL)
    soup = BeautifulSoup(html, "html.parser")

    vacancies = soup.select(".vacancies-list_item__pOEbS")

    for v in vacancies:
        blocks = v.select("div.card_content__t4Uk0 > div")

        title = blocks[0].get_text(strip=True) if len(blocks) > 0 else "—"
        price = blocks[1].get_text(strip=True) if len(blocks) > 1 else "—"
        desc  = blocks[2].get_text(strip=True) if len(blocks) > 2 else "—"

        print("Заголовок:", title)
        print("Цена:", price)
        print("Описание:", desc)
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
