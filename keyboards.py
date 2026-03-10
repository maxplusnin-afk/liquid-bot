from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ===== ОСНОВНЫЕ КЛАВИАТУРЫ =====

def get_main_keyboard():
    """Главное меню для пользователя"""
    buttons = [
        [KeyboardButton(text="📋 Каталог")],
        [KeyboardButton(text="🛒 Корзина")],
        [KeyboardButton(text="ℹ️ Информация для покупки")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_admin_keyboard():
    """Главное меню для админа"""
    buttons = [
        [KeyboardButton(text="➕ Добавить бренд")],
        [KeyboardButton(text="📝 Управление товарами")],
        [KeyboardButton(text="📦 Заказы")],
        [KeyboardButton(text="🏠 Выйти в пользовательское меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_back_keyboard():
    """Кнопка назад"""
    buttons = [[KeyboardButton(text="◀️ Назад")]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ===== INLINE КЛАВИАТУРЫ =====

def get_brands_keyboard(brands: list):
    """Клавиатура со списком брендов"""
    keyboard = []
    for brand in brands:
        keyboard.append([InlineKeyboardButton(
            text=f"🏭 {brand['name']}",
            callback_data=f"brand_{brand['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_products_keyboard(products: list):
    """Клавиатура со списком товаров"""
    keyboard = []
    for product in products:
        keyboard.append([InlineKeyboardButton(
            text=f"{product['name']} - {product['price']}₽",
            callback_data=f"product_{product['id']}"
        )])
    keyboard.append([InlineKeyboardButton(
        text="◀️ Назад к брендам",
        callback_data="back_to_brands"
    )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_product_actions_keyboard(product_id: int):
    """Клавиатура действий с товаром (в корзину/назад)"""
    keyboard = [
        [InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_to_cart_{product_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_products")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_cart_keyboard(cart_items: list):
    """Клавиатура корзины"""
    keyboard = []
    for item in cart_items:
        keyboard.append([InlineKeyboardButton(
            text=f"❌ Удалить: {item['name']} x{item['quantity']}",
            callback_data=f"remove_from_cart_{item['cart_id']}"
        )])
    keyboard.append([
        InlineKeyboardButton(text="✅ Сделать заказ", callback_data="checkout"),
        InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")
    ])
    keyboard.append([InlineKeyboardButton(text="◀️ Продолжить покупки", callback_data="back_to_brands")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_checkout_keyboard():
    """Клавиатура подтверждения заказа"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="confirm_order")],
        [InlineKeyboardButton(text="◀️ Вернуться в корзину", callback_data="back_to_cart")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_brands_keyboard(brands: list):
    """Клавиатура брендов для админа"""
    keyboard = []
    for brand in brands:
        keyboard.append([InlineKeyboardButton(
            text=f"📝 {brand['name']}",
            callback_data=f"admin_brand_{brand['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_products_keyboard(products: list, brand_id: int):
    """Клавиатура товаров для админа"""
    keyboard = []
    for product in products:
        keyboard.append([InlineKeyboardButton(
            text=f"✏️ {product['name']} - {product['price']}₽",
            callback_data=f"admin_product_{product['id']}"
        )])
    keyboard.append([InlineKeyboardButton(
        text="➕ Добавить товар",
        callback_data=f"add_product_{brand_id}"
    )])
    keyboard.append([InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_admin_brands"
    )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_product_actions(product_id: int):
    """Клавиатура действий с товаром для админа"""
    keyboard = [
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{product_id}")],
        [InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_{product_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin_products")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirm_keyboard(action: str, item_id: int):
    """Клавиатура подтверждения"""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}_{item_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel_{action}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_orders_keyboard(orders: list):
    """Клавиатура заказов для админа"""
    keyboard = []
    for order in orders[:10]:
        status = "✅" if order['status'] == 'выполнен' else "⏳"
        keyboard.append([InlineKeyboardButton(
            text=f"{status} Заказ #{order['id']} - {order['total_price']}₽",
            callback_data=f"order_{order['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_order_actions_keyboard(order_id: int):
    """Клавиатура действий с заказом"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Отметить выполненным", callback_data=f"complete_{order_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_orders")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)