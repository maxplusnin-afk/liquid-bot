from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ===== ОСНОВНЫЕ КЛАВИАТУРЫ =====

def get_main_keyboard():
    """Главное меню для пользователя"""
    buttons = [
        [KeyboardButton(text="📋 Каталог")],
        [KeyboardButton(text="ℹ️ Информация для покупки")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_admin_keyboard():
    """Главное меню для админа"""
    buttons = [
        [KeyboardButton(text="📁 Управление категориями")],
        [KeyboardButton(text="📦 Управление товарами")],
        [KeyboardButton(text="🏠 Выйти в пользовательское меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_back_keyboard():
    """Кнопка назад"""
    buttons = [[KeyboardButton(text="◀️ Назад")]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ===== INLINE КЛАВИАТУРЫ =====

def get_categories_keyboard(categories: list):
    """Клавиатура со списком категорий для пользователя"""
    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(
            text=f"📁 {cat['name']}",
            callback_data=f"category_{cat['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_products_keyboard(products: list, category_id: int):
    """Клавиатура со списком товаров"""
    keyboard = []
    for product in products:
        keyboard.append([InlineKeyboardButton(
            text=f"{product['name']} - {product['flavor']}",
            callback_data=f"product_{product['id']}"
        )])
    keyboard.append([InlineKeyboardButton(
        text="◀️ Назад к категориям",
        callback_data="back_to_categories"
    )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_categories_keyboard(categories: list):
    """Клавиатура категорий для админа"""
    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(
            text=f"📁 {cat['name']}",
            callback_data=f"admin_category_{cat['id']}"
        )])
    keyboard.append([InlineKeyboardButton(
        text="➕ Добавить категорию",
        callback_data="add_category"
    )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_products_keyboard(products: list, category_id: int):
    """Клавиатура товаров для админа"""
    keyboard = []
    for product in products:
        keyboard.append([InlineKeyboardButton(
            text=f"✏️ {product['name']} - {product['flavor']}",
            callback_data=f"admin_product_{product['id']}"
        )])
    keyboard.append([InlineKeyboardButton(
        text="➕ Добавить товар",
        callback_data=f"add_product_{category_id}"
    )])
    keyboard.append([InlineKeyboardButton(
        text="◀️ Назад к категориям",
        callback_data="back_to_admin_categories"
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

def get_edit_fields_keyboard():
    """Клавиатура выбора поля для редактирования"""
    keyboard = [
        [InlineKeyboardButton(text="📝 Название", callback_data="field_name")],
        [InlineKeyboardButton(text="👃 Вкус", callback_data="field_flavor")],
        [InlineKeyboardButton(text="💪 Крепость", callback_data="field_strength")],
        [InlineKeyboardButton(text="🖼 Фото", callback_data="field_photo")],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="cancel_edit")]
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