import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.telegram import TelegramAPIServer
from aiogram.client.session.aiohttp import AiohttpSession
import aiohttp
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    try:
        from config import BOT_TOKEN, ADMIN_IDS
        from admin import router as admin_router
        from user import router as user_router
    except ImportError as e:
        logger.error(f"Ошибка импорта: {e}")
        return

    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не найден в .env файле")
        return

    logger.info(f"Бот запускается... Админы: {ADMIN_IDS}")

    # Создаем сессию с таймаутами
    session = AiohttpSession(
        timeout=30,
        api=TelegramAPIServer.from_base('https://api.telegram.org')
    )

    # Создаем бота и диспетчер
    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем роутеры
    dp.include_router(user_router)
    dp.include_router(admin_router)

    try:
        # Пробуем получить информацию о боте для проверки подключения
        bot_info = await bot.get_me()
        logger.info(f"Бот @{bot_info.username} успешно подключен!")

        # Запускаем поллинг
        await dp.start_polling(bot)
    except aiohttp.client_exceptions.ClientConnectorError as e:
        logger.error(f"Ошибка подключения к Telegram API: {e}")
        logger.error("Проверьте интернет соединение или настройки прокси")
    except AttributeError as e:
        logger.error(f"Ошибка атрибута: {e}")
        logger.error("Возможно проблема с версией aiogram или сетью")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        logger.error(f"Тип ошибки: {type(e).__name__}")
    finally:
        await bot.session.close()
        logger.info("Сессия бота закрыта")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}")
        logger.error(f"Тип ошибки: {type(e).__name__}")