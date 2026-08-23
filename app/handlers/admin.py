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
    ORDER_LIST_ACTIVE,
    ORDER_LIST_ARCHIVED,
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
from app.services.order_management import OrderNotCancellableError, OrderNotFoundError, cancel_order
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


class AdminStates(StatesGroup):
    waiting_for_tracking = State()


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


@router.callback_query(F.data.startswith("adm:list:"))
async def handle_orders_list(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer()
        return
    kind = parts[2]
    page = int(parts[3])
    if kind not in {ORDER_LIST_ACTIVE, ORDER_LIST_ARCHIVED}:
        await callback.answer()
        return
    repository = OrderRepository(session)
    if kind == ORDER_LIST_ACTIVE:
        total = await repository.count_active()
        orders = await repository.get_active_orders(page * ORDERS_PAGE_SIZE, ORDERS_PAGE_SIZE)
        title = f"🟢 Активные заказы ({total}):"
        empty = "Активных заказов пока нет."
    else:
        total = await repository.count_archived()
        orders = await repository.get_archived_orders(page * ORDERS_PAGE_SIZE, ORDERS_PAGE_SIZE)
        title = f"🏁 Завершенные и отмененные ({total}):"
        empty = "Завершённых заказов пока нет."
    await callback.answer()
    if total == 0:
        await callback.message.edit_text(empty, reply_markup=admin_panel_keyboard())
        return
    await callback.message.edit_text(
        title,
        reply_markup=orders_keyboard(orders, page, total, kind),
    )


@router.callback_query(F.data.startswith("adm:show:"))
async def handle_order_details(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 5:
        await callback.answer()
        return
    kind = parts[2]
    page = int(parts[3])
    order_id = int(parts[4])
    order = await OrderRepository(session).get_with_items(order_id)
    if order is None:
        await callback.answer("Заказ не найден.", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(
        build_order_message(order, f"<b>Заказ #{order.id}</b>"),
        reply_markup=order_details_keyboard(order, page=page, kind=kind),
    )


@router.callback_query(F.data == "adm:noop")
async def handle_admin_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith("adm:st:"))
async def handle_order_status(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
    state: FSMContext,
) -> None:
    await callback.answer()
    if callback.message is None or callback.data is None:
        return
    parts = callback.data.split(":")
    if len(parts) != 6:
        return
    kind = parts[2]
    page = int(parts[3])
    order_id = int(parts[4])
    new_status = parts[5]
    allowed = {
        OrderStatus.IN_PROGRESS.value,
        OrderStatus.PACKED.value,
        OrderStatus.SHIPPED.value,
        OrderStatus.DONE.value,
    }
    if new_status not in allowed:
        return
    if new_status == OrderStatus.SHIPPED.value:
        order = await OrderRepository(session).get_with_items(order_id)
        if order is None:
            return
        await state.set_state(AdminStates.waiting_for_tracking)
        await state.update_data(
            order_id=order_id,
            order_chat_id=callback.message.chat.id,
            order_message_id=callback.message.message_id,
            order_kind=kind,
            order_page=page,
        )
        await callback.message.answer(
            "Введите трек-номер для отправки",
            reply_markup=cancel_menu(),
        )
        return
    repository = OrderRepository(session)
    order = await repository.update_status(order_id, new_status)
    if order is None:
        return
    try:
        await callback.message.edit_text(
            build_order_message(order, f"<b>Заказ #{order.id}</b>"),
            reply_markup=order_details_keyboard(order, page=page, kind=kind),
        )
    except TelegramBadRequest:
        pass
    if order.user is None:
        return
    try:
        await bot.send_message(
            order.user.telegram_id,
            user_status_notification(order.id, order.status, order.tracking_number),
        )
    except TelegramAPIError:
        return


@router.callback_query(F.data.startswith("adm:cnl:"))
async def handle_admin_cancel_order(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 5:
        await callback.answer()
        return
    kind = parts[2]
    page = int(parts[3])
    order_id = int(parts[4])
    try:
        order = await cancel_order(session, bot, order_id, "admin")
    except OrderNotFoundError:
        await callback.answer("Заказ не найден.", show_alert=True)
        return
    except OrderNotCancellableError:
        await callback.answer("Этот заказ уже нельзя отменить.", show_alert=True)
        return
    await callback.answer("Заказ отменён.")
    try:
        await callback.message.edit_text(
            build_order_message(order, f"<b>Заказ #{order.id}</b>"),
            reply_markup=order_details_keyboard(order, page=page, kind=kind),
        )
    except TelegramBadRequest:
        return


@router.message(AdminStates.waiting_for_tracking, F.text == CANCEL_BUTTON)
async def handle_tracking_cancel(
    message: Message,
    state: FSMContext,
    staff_user: User,
) -> None:
    await state.clear()
    await send_home(message, staff_user, "Отправка без трек-номера отменена.")


@router.message(AdminStates.waiting_for_tracking, F.text)
async def handle_tracking_number(
    message: Message,
    session: AsyncSession,
    bot: Bot,
    state: FSMContext,
    staff_user: User,
) -> None:
    tracking_number = (message.text or "").strip()
    if len(tracking_number) < 4:
        await message.answer("Введите трек-номер для отправки")
        return
    data = await state.get_data()
    order_id = int(data.get("order_id", 0))
    if order_id <= 0:
        await state.clear()
        await send_home(message, staff_user, "Заказ не найден.")
        return
    repository = OrderRepository(session)
    order = await repository.set_shipped(order_id, tracking_number)
    chat_id = data.get("order_chat_id")
    message_id = data.get("order_message_id")
    kind = str(data.get("order_kind") or ORDER_LIST_ACTIVE)
    page = int(data.get("order_page") or 0)
    await state.clear()
    if order is None:
        await send_home(message, staff_user, "Заказ не найден.")
        return
    if chat_id is not None and message_id is not None:
        try:
            await bot.edit_message_text(
                build_order_message(order, f"<b>Заказ #{order.id}</b>"),
                chat_id=int(chat_id),
                message_id=int(message_id),
                reply_markup=order_details_keyboard(order, page=page, kind=kind),
            )
        except TelegramBadRequest:
            pass
    await send_home(message, staff_user, f"Заказ #{order.id} отправлен. Трек-номер: {tracking_number}")
    if order.user is None:
        return
    try:
        await bot.send_message(
            order.user.telegram_id,
            user_status_notification(order.id, order.status, order.tracking_number),
        )
    except TelegramAPIError:
        return
