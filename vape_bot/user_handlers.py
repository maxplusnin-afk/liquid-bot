from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import Database
from keyboards import (
    get_user_keyboard,
    get_liquids_keyboard,
    get_liquid_action_keyboard,
    get_confirm_purchase_keyboard,
    get_back_to_catalog_keyboard
)
from config import OWNER_CONTACT, ADMIN_IDS
from states import PurchaseStates
import logging
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

router = Router()
db = Database()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Стартовое сообщение"""
    try:
        await message.answer(
            f"👋 **Добро пожаловать, {message.from_user.first_name}!**\n\n"
            "🍼 Здесь вы можете посмотреть каталог электронных жидкостей.\n"
            "Для покупки нажмите кнопку 'Купить' под интересующим товаром.",
            reply_markup=get_user_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"Пользователь {message.from_user.id} запустил бота")
    except Exception as e:
        logger.error(f"Ошибка в cmd_start: {e}")


@router.message(F.text == "🍼 Каталог жидкостей")
async def show_catalog(message: Message, state: FSMContext):
    """Показать каталог жидкостей"""
    try:
        await state.clear()
        logger.info(f"Пользователь {message.from_user.id} открыл каталог")

        liquids = db.get_all_liquids()

        if not liquids:
            await message.answer("📭 Каталог пуст. Скоро здесь появятся жидкости!")
            return

        await message.answer(
            "🍼 **Каталог жидкостей:**\n\n"
            "Нажмите на интересующую позицию для просмотра деталей:",
            reply_markup=get_liquids_keyboard(liquids),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в show_catalog: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.callback_query(lambda c: c.data.startswith('liquid_'))
async def show_liquid_details(callback: CallbackQuery):
    """Показать детали жидкости"""
    try:
        liquid_id = int(callback.data.replace('liquid_', ''))
        logger.info(f"Пользователь {callback.from_user.id} смотрит жидкость ID {liquid_id}")

        await callback.answer()

        liquid = db.get_liquid_by_id(liquid_id)

        if not liquid:
            await callback.message.edit_text("❌ Жидкость не найдена")
            return

        text = (
            f"🍼 **{liquid['name']}**\n\n"
            f"👃 **Вкус:** {liquid['flavor']}\n"
            f"💪 **Крепость:** {liquid['strength']} mg\n"
            f"🧪 **Объем:** {liquid['volume']} ml\n"
            f"💰 **Цена:** {liquid['price']}₽\n\n"
            f"📞 **Продавец:** {OWNER_CONTACT}"
        )

        if liquid['image_id']:
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=liquid['image_id'],
                caption=text,
                reply_markup=get_liquid_action_keyboard(liquid['id']),
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(
                text,
                reply_markup=get_liquid_action_keyboard(liquid['id']),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Ошибка в show_liquid_details: {e}")
        await callback.message.edit_text("❌ Произошла ошибка")


@router.callback_query(lambda c: c.data.startswith('buy_'))
async def start_purchase(callback: CallbackQuery, state: FSMContext):
    """Начать процесс покупки"""
    try:
        liquid_id = int(callback.data.replace('buy_', ''))
        logger.info(f"Пользователь {callback.from_user.id} нажал КУПИТЬ на товар ID {liquid_id}")

        await callback.answer()

        liquid = db.get_liquid_by_id(liquid_id)

        if not liquid:
            await callback.message.edit_text("❌ Товар не найден")
            return

        await state.update_data(
            liquid_id=liquid['id'],
            liquid_name=liquid['name'],
            liquid_price=liquid['price']
        )

        await state.set_state(PurchaseStates.waiting_for_username)

        await callback.message.edit_text(
            f"📝 **Оформление покупки**\n\n"
            f"Товар: {liquid['name']}\n"
            f"Цена: {liquid['price']}₽\n\n"
            f"✏️ Введите ваш Telegram username (например: @username):",
            reply_markup=get_back_to_catalog_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в start_purchase: {e}")
        await callback.message.edit_text("❌ Ошибка при оформлении покупки")


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

    except Exception as e:
        logger.error(f"Ошибка в process_username: {e}")
        await message.answer("❌ Ошибка при обработке username")


@router.callback_query(lambda c: c.data.startswith('confirm_buy_'))
async def confirm_purchase(callback: CallbackQuery, state: FSMContext):
    """Подтверждение покупки"""
    try:
        liquid_id = int(callback.data.replace('confirm_buy_', ''))
        logger.info(f"Пользователь {callback.from_user.id} подтвердил покупку товара ID {liquid_id}")

        await callback.answer()

        data = await state.get_data()

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
                except Exception as e:
                    logger.error(f"Ошибка при уведомлении админа {admin_id}: {e}")
        else:
            await callback.message.edit_text("❌ Ошибка при создании заявки")

        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка в confirm_purchase: {e}")
        await callback.message.edit_text("❌ Ошибка при подтверждении покупки")
        await state.clear()


@router.callback_query(lambda c: c.data.startswith('cancel_buy_'))
async def cancel_purchase(callback: CallbackQuery, state: FSMContext):
    """Отмена покупки"""
    try:
        logger.info(f"Пользователь {callback.from_user.id} отменил покупку")
        await callback.answer()
        await state.clear()

        liquids = db.get_all_liquids()

        if liquids:
            await callback.message.edit_text(
                "🍼 **Каталог жидкостей:**\n\n"
                "Нажмите на интересующую позицию:",
                reply_markup=get_liquids_keyboard(liquids),
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text("📭 Каталог пуст")

    except Exception as e:
        logger.error(f"Ошибка в cancel_purchase: {e}")
        await callback.message.edit_text("❌ Ошибка")


@router.message(F.text == "📞 Информация для покупки")
async def purchase_info(message: Message):
    """Информация для покупки"""
    try:
        await message.answer(
            "📞 **Как купить:**\n\n"
            f"👤 **Продавец:** {OWNER_CONTACT}\n\n"
            "1️⃣ Выберите жидкость в каталоге\n"
            "2️⃣ Нажмите кнопку 'Купить'\n"
            "3️⃣ Введите ваш Telegram username\n"
            "4️⃣ Подтвердите заказ\n\n"
            "После этого продавец свяжется с вами!",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в purchase_info: {e}")


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
    except Exception as e:
        logger.error(f"Ошибка в back_to_main: {e}")


@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery, state: FSMContext):
    """Возврат к каталогу"""
    try:
        await callback.answer()
        await state.clear()
        logger.info(f"Пользователь {callback.from_user.id} вернулся в каталог")

        liquids = db.get_all_liquids()

        if not liquids:
            await callback.message.edit_text("📭 Каталог пуст")
            return

        try:
            await callback.message.delete()
        except:
            pass

        await callback.message.answer(
            "🍼 **Каталог жидкостей:**\n\n"
            "Нажмите на интересующую позицию:",
            reply_markup=get_liquids_keyboard(liquids),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в back_to_catalog: {e}")