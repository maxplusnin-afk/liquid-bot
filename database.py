import sqlite3
from typing import List, Dict, Optional


class Database:
    def __init__(self):
        self.conn = sqlite3.connect('shop.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
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

        # Таблица корзины
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            )
        ''')

        # Таблица заказов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                products TEXT NOT NULL,
                total_price INTEGER NOT NULL,
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
        except:
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

    # ===== КОРЗИНА =====

    def add_to_cart(self, user_id: int, product_id: int):
        # Проверяем, есть ли уже такой товар в корзине
        self.cursor.execute(
            'SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ?',
            (user_id, product_id)
        )
        existing = self.cursor.fetchone()

        if existing:
            # Увеличиваем количество
            self.cursor.execute(
                'UPDATE cart SET quantity = quantity + 1 WHERE id = ?',
                (existing[0],)
            )
        else:
            # Добавляем новый товар
            self.cursor.execute(
                'INSERT INTO cart (user_id, product_id) VALUES (?, ?)',
                (user_id, product_id)
            )
        self.conn.commit()

    def get_cart(self, user_id: int) -> List[Dict]:
        self.cursor.execute('''
            SELECT c.id, c.product_id, c.quantity, p.name, p.flavor, p.strength, p.price, b.name
            FROM cart c
            JOIN products p ON c.product_id = p.id
            JOIN brands b ON p.brand_id = b.id
            WHERE c.user_id = ?
        ''', (user_id,))

        items = []
        total = 0
        for row in self.cursor.fetchall():
            item_total = row[2] * row[6]  # quantity * price
            total += item_total
            items.append({
                'cart_id': row[0],
                'product_id': row[1],
                'quantity': row[2],
                'name': row[3],
                'flavor': row[4],
                'strength': row[5],
                'price': row[6],
                'brand_name': row[7],
                'total': item_total
            })

        return {'items': items, 'total': total}

    def remove_from_cart(self, cart_id: int):
        self.cursor.execute('DELETE FROM cart WHERE id = ?', (cart_id,))
        self.conn.commit()

    def clear_cart(self, user_id: int):
        self.cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        self.conn.commit()

    # ===== ЗАКАЗЫ =====

    def create_order(self, user_id: int, username: str, cart_items: List[Dict], total_price: int) -> int:
        # Формируем текст заказа
        products_text = ""
        for item in cart_items:
            products_text += f"{item['brand_name']} - {item['name']} ({item['flavor']}) x{item['quantity']} = {item['total']}₽\n"

        self.cursor.execute(
            'INSERT INTO orders (user_id, username, products, total_price) VALUES (?, ?, ?, ?)',
            (user_id, username, products_text, total_price)
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
                'products': row[3],
                'total_price': row[4],
                'status': row[5],
                'created_at': row[6]
            }
            for row in self.cursor.fetchall()
        ]

    def update_order_status(self, order_id: int, status: str):
        self.cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
        self.conn.commit()