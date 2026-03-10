import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env")

# ID администратора (жестко прописан для надежности)
ADMIN_IDS = [888328825]

# Контакт продавца
SELLER_CONTACT = "@maxon2205"