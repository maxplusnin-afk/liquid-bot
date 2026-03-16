import sqlite3
from typing import List, Dict, Optional


class Database:
    def __init__(self):
        self.conn = sqlite3.connect('shop.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Создание таблиц"""
        # Таблица брендов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                photo_id TEXT
            )
        ''')

        # Таблица товаров
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                flavor TEXT NOT NULL,
                strength TEXT NOT NULL,
                price INTEGER NOT NULL,
                FOREIGN KEY (brand_id) REFERENCES brands (id) ON DELETE CASCADE
            )
        ''')

        # Таблица заказов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price INTEGER NOT NULL,
                status TEXT DEFAULT 'новый',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()

    # ===== БРЕНДЫ =====

    def add_brand(self, name: str, photo_id: str) -> Optional[int]:
        try:
            self.cursor.execute(
                'INSERT INTO brands (name, photo_id) VALUES (?, ?)',
                (name, photo_id)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_all_brands(self) -> List[Dict]:
        self.cursor.execute('SELECT id, name, photo_id FROM brands ORDER BY name')
        return [
            {'id': row[0], 'name': row[1], 'photo_id': row[2]}
            for row in self.cursor.fetchall()
        ]

    def get_brand(self, brand_id: int) -> Optional[Dict]:
        self.cursor.execute('SELECT id, name, photo_id FROM brands WHERE id = ?', (brand_id,))
        row = self.cursor.fetchone()
        if row:
            return {'id': row[0], 'name': row[1], 'photo_id': row[2]}
        return None

    def delete_brand(self, brand_id: int):
        self.cursor.execute('DELETE FROM brands WHERE id = ?', (brand_id,))
        self.conn.commit()

    # ===== ТОВАРЫ =====

    def add_product(self, brand_id: int, name: str, flavor: str, strength: str, price: int) -> int:
        self.cursor.execute(
            'INSERT INTO products (brand_id, name, flavor, strength, price) VALUES (?, ?, ?, ?, ?)',
            (brand_id, name, flavor, strength, price)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_products_by_brand(self, brand_id: int) -> List[Dict]:
        self.cursor.execute(
            'SELECT id, name, flavor, strength, price FROM products WHERE brand_id = ? ORDER BY name',
            (brand_id,)
        )
        return [
            {'id': row[0], 'name': row[1], 'flavor': row[2], 'strength': row[3], 'price': row[4]}
            for row in self.cursor.fetchall()
        ]

    def get_product(self, product_id: int) -> Optional[Dict]:
        self.cursor.execute('''
            SELECT p.id, p.name, p.flavor, p.strength, p.price, b.name, b.photo_id
            FROM products p
            JOIN brands b ON p.brand_id = b.id
            WHERE p.id = ?
        ''', (product_id,))
        row = self.cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'flavor': row[2],
                'strength': row[3],
                'price': row[4],
                'brand_name': row[5],
                'brand_photo': row[6]
            }
        return None

    def update_product(self, product_id: int, name: str, flavor: str, strength: str, price: int):
        self.cursor.execute(
            'UPDATE products SET name = ?, flavor = ?, strength = ?, price = ? WHERE id = ?',
            (name, flavor, strength, price, product_id)
        )
        self.conn.commit()

    def delete_product(self, product_id: int):
        self.cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        self.conn.commit()

    # ===== ЗАКАЗЫ =====

    def add_order(self, user_id: int, username: str, product_id: int, product_name: str, price: int) -> int:
        self.cursor.execute(
            'INSERT INTO orders (user_id, username, product_id, product_name, price) VALUES (?, ?, ?, ?, ?)',
            (user_id, username, product_id, product_name, price)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_all_orders(self) -> List[Dict]:
        self.cursor.execute('SELECT * FROM orders ORDER BY created_at DESC')
        return [
            {
                'id': row[0],
                'user_id': row[1],
                'username': row[2],
                'product_id': row[3],
                'product_name': row[4],
                'price': row[5],
                'status': row[6],
                'created_at': row[7]
            }
            for row in self.cursor.fetchall()
        ]

    def update_order_status(self, order_id: int, status: str):
        self.cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
        self.conn.commit()