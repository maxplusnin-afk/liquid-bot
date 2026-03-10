from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import ADMIN_IDS
from database import Database
from keyboards import *
from states import BrandStates, ProductStates
import logging

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


# ===== ДОБАВЛЕНИЕ БРЕНДА =====

@router.message(F.text == "➕ Добавить бренд")
async def add_brand_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(BrandStates.name)
    await message.answer(
        "📝 Введите название бренда:",
        reply_markup=get_back_keyboard()
    )


@router.message(BrandStates.name)
async def add_brand_name(message: Message, state: FSMContext):
    if message.text == "◀️ Назад":
        await state.clear()
        await message.answer("Главное меню", reply_markup=get_admin_keyboard())
        return

    await state.update_data(name=message.text)
    await state.set_state(BrandStates.photo)
    await message.answer("📸 Отправьте фото бренда:")


@router.message(BrandStates.photo)
async def add_brand_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фото")
        return

    data = await state.get_data()
    photo_id = message.photo[-1].file_id

    brand_id = db.add_brand(data['name'], photo_id)

    if brand_id:
        await message.answer_photo(
            photo=photo_id,
            caption=f"✅ Бренд '{data['name']}' добавлен!",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer(
            "❌ Бренд с таким названием уже существует",
            reply_markup=get_admin_keyboard()
        )

    await state.clear()


# ===== УПРАВЛЕНИЕ ТОВАРАМИ =====

@router.message(F.text == "📝 Управление товарами")
async def manage_products(message: Message):
    if not is_admin(message.from_user.id):
        return

    brands = db.get_all_brands()

    if not brands:
        await message.answer("❌ Сначала добавьте бренд")
        return

    await message.answer(
        "Выберите бренд:",
        reply_markup=get_admin_brands_keyboard(brands)
    )


@router.callback_query(F.data.startswith('admin_brand_'))
async def admin_brand_products(callback: CallbackQuery):
    await callback.answer()

    brand_id = int(callback.data.replace('admin_brand_', ''))
    products = db.get_products_by_brand(brand_id)

    if products:
        await callback.message.edit_text(
            "Товары бренда:",
            reply_markup=get_admin_products_keyboard(products, brand_id)
        )
    else:
        # Если товаров нет, показываем кнопку добавления
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить товар", callback_data=f"add_product_{brand_id}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin_brands")]
        ])
        await callback.message.edit_text(
            "У бренда пока нет товаров. Добавьте первый товар:",
            reply_markup=keyboard
        )


@router.callback_query(F.data.startswith('add_product_'))
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    brand_id = int(callback.data.replace('add_product_', ''))
    await state.update_data(brand_id=brand_id)
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
    await message.answer("💪 Введите крепость (mg):")


@router.message(ProductStates.strength)
async def add_product_strength(message: Message, state: FSMContext):
    await state.update_data(strength=message.text)
    await state.set_state(ProductStates.price)
    await message.answer("💰 Введите цену (руб):")


@router.message(ProductStates.price)
async def add_product_price(message: Message, state: FSMContext):
    try:
        price = int(message.text)
        if price <= 0:
            await message.answer("❌ Цена должна быть больше 0")
            return

        data = await state.get_data()

        product_id = db.add_product(
            data['brand_id'],
            data['name'],
            data['flavor'],
            data['strength'],
            price
        )

        brand = db.get_brand(data['brand_id'])

        await message.answer(
            f"✅ Товар добавлен!\n\n"
            f"🏭 Бренд: {brand['name']}\n"
            f"🍼 Товар: {data['name']}\n"
            f"👃 Вкус: {data['flavor']}\n"
            f"💪 Крепость: {data['strength']} mg\n"
            f"💰 Цена: {price}₽",
            reply_markup=get_admin_keyboard()
        )

        await state.clear()

    except ValueError:
        await message.answer("❌ Введите число")


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
        f"💪 Крепость: {product['strength']} mg\n"
        f"💰 Цена: {product['price']}₽"
    )

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

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Название", callback_data="field_name")],
        [InlineKeyboardButton(text="👃 Вкус", callback_data="field_flavor")],
        [InlineKeyboardButton(text="💪 Крепость", callback_data="field_strength")],
        [InlineKeyboardButton(text="💰 Цена", callback_data="field_price")],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="cancel_edit")]
    ])

    await callback.message.edit_text(
        "Что хотите изменить?",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith('field_'))
async def edit_product_field(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    field = callback.data.replace('field_', '')
    await state.update_data(edit_field=field)
    await state.set_state(ProductStates.edit_value)

    field_names = {
        'name': 'название',
        'flavor': 'вкус',
        'strength': 'крепость',
        'price': 'цену'
    }

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

    name, flavor, strength, price = product['name'], product['flavor'], product['strength'], product['price']

    if field == 'price':
        try:
            price = int(message.text)
            if price <= 0:
                await message.answer("❌ Цена должна быть больше 0")
                return
        except ValueError:
            await message.answer("❌ Введите число")
            return
    else:
        if field == 'name':
            name = message.text
        elif field == 'flavor':
            flavor = message.text
        elif field == 'strength':
            strength = message.text

    db.update_product(product_id, name, flavor, strength, price)

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


# ===== ЗАКАЗЫ =====

@router.message(F.text == "📦 Заказы")
async def show_orders(message: Message):
    if not is_admin(message.from_user.id):
        return

    orders = db.get_all_orders()

    if not orders:
        await message.answer("📭 Заказов пока нет")
        return

    await message.answer(
        "Список заказов:",
        reply_markup=get_orders_keyboard(orders)
    )


@router.callback_query(F.data.startswith('order_'))
async def order_details(callback: CallbackQuery):
    await callback.answer()

    order_id = int(callback.data.replace('order_', ''))
    orders = db.get_all_orders()
    order = next((o for o in orders if o['id'] == order_id), None)

    if not order:
        await callback.message.edit_text("❌ Заказ не найден")
        return

    text = (
        f"📋 **Заказ #{order['id']}**\n\n"
        f"👤 Пользователь: {order['username'] or 'не указан'}\n"
        f"🆔 User ID: {order['user_id']}\n"
        f"🍼 Товар: {order['product_name']}\n"
        f"💰 Цена: {order['price']}₽\n"
        f"📊 Статус: {order['status']}\n"
        f"📅 Дата: {order['created_at'][:16]}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_order_actions_keyboard(order_id)
    )


@router.callback_query(F.data.startswith('complete_'))
async def complete_order(callback: CallbackQuery):
    await callback.answer()

    order_id = int(callback.data.replace('complete_', ''))
    db.update_order_status(order_id, 'выполнен')

    await callback.message.edit_text("✅ Заказ отмечен как выполненный")


# ===== НАВИГАЦИЯ =====

@router.callback_query(F.data == "back_to_admin_brands")
async def back_to_admin_brands(callback: CallbackQuery):
    await callback.answer()

    brands = db.get_all_brands()
    await callback.message.edit_text(
        "Выберите бренд:",
        reply_markup=get_admin_brands_keyboard(brands)
    )


@router.callback_query(F.data == "back_to_admin_products")
async def back_to_admin_products(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()

    brands = db.get_all_brands()
    await callback.message.edit_text(
        "Выберите бренд:",
        reply_markup=get_admin_brands_keyboard(brands)
    )


@router.callback_query(F.data == "back_to_orders")
async def back_to_orders(callback: CallbackQuery):
    await callback.answer()

    orders = db.get_all_orders()
    await callback.message.edit_text(
        "Список заказов:",
        reply_markup=get_orders_keyboard(orders)
    )


@router.callback_query(F.data == "cancel_edit")
async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()

    brands = db.get_all_brands()
    await callback.message.edit_text(
        "Выберите бренд:",
        reply_markup=get_admin_brands_keyboard(brands)
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