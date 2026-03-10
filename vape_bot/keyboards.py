from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_admin_keyboard():
    """Клавиатура для админа"""
    buttons = [
        [KeyboardButton(text="🏭 Добавить бренд")],
        [KeyboardButton(text="🍼 Добавить жидкость")],
        [KeyboardButton(text="📋 Список брендов")],
        [KeyboardButton(text="📊 Заявки на покупку")],
        [KeyboardButton(text="🗑 Удалить бренд")],
        [KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_user_keyboard():
    """Клавиатура для пользователя"""
    buttons = [
        [KeyboardButton(text="🍼 Каталог жидкостей")],
        [KeyboardButton(text="📞 Информация для покупки")],
        [KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_cancel_keyboard():
    """Клавиатура отмены"""
    buttons = [[KeyboardButton(text="❌ Отмена")]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_brands_keyboard(brands: list):
    """Клавиатура со списком брендов"""
    builder = InlineKeyboardBuilder()
    for brand in brands:
        builder.button(
            text=f"🏭 {brand['name']}",
            callback_data=f"brand_{brand['id']}"
        )
    builder.adjust(1)
    return builder.as_markup()

def get_admin_brands_keyboard(brands: list):
    """Клавиатура со списком брендов для админа (для удаления)"""
    builder = InlineKeyboardBuilder()
    for brand in brands:
        builder.button(
            text=f"❌ {brand['name']}",
            callback_data=f"admin_delete_brand_{brand['id']}"
        )
    builder.button(text="◀️ Назад", callback_data="back_to_admin_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_brand_liquids_keyboard(liquids: list, brand_id: int):
    """Клавиатура с жидкостями бренда для покупки"""
    builder = InlineKeyboardBuilder()
    for liquid in liquids:
        builder.button(
            text=f"🍼 {liquid['name']} - {liquid['flavor']} ({liquid['strength']} mg) - {liquid['price']}₽",
            callback_data=f"buy_liquid_{liquid['id']}"
        )
    builder.button(text="◀️ Назад к брендам", callback_data="back_to_brands")
    builder.adjust(1)
    return builder.as_markup()

def get_confirm_purchase_keyboard(liquid_id: int):
    """Клавиатура подтверждения покупки"""
    buttons = [
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_buy_{liquid_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_buy_{liquid_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_to_admin_keyboard():
    """Клавиатура возврата в админ-меню"""
    buttons = [[InlineKeyboardButton(text="◀️ Назад в админ-меню", callback_data="back_to_admin_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_to_catalog_keyboard():
    """Клавиатура возврата к брендам"""
    buttons = [[InlineKeyboardButton(text="◀️ Назад к брендам", callback_data="back_to_brands")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)