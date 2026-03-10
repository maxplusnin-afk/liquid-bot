from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import Database
from keyboards import *
from config import SELLER_CONTACT, ADMIN_IDS
from states import OrderStates
import logging
from aiogram.exceptions import TelegramBadRequest

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
        # Проверяем тип сообщения перед редактированием
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(
                "❌ У этого бренда пока нет товаров",
                reply_markup=get_brands_keyboard(db.get_all_brands())
            )
        else:
            try:
                await callback.message.edit_text(
                    "❌ У этого бренда пока нет товаров",
                    reply_markup=get_brands_keyboard(db.get_all_brands())
                )
            except TelegramBadRequest:
                await callback.message.delete()
                await callback.message.answer(
                    "❌ У этого бренда пока нет товаров",
                    reply_markup=get_brands_keyboard(db.get_all_brands())
                )
        return

    # Формируем текст со списком товаров
    text = f"🏭 **{brand['name']}**\n\n"
    for i, product in enumerate(products, 1):
        text += f"{i}. **{product['name']}**\n"
        text += f"   👃 Вкус: {product['flavor']}\n"
        text += f"   💪 Крепость: {product['strength']} mg\n"
        text += f"   💰 Цена: {product['price']}₽\n\n"

    # Отправляем фото бренда со списком товаров
    if callback.message.photo:
        await callback.message.delete()

    await callback.message.answer_photo(
        photo=brand['photo_id'],
        caption=text,
        reply_markup=get_products_keyboard(products)
    )


@router.callback_query(F.data.startswith('product_'))
async def show_product(callback: CallbackQuery):
    await callback.answer()

    product_id = int(callback.data.replace('product_', ''))
    product = db.get_product(product_id)

    if not product:
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer("❌ Товар не найден")
        else:
            try:
                await callback.message.edit_text("❌ Товар не найден")
            except TelegramBadRequest:
                await callback.message.delete()
                await callback.message.answer("❌ Товар не найден")
        return

    text = (
        f"🍼 **{product['name']}**\n"
        f"🏭 Бренд: {product['brand_name']}\n"
        f"👃 Вкус: {product['flavor']}\n"
        f"💪 Крепость: {product['strength']} mg\n"
        f"💰 Цена: {product['price']}₽"
    )

    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=get_product_actions_keyboard(product_id)
        )
    else:
        try:
            await callback.message.edit_text(
                text,
                reply_markup=get_product_actions_keyboard(product_id)
            )
        except TelegramBadRequest:
            await callback.message.delete()
            await callback.message.answer(
                text,
                reply_markup=get_product_actions_keyboard(product_id)
            )


# ===== КОРЗИНА =====

@router.callback_query(F.data.startswith('add_to_cart_'))
async def add_to_cart(callback: CallbackQuery):
    await callback.answer()

    product_id = int(callback.data.replace('add_to_cart_', ''))
    product = db.get_product(product_id)

    if not product:
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer("❌ Товар не найден")
        else:
            try:
                await callback.message.edit_text("❌ Товар не найден")
            except TelegramBadRequest:
                await callback.message.delete()
                await callback.message.answer("❌ Товар не найден")
        return

    # Добавляем в корзину
    db.add_to_cart(callback.from_user.id, product_id)

    # Показываем подтверждение
    await callback.answer("✅ Товар добавлен в корзину!", show_alert=False)

    # Обновляем сообщение с кнопкой
    text = (
        f"✅ **Товар добавлен в корзину!**\n\n"
        f"🍼 **{product['name']}**\n"
        f"🏭 Бренд: {product['brand_name']}\n"
        f"👃 Вкус: {product['flavor']}\n"
        f"💪 Крепость: {product['strength']} mg\n"
        f"💰 Цена: {product['price']}₽"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Перейти в корзину", callback_data="go_to_cart")],
        [InlineKeyboardButton(text="◀️ Продолжить покупки", callback_data="back_to_brands")]
    ])

    if callback.message.photo:
        await callback.message.edit_caption(caption=text, reply_markup=keyboard)
    else:
        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=keyboard)


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message):
    cart = db.get_cart(message.from_user.id)

    if not cart['items']:
        await message.answer(
            "🛒 **Корзина пуста**\n\nДобавьте товары из каталога.",
            reply_markup=get_main_keyboard()
        )
        return

    # Формируем текст корзины
    text = "🛒 **Ваша корзина:**\n\n"
    for i, item in enumerate(cart['items'], 1):
        text += f"{i}. **{item['brand_name']} - {item['name']}**\n"
        text += f"   👃 Вкус: {item['flavor']}\n"
        text += f"   💪 Крепость: {item['strength']} mg\n"
        text += f"   {item['quantity']} x {item['price']}₽ = {item['total']}₽\n\n"

    text += f"💰 **ИТОГО: {cart['total']}₽**"

    await message.answer(
        text,
        reply_markup=get_cart_keyboard(cart['items'])
    )


@router.callback_query(F.data.startswith('remove_from_cart_'))
async def remove_from_cart(callback: CallbackQuery):
    await callback.answer()

    cart_id = int(callback.data.replace('remove_from_cart_', ''))
    db.remove_from_cart(cart_id)

    # Показываем обновленную корзину
    cart = db.get_cart(callback.from_user.id)

    if not cart['items']:
        # Проверяем тип сообщения
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(
                "🛒 **Корзина пуста**\n\nДобавьте товары из каталога.",
                reply_markup=get_main_keyboard()
            )
        else:
            try:
                await callback.message.edit_text(
                    "🛒 **Корзина пуста**\n\nДобавьте товары из каталога.",
                    reply_markup=get_main_keyboard()
                )
            except TelegramBadRequest:
                await callback.message.delete()
                await callback.message.answer(
                    "🛒 **Корзина пуста**\n\nДобавьте товары из каталога.",
                    reply_markup=get_main_keyboard()
                )
        return

    text = "🛒 **Ваша корзина:**\n\n"
    for i, item in enumerate(cart['items'], 1):
        text += f"{i}. **{item['brand_name']} - {item['name']}**\n"
        text += f"   👃 Вкус: {item['flavor']}\n"
        text += f"   💪 Крепость: {item['strength']} mg\n"
        text += f"   {item['quantity']} x {item['price']}₽ = {item['total']}₽\n\n"

    text += f"💰 **ИТОГО: {cart['total']}₽**"

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=get_cart_keyboard(cart['items']))
    else:
        try:
            await callback.message.edit_text(text, reply_markup=get_cart_keyboard(cart['items']))
        except TelegramBadRequest:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=get_cart_keyboard(cart['items']))


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    await callback.answer()

    db.clear_cart(callback.from_user.id)

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            "🗑 **Корзина очищена**\n\nДобавьте товары из каталога.",
            reply_markup=get_main_keyboard()
        )
    else:
        try:
            await callback.message.edit_text(
                "🗑 **Корзина очищена**\n\nДобавьте товары из каталога.",
                reply_markup=get_main_keyboard()
            )
        except TelegramBadRequest:
            await callback.message.delete()
            await callback.message.answer(
                "🗑 **Корзина очищена**\n\nДобавьте товары из каталога.",
                reply_markup=get_main_keyboard()
            )


@router.callback_query(F.data == "go_to_cart")
async def go_to_cart(callback: CallbackQuery):
    await callback.answer()

    cart = db.get_cart(callback.from_user.id)

    if not cart['items']:
        if callback.message.photo:
            await callback.message.edit_caption(
                caption="🛒 **Корзина пуста**",
                reply_markup=get_brands_keyboard(db.get_all_brands())
            )
        else:
            try:
                await callback.message.edit_text(
                    "🛒 **Корзина пуста**",
                    reply_markup=get_brands_keyboard(db.get_all_brands())
                )
            except TelegramBadRequest:
                await callback.message.delete()
                await callback.message.answer(
                    "🛒 **Корзина пуста**",
                    reply_markup=get_brands_keyboard(db.get_all_brands())
                )
        return

    text = "🛒 **Ваша корзина:**\n\n"
    for i, item in enumerate(cart['items'], 1):
        text += f"{i}. **{item['brand_name']} - {item['name']}**\n"
        text += f"   👃 Вкус: {item['flavor']}\n"
        text += f"   💪 Крепость: {item['strength']} mg\n"
        text += f"   {item['quantity']} x {item['price']}₽ = {item['total']}₽\n\n"

    text += f"💰 **ИТОГО: {cart['total']}₽**"

    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=get_cart_keyboard(cart['items'])
        )
    else:
        try:
            await callback.message.edit_text(
                text,
                reply_markup=get_cart_keyboard(cart['items'])
            )
        except TelegramBadRequest:
            await callback.message.delete()
            await callback.message.answer(
                text,
                reply_markup=get_cart_keyboard(cart['items'])
            )


# ===== ОФОРМЛЕНИЕ ЗАКАЗА =====

@router.callback_query(F.data == "checkout")
async def checkout_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    cart = db.get_cart(callback.from_user.id)

    if not cart['items']:
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(
                "❌ Корзина пуста",
                reply_markup=get_main_keyboard()
            )
        else:
            try:
                await callback.message.edit_text(
                    "❌ Корзина пуста",
                    reply_markup=get_main_keyboard()
                )
            except TelegramBadRequest:
                await callback.message.delete()
                await callback.message.answer(
                    "❌ Корзина пуста",
                    reply_markup=get_main_keyboard()
                )
        return

    # Сохраняем данные корзины в состояние
    await state.update_data(cart=cart)
    await state.set_state(OrderStates.username)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    text = (
        "📝 **Оформление заказа**\n\n"
        f"💰 Сумма заказа: {cart['total']}₽\n\n"
        "✏️ **Пожалуйста, напишите ваш Telegram username**\n"
        "(например: @username)\n\n"
        "Это нужно, чтобы продавец мог с вами связаться."
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Вернуться в корзину", callback_data="back_to_cart")]
    ])

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=keyboard)
    else:
        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=keyboard)


@router.message(OrderStates.username)
async def process_username(message: Message, state: FSMContext):
    username = message.text.strip()

    if not username.startswith('@'):
        username = '@' + username

    data = await state.get_data()
    cart = data.get('cart')

    if not cart:
        await message.answer(
            "❌ Ошибка! Пожалуйста, начните заново.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        return

    # Создаем заказ
    order_id = db.create_order(
        user_id=message.from_user.id,
        username=username,
        cart_items=cart['items'],
        total_price=cart['total']
    )

    # Очищаем корзину
    db.clear_cart(message.from_user.id)

    # Сообщение пользователю
    await message.answer(
        f"✅ **Заказ #{order_id} успешно оформлен!**\n\n"
        f"💰 **Сумма заказа:** {cart['total']}₽\n"
        f"📱 **Ваш username:** {username}\n\n"
        f"⏳ **Продавец свяжется с вами в ближайшие 5 минут!**\n\n"
        f"Спасибо за покупку!",
        reply_markup=get_main_keyboard()
    )

    # Уведомление админам
    products_text = ""
    for item in cart['items']:
        products_text += f"{item['brand_name']} - {item['name']} x{item['quantity']} = {item['total']}₽\n"

    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"🔔 **НОВЫЙ ЗАКАЗ #{order_id}!**\n\n"
                f"👤 **Покупатель:** {message.from_user.full_name}\n"
                f"📱 **Username:** {username}\n"
                f"🆔 **User ID:** {message.from_user.id}\n"
                f"📦 **Товары:**\n{products_text}\n"
                f"💰 **ИТОГО:** {cart['total']}₽"
            )
        except Exception as e:
            logger.error(f"Ошибка при уведомлении админа {admin_id}: {e}")

    await state.clear()


# ===== ИНФОРМАЦИЯ =====

@router.message(F.text == "ℹ️ Информация для покупки")
async def info(message: Message):
    await message.answer(
        "📞 **Как купить:**\n\n"
        "1️⃣ Зайдите в **Каталог**\n"
        "2️⃣ Выберите бренд и товар\n"
        "3️⃣ Нажмите **Добавить в корзину**\n"
        "4️⃣ Зайдите в **Корзину**\n"
        "5️⃣ Нажмите **Сделать заказ**\n"
        "6️⃣ Введите свой Telegram username\n"
        "7️⃣ Ожидайте! Продавец свяжется с вами в ближайшие 5 минут\n\n"
        f"👤 **Продавец:** {SELLER_CONTACT}"
    )


# ===== НАВИГАЦИЯ =====

@router.callback_query(F.data == "back_to_brands")
async def back_to_brands(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()

    brands = db.get_all_brands()

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            "Выберите бренд:",
            reply_markup=get_brands_keyboard(brands)
        )
    else:
        try:
            await callback.message.edit_text(
                "Выберите бренд:",
                reply_markup=get_brands_keyboard(brands)
            )
        except TelegramBadRequest:
            await callback.message.delete()
            await callback.message.answer(
                "Выберите бренд:",
                reply_markup=get_brands_keyboard(brands)
            )


@router.callback_query(F.data == "back_to_products")
async def back_to_products(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()

    # Возвращаемся к брендам
    brands = db.get_all_brands()

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            "Выберите бренд:",
            reply_markup=get_brands_keyboard(brands)
        )
    else:
        try:
            await callback.message.edit_text(
                "Выберите бренд:",
                reply_markup=get_brands_keyboard(brands)
            )
        except TelegramBadRequest:
            await callback.message.delete()
            await callback.message.answer(
                "Выберите бренд:",
                reply_markup=get_brands_keyboard(brands)
            )


@router.callback_query(F.data == "back_to_cart")
async def back_to_cart(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()

    cart = db.get_cart(callback.from_user.id)

    if not cart['items']:
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(
                "🛒 **Корзина пуста**",
                reply_markup=get_main_keyboard()
            )
        else:
            try:
                await callback.message.edit_text(
                    "🛒 **Корзина пуста**",
                    reply_markup=get_main_keyboard()
                )
            except TelegramBadRequest:
                await callback.message.delete()
                await callback.message.answer(
                    "🛒 **Корзина пуста**",
                    reply_markup=get_main_keyboard()
                )
        return

    text = "🛒 **Ваша корзина:**\n\n"
    for i, item in enumerate(cart['items'], 1):
        text += f"{i}. **{item['brand_name']} - {item['name']}**\n"
        text += f"   👃 Вкус: {item['flavor']}\n"
        text += f"   💪 Крепость: {item['strength']} mg\n"
        text += f"   {item['quantity']} x {item['price']}₽ = {item['total']}₽\n\n"

    text += f"💰 **ИТОГО: {cart['total']}₽**"

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=get_cart_keyboard(cart['items']))
    else:
        try:
            await callback.message.edit_text(text, reply_markup=get_cart_keyboard(cart['items']))
        except TelegramBadRequest:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=get_cart_keyboard(cart['items']))


@router.message(F.text == "◀️ Назад")
async def back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Главное меню",
        reply_markup=get_main_keyboard()
    )