from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import ADMIN_IDS
from database import Database
from keyboards import (
    get_admin_keyboard,
    get_user_keyboard,
    get_cancel_keyboard,
    get_admin_brands_keyboard,
    get_back_to_admin_keyboard
)
from states import BrandStates, LiquidStates
import logging
from aiogram.exceptions import TelegramBadRequest

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


# ========== УПРАВЛЕНИЕ БРЕНДАМИ ==========

@router.message(F.text == "🏭 Добавить бренд")
async def add_brand_start(message: Message, state: FSMContext):
    """Начало добавления бренда"""
    if not is_admin(message.from_user.id):
        return

    await state.set_state(BrandStates.name)
    await message.answer(
        "📝 Введите **название** бренда:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )


@router.message(BrandStates.name)
async def process_brand_name(message: Message, state: FSMContext):
    """Обработка названия бренда"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено", reply_markup=get_admin_keyboard())
        return

    await state.update_data(name=message.text)
    await state.set_state(BrandStates.image)
    await message.answer(
        "🖼 Отправьте **фото** для бренда (одно фото для всех жидкостей этого бренда):",
        parse_mode="Markdown"
    )


@router.message(BrandStates.image)
async def process_brand_image(message: Message, state: FSMContext):
    """Обработка изображения бренда"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено", reply_markup=get_admin_keyboard())
        return

    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фото для бренда")
        return

    image_id = message.photo[-1].file_id
    data = await state.get_data()

    brand_id = db.add_brand(
        name=data['name'],
        image_id=image_id
    )

    if brand_id:
        await message.answer_photo(
            photo=image_id,
            caption=f"✅ **Бренд успешно добавлен!**\n\n🏭 **Название:** {data['name']}",
            reply_markup=get_admin_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "❌ Ошибка при добавлении бренда (возможно, такое название уже существует)",
            reply_markup=get_admin_keyboard()
        )

    await state.clear()


@router.message(F.text == "📋 Список брендов")
async def list_brands(message: Message):
    """Просмотр всех брендов (админ)"""
    if not is_admin(message.from_user.id):
        return

    brands = db.get_all_brands()

    if not brands:
        await message.answer("📭 Брендов пока нет")
        return

    await message.answer(f"📋 **Всего брендов: {len(brands)}**", parse_mode="Markdown")

    for brand in brands:
        liquids = db.get_liquids_by_brand(brand['id'])
        text = (
            f"🏭 **ID:** {brand['id']}\n"
            f"🏷 **Название:** {brand['name']}\n"
            f"🍼 **Количество жидкостей:** {len(liquids)}\n"
        )

        if liquids:
            text += "\n**Жидкости:**\n"
            for liquid in liquids:
                text += f"• {liquid['name']} - {liquid['flavor']} ({liquid['strength']} mg) - {liquid['price']}₽\n"

        try:
            if brand['image_id']:
                await message.answer_photo(
                    photo=brand['image_id'],
                    caption=text,
                    parse_mode="Markdown"
                )
            else:
                await message.answer(text, parse_mode="Markdown")
        except TelegramBadRequest as e:
            logger.error(f"Ошибка отправки бренда {brand['id']}: {e}")
            await message.answer(text + "\n❌ Ошибка загрузки изображения", parse_mode="Markdown")


@router.message(F.text == "🗑 Удалить бренд")
async def delete_brand_menu(message: Message):
    """Меню удаления бренда"""
    if not is_admin(message.from_user.id):
        return

    brands = db.get_all_brands()

    if not brands:
        await message.answer("📭 Нет брендов для удаления")
        return

    await message.answer(
        "Выберите бренд для удаления (все его жидкости будут удалены):",
        reply_markup=get_admin_brands_keyboard(brands)
    )


@router.callback_query(lambda c: c.data.startswith('admin_delete_brand_'))
async def delete_brand(callback: CallbackQuery):
    """Удаление бренда"""
    await callback.answer()

    if not is_admin(callback.from_user.id):
        await callback.message.edit_text("⛔ Доступ запрещен")
        return

    try:
        brand_id = int(callback.data.replace('admin_delete_brand_', ''))

        if db.delete_brand(brand_id):
            await callback.message.edit_text(f"✅ Бренд #{brand_id} и все его жидкости успешно удалены")
        else:
            await callback.message.edit_text(f"❌ Ошибка при удалении бренда #{brand_id}")
    except ValueError:
        await callback.message.edit_text("❌ Некорректный ID")
    except Exception as e:
        logger.error(f"Ошибка удаления бренда: {e}")
        await callback.message.edit_text("❌ Ошибка при удалении")


# ========== УПРАВЛЕНИЕ ЖИДКОСТЯМИ ==========

@router.message(F.text == "🍼 Добавить жидкость")
async def add_liquid_start(message: Message, state: FSMContext):
    """Начало добавления жидкости"""
    if not is_admin(message.from_user.id):
        return

    brands = db.get_all_brands()

    if not brands:
        await message.answer(
            "❌ Сначала добавьте бренд!",
            reply_markup=get_admin_keyboard()
        )
        return

    # Создаем клавиатуру с брендами
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🏭 {brand['name']}", callback_data=f"select_brand_{brand['id']}")]
            for brand in brands
        ]
    )

    await message.answer(
        "Выберите бренд для жидкости:",
        reply_markup=keyboard
    )
    await state.set_state(LiquidStates.brand_id)


@router.callback_query(lambda c: c.data.startswith('select_brand_'))
async def process_brand_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора бренда"""
    await callback.answer()

    brand_id = int(callback.data.replace('select_brand_', ''))
    await state.update_data(brand_id=brand_id)
    await state.set_state(LiquidStates.name)

    await callback.message.delete()
    await callback.message.answer(
        "📝 Введите **название** жидкости:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )


@router.message(LiquidStates.name)
async def process_liquid_name(message: Message, state: FSMContext):
    """Обработка названия жидкости"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено", reply_markup=get_admin_keyboard())
        return

    await state.update_data(name=message.text)
    await state.set_state(LiquidStates.flavor)
    await message.answer("👃 Введите **вкус**:", parse_mode="Markdown")


@router.message(LiquidStates.flavor)
async def process_liquid_flavor(message: Message, state: FSMContext):
    """Обработка вкуса"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено", reply_markup=get_admin_keyboard())
        return

    await state.update_data(flavor=message.text)
    await state.set_state(LiquidStates.strength)
    await message.answer("💪 Введите **крепость** (в mg):", parse_mode="Markdown")


@router.message(LiquidStates.strength)
async def process_liquid_strength(message: Message, state: FSMContext):
    """Обработка крепости"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено", reply_markup=get_admin_keyboard())
        return

    await state.update_data(strength=message.text)
    await state.set_state(LiquidStates.price)
    await message.answer("💰 Введите **цену** (в рублях):", parse_mode="Markdown")


@router.message(LiquidStates.price)
async def process_liquid_price(message: Message, state: FSMContext):
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

        data = await state.get_data()

        liquid_id = db.add_liquid(
            brand_id=data['brand_id'],
            name=data['name'],
            flavor=data['flavor'],
            strength=data['strength'],
            price=price
        )

        if liquid_id:
            # Получаем информацию о бренде
            brand = db.get_brand_by_id(data['brand_id'])

            await message.answer(
                f"✅ **Жидкость успешно добавлена!**\n\n"
                f"🏭 **Бренд:** {brand['name'] if brand else 'Неизвестно'}\n"
                f"🍼 **Название:** {data['name']}\n"
                f"👃 **Вкус:** {data['flavor']}\n"
                f"💪 **Крепость:** {data['strength']} mg\n"
                f"💰 **Цена:** {price}₽",
                reply_markup=get_admin_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                "❌ Ошибка при добавлении жидкости",
                reply_markup=get_admin_keyboard()
            )

        await state.clear()
    except ValueError:
        await message.answer("❌ Введите корректное число")


# ========== ЗАЯВКИ НА ПОКУПКУ ==========

@router.message(F.text == "📊 Заявки на покупку")
async def show_purchase_requests(message: Message):
    """Показать заявки на покупку (админ)"""
    if not is_admin(message.from_user.id):
        return

    requests = db.get_purchase_requests()

    if not requests:
        await message.answer("📭 Заявок на покупку пока нет")
        return

    for req in requests[:10]:
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


# ========== НАВИГАЦИЯ ==========

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