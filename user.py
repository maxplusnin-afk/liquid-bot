from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import Database
from keyboards import *
from config import SELLER_CONTACT
import logging
from aiogram.exceptions import TelegramBadRequest

router = Router()
db = Database()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Добро пожаловать, {message.from_user.first_name}!\n\n"
        "📋 Здесь вы можете посмотреть каталог товаров.",
        reply_markup=get_main_keyboard()
    )


# ===== КАТАЛОГ =====

@router.message(F.text == "📋 Каталог")
async def show_categories(message: Message, state: FSMContext):
    await state.clear()

    categories = db.get_all_categories()

    await message.answer(
        "Выберите категорию:",
        reply_markup=get_categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith('category_'))
async def show_products(callback: CallbackQuery):
    await callback.answer()

    category_id = int(callback.data.replace('category_', ''))
    products = db.get_products_by_category(category_id)

    if not products:
        await callback.message.edit_text(
            "❌ В этой категории пока нет товаров",
            reply_markup=get_categories_keyboard(db.get_all_categories())
        )
        return

    await callback.message.edit_text(
        "Выберите товар:",
        reply_markup=get_products_keyboard(products, category_id)
    )


@router.callback_query(F.data.startswith('product_'))
async def show_product(callback: CallbackQuery):
    await callback.answer()

    product_id = int(callback.data.replace('product_', ''))
    product = db.get_product(product_id)

    if not product:
        await callback.message.edit_text(
            "❌ Товар не найден",
            reply_markup=get_categories_keyboard(db.get_all_categories())
        )
        return

    text = (
        f"🍼 **{product['name']}**\n"
        f"👃 **Вкус:** {product['flavor']}\n"
        f"💪 **Крепость:** {product['strength']} мг\n\n"
        f"📞 **Для покупки напишите:** {SELLER_CONTACT}"
    )

    if product['photo_id']:
        if callback.message.photo:
            await callback.message.delete()
        await callback.message.answer_photo(
            photo=product['photo_id'],
            caption=text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад к товарам", callback_data=f"category_{product['category_id']}")]
            ])
        )
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад к товарам", callback_data=f"category_{product['category_id']}")]
        ])
        await callback.message.edit_text(text, reply_markup=keyboard)


# ===== ИНФОРМАЦИЯ =====

@router.message(F.text == "ℹ️ Информация для покупки")
async def info(message: Message):
    await message.answer(
        f"📞 **Как купить:**\n\n"
        f"1️⃣ Выберите товар в каталоге\n"
        f"2️⃣ Напишите продавцу: {SELLER_CONTACT}\n"
        f"3️⃣ Укажите название товара\n"
        f"4️⃣ Договоритесь о деталях\n\n"
        f"👤 **Продавец:** {SELLER_CONTACT}"
    )


# ===== НАВИГАЦИЯ =====

@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()

    categories = db.get_all_categories()

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            "Выберите категорию:",
            reply_markup=get_categories_keyboard(categories)
        )
    else:
        try:
            await callback.message.edit_text(
                "Выберите категорию:",
                reply_markup=get_categories_keyboard(categories)
            )
        except TelegramBadRequest:
            await callback.message.delete()
            await callback.message.answer(
                "Выберите категорию:",
                reply_markup=get_categories_keyboard(categories)
            )