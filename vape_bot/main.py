import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
import aiohttp

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

try:
    from config import BOT_TOKEN, ADMIN_IDS
    from admin_handlers import router as admin_router
    from user_handlers import router as user_router
except ImportError as import_error:
    logger.error(f"Ошибка импорта: {import_error}")
    raise


async def main():
    """Главная функция запуска бота"""
    logger.info("Запуск бота...")

    # Проверяем наличие токена
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не найден!")
        return

    # Создаем сессию с таймаутами
    session = AiohttpSession(timeout=30)

    # Инициализируем бота и диспетчер
    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем роутеры
    dp.include_router(user_router)
    dp.include_router(admin_router)

    logger.info(f"Бот успешно запущен! Админы: {ADMIN_IDS}")

    try:
        # Запускаем поллинг
        await dp.start_polling(bot)
    except aiohttp.client_exceptions.ClientConnectorError as connection_error:
        logger.error(f"Ошибка подключения к Telegram: {connection_error}")
        logger.info("Проверьте интернет соединение или используйте VPN")
    except Exception as unexpected_error:
        logger.error(f"Ошибка при запуске бота: {unexpected_error}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as critical_error:
        logger.error(f"Критическая ошибка: {critical_error}")