from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.start import has_shop_access, resolve_user, send_subscribe_gate
from app.keyboards.user_kb import MY_ORDERS_BUTTON, my_orders_keyboard, order_roadmap_keyboard
from app.repositories.orders import OrderRepository
from app.services.order_management import OrderNotCancellableError, OrderNotFoundError, cancel_order
from app.services.order_tracking import generate_roadmap_text

router = Router()


async def show_user_orders(message: Message, session: AsyncSession, user_id: int) -> None:
    orders = list(await OrderRepository(session).list_for_user(user_id))
    if not orders:
        await message.answer("У вас пока нет заказов.")
        return
    await message.answer("Ваши последние заказы:", reply_markup=my_orders_keyboard(orders))


@router.message(StateFilter(default_state), F.text == MY_ORDERS_BUTTON)
async def handle_my_orders(message: Message, session: AsyncSession, bot: Bot) -> None:
    if message.from_user is None:
        return
    user = await resolve_user(session, message.from_user.id, message.from_user.username)
    if not await has_shop_access(bot, user):
        await send_subscribe_gate(message, bot)
        return
    await show_user_orders(message, session, user.id)


@router.callback_query(F.data == "usr:ords")
async def handle_my_orders_list(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    await callback.answer()
    if callback.from_user is None or callback.message is None:
        return
    user = await resolve_user(session, callback.from_user.id, callback.from_user.username)
    if not await has_shop_access(bot, user):
        return
    orders = list(await OrderRepository(session).list_for_user(user.id))
    if not orders:
        try:
            await callback.message.edit_text("У вас пока нет заказов.")
        except TelegramBadRequest:
            return
        return
    try:
        await callback.message.edit_text(
            "Ваши последние заказы:",
            reply_markup=my_orders_keyboard(orders),
        )
    except TelegramBadRequest:
        return


@router.callback_query(F.data.startswith("usr:cnl:"))
async def handle_user_cancel_order(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        await callback.answer()
        return
    user = await resolve_user(session, callback.from_user.id, callback.from_user.username)
    if not await has_shop_access(bot, user):
        await callback.answer()
        return
    order_id = int(callback.data.split(":")[2])
    order = await OrderRepository(session).get_for_user(order_id, user.id)
    if order is None:
        await callback.answer("Заказ не найден.", show_alert=True)
        return
    try:
        cancelled = await cancel_order(session, bot, order.id, "user")
    except OrderNotFoundError:
        await callback.answer("Заказ не найден.", show_alert=True)
        return
    except OrderNotCancellableError:
        await callback.answer("Этот заказ уже нельзя отменить.", show_alert=True)
        return
    await callback.answer("Заказ отменён.")
    text = f"📦 Статус заказа №{cancelled.id}\n\n{generate_roadmap_text(cancelled.status, cancelled.tracking_number)}"
    try:
        await callback.message.edit_text(text, reply_markup=order_roadmap_keyboard(cancelled))
    except TelegramBadRequest:
        return


@router.callback_query(F.data.startswith("usr:ord:"))
async def handle_order_roadmap(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    await callback.answer()
    if callback.from_user is None or callback.message is None or callback.data is None:
        return
    user = await resolve_user(session, callback.from_user.id, callback.from_user.username)
    if not await has_shop_access(bot, user):
        return
    order_id = int(callback.data.split(":")[2])
    order = await OrderRepository(session).get_for_user(order_id, user.id)
    if order is None:
        return
    text = f"📦 Статус заказа №{order.id}\n\n{generate_roadmap_text(order.status, order.tracking_number)}"
    try:
        await callback.message.edit_text(text, reply_markup=order_roadmap_keyboard(order))
    except TelegramBadRequest:
        return
