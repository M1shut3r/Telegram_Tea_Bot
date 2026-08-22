import re
from decimal import Decimal
from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.start import has_shop_access, resolve_user, send_home, send_subscribe_gate
from app.keyboards.user_kb import (
    CANCEL_BUTTON,
    CART_BUTTON,
    COUNTRY_RUSSIA,
    COUNTRY_RUSSIA_CODE,
    cancel_menu,
    cart_keyboard,
    country_keyboard,
)
from app.models.cart import Cart
from app.repositories.carts import CartRepository
from app.repositories.products import ProductRepository
from app.services.cart_lifecycle import cancel_cart_jobs_for_user, schedule_cart_jobs
from app.services.ordering import EmptyCartError, format_price, place_order

router = Router()
PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9\-\s()]{8,20}$")
EMPTY_CART_TEXT = "Корзина пуста. Добавьте чай из каталога."
COUNTRY_LABELS = {COUNTRY_RUSSIA_CODE: COUNTRY_RUSSIA}


class OrderCheckout(StatesGroup):
    full_name = State()
    phone = State()
    country = State()
    city = State()
    address = State()


def cart_text(items: list[Cart]) -> str:
    lines = ["<b>Ваша корзина</b>", ""]
    total = Decimal("0.00")
    for item in items:
        name = escape(item.product.name) if item.product is not None else f"Товар #{item.product_id}"
        price = Decimal(item.product.price) if item.product is not None else Decimal("0")
        line_total = price * item.quantity
        total += line_total
        lines.append(f"• {name} × {item.quantity} = {format_price(line_total)}")
    lines.append("")
    lines.append(f"<b>Итого: {format_price(total)}</b>")
    return "\n".join(lines)


async def load_cart(session: AsyncSession, user_id: int) -> list[Cart]:
    items = await CartRepository(session).get_with_products(user_id)
    return [item for item in items if item.product is not None and item.product.is_active]


def current_message_html(callback: CallbackQuery) -> str:
    if callback.message is None:
        return ""
    return callback.message.html_text or callback.message.text or ""


async def edit_cart_message(callback: CallbackQuery, items: list[Cart]) -> None:
    if callback.message is None:
        return
    text = EMPTY_CART_TEXT if not items else cart_text(items)
    markup = None if not items else cart_keyboard(items)
    if current_message_html(callback) == text:
        try:
            await callback.message.edit_reply_markup(reply_markup=markup)
        except TelegramBadRequest:
            return
        return
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest:
        return


@router.message(StateFilter(default_state), F.text == CART_BUTTON)
async def handle_cart(message: Message, session: AsyncSession, bot: Bot) -> None:
    if message.from_user is None:
        return
    user = await resolve_user(session, message.from_user.id, message.from_user.username)
    if not await has_shop_access(bot, user):
        await send_subscribe_gate(message, bot)
        return
    items = await load_cart(session, user.id)
    if not items:
        await message.answer(EMPTY_CART_TEXT)
        return
    await message.answer(cart_text(items), reply_markup=cart_keyboard(items))


@router.callback_query(F.data.startswith("cart:add:"))
async def handle_add_to_cart(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
) -> None:
    if callback.from_user is None or callback.data is None:
        await callback.answer()
        return
    user = await resolve_user(session, callback.from_user.id, callback.from_user.username)
    if not await has_shop_access(bot, user):
        await callback.answer("Сначала подпишитесь на канал.", show_alert=True)
        return
    product_id = int(callback.data.split(":")[2])
    product = await ProductRepository(session).get_by_id(product_id)
    if product is None or not product.is_active:
        await callback.answer("Товар недоступен.", show_alert=True)
        return
    repository = CartRepository(session)
    was_empty = await repository.count_items(user.id) == 0
    await repository.add_product(user.id, product_id)
    if was_empty:
        schedule_cart_jobs(bot, user.telegram_id)
    await callback.answer("Добавлено в корзину.")


@router.callback_query(F.data.startswith("cart:inc:"))
async def handle_cart_inc(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    if callback.from_user is None or callback.data is None:
        return
    user = await resolve_user(session, callback.from_user.id, callback.from_user.username)
    cart_id = int(callback.data.split(":")[2])
    repository = CartRepository(session)
    item = await repository.get_by_id(cart_id)
    if item is None or item.user_id != user.id:
        return
    await repository.increment(cart_id)
    await edit_cart_message(callback, await load_cart(session, user.id))


@router.callback_query(F.data.startswith("cart:dec:"))
async def handle_cart_dec(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    if callback.from_user is None or callback.data is None:
        return
    user = await resolve_user(session, callback.from_user.id, callback.from_user.username)
    cart_id = int(callback.data.split(":")[2])
    repository = CartRepository(session)
    item = await repository.get_by_id(cart_id)
    if item is None or item.user_id != user.id:
        return
    await repository.decrement(cart_id)
    items = await load_cart(session, user.id)
    if not items:
        await cancel_cart_jobs_for_user(session, user.id)
    await edit_cart_message(callback, items)


@router.callback_query(F.data.startswith("cart:noop:"))
async def handle_cart_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data == "cart:clear")
async def handle_cart_clear(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    if callback.from_user is None:
        return
    user = await resolve_user(session, callback.from_user.id, callback.from_user.username)
    await CartRepository(session).clear_for_user(user.id)
    await cancel_cart_jobs_for_user(session, user.id)
    await edit_cart_message(callback, [])


@router.callback_query(F.data == "cart:checkout")
async def handle_checkout_start(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
    state: FSMContext,
) -> None:
    await callback.answer()
    if callback.from_user is None or callback.message is None:
        return
    user = await resolve_user(session, callback.from_user.id, callback.from_user.username)
    if not await has_shop_access(bot, user):
        return
    items = await load_cart(session, user.id)
    if not items:
        return
    await state.set_state(OrderCheckout.full_name)
    await callback.message.answer(
        "Оформление заказа.\nВведите ФИО получателя.\nЧтобы отменить, нажмите «Отмена» или /cancel.",
        reply_markup=cancel_menu(),
    )


@router.message(StateFilter(OrderCheckout), Command("cancel"))
@router.message(StateFilter(OrderCheckout), F.text == CANCEL_BUTTON)
async def handle_checkout_cancel(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await state.clear()
    if message.from_user is None:
        return
    user = await resolve_user(session, message.from_user.id, message.from_user.username)
    await send_home(message, user, "Оформление заказа отменено.")


@router.message(OrderCheckout.full_name, F.text)
async def handle_checkout_name(message: Message, state: FSMContext) -> None:
    full_name = (message.text or "").strip()
    if len(full_name) < 2:
        await message.answer("Введите корректное ФИО.")
        return
    await state.update_data(full_name=full_name)
    await state.set_state(OrderCheckout.phone)
    await message.answer("Введите телефон для связи.")


@router.message(OrderCheckout.phone, F.text)
async def handle_checkout_phone(message: Message, state: FSMContext) -> None:
    phone = (message.text or "").strip()
    if not PHONE_PATTERN.match(phone):
        await message.answer("Введите телефон в формате +79991234567.")
        return
    await state.update_data(phone=phone)
    await state.set_state(OrderCheckout.country)
    await message.answer("Выберите страну доставки:", reply_markup=country_keyboard())


@router.callback_query(OrderCheckout.country, F.data.startswith("checkout:country:"))
async def handle_checkout_country(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.data is None or callback.message is None:
        return
    code = callback.data.split(":")[2]
    country = COUNTRY_LABELS.get(code)
    if country is None:
        return
    await state.update_data(country=country)
    await state.set_state(OrderCheckout.city)
    await callback.message.answer("Введите город доставки.")


@router.message(OrderCheckout.country)
async def handle_checkout_country_text(message: Message) -> None:
    await message.answer("Выберите страну кнопкой ниже.", reply_markup=country_keyboard())


@router.message(OrderCheckout.city, F.text)
async def handle_checkout_city(message: Message, state: FSMContext) -> None:
    city = (message.text or "").strip()
    if len(city) < 2:
        await message.answer("Введите название города.")
        return
    await state.update_data(city=city)
    await state.set_state(OrderCheckout.address)
    await message.answer("Введите адрес: улица, дом, квартира.")


@router.message(OrderCheckout.address, F.text)
async def handle_checkout_address(
    message: Message,
    session: AsyncSession,
    bot: Bot,
    state: FSMContext,
) -> None:
    address = (message.text or "").strip()
    if len(address) < 5:
        await message.answer("Введите полный адрес: улица, дом, квартира.")
        return
    if message.from_user is None:
        return
    user = await resolve_user(session, message.from_user.id, message.from_user.username)
    data = await state.get_data()
    try:
        order = await place_order(
            session=session,
            bot=bot,
            user=user,
            customer_name=str(data["full_name"]),
            phone=str(data["phone"]),
            country=str(data["country"]),
            city=str(data["city"]),
            address=address,
        )
    except EmptyCartError:
        await state.clear()
        await send_home(message, user, "Корзина пуста. Оформление невозможно.")
        return
    await state.clear()
    await send_home(
        message,
        user,
        f"Заказ #{order.id} оформлен. Сумма: {format_price(order.total_price)}.\n"
        "Администратор свяжется с вами для подтверждения.",
    )


@router.message(StateFilter(OrderCheckout))
async def handle_checkout_unexpected(message: Message) -> None:
    await message.answer("Пожалуйста, отправьте текстовый ответ или нажмите «Отмена».")
