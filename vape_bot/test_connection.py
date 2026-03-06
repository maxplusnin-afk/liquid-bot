# Создайте отдельный файл test_connection.py для проверки
import asyncio
import aiohttp
import socket


async def test_connection():
    print("Проверка подключения к Telegram...")

    # Проверка DNS
    try:
        ip = socket.gethostbyname('api.telegram.org')
        print(f"✅ DNS работает. IP адрес: {ip}")
    except Exception as e:
        print(f"❌ Ошибка DNS: {e}")

    # Проверка HTTP подключения
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.telegram.org') as response:
                print(f"✅ HTTP подключение работает. Статус: {response.status}")
    except Exception as e:
        print(f"❌ Ошибка HTTP подключения: {e}")


if __name__ == "__main__":
    asyncio.run(test_connection())