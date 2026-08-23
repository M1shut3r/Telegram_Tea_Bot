from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import CANCELLABLE_ORDER_STATUSES, Order, OrderStatus
from app.models.user import UserRole
from app.repositories.orders import OrderRepository
from app.repositories.users import UserRepository


class OrderNotFoundError(Exception):
    pass


class OrderNotCancellableError(Exception):
    def __init__(self, status: str) -> None:
        super().__init__(status)
        self.status = status


async def cancel_order(
    session: AsyncSession,
    bot: Bot,
    order_id: int,
    cancelled_by: str,
) -> Order:
    repository = OrderRepository(session)
    order = await repository.get_with_items(order_id)
    if order is None:
        raise OrderNotFoundError
    if order.status not in CANCELLABLE_ORDER_STATUSES:
        raise OrderNotCancellableError(order.status)
    updated = await repository.update_status(order_id, OrderStatus.CANCELLED.value)
    if updated is None:
        raise OrderNotFoundError
    if cancelled_by == "admin":
        await _notify_user_cancelled_by_admin(bot, updated)
    else:
        await _notify_admins_cancelled_by_user(session, bot, updated)
    return updated


async def _notify_user_cancelled_by_admin(bot: Bot, order: Order) -> None:
    if order.user is None:
        return
    try:
        await bot.send_message(
            order.user.telegram_id,
            f"❌ Ваш заказ №{order.id} был отменен администрацией",
        )
    except TelegramAPIError:
        return


async def _notify_admins_cancelled_by_user(
    session: AsyncSession,
    bot: Bot,
    order: Order,
) -> None:
    staff = await UserRepository(session).list_by_roles(
        (UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value),
    )
    text = f"❌ Заказ №{order.id} отменен покупателем"
    for admin in staff:
        try:
            await bot.send_message(admin.telegram_id, text)
        except TelegramAPIError:
            continue
