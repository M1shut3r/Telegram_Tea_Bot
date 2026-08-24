from decimal import Decimal, InvalidOperation
from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.types import CallbackQuery, InputMediaPhoto, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.start import send_home
from app.keyboards.admin_kb import (
    ORDER_LIST_ACTIVE,
    ORDER_LIST_ARCHIVED,
    ORDERS_PAGE_SIZE,
    PRODUCTS_PAGE_SIZE,
    admin_panel_keyboard,
    order_details_keyboard,
    orders_keyboard,
    product_delete_keyboard,
    product_edit_keyboard,
    products_keyboard,
)
from app.keyboards.user_kb import ADMIN_PANEL_BUTTON, CANCEL_BUTTON, cancel_menu
from app.models.order import OrderStatus
from app.models.product import Product
from app.models.user import User, UserRole
from app.repositories.orders import OrderRepository
from app.repositories.products import ProductRepository
from app.services.admin_manager import HasRole
from app.services.order_management import OrderNotCancellableError, OrderNotFoundError, cancel_order
from app.services.order_tracking import user_status_notification
from app.services.ordering import build_order_message, format_price

router = Router()
router.message.filter(HasRole(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))
router.callback_query.filter(HasRole(UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value))


class ProductCreate(StatesGroup):
    name = State()
    photo = State()
    description = State()
    composition = State()
    price = State()


class ProductEdit(StatesGroup):
    value = State()


class AdminStates(StatesGroup):
    waiting_for_tracking = State()


EDIT_FIELDS = {
    "name": "name",
    "photo": "photo_id",
    "desc": "description",
    "comp": "composition",
    "price": "price",
}

EDIT_PROMPTS = {
    "name": "Отправьте новое название товара.",
    "photo": "Отправьте новое фото товара.",
    "desc": "Отправьте новое описание товара.",
    "comp": "Отправьте новый состав товара.",
    "price": "Введите новую цену числом, например 1200 или 1200.50",
}


def _clip(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    if max_len <= 1:
        return "…"
    return text[: max_len - 1] + "…"


def admin_product_caption(product: Product) -> str:
    name = escape(product.name)
    price = format_price(product.price)
    description = escape(product.description)
    composition = escape(product.composition)
    caption = f"<b>{name}</b>\nЦена: {price}\n\n<i>Описание:</i>\n{description}\n\n<i>Состав:</i>\n{composition}"
    if len(caption) <= 1024:
        return caption
    overhead = len(f"<b>{name}</b>\nЦена: {price}\n\n<i>Описание:</i>\n\n\n<i>Состав:</i>\n")
    budget = max(20, 1024 - overhead)
    desc_budget = budget // 2
    return (
        f"<b>{name}</b>\nЦена: {price}\n\n"
        f"<i>Описание:</i>\n{_clip(description, desc_budget)}\n\n"
        f"<i>Состав:</i>\n{_clip(composition, budget - desc_budget)}"
    )


def _parse_price(raw: str) -> Decimal | None:
    cleaned = raw.replace(" ", "").replace(",", ".")
    try:
        price = Decimal(cleaned)
    except InvalidOperation:
        return None
    if price <= 0:
        return None
    return price


def _parse_ints(*values: str) -> list[int] | None:
    try:
        return [int(value) for value in values]
    except ValueError:
        return None


async def _load_active_product(session: AsyncSession, product_id: int) -> Product | None:
    product = await ProductRepository(session).get_by_id(product_id)
    if product is None or not product.is_active:
        return None
    return product


async def _delete_callback_message(callback: CallbackQuery) -> None:
    if callback.message is None:
        return
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        return


async def send_admin_product_card(message: Message, product: Product, page: int) -> None:
    await message.answer_photo(
        photo=product.photo_id,
        caption=admin_product_caption(product),
        reply_markup=product_edit_keyboard(product.id, page),
    )


async def show_admin_product_card(callback: CallbackQuery, product: Product, page: int) -> None:
    if callback.message is None:
        return
    caption = admin_product_caption(product)
    markup = product_edit_keyboard(product.id, page)
    if callback.message.photo:
        try:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=product.photo_id, caption=caption),
                reply_markup=markup,
            )
            return
        except TelegramBadRequest:
            pass
        try:
            await callback.message.edit_caption(caption=caption, reply_markup=markup)
            return
        except TelegramBadRequest:
            pass
    await _delete_callback_message(callback)
    await send_admin_product_card(callback.message, product, page)


async def show_products_list(callback: CallbackQuery, session: AsyncSession, page: int) -> None:
    if callback.message is None:
        return
    repository = ProductRepository(session)
    total = await repository.count_active()
    if total == 0:
        text = "Активных товаров пока нет."
        markup = admin_panel_keyboard()
    else:
        last_page = max(0, (total - 1) // PRODUCTS_PAGE_SIZE)
        page = max(0, min(page, last_page))
        products = await repository.list_active_page(page * PRODUCTS_PAGE_SIZE, PRODUCTS_PAGE_SIZE)
        text = f"Товары ({total}):"
        markup = products_keyboard(products, page, total)
    if callback.message.photo:
        await _delete_callback_message(callback)
        await callback.message.answer(text, reply_markup=markup)
        return
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=markup)


@router.message(StateFilter(default_state), F.text == ADMIN_PANEL_BUTTON)
async def handle_admin_panel(message: Message) -> None:
    await message.answer("Админ-панель", reply_markup=admin_panel_keyboard())


@router.callback_query(F.data == "adm:home")
async def handle_admin_home(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await state.clear()
    await callback.answer()
    if callback.message.photo:
        await _delete_callback_message(callback)
        await callback.message.answer("Админ-панель", reply_markup=admin_panel_keyboard())
        return
    try:
        await callback.message.edit_text("Админ-панель", reply_markup=admin_panel_keyboard())
    except TelegramBadRequest:
        await callback.message.answer("Админ-панель", reply_markup=admin_panel_keyboard())


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
    price = _parse_price(message.text or "")
    if price is None:
        await message.answer("Введите цену числом, например 1200 или 1200.50")
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


@router.callback_query(F.data.startswith("adm:plist:"))
async def handle_products_list(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer()
        return
    parsed = _parse_ints(parts[2])
    if parsed is None:
        await callback.answer()
        return
    await state.clear()
    await callback.answer()
    await show_products_list(callback, session, parsed[0])


@router.callback_query(F.data.startswith("adm:pshow:"))
async def handle_product_show(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer()
        return
    parsed = _parse_ints(parts[2], parts[3])
    if parsed is None:
        await callback.answer()
        return
    page, product_id = parsed
    product = await _load_active_product(session, product_id)
    if product is None:
        await callback.answer("Товар не найден.", show_alert=True)
        await state.clear()
        await show_products_list(callback, session, page)
        return
    await state.clear()
    await callback.answer()
    await show_admin_product_card(callback, product, page)


@router.callback_query(F.data.startswith("adm:pe:"))
async def handle_product_edit_start(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 5:
        await callback.answer()
        return
    field = parts[2]
    if field not in EDIT_FIELDS:
        await callback.answer()
        return
    parsed = _parse_ints(parts[3], parts[4])
    if parsed is None:
        await callback.answer()
        return
    page, product_id = parsed
    product = await _load_active_product(session, product_id)
    if product is None:
        await callback.answer("Товар не найден.", show_alert=True)
        await state.clear()
        await show_products_list(callback, session, page)
        return
    await state.set_state(ProductEdit.value)
    await state.update_data(product_id=product_id, page=page, field=field)
    await callback.answer()
    current = {
        "name": f"Сейчас: {escape(product.name)}",
        "photo": "Пришлите новое фото товара.",
        "desc": f"Сейчас:\n{escape(product.description)}",
        "comp": f"Сейчас:\n{escape(product.composition)}",
        "price": f"Сейчас: {format_price(product.price)}",
    }[field]
    await callback.message.answer(
        f"{current}\n\n{EDIT_PROMPTS[field]}\nЧтобы отменить, нажмите «Отмена».",
        reply_markup=cancel_menu(),
    )


@router.callback_query(F.data.startswith("adm:pdy:"))
async def handle_product_delete_confirm(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer()
        return
    parsed = _parse_ints(parts[2], parts[3])
    if parsed is None:
        await callback.answer()
        return
    page, product_id = parsed
    product = await ProductRepository(session).deactivate(product_id)
    await state.clear()
    if product is None:
        await callback.answer("Товар не найден.", show_alert=True)
        await show_products_list(callback, session, page)
        return
    await callback.answer("Товар удалён из каталога.")
    await show_products_list(callback, session, page)


@router.callback_query(F.data.startswith("adm:pd:"))
async def handle_product_delete_ask(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer()
        return
    parsed = _parse_ints(parts[2], parts[3])
    if parsed is None:
        await callback.answer()
        return
    page, product_id = parsed
    product = await _load_active_product(session, product_id)
    if product is None:
        await callback.answer("Товар не найден.", show_alert=True)
        await show_products_list(callback, session, page)
        return
    await callback.answer()
    text = f"Удалить товар «{escape(product.name)}» из каталога?"
    markup = product_delete_keyboard(product.id, page)
    if callback.message.photo:
        try:
            await callback.message.edit_caption(caption=text, reply_markup=markup)
            return
        except TelegramBadRequest:
            pass
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=markup)


@router.message(StateFilter(ProductEdit), F.text == CANCEL_BUTTON)
async def handle_product_edit_cancel(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    staff_user: User,
) -> None:
    data = await state.get_data()
    product_id = int(data.get("product_id") or 0)
    page = int(data.get("page") or 0)
    await state.clear()
    await send_home(message, staff_user, "Изменение товара отменено.")
    product = await _load_active_product(session, product_id)
    if product is not None:
        await send_admin_product_card(message, product, page)


@router.message(ProductEdit.value, F.photo)
async def handle_product_edit_photo(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    staff_user: User,
) -> None:
    data = await state.get_data()
    if str(data.get("field")) != "photo":
        await message.answer("Отправьте текст, а не фото.")
        return
    if not message.photo:
        await message.answer("Пришлите фотографию товара.")
        return
    product_id = int(data.get("product_id") or 0)
    page = int(data.get("page") or 0)
    product = await ProductRepository(session).update_fields(
        product_id,
        photo_id=message.photo[-1].file_id,
    )
    await state.clear()
    if product is None:
        await send_home(message, staff_user, "Товар не найден.")
        return
    await send_home(message, staff_user, "Фото товара обновлено.")
    await send_admin_product_card(message, product, page)


@router.message(ProductEdit.value, F.text)
async def handle_product_edit_text(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    staff_user: User,
) -> None:
    data = await state.get_data()
    field = str(data.get("field") or "")
    if field == "photo":
        await message.answer("Нужна именно фотография. Отправьте снимок товара.")
        return
    if field not in EDIT_FIELDS:
        await state.clear()
        await send_home(message, staff_user, "Изменение товара отменено.")
        return
    product_id = int(data.get("product_id") or 0)
    page = int(data.get("page") or 0)
    raw = (message.text or "").strip()
    values: dict[str, str | Decimal] = {}
    if field == "name":
        if len(raw) < 2:
            await message.answer("Введите название товара.")
            return
        values["name"] = raw
        done = "Название товара обновлено."
    elif field == "desc":
        if len(raw) < 3:
            await message.answer("Описание слишком короткое.")
            return
        values["description"] = raw
        done = "Описание товара обновлено."
    elif field == "comp":
        if len(raw) < 3:
            await message.answer("Состав слишком короткий.")
            return
        values["composition"] = raw
        done = "Состав товара обновлён."
    elif field == "price":
        price = _parse_price(raw)
        if price is None:
            await message.answer("Введите цену числом, например 1200 или 1200.50")
            return
        values["price"] = price
        done = "Цена товара обновлена."
    else:
        await message.answer(EDIT_PROMPTS.get(field, "Отправьте новое значение."))
        return
    product = await ProductRepository(session).update_fields(product_id, **values)
    await state.clear()
    if product is None:
        await send_home(message, staff_user, "Товар не найден.")
        return
    await send_home(message, staff_user, done)
    await send_admin_product_card(message, product, page)


@router.message(ProductEdit.value)
async def handle_product_edit_invalid(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    field = str(data.get("field") or "")
    if field == "photo":
        await message.answer("Нужна именно фотография. Отправьте снимок товара.")
        return
    await message.answer(EDIT_PROMPTS.get(field, "Отправьте новое значение."))


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
