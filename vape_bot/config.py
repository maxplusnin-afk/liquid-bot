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

# ВАШ ID АДМИНА - пропишите здесь жестко
YOUR_ADMIN_ID = 888328825  # Ваш ID

# Получаем ID администраторов из .env, но добавляем ваш ID принудительно
admin_ids_str = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [YOUR_ADMIN_ID]  # Сначала добавляем ваш ID

# Добавляем остальных админов из .env если они есть
if admin_ids_str:
    for id_str in admin_ids_str.split(','):
        try:
            admin_id = int(id_str.strip())
            if admin_id and admin_id not in ADMIN_IDS:  # Избегаем дубликатов
                ADMIN_IDS.append(admin_id)
        except ValueError:
            logging.warning(f"Некорректный ID администратора: {id_str}")

# Контакт владельца для связи
OWNER_CONTACT = "@maxon2205"

logging.info(f"Загружена конфигурация. ADMIN_IDS: {ADMIN_IDS}")