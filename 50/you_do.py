import asyncio
import aiohttp


async def fetch_you_do():
    json_data = {
        "q": "",
        "status": "opened",
        "radius": None,
        "lat": 55.755864,   # Москва
        "lng": 37.617698,
        "page": 1,
        "priceMin": "",
        "sortType": 1,
        "categories": ["all"],
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://youdo.com/api/tasks/tasks", json=json_data) as resp:
            return await resp.json()


async def main():
    while True:
        try:
            result = await fetch_you_do()
            items = result.get("ResultObject", {}).get("Items", [])

            if not items:
                print("❌ Нет заданий")
            else:
                for item in items[:5]:  # ограничим первыми 5
                    task_id = item.get("Id")
                    title = item.get("Name")
                    address = item.get("Address")
                    budget = item.get("BudgetDescription")
                    date_time_string = item.get("DateTimeString")
                    url = f"https://youdo.com{item.get('Url')}"

                    print(f"""
🆔 {task_id}
📌 {title}
📍 {address}
💰 {budget}
🕒 {date_time_string}
🔗 {url}
                    """)
                print("=" * 50)

        except Exception as e:
            print(f"Ошибка: {e}")

        await asyncio.sleep(30)  # повторять каждые 30 сек


if __name__ == "__main__":
    asyncio.run(main())
