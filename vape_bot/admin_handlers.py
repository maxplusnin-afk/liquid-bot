from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, \
    InlineKeyboardButton  # Добавлены недостающие импорты
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import ADMIN_IDS  # Убрал OWNER_CONTACT, так как он не используется
from database import Database
from keyboards import (
    get_admin_keyboard,
    get_user_keyboard,
    get_cancel_keyboard,
    get_admin_liquids_keyboard
    # Убрал неиспользуемый get_back_to_admin_keyboard
)
from states import LiquidStates
import logging
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

router = Router()
db = Database()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Проверка на админа"""
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Вход в админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещен")
        return

    await message.answer(
        "🔐 **Панель администратора**\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
    )


@router.message(F.text == "📦 Добавить жидкость")
async def add_liquid_start(message: Message, state: FSMContext):
    """Начало добавления жидкости"""
    if not is_admin(message.from_user.id):
        return

    await state.set_state(LiquidStates.name)
    await message.answer(
        "📝 Введите **название** жидкости:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )


@router.message(LiquidStates.name)
async def process_name(message: Message, state: FSMContext):
    """Обработка названия"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено", reply_markup=get_admin_keyboard())
        return

    await state.update_data(name=message.text)
    await state.set_state(LiquidStates.flavor)
    await message.answer("👃 Введите **вкус**:", parse_mode="Markdown")


@router.message(LiquidStates.flavor)
async def process_flavor(message: Message, state: FSMContext):
    """Обработка вкуса"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено", reply_markup=get_admin_keyboard())
        return

    await state.update_data(flavor=message.text)
    await state.set_state(LiquidStates.strength)
    await message.answer("💪 Введите **крепость** (в mg):", parse_mode="Markdown")


@router.message(LiquidStates.strength)
async def process_strength(message: Message, state: FSMContext):
    """Обработка крепости"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено", reply_markup=get_admin_keyboard())
        return

    await state.update_data(strength=message.text)
    await state.set_state(LiquidStates.volume)
    await message.answer("🧪 Введите **объем** (в ml):", parse_mode="Markdown")


@router.message(LiquidStates.volume)
async def process_volume(message: Message, state: FSMContext):
    """Обработка объема"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено", reply_markup=get_admin_keyboard())
        return

    await state.update_data(volume=message.text)
    await state.set_state(LiquidStates.price)
    await message.answer("💰 Введите **цену** (в рублях):", parse_mode="Markdown")


@router.message(LiquidStates.price)
async def process_price(message: Message, state: FSMContext):
    """Обработка цены"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено", reply_markup=get_admin_keyboard())
        return

    try:
        price = int(message.text)
        if price <= 0:
            await message.answer("❌ Цена должна быть больше 0")
            return
        await state.update_data(price=price)
        await state.set_state(LiquidStates.image)
        await message.answer("🖼 Отправьте **фото** жидкости (или отправьте 'нет'):", parse_mode="Markdown")
    except ValueError:
        await message.answer("❌ Введите корректное число")


@router.message(LiquidStates.image)
async def process_image(message: Message, state: FSMContext):
    """Обработка изображения"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено", reply_markup=get_admin_keyboard())
        return

    image_id_value = ""
    if message.photo:
        image_id_value = message.photo[-1].file_id
    elif message.text and message.text.lower() == 'нет':
        image_id_value = ""
    else:
        await message.answer("❌ Отправьте фото или напишите 'нет'")
        return

    data = await state.get_data()

    # Сохраняем жидкость с ценой - ИСПОЛЬЗУЕМ image_id_value
    liquid_id = db.add_liquid(
        name=data['name'],
        flavor=data['flavor'],
        strength=data['strength'],
        volume=data['volume'],
        price=data['price'],
        image_id=image_id_value  # Переменная ИСПОЛЬЗУЕТСЯ здесь
    )

    if liquid_id:
        await message.answer(
            f"✅ **Жидкость успешно добавлена!**\n\n"
            f"🆔 ID: {liquid_id}\n"
            f"🏷 Название: {data['name']}\n"
            f"👃 Вкус: {data['flavor']}\n"
            f"💪 Крепость: {data['strength']} mg\n"
            f"🧪 Объем: {data['volume']} ml\n"
            f"💰 Цена: {data['price']}₽",
            reply_markup=get_admin_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "❌ Ошибка при добавлении жидкости",
            reply_markup=get_admin_keyboard()
        )

    await state.clear()


@router.message(F.text == "📋 Список жидкостей")
async def list_liquids(message: Message):
    """Просмотр всех жидкостей (админ)"""
    if not is_admin(message.from_user.id):
        return

    liquids = db.get_all_liquids()

    if not liquids:
        await message.answer("📭 Жидкостей пока нет")
        return

    await message.answer(f"📋 **Всего жидкостей: {len(liquids)}**", parse_mode="Markdown")

    for liquid in liquids:
        text = (
            f"🆔 **ID:** {liquid['id']}\n"
            f"🏷 **Название:** {liquid['name']}\n"
            f"👃 **Вкус:** {liquid['flavor']}\n"
            f"💪 **Крепость:** {liquid['strength']} mg\n"
            f"🧪 **Объем:** {liquid['volume']} ml\n"
            f"💰 **Цена:** {liquid['price']}₽\n"
        )

        if liquid['created_at']:
            text += f"📅 **Добавлен:** {liquid['created_at'][:16]}\n"

        try:
            if liquid['image_id']:
                await message.answer_photo(
                    photo=liquid['image_id'],
                    caption=text,
                    parse_mode="Markdown"
                )
            else:
                await message.answer(text, parse_mode="Markdown")
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.error(f"Ошибка отправки жидкости {liquid['id']}: {e}")
            await message.answer(text + "\n❌ Ошибка загрузки изображения", parse_mode="Markdown")


@router.message(F.text == "📊 Заявки на покупку")
async def show_purchase_requests(message: Message):
    """Показать заявки на покупку (админ)"""
    if not is_admin(message.from_user.id):
        return

    requests = db.get_purchase_requests()

    if not requests:
        await message.answer("📭 Заявок на покупку пока нет")
        return

    for req in requests[:10]:  # Показываем последние 10
        status_emoji = "⏳" if req['status'] == 'pending' else "✅"
        username_display = f"@{req['username']}" if req['username'] else "не указан"

        text = (
            f"{status_emoji} **Заявка #{req['id']}**\n"
            f"👤 **Пользователь:** {req['user_name']}\n"
            f"📱 **Username:** {username_display}\n"
            f"🍼 **Товар:** {req['liquid_name']}\n"
            f"💰 **Цена:** {req['price']}₽\n"
            f"📅 **Дата:** {req['created_at'][:16]}\n"
            f"📊 **Статус:** {'Ожидает' if req['status'] == 'pending' else 'Обработана'}"
        )

        # Добавляем кнопки для админа - ИСПОЛЬЗУЕМ импортированные классы
        if req['status'] == 'pending':
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Отметить как обработано", callback_data=f"mark_done_{req['id']}")]
                ]
            )
            await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.answer(text, parse_mode="Markdown")


@router.callback_query(lambda c: c.data.startswith('mark_done_'))
async def mark_request_done(callback: CallbackQuery):
    """Отметить заявку как обработанную"""
    await callback.answer()

    if not is_admin(callback.from_user.id):
        await callback.message.edit_text("⛔ Доступ запрещен")
        return

    try:
        request_id = int(callback.data.replace('mark_done_', ''))

        if db.update_request_status(request_id, 'completed'):
            await callback.message.edit_text(
                callback.message.text.replace('⏳', '✅') + "\n\n✅ Заявка обработана!"
            )
        else:
            await callback.message.edit_text("❌ Ошибка при обновлении статуса")
    except Exception as e:
        logger.error(f"Ошибка при обработке заявки: {e}")
        await callback.message.edit_text("❌ Ошибка")


@router.message(F.text == "🗑 Удалить жидкость")
async def delete_liquid_menu(message: Message):
    """Меню удаления жидкости"""
    if not is_admin(message.from_user.id):
        return

    liquids = db.get_all_liquids()

    if not liquids:
        await message.answer("📭 Нет жидкостей для удаления")
        return

    await message.answer(
        "Выберите жидкость для удаления:",
        reply_markup=get_admin_liquids_keyboard(liquids)
    )


@router.callback_query(lambda c: c.data.startswith('admin_delete_'))
async def delete_liquid(callback: CallbackQuery):
    """Удаление жидкости"""
    await callback.answer()

    if not is_admin(callback.from_user.id):
        await callback.message.edit_text("⛔ Доступ запрещен")
        return

    try:
        liquid_id = int(callback.data.replace('admin_delete_', ''))

        if db.delete_liquid(liquid_id):
            await callback.message.edit_text(f"✅ Жидкость #{liquid_id} успешно удалена")
        else:
            await callback.message.edit_text(f"❌ Ошибка при удалении жидкости #{liquid_id}")
    except ValueError:
        await callback.message.edit_text("❌ Некорректный ID")
    except Exception as e:
        logger.error(f"Ошибка удаления жидкости: {e}")
        await callback.message.edit_text("❌ Ошибка при удалении")


@router.callback_query(F.data == "back_to_admin_menu")
async def back_to_admin_menu(callback: CallbackQuery):
    """Возврат в админ-меню"""
    await callback.answer()

    if not is_admin(callback.from_user.id):
        await callback.message.edit_text("⛔ Доступ запрещен")
        return

    await callback.message.delete()
    await callback.message.answer(
        "🔐 **Панель администратора**\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
    )


@router.message(F.text == "🏠 Главное меню")
async def back_to_main(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()

    if is_admin(message.from_user.id):
        await message.answer(
            "🏠 **Главное меню**\n\n"
            "Выберите раздел:",
            reply_markup=get_admin_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "🏠 **Главное меню**\n\n"
            "Выберите раздел:",
            reply_markup=get_user_keyboard(),
            parse_mode="Markdown"
        )