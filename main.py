import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

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
        logger.error("BOT_TOKEN не найден")
        return

    # Создаем бота и диспетчер
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем роутеры
    dp.include_router(user_router)
    dp.include_router(admin_router)

    logger.info(f"Бот запущен! Админы: {ADMIN_IDS}")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())