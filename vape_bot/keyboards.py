from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_admin_keyboard():
    """Клавиатура для админа"""
    buttons = [
        [KeyboardButton(text="📦 Добавить жидкость")],
        [KeyboardButton(text="📋 Список жидкостей")],
        [KeyboardButton(text="🗑 Удалить жидкость")],
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

def get_liquids_keyboard(liquids: list):
    """Клавиатура со списком жидкостей для пользователя"""
    builder = InlineKeyboardBuilder()
    for liquid in liquids:
        builder.button(
            text=f"{liquid['name']} - {liquid['flavor']} ({liquid['strength']} mg, {liquid['volume']} ml)",
            callback_data=f"liquid_{liquid['id']}"
        )
    builder.adjust(1)
    return builder.as_markup()

def get_admin_liquids_keyboard(liquids: list):
    """Клавиатура со списком жидкостей для админа (для удаления)"""
    builder = InlineKeyboardBuilder()
    for liquid in liquids:
        builder.button(
            text=f"❌ {liquid['name']} - {liquid['flavor']}",
            callback_data=f"admin_delete_{liquid['id']}"
        )
    builder.button(text="◀️ Назад", callback_data="back_to_admin_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_back_to_admin_keyboard():
    """Клавиатура возврата в админ-меню"""
    buttons = [[InlineKeyboardButton(text="◀️ Назад в админ-меню", callback_data="back_to_admin_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_to_catalog_keyboard():
    """Клавиатура возврата в каталог"""
    buttons = [[InlineKeyboardButton(text="◀️ Назад к каталогу", callback_data="back_to_catalog")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)