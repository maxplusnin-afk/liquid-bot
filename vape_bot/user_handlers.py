from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import Database
from keyboards import (
    get_user_keyboard,
    get_liquids_keyboard,
    get_back_to_catalog_keyboard
)
from config import OWNER_CONTACT
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
            "Для покупки свяжитесь с продавцом по кнопке ниже.",
            reply_markup=get_user_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в cmd_start: {e}")


@router.message(F.text == "🍼 Каталог жидкостей")
async def show_catalog(message: Message, state: FSMContext):
    """Показать каталог жидкостей"""
    try:
        # Очищаем состояние при входе в каталог
        await state.clear()

        liquids = db.get_all_liquids()

        if not liquids:
            await message.answer("📭 Каталог пуст. Скоро здесь появятся жидкости!")
            return

        await message.answer(
            "🍼 **Каталог жидкостей:**\n\n"
            "Нажмите на интересующую позицию:",
            reply_markup=get_liquids_keyboard(liquids),
            parse_mode="Markdown"
        )
    except TelegramBadRequest as e:
        logger.error(f"Ошибка Telegram в show_catalog: {e}")
        await message.answer("❌ Ошибка при загрузке каталога")
    except TelegramForbiddenError as e:
        logger.error(f"Ошибка доступа в show_catalog: {e}")
    except Exception as unexpected_error:
        logger.error(f"Неожиданная ошибка в show_catalog: {unexpected_error}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


@router.callback_query(lambda c: c.data.startswith('liquid_'))
async def show_liquid_details(callback: CallbackQuery):
    """Показать детали жидкости"""
    try:
        await callback.answer()

        liquid_id = int(callback.data.replace('liquid_', ''))
        liquid = db.get_liquid_by_id(liquid_id)

        if not liquid:
            await callback.message.edit_text("❌ Жидкость не найдена")
            return

        text = (
            f"🍼 **{liquid['name']}**\n\n"
            f"👃 **Вкус:** {liquid['flavor']}\n"
            f"💪 **Крепость:** {liquid['strength']} mg\n"
            f"🧪 **Объем:** {liquid['volume']} ml\n\n"
            f"📞 **Для покупки напишите:** {OWNER_CONTACT}"
        )

        if liquid['image_id']:
            # Удаляем предыдущее сообщение с каталогом
            await callback.message.delete()
            # Отправляем новое сообщение с фото
            await callback.message.answer_photo(
                photo=liquid['image_id'],
                caption=text,
                reply_markup=get_back_to_catalog_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(
                text,
                reply_markup=get_back_to_catalog_keyboard(),
                parse_mode="Markdown"
            )
    except TelegramBadRequest as e:
        logger.error(f"Ошибка Telegram в show_liquid_details: {e}")
        await callback.message.edit_text("❌ Ошибка при загрузке информации")
    except TelegramForbiddenError as e:
        logger.error(f"Ошибка доступа в show_liquid_details: {e}")
    except Exception as unexpected_error:
        logger.error(f"Неожиданная ошибка в show_liquid_details: {unexpected_error}")
        await callback.message.edit_text("❌ Произошла ошибка")


@router.message(F.text == "📞 Информация для покупки")
async def purchase_info(message: Message):
    """Информация для покупки"""
    try:
        text = (
            "📞 **Как купить:**\n\n"
            f"👤 **Продавец:** {OWNER_CONTACT}\n\n"
            "1️⃣ Выберите жидкость в каталоге\n"
            "2️⃣ Напишите продавцу с названием товара\n"
            "3️⃣ Договоритесь о доставке и оплате\n\n"
            "По всем вопросам обращайтесь к продавцу!"
        )
        await message.answer(text, parse_mode="Markdown")
    except TelegramBadRequest as e:
        logger.error(f"Ошибка Telegram в purchase_info: {e}")
        await message.answer("❌ Ошибка при отправке информации")
    except TelegramForbiddenError as e:
        logger.error(f"Ошибка доступа в purchase_info: {e}")
    except Exception as unexpected_error:
        logger.error(f"Неожиданная ошибка в purchase_info: {unexpected_error}")
        await message.answer("❌ Произошла ошибка")


@router.message(F.text == "🏠 Главное меню")
async def back_to_main(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    try:
        # Очищаем состояние
        await state.clear()

        # Отправляем новое сообщение с главным меню
        await message.answer(
            "🏠 **Главное меню**\n\n"
            "Выберите раздел:",
            reply_markup=get_user_keyboard(),
            parse_mode="Markdown"
        )
    except TelegramBadRequest as e:
        logger.error(f"Ошибка Telegram в back_to_main: {e}")
    except TelegramForbiddenError as e:
        logger.error(f"Ошибка доступа в back_to_main: {e}")
    except Exception as unexpected_error:
        logger.error(f"Неожиданная ошибка в back_to_main: {unexpected_error}")


@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery):
    """Возврат к каталогу"""
    try:
        await callback.answer()

        liquids = db.get_all_liquids()

        if not liquids:
            await callback.message.edit_text("📭 Каталог пуст")
            return

        # Если текущее сообщение - фото, удаляем его
        try:
            await callback.message.delete()
        except (TelegramBadRequest, TelegramForbiddenError):
            pass  # Игнорируем ошибку удаления

        # Отправляем новое сообщение с каталогом
        await callback.message.answer(
            "🍼 **Каталог жидкостей:**\n\n"
            "Нажмите на интересующую позицию:",
            reply_markup=get_liquids_keyboard(liquids),
            parse_mode="Markdown"
        )
    except TelegramBadRequest as e:
        logger.error(f"Ошибка Telegram в back_to_catalog: {e}")
        await callback.message.answer("❌ Ошибка при загрузке каталога")
    except TelegramForbiddenError as e:
        logger.error(f"Ошибка доступа в back_to_catalog: {e}")
    except Exception as unexpected_error:
        logger.error(f"Неожиданная ошибка в back_to_catalog: {unexpected_error}")
        try:
            await callback.message.answer("❌ Произошла ошибка")
        except:
            pass