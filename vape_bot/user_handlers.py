from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import Database
from keyboards import (
    get_user_keyboard,
    get_brands_keyboard,
    get_brand_liquids_keyboard,
    get_confirm_purchase_keyboard,
    get_back_to_catalog_keyboard
)
from config import OWNER_CONTACT, ADMIN_IDS
from states import PurchaseStates
import logging
from aiogram.exceptions import TelegramBadRequest

router = Router()
db = Database()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Стартовое сообщение"""
    try:
        await message.answer(
            f"👋 **Добро пожаловать, {message.from_user.first_name}!**\n\n"
            "🍼 Здесь вы можете посмотреть каталог электронных жидкостей по брендам.\n"
            "Для покупки выберите бренд, затем жидкость и нажмите кнопку 'Купить'.",
            reply_markup=get_user_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"Пользователь {message.from_user.id} запустил бота")
    except TelegramBadRequest as e:
        logger.error(f"Ошибка Telegram в cmd_start: {e}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка в cmd_start: {e}")


@router.message(F.text == "🍼 Каталог жидкостей")
async def show_brands(message: Message, state: FSMContext):
    """Показать список брендов"""
    try:
        await state.clear()
        logger.info(f"Пользователь {message.from_user.id} открыл каталог брендов")

        brands = db.get_all_brands()

        if not brands:
            await message.answer("📭 Каталог пуст. Скоро здесь появятся бренды!")
            return

        await message.answer(
            "🍼 **Выберите бренд:**",
            reply_markup=get_brands_keyboard(brands),
            parse_mode="Markdown"
        )
    except TelegramBadRequest as e:
        logger.error(f"Ошибка Telegram в show_brands: {e}")
        await message.answer("❌ Ошибка при загрузке каталога")
    except Exception as e:
        logger.error(f"Неожиданная ошибка в show_brands: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.callback_query(lambda c: c.data.startswith('brand_'))
async def show_brand_liquids(callback: CallbackQuery):
    """Показать жидкости выбранного бренда"""
    try:
        brand_id = int(callback.data.replace('brand_', ''))
        logger.info(f"Пользователь {callback.from_user.id} смотрит бренд ID {brand_id}")

        await callback.answer()

        brand = db.get_brand_by_id(brand_id)
        liquids = db.get_liquids_by_brand(brand_id)

        if not brand:
            await callback.message.edit_text("❌ Бренд не найден")
            return

        if not liquids:
            await callback.message.edit_text(f"❌ У бренда {brand['name']} пока нет жидкостей")
            return

        # Формируем текст со списком всех жидкостей бренда
        text = f"🏭 **{brand['name']}**\n\n"
        text += "**Доступные жидкости:**\n\n"

        for i, liquid in enumerate(liquids, 1):
            text += f"{i}. **{liquid['name']}**\n"
            text += f"   👃 Вкус: {liquid['flavor']}\n"
            text += f"   💪 Крепость: {liquid['strength']} mg\n"
            text += f"   💰 Цена: {liquid['price']}₽\n\n"

        # Отправляем одно фото бренда со списком жидкостей
        if callback.message.photo:
            await callback.message.delete()

        if brand['image_id']:
            await callback.message.answer_photo(
                photo=brand['image_id'],
                caption=text,
                reply_markup=get_brand_liquids_keyboard(liquids, brand_id),
                parse_mode="Markdown"
            )
        else:
            await callback.message.answer(
                text,
                reply_markup=get_brand_liquids_keyboard(liquids, brand_id),
                parse_mode="Markdown"
            )
    except ValueError:
        logger.error(f"Некорректный ID бренда: {callback.data}")
        await callback.message.edit_text("❌ Ошибка в ID бренда")
    except TelegramBadRequest as e:
        logger.error(f"Ошибка Telegram в show_brand_liquids: {e}")
        await callback.message.answer("❌ Ошибка при загрузке жидкостей")
    except Exception as e:
        logger.error(f"Неожиданная ошибка в show_brand_liquids: {e}")
        await callback.message.answer("❌ Произошла ошибка")


@router.callback_query(lambda c: c.data.startswith('buy_liquid_'))
async def start_purchase(callback: CallbackQuery, state: FSMContext):
    """Начать процесс покупки"""
    try:
        liquid_id = int(callback.data.replace('buy_liquid_', ''))
        logger.info(f"Пользователь {callback.from_user.id} нажал КУПИТЬ на товар ID {liquid_id}")

        await callback.answer()

        liquid = db.get_liquid_by_id(liquid_id)

        if not liquid:
            await callback.message.edit_text("❌ Товар не найден")
            return

        await state.update_data(
            liquid_id=liquid['id'],
            liquid_name=f"{liquid['brand_name']} - {liquid['name']} ({liquid['flavor']})",
            liquid_price=liquid['price']
        )

        await state.set_state(PurchaseStates.waiting_for_username)

        text = (
            f"📝 **Оформление покупки**\n\n"
            f"🏭 **Бренд:** {liquid['brand_name']}\n"
            f"🍼 **Товар:** {liquid['name']} - {liquid['flavor']}\n"
            f"💪 **Крепость:** {liquid['strength']} mg\n"
            f"💰 **Цена:** {liquid['price']}₽\n\n"
            f"✏️ Введите ваш Telegram username (например: @username):"
        )

        # Проверяем тип сообщения
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(
                text,
                reply_markup=get_back_to_catalog_keyboard(),
                parse_mode="Markdown"
            )
        else:
            try:
                await callback.message.edit_text(
                    text,
                    reply_markup=get_back_to_catalog_keyboard(),
                    parse_mode="Markdown"
                )
            except TelegramBadRequest:
                await callback.message.delete()
                await callback.message.answer(
                    text,
                    reply_markup=get_back_to_catalog_keyboard(),
                    parse_mode="Markdown"
                )
    except ValueError:
        logger.error(f"Некорректный ID товара: {callback.data}")
        await callback.message.edit_text("❌ Ошибка в ID товара")
    except TelegramBadRequest as e:
        logger.error(f"Ошибка Telegram в start_purchase: {e}")
        await callback.message.answer("❌ Ошибка при оформлении покупки")
    except Exception as e:
        logger.error(f"Неожиданная ошибка в start_purchase: {e}")
        await callback.message.answer("❌ Ошибка при оформлении покупки")


@router.message(PurchaseStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    """Обработка ввода username"""
    try:
        logger.info(f"Получен username: {message.text}")

        username = message.text.strip()

        if not username.startswith('@'):
            username = '@' + username

        await state.update_data(username=username)

        data = await state.get_data()

        text = (
            f"✅ **Проверьте данные:**\n\n"
            f"🍼 **Товар:** {data['liquid_name']}\n"
            f"💰 **Цена:** {data['liquid_price']}₽\n"
            f"📱 **Ваш username:** {username}\n\n"
            f"📞 **Продавец:** {OWNER_CONTACT}\n\n"
            f"Всё верно?"
        )

        await message.answer(
            text,
            reply_markup=get_confirm_purchase_keyboard(data['liquid_id']),
            parse_mode="Markdown"
        )

        await state.set_state(PurchaseStates.confirm_purchase)

    except TelegramBadRequest as e:
        logger.error(f"Ошибка Telegram в process_username: {e}")
        await message.answer("❌ Ошибка при обработке username")
    except Exception as e:
        logger.error(f"Неожиданная ошибка в process_username: {e}")
        await message.answer("❌ Ошибка при обработке username")


@router.callback_query(lambda c: c.data.startswith('confirm_buy_'))
async def confirm_purchase(callback: CallbackQuery, state: FSMContext):
    """Подтверждение покупки"""
    try:
        liquid_id = int(callback.data.replace('confirm_buy_', ''))
        logger.info(f"Пользователь {callback.from_user.id} подтвердил покупку товара ID {liquid_id}")

        await callback.answer()

        data = await state.get_data()

        if not data or 'liquid_id' not in data:
            await callback.message.edit_text("❌ Данные покупки не найдены. Начните заново.")
            await state.clear()
            return

        request_id = db.create_purchase_request(
            user_id=callback.from_user.id,
            user_name=callback.from_user.full_name,
            username=data.get('username', 'не указан'),
            liquid_id=data['liquid_id'],
            liquid_name=data['liquid_name'],
            price=data['liquid_price']
        )

        if request_id:
            logger.info(f"Заявка #{request_id} создана успешно")

            await callback.message.edit_text(
                f"✅ **Заявка на покупку отправлена!**\n\n"
                f"Номер заявки: #{request_id}\n"
                f"Товар: {data['liquid_name']}\n"
                f"Цена: {data['liquid_price']}₽\n"
                f"Ваш username: {data.get('username', 'не указан')}\n\n"
                f"📞 Продавец свяжется с вами в ближайшее время!\n\n"
                f"Спасибо за покупку!",
                parse_mode="Markdown"
            )

            for admin_id in ADMIN_IDS:
                try:
                    await callback.bot.send_message(
                        admin_id,
                        f"🔔 **Новая заявка на покупку!**\n\n"
                        f"📋 **Заявка #{request_id}**\n"
                        f"👤 **Покупатель:** {callback.from_user.full_name}\n"
                        f"📱 **Username:** {data.get('username', 'не указан')}\n"
                        f"🆔 **User ID:** `{callback.from_user.id}`\n"
                        f"🍼 **Товар:** {data['liquid_name']}\n"
                        f"💰 **Цена:** {data['liquid_price']}₽",
                        parse_mode="Markdown"
                    )
                except TelegramBadRequest as e:
                    logger.error(f"Ошибка Telegram при уведомлении админа {admin_id}: {e}")
                except Exception as e:
                    logger.error(f"Неожиданная ошибка при уведомлении админа {admin_id}: {e}")
        else:
            await callback.message.edit_text("❌ Ошибка при создании заявки")

        await state.clear()

    except ValueError:
        logger.error(f"Некорректный ID заявки: {callback.data}")
        await callback.message.edit_text("❌ Ошибка в ID заявки")
        await state.clear()
    except TelegramBadRequest as e:
        logger.error(f"Ошибка Telegram в confirm_purchase: {e}")
        await callback.message.edit_text("❌ Ошибка при подтверждении покупки")
        await state.clear()
    except Exception as e:
        logger.error(f"Неожиданная ошибка в confirm_purchase: {e}")
        await callback.message.edit_text("❌ Ошибка при подтверждении покупки")
        await state.clear()


@router.callback_query(lambda c: c.data.startswith('cancel_buy_'))
async def cancel_purchase(callback: CallbackQuery, state: FSMContext):
    """Отмена покупки"""
    try:
        logger.info(f"Пользователь {callback.from_user.id} отменил покупку")
        await callback.answer()
        await state.clear()

        brands = db.get_all_brands()

        if not brands:
            await callback.message.edit_text("📭 Каталог пуст")
            return

        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(
                "🍼 **Выберите бренд:**",
                reply_markup=get_brands_keyboard(brands),
                parse_mode="Markdown"
            )
        else:
            try:
                await callback.message.edit_text(
                    "🍼 **Выберите бренд:**",
                    reply_markup=get_brands_keyboard(brands),
                    parse_mode="Markdown"
                )
            except TelegramBadRequest:
                await callback.message.delete()
                await callback.message.answer(
                    "🍼 **Выберите бренд:**",
                    reply_markup=get_brands_keyboard(brands),
                    parse_mode="Markdown"
                )
    except TelegramBadRequest as e:
        logger.error(f"Ошибка Telegram в cancel_purchase: {e}")
        await callback.message.answer("❌ Ошибка при отмене")
    except Exception as e:
        logger.error(f"Неожиданная ошибка в cancel_purchase: {e}")
        await callback.message.answer("❌ Ошибка")


@router.message(F.text == "📞 Информация для покупки")
async def purchase_info(message: Message):
    """Информация для покупки"""
    try:
        await message.answer(
            "📞 **Как купить:**\n\n"
            f"👤 **Продавец:** {OWNER_CONTACT}\n\n"
            "1️⃣ Выберите бренд в каталоге\n"
            "2️⃣ Посмотрите список жидкостей\n"
            "3️⃣ Нажмите кнопку 'Купить' под нужной жидкостью\n"
            "4️⃣ Введите ваш Telegram username\n"
            "5️⃣ Подтвердите заказ\n\n"
            "После этого продавец свяжется с вами!",
            parse_mode="Markdown"
        )
    except TelegramBadRequest as e:
        logger.error(f"Ошибка Telegram в purchase_info: {e}")
        await message.answer("❌ Ошибка при отправке информации")
    except Exception as e:
        logger.error(f"Неожиданная ошибка в purchase_info: {e}")
        await message.answer("❌ Произошла ошибка")


@router.message(F.text == "🏠 Главное меню")
async def back_to_main(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    try:
        await state.clear()
        logger.info(f"Пользователь {message.from_user.id} вернулся в главное меню")

        await message.answer(
            "🏠 **Главное меню**\n\n"
            "Выберите раздел:",
            reply_markup=get_user_keyboard(),
            parse_mode="Markdown"
        )
    except TelegramBadRequest as e:
        logger.error(f"Ошибка Telegram в back_to_main: {e}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка в back_to_main: {e}")


@router.callback_query(F.data == "back_to_brands")
async def back_to_brands(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку брендов"""
    try:
        await callback.answer()
        await state.clear()
        logger.info(f"Пользователь {callback.from_user.id} вернулся к брендам")

        brands = db.get_all_brands()

        if not brands:
            await callback.message.edit_text("📭 Каталог пуст")
            return

        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(
                "🍼 **Выберите бренд:**",
                reply_markup=get_brands_keyboard(brands),
                parse_mode="Markdown"
            )
        else:
            try:
                await callback.message.edit_text(
                    "🍼 **Выберите бренд:**",
                    reply_markup=get_brands_keyboard(brands),
                    parse_mode="Markdown"
                )
            except TelegramBadRequest:
                await callback.message.delete()
                await callback.message.answer(
                    "🍼 **Выберите бренд:**",
                    reply_markup=get_brands_keyboard(brands),
                    parse_mode="Markdown"
                )
    except TelegramBadRequest as e:
        logger.error(f"Ошибка Telegram в back_to_brands: {e}")
        await callback.message.answer("❌ Ошибка при загрузке брендов")
    except Exception as e:
        logger.error(f"Неожиданная ошибка в back_to_brands: {e}")
        await callback.message.answer("❌ Произошла ошибка")