from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import Database
from keyboards import *
from config import SELLER_CONTACT, ADMIN_IDS
from states import OrderStates
import logging

router = Router()
db = Database()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Добро пожаловать, {message.from_user.first_name}!\n\n"
        "🍼 Здесь вы можете заказать жидкости для электронных сигарет.",
        reply_markup=get_main_keyboard()
    )


# ===== КАТАЛОГ =====

@router.message(F.text == "📋 Каталог")
async def show_brands(message: Message, state: FSMContext):
    await state.clear()

    brands = db.get_all_brands()

    if not brands:
        await message.answer("📭 Каталог пуст. Скоро здесь появятся товары!")
        return

    await message.answer(
        "Выберите бренд:",
        reply_markup=get_brands_keyboard(brands)
    )


@router.callback_query(F.data.startswith('brand_'))
async def show_products(callback: CallbackQuery):
    await callback.answer()

    brand_id = int(callback.data.replace('brand_', ''))
    brand = db.get_brand(brand_id)
    products = db.get_products_by_brand(brand_id)

    if not products:
        await callback.message.edit_text(
            "❌ У этого бренда пока нет товаров",
            reply_markup=get_brands_keyboard(db.get_all_brands())
        )
        return

    # Отправляем фото бренда со списком товаров
    text = f"🏭 **{brand['name']}**\n\n"
    for i, p in enumerate(products, 1):
        text += f"{i}. **{p['name']}**\n"
        text += f"   👃 Вкус: {p['flavor']}\n"
        text += f"   💪 Крепость: {p['strength']} mg\n"
        text += f"   💰 Цена: {p['price']}₽\n\n"

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=brand['photo_id'],
            caption=text,
            reply_markup=get_products_keyboard(products)
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=get_products_keyboard(products)
        )


@router.callback_query(F.data.startswith('product_'))
async def show_product(callback: CallbackQuery):
    await callback.answer()

    product_id = int(callback.data.replace('product_', ''))
    product = db.get_product(product_id)

    if not product:
        await callback.message.edit_text("❌ Товар не найден")
        return

    text = (
        f"🍼 **{product['name']}**\n"
        f"🏭 Бренд: {product['brand_name']}\n"
        f"👃 Вкус: {product['flavor']}\n"
        f"💪 Крепость: {product['strength']} mg\n"
        f"💰 Цена: {product['price']}₽"
    )

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=product['brand_photo'],
            caption=text,
            reply_markup=get_product_actions_keyboard(product_id)
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=get_product_actions_keyboard(product_id)
        )


# ===== ПОКУПКА =====

@router.callback_query(F.data.startswith('buy_'))
async def buy_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    product_id = int(callback.data.replace('buy_', ''))
    product = db.get_product(product_id)

    if not product:
        await callback.message.edit_text("❌ Товар не найден")
        return

    await state.update_data(
        product_id=product_id,
        product_name=f"{product['brand_name']} - {product['name']}",
        product_price=product['price']
    )

    await state.set_state(OrderStates.username)

    await callback.message.edit_text(
        "📝 **Для покупки введите ваш Telegram username**\n\n"
        "Пример: @username\n\n"
        "Это нужно, чтобы продавец мог с вами связаться.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="cancel_buy")]
        ])
    )


@router.message(OrderStates.username)
async def process_username(message: Message, state: FSMContext):
    username = message.text.strip()

    if not username.startswith('@'):
        username = '@' + username

    data = await state.get_data()

    # Создаем заказ
    order_id = db.add_order(
        user_id=message.from_user.id,
        username=username,
        product_id=data['product_id'],
        product_name=data['product_name'],
        price=data['product_price']
    )

    # Уведомление пользователю
    await message.answer(
        f"✅ **Заказ #{order_id} оформлен!**\n\n"
        f"Товар: {data['product_name']}\n"
        f"Цена: {data['product_price']}₽\n"
        f"Ваш username: {username}\n\n"
        f"⏳ Продавец свяжется с вами в ближайшие 5 минут!\n\n"
        f"Спасибо за покупку!",
        reply_markup=get_main_keyboard()
    )

    # Уведомление админам
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"🔔 **Новый заказ #{order_id}!**\n\n"
                f"👤 Пользователь: {message.from_user.full_name}\n"
                f"📱 Username: {username}\n"
                f"🆔 User ID: {message.from_user.id}\n"
                f"🍼 Товар: {data['product_name']}\n"
                f"💰 Цена: {data['product_price']}₽"
            )
        except:
            pass

    await state.clear()


@router.callback_query(F.data == "cancel_buy")
async def cancel_buy(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()

    await callback.message.edit_text(
        "❌ Покупка отменена",
        reply_markup=get_brands_keyboard(db.get_all_brands())
    )


# ===== ИНФОРМАЦИЯ =====

@router.message(F.text == "ℹ️ Информация для покупки")
async def info(message: Message):
    await message.answer(
        "📞 **Как купить:**\n\n"
        "1️⃣ Зайдите в **Каталог**\n"
        "2️⃣ Выберите бренд и товар\n"
        "3️⃣ Нажмите **Купить** и введите свой Telegram username\n"
        "4️⃣ Ожидайте! В ближайшие 5 минут вам напишут\n\n"
        f"👤 **Продавец:** {SELLER_CONTACT}"
    )


# ===== НАВИГАЦИЯ =====

@router.callback_query(F.data == "back_to_brands")
async def back_to_brands(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()

    brands = db.get_all_brands()
    await callback.message.edit_text(
        "Выберите бренд:",
        reply_markup=get_brands_keyboard(brands)
    )


@router.callback_query(F.data == "back_to_products")
async def back_to_products(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()

    # Пытаемся получить brand_id из callback_data последнего товара
    # Для простоты возвращаемся к брендам
    brands = db.get_all_brands()
    await callback.message.edit_text(
        "Выберите бренд:",
        reply_markup=get_brands_keyboard(brands)
    )


@router.message(F.text == "◀️ Назад")
async def back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Главное меню",
        reply_markup=get_main_keyboard()
    )