import sqlite3
from typing import List, Dict, Optional


class Database:
    def __init__(self):
        self.conn = sqlite3.connect('catalog.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Таблица категорий
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')

        # Таблица товаров
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                flavor TEXT NOT NULL,
                strength TEXT NOT NULL,
                photo_id TEXT,
                FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
            )
        ''')

        # Добавляем стандартные категории, если их нет
        categories = ['Снюс', 'Вейпы', 'Жидкости', 'Никотиновые пластины']
        for cat in categories:
            try:
                self.cursor.execute('INSERT INTO categories (name) VALUES (?)', (cat,))
            except:
                pass

        self.conn.commit()

    # ===== КАТЕГОРИИ =====

    def get_all_categories(self) -> List[Dict]:
        self.cursor.execute('SELECT id, name FROM categories ORDER BY name')
        return [
            {'id': row[0], 'name': row[1]}
            for row in self.cursor.fetchall()
        ]

    def add_category(self, name: str) -> Optional[int]:
        try:
            self.cursor.execute('INSERT INTO categories (name) VALUES (?)', (name,))
            self.conn.commit()
            return self.cursor.lastrowid
        except:
            return None

    def delete_category(self, category_id: int):
        self.cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        self.conn.commit()

    # ===== ТОВАРЫ =====

    def add_product(self, category_id: int, name: str, flavor: str, strength: str, photo_id: str = "") -> int:
        self.cursor.execute(
            'INSERT INTO products (category_id, name, flavor, strength, photo_id) VALUES (?, ?, ?, ?, ?)',
            (category_id, name, flavor, strength, photo_id)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_products_by_category(self, category_id: int) -> List[Dict]:
        self.cursor.execute(
            'SELECT id, name, flavor, strength, photo_id FROM products WHERE category_id = ? ORDER BY name',
            (category_id,)
        )
        return [
            {
                'id': row[0],
                'name': row[1],
                'flavor': row[2],
                'strength': row[3],
                'photo_id': row[4]
            }
            for row in self.cursor.fetchall()
        ]

    def get_product(self, product_id: int) -> Optional[Dict]:
        self.cursor.execute('''
            SELECT p.id, p.name, p.flavor, p.strength, p.photo_id, c.name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.id = ?
        ''', (product_id,))
        row = self.cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'flavor': row[2],
                'strength': row[3],
                'photo_id': row[4],
                'category_name': row[5]
            }
        return None

    def update_product(self, product_id: int, name: str, flavor: str, strength: str, photo_id: str = ""):
        if photo_id:
            self.cursor.execute(
                'UPDATE products SET name = ?, flavor = ?, strength = ?, photo_id = ? WHERE id = ?',
                (name, flavor, strength, photo_id, product_id)
            )
        else:
            self.cursor.execute(
                'UPDATE products SET name = ?, flavor = ?, strength = ? WHERE id = ?',
                (name, flavor, strength, product_id)
            )
        self.conn.commit()

    def delete_product(self, product_id: int):
        self.cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        self.conn.commit()