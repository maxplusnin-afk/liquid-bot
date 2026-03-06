import os
from dotenv import load_dotenv
import logging

# Загружаем переменные окружения
load_dotenv()

# Получаем токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logging.error("BOT_TOKEN не найден в .env файле!")
    raise ValueError("BOT_TOKEN не найден! Проверьте файл .env")

# Получаем ID администраторов
admin_ids_str = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = []
if admin_ids_str:
    for id_str in admin_ids_str.split(','):
        try:
            admin_id = int(id_str.strip())
            if admin_id:
                ADMIN_IDS.append(admin_id)
        except ValueError:
            logging.warning(f"Некорректный ID администратора: {id_str}")

# Контакт владельца для связи
OWNER_CONTACT = "@maxon2205"

logging.info(f"Загружена конфигурация. ADMIN_IDS: {ADMIN_IDS}")