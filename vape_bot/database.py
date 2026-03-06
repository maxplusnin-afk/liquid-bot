import sqlite3
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_name: str = "catalog.db"):
        self.db_name = db_name
        self.init_db()

    def _get_connection(self):
        """Получение соединения с БД"""
        return sqlite3.connect(self.db_name)

    def init_db(self):
        """Инициализация таблиц"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Таблица товаров (жидкости)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS liquids (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        flavor TEXT NOT NULL,
                        strength TEXT NOT NULL,
                        volume TEXT NOT NULL,
                        image_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.commit()
                logger.info("База данных инициализирована")
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")

    # ===== Функции для жидкостей =====

    def add_liquid(self, name: str, flavor: str, strength: str, volume: str, image_id: str = "") -> Optional[int]:
        """Добавление жидкости"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO liquids (name, flavor, strength, volume, image_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, flavor, strength, volume, image_id))
                conn.commit()
                liquid_id = cursor.lastrowid
                logger.info(f"Жидкость добавлена с ID: {liquid_id}")
                return liquid_id
        except Exception as e:
            logger.error(f"Ошибка добавления жидкости: {e}")
            return None

    def get_all_liquids(self) -> List[Dict]:
        """Получение всех жидкостей"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, name, flavor, strength, volume, image_id, created_at 
                    FROM liquids 
                    ORDER BY created_at DESC
                ''')
                items = cursor.fetchall()
                return [
                    {
                        'id': item[0],
                        'name': item[1],
                        'flavor': item[2],
                        'strength': item[3],
                        'volume': item[4],
                        'image_id': item[5] if item[5] else "",
                        'created_at': item[6]
                    }
                    for item in items
                ]
        except Exception as e:
            logger.error(f"Ошибка получения жидкостей: {e}")
            return []

    def get_liquid_by_id(self, liquid_id: int) -> Optional[Dict]:
        """Получение жидкости по ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, name, flavor, strength, volume, image_id, created_at 
                    FROM liquids 
                    WHERE id = ?
                ''', (liquid_id,))
                item = cursor.fetchone()
                if item:
                    return {
                        'id': item[0],
                        'name': item[1],
                        'flavor': item[2],
                        'strength': item[3],
                        'volume': item[4],
                        'image_id': item[5] if item[5] else "",
                        'created_at': item[6]
                    }
                return None
        except Exception as e:
            logger.error(f"Ошибка получения жидкости по ID: {e}")
            return None

    def delete_liquid(self, liquid_id: int) -> bool:
        """Удаление жидкости"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM liquids WHERE id = ?', (liquid_id,))
                conn.commit()
                logger.info(f"Жидкость {liquid_id} удалена")
                return True
        except Exception as e:
            logger.error(f"Ошибка удаления жидкости: {e}")
            return False