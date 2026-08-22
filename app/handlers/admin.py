from decimal import Decimal, InvalidOperation

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.start import send_home
from app.keyboards.admin_kb import (
    ORDERS_PAGE_SIZE,
    admin_panel_keyboard,
    order_details_keyboard,
    orders_keyboard,
)
from app.keyboards.user_kb import ADMIN_PANEL_BUTTON, CANCEL_BUTTON, cancel_menu
from app.models.order import OrderStatus
from app.models.user import User, UserRole
from app.repositories.orders import OrderRepository
from app.repositories.products import ProductRepository
from app.services.admin_manager import HasRole
from app.services.order_tracking import user_status_notification
from app.services.ordering import build_order_message

router = Router()
router.message.filter(HasRole(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
router.callback_query.filter(HasRole(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))


class ProductCreate(StatesGroup):
    name = State()
    photo = State()
    description = State()
    composition = State()
    price = State()


@router.message(StateFilter(default_state), F.text == ADMIN_PANEL_BUTTON)
async def handle_admin_panel(message: Message) -> None:
    await message.answer("Админ-панель", reply_markup=admin_panel_keyboard())


@router.callback_query(F.data == "adm:home")
async def handle_admin_home(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await callback.answer()
    await callback.message.edit_text("Админ-панель", reply_markup=admin_panel_keyboard())


@router.callback_query(F.data == "adm:add")
async def handle_product_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await state.set_state(ProductCreate.name)
    await callback.answer()
    await callback.message.answer(
        "Добавление товара.\nВведите название.\nЧтобы отменить, нажмите «Отмена».",
        reply_markup=cancel_menu(),
    )


@router.message(StateFilter(ProductCreate), F.text == CANCEL_BUTTON)
async def handle_product_add_cancel(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    staff_user: User,
) -> None:
    await state.clear()
    await send_home(message, staff_user, "Добавление товара отменено.")


@router.message(ProductCreate.name, F.text)
async def handle_product_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("Введите название товара.")
        return
    await state.update_data(name=name)
    await state.set_state(ProductCreate.photo)
    await message.answer("Отправьте фотографию товара.")


@router.message(ProductCreate.photo, F.photo)
async def handle_product_photo(message: Message, state: FSMContext) -> None:
    if not message.photo:
        await message.answer("Пришлите фотографию товара.")
        return
    await state.update_data(photo_id=message.photo[-1].file_id)
    await state.set_state(ProductCreate.description)
    await message.answer("Отправьте описание товара.")


@router.message(ProductCreate.photo)
async def handle_product_photo_invalid(message: Message) -> None:
    await message.answer("Нужна именно фотография. Отправьте снимок товара.")


@router.message(ProductCreate.description, F.text)
async def handle_product_description(message: Message, state: FSMContext) -> None:
    description = (message.text or "").strip()
    if len(description) < 3:
        await message.answer("Описание слишком короткое.")
        return
    await state.update_data(description=description)
    await state.set_state(ProductCreate.composition)
    await message.answer("Отправьте состав товара. Он будет скрыт до нажатия кнопки «Показать состав».")


@router.message(ProductCreate.composition, F.text)
async def handle_product_composition(message: Message, state: FSMContext) -> None:
    composition = (message.text or "").strip()
    if len(composition) < 3:
        await message.answer("Состав слишком короткий.")
        return
    await state.update_data(composition=composition)
    await state.set_state(ProductCreate.price)
    await message.answer("Введите цену числом, например 1200 или 1200.50")


@router.message(ProductCreate.price, F.text)
async def handle_product_price(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    staff_user: User,
) -> None:
    raw = (message.text or "").replace(" ", "").replace(",", ".")
    try:
        price = Decimal(raw)
    except InvalidOperation:
        await message.answer("Введите цену числом, например 1200 или 1200.50")
        return
    if price <= 0:
        await message.answer("Цена должна быть больше нуля.")
        return
    data = await state.get_data()
    product = await ProductRepository(session).add_product(
        name=str(data["name"]),
        photo_id=str(data["photo_id"]),
        description=str(data["description"]),
        composition=str(data["composition"]),
        price=price,
    )
    await state.clear()
    await send_home(message, staff_user, f"Товар «{product.name}» добавлен в каталог.")


@router.callback_query(F.data.startswith("adm:orders:"))
async def handle_orders_list(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    page = int(callback.data.split(":")[2])
    repository = OrderRepository(session)
    total = await repository.count_all()
    orders = await repository.list_recent(page * ORDERS_PAGE_SIZE, ORDERS_PAGE_SIZE)
    await callback.answer()
    if total == 0:
        await callback.message.edit_text("Заказов пока нет.", reply_markup=admin_panel_keyboard())
        return
    await callback.message.edit_text(
        f"Заказы ({total}):",
        reply_markup=orders_keyboard(orders, page, total),
    )


@router.callback_query(F.data.startswith("adm:order:"))
async def handle_order_details(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    order_id = int(callback.data.split(":")[2])
    order = await OrderRepository(session).get_with_items(order_id)
    if order is None:
        await callback.answer("Заказ не найден.", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(
        build_order_message(order, f"<b>Заказ #{order.id}</b>"),
        reply_markup=order_details_keyboard(order),
    )


@router.callback_query(F.data == "adm:noop")
async def handle_admin_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith("adm:st:"))
async def handle_order_status(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
) -> None:
    await callback.answer()
    if callback.message is None or callback.data is None:
        return
    parts = callback.data.split(":")
    if len(parts) != 4:
        return
    order_id = int(parts[2])
    new_status = parts[3]
    allowed = {
        OrderStatus.IN_PROGRESS.value,
        OrderStatus.PACKED.value,
        OrderStatus.SHIPPED.value,
        OrderStatus.DONE.value,
    }
    if new_status not in allowed:
        return
    repository = OrderRepository(session)
    order = await repository.update_status(order_id, new_status)
    if order is None:
        return
    try:
        await callback.message.edit_text(
            build_order_message(order, f"<b>Заказ #{order.id}</b>"),
            reply_markup=order_details_keyboard(order),
        )
    except TelegramBadRequest:
        pass
    if order.user is None:
        return
    try:
        await bot.send_message(
            order.user.telegram_id,
            user_status_notification(order.id, order.status),
        )
    except TelegramAPIError:
        return
