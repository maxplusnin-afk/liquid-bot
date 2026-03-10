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
                        price INTEGER NOT NULL DEFAULT 0,
                        image_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Таблица заявок на покупку
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS purchase_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        username TEXT,
                        liquid_id INTEGER NOT NULL,
                        liquid_name TEXT NOT NULL,
                        price INTEGER NOT NULL,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (liquid_id) REFERENCES liquids (id) ON DELETE CASCADE
                    )
                ''')

                conn.commit()
                logger.info("База данных инициализирована")
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")

    # ===== Функции для жидкостей =====

    def add_liquid(self, name: str, flavor: str, strength: str, volume: str, price: int, image_id: str = "") -> \
    Optional[int]:
        """Добавление жидкости с ценой"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO liquids (name, flavor, strength, volume, price, image_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, flavor, strength, volume, price, image_id))
                conn.commit()
                liquid_id = cursor.lastrowid
                logger.info(f"Жидкость добавлена с ID: {liquid_id}, цена: {price}₽, image_id: {image_id}")
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
                    SELECT id, name, flavor, strength, volume, price, image_id, created_at 
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
                        'price': item[5],
                        'image_id': item[6] if item[6] else "",
                        'created_at': item[7]
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
                    SELECT id, name, flavor, strength, volume, price, image_id, created_at 
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
                        'price': item[5],
                        'image_id': item[6] if item[6] else "",
                        'created_at': item[7]
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

    # ===== Функции для заявок на покупку =====

    def create_purchase_request(self, user_id: int, user_name: str, username: str, liquid_id: int, liquid_name: str,
                                price: int) -> Optional[int]:
        """Создание заявки на покупку"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO purchase_requests (user_id, user_name, username, liquid_id, liquid_name, price, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, user_name, username, liquid_id, liquid_name, price, 'pending'))
                conn.commit()
                request_id = cursor.lastrowid
                logger.info(f"Заявка на покупку #{request_id} создана для жидкости {liquid_name}")
                return request_id
        except Exception as e:
            logger.error(f"Ошибка создания заявки на покупку: {e}")
            return None

    def get_purchase_requests(self, status: str = None) -> List[Dict]:
        """Получение заявок на покупку (для админа)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if status:
                    cursor.execute('''
                        SELECT id, user_id, user_name, username, liquid_id, liquid_name, price, status, created_at 
                        FROM purchase_requests 
                        WHERE status = ?
                        ORDER BY created_at DESC
                    ''', (status,))
                else:
                    cursor.execute('''
                        SELECT id, user_id, user_name, username, liquid_id, liquid_name, price, status, created_at 
                        FROM purchase_requests 
                        ORDER BY created_at DESC
                    ''')
                items = cursor.fetchall()
                return [
                    {
                        'id': item[0],
                        'user_id': item[1],
                        'user_name': item[2],
                        'username': item[3],
                        'liquid_id': item[4],
                        'liquid_name': item[5],
                        'price': item[6],
                        'status': item[7],
                        'created_at': item[8]
                    }
                    for item in items
                ]
        except Exception as e:
            logger.error(f"Ошибка получения заявок на покупку: {e}")
            return []

    def update_request_status(self, request_id: int, status: str) -> bool:
        """Обновление статуса заявки"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE purchase_requests SET status = ? WHERE id = ?', (status, request_id))
                conn.commit()
                logger.info(f"Статус заявки {request_id} обновлен на {status}")
                return True
        except Exception as e:
            logger.error(f"Ошибка обновления статуса заявки: {e}")
            return False