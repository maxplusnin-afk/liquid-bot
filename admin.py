from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import ADMIN_IDS
from database import Database
from keyboards import *
from states import CategoryStates, ProductStates
import logging
from aiogram.exceptions import TelegramBadRequest

router = Router()
db = Database()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ===== ВХОД В АДМИНКУ =====

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещен")
        return

    await message.answer(
        "🔐 **Панель администратора**\n\nВыберите действие:",
        reply_markup=get_admin_keyboard()
    )


# ===== УПРАВЛЕНИЕ КАТЕГОРИЯМИ =====

@router.message(F.text == "📁 Управление категориями")
async def manage_categories(message: Message):
    if not is_admin(message.from_user.id):
        return

    categories = db.get_all_categories()
    await message.answer(
        "Управление категориями:",
        reply_markup=get_admin_categories_keyboard(categories)
    )


@router.callback_query(F.data == "add_category")
async def add_category_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(CategoryStates.name)
    await callback.message.edit_text(
        "📝 Введите название новой категории:"
    )


@router.message(CategoryStates.name)
async def add_category_name(message: Message, state: FSMContext):
    category_id = db.add_category(message.text)

    if category_id:
        await message.answer(
            f"✅ Категория '{message.text}' добавлена!",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer(
            "❌ Такая категория уже существует",
            reply_markup=get_admin_keyboard()
        )

    await state.clear()


@router.callback_query(F.data.startswith('admin_category_'))
async def admin_category_actions(callback: CallbackQuery):
    await callback.answer()

    category_id = int(callback.data.replace('admin_category_', ''))
    products = db.get_products_by_category(category_id)

    if products:
        await callback.message.edit_text(
            "Товары в категории:",
            reply_markup=get_admin_products_keyboard(products, category_id)
        )
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить товар", callback_data=f"add_product_{category_id}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin_categories")]
        ])
        await callback.message.edit_text(
            "В этой категории пока нет товаров",
            reply_markup=keyboard
        )


# ===== УПРАВЛЕНИЕ ТОВАРАМИ =====

@router.message(F.text == "📦 Управление товарами")
async def manage_products_start(message: Message):
    if not is_admin(message.from_user.id):
        return

    categories = db.get_all_categories()
    await message.answer(
        "Выберите категорию:",
        reply_markup=get_admin_categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith('add_product_'))
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    category_id = int(callback.data.replace('add_product_', ''))
    await state.update_data(category_id=category_id)
    await state.set_state(ProductStates.name)

    await callback.message.edit_text("📝 Введите название товара:")


@router.message(ProductStates.name)
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(ProductStates.flavor)
    await message.answer("👃 Введите вкус:")


@router.message(ProductStates.flavor)
async def add_product_flavor(message: Message, state: FSMContext):
    await state.update_data(flavor=message.text)
    await state.set_state(ProductStates.strength)
    await message.answer("💪 Введите крепость (мг):")


@router.message(ProductStates.strength)
async def add_product_strength(message: Message, state: FSMContext):
    await state.update_data(strength=message.text)
    await state.set_state(ProductStates.photo)
    await message.answer("🖼 Отправьте фото товара (или отправьте 'нет'):")


@router.message(ProductStates.photo)
async def add_product_photo(message: Message, state: FSMContext):
    photo_id = ""
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text and message.text.lower() == 'нет':
        photo_id = ""
    else:
        await message.answer("❌ Отправьте фото или напишите 'нет'")
        return

    data = await state.get_data()

    product_id = db.add_product(
        data['category_id'],
        data['name'],
        data['flavor'],
        data['strength'],
        photo_id
    )

    await message.answer(
        f"✅ Товар добавлен!\n\n"
        f"📝 Название: {data['name']}\n"
        f"👃 Вкус: {data['flavor']}\n"
        f"💪 Крепость: {data['strength']} мг",
        reply_markup=get_admin_keyboard()
    )

    await state.clear()


@router.callback_query(F.data.startswith('admin_product_'))
async def admin_product_actions(callback: CallbackQuery):
    await callback.answer()

    product_id = int(callback.data.replace('admin_product_', ''))
    product = db.get_product(product_id)

    if not product:
        await callback.message.edit_text("❌ Товар не найден")
        return

    text = (
        f"🍼 **{product['name']}**\n"
        f"👃 Вкус: {product['flavor']}\n"
        f"💪 Крепость: {product['strength']} мг"
    )

    if product['photo_id'] and callback.message.photo:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=get_admin_product_actions(product_id)
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_product_actions(product_id)
        )


@router.callback_query(F.data.startswith('edit_'))
async def edit_product_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    product_id = int(callback.data.replace('edit_', ''))
    await state.update_data(edit_id=product_id)
    await state.set_state(ProductStates.edit_field)

    await callback.message.edit_text(
        "Что хотите изменить?",
        reply_markup=get_edit_fields_keyboard()
    )


@router.callback_query(F.data.startswith('field_'))
async def edit_product_field(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    field = callback.data.replace('field_', '')
    await state.update_data(edit_field=field)

    if field == 'photo':
        await state.set_state(ProductStates.edit_value)
        await callback.message.edit_text(
            "📸 Отправьте новое фото:"
        )
    else:
        field_names = {
            'name': 'название',
            'flavor': 'вкус',
            'strength': 'крепость'
        }
        await state.set_state(ProductStates.edit_value)
        await callback.message.edit_text(
            f"Введите новое {field_names.get(field, 'значение')}:"
        )


@router.message(ProductStates.edit_value)
async def edit_product_value(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data['edit_id']
    field = data['edit_field']

    product = db.get_product(product_id)
    if not product:
        await message.answer("❌ Товар не найден")
        await state.clear()
        return

    name, flavor, strength, photo_id = product['name'], product['flavor'], product['strength'], product['photo_id']

    if field == 'photo':
        if message.photo:
            photo_id = message.photo[-1].file_id
        else:
            await message.answer("❌ Отправьте фото")
            return
    elif field == 'name':
        name = message.text
    elif field == 'flavor':
        flavor = message.text
    elif field == 'strength':
        strength = message.text

    db.update_product(product_id, name, flavor, strength, photo_id)

    await message.answer(
        f"✅ Товар обновлен!",
        reply_markup=get_admin_keyboard()
    )

    await state.clear()


@router.callback_query(F.data.startswith('delete_'))
async def delete_product_confirm(callback: CallbackQuery):
    await callback.answer()

    product_id = int(callback.data.replace('delete_', ''))

    await callback.message.edit_text(
        "❓ Точно удалить этот товар?",
        reply_markup=get_confirm_keyboard('delete_product', product_id)
    )


@router.callback_query(F.data.startswith('confirm_delete_product_'))
async def confirm_delete_product(callback: CallbackQuery):
    await callback.answer()

    product_id = int(callback.data.split('_')[-1])
    db.delete_product(product_id)

    await callback.message.edit_text("✅ Товар удален")


# ===== НАВИГАЦИЯ =====

@router.callback_query(F.data == "back_to_admin_categories")
async def back_to_admin_categories(callback: CallbackQuery):
    await callback.answer()

    categories = db.get_all_categories()
    await callback.message.edit_text(
        "Управление категориями:",
        reply_markup=get_admin_categories_keyboard(categories)
    )


@router.callback_query(F.data == "back_to_admin_products")
async def back_to_admin_products(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()

    categories = db.get_all_categories()
    await callback.message.edit_text(
        "Выберите категорию:",
        reply_markup=get_admin_categories_keyboard(categories)
    )


@router.callback_query(F.data == "cancel_edit")
async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()

    categories = db.get_all_categories()
    await callback.message.edit_text(
        "Управление категориями:",
        reply_markup=get_admin_categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith('cancel_'))
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()

    await callback.message.edit_text(
        "Действие отменено",
        reply_markup=get_admin_keyboard()
    )


@router.message(F.text == "🏠 Выйти в пользовательское меню")
async def exit_to_user(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Вы вышли в пользовательское меню",
        reply_markup=get_main_keyboard()
    )