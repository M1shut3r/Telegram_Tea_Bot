from decimal import Decimal
from html import escape

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.admin_kb import order_status_keyboard
from app.models.order import Order
from app.models.user import User, UserRole
from app.repositories.carts import CartRepository
from app.repositories.orders import OrderRepository
from app.repositories.users import UserRepository
from app.services.cart_lifecycle import cancel_cart_jobs
from app.services.order_tracking import status_title, tracking_line


class EmptyCartError(Exception):
    pass


def format_price(value: Decimal) -> str:
    quantized = Decimal(value).quantize(Decimal("0.01"))
    if quantized == quantized.to_integral():
        return f"{int(quantized)} ₽"
    return f"{quantized:.2f} ₽"


def build_order_message(order: Order, title: str | None = None) -> str:
    username = order.user.username
    username_line = f"@{escape(username)}" if username else "без username"
    created_at = order.created_at.strftime("%d.%m.%Y %H:%M") if order.created_at else "—"
    heading = title or f"<b>Новый заказ #{order.id}</b>"
    lines = [
        heading,
        f"Статус: {escape(status_title(order.status))}",
        f"Создан: {created_at}",
        f"Клиент: {escape(order.customer_name)} ({username_line})",
        f"Telegram ID: <code>{order.user.telegram_id}</code>",
        f"Телефон: {escape(order.phone)}",
        f"Страна: {escape(order.country or '—')}",
        f"Город: {escape(order.city or '—')}",
        f"Адрес: {escape(order.address)}",
    ]
    track = tracking_line(order.tracking_number)
    if track is not None:
        lines.append(escape(track))
    lines.extend(["", "<b>Состав заказа:</b>"])
    for item in order.items:
        product_name = escape(item.product.name) if item.product is not None else f"#{item.product_id}"
        line_total = format_price(item.price_at_purchase * item.quantity)
        unit = format_price(item.price_at_purchase)
        lines.append(f"• {product_name} × {item.quantity} ({unit}) = {line_total}")
    lines.append("")
    lines.append(f"<b>Итого: {format_price(order.total_price)}</b>")
    return "\n".join(lines)


async def notify_admins(bot: Bot, session: AsyncSession, order: Order) -> None:
    repository = UserRepository(session)
    staff = await repository.list_by_roles(
        (UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value),
    )
    text = build_order_message(order)
    markup = order_status_keyboard(order.id, order.status)
    for admin in staff:
        try:
            await bot.send_message(admin.telegram_id, text, reply_markup=markup)
        except TelegramAPIError:
            continue


async def place_order(
    session: AsyncSession,
    bot: Bot,
    user: User,
    customer_name: str,
    phone: str,
    country: str,
    city: str,
    address: str,
) -> Order:
    cart_repository = CartRepository(session)
    cart_items = await cart_repository.get_with_products(user.id)
    active_items = [item for item in cart_items if item.product is not None and item.product.is_active]
    if not active_items:
        raise EmptyCartError
    payload: list[tuple[int, int, Decimal]] = []
    total = Decimal("0.00")
    for item in active_items:
        price = Decimal(item.product.price)
        payload.append((item.product_id, item.quantity, price))
        total += price * item.quantity
    order_repository = OrderRepository(session)
    order = await order_repository.create_with_items(
        user_id=user.id,
        customer_name=customer_name,
        phone=phone,
        country=country,
        city=city,
        address=address,
        items=payload,
        total_price=total,
    )
    await cart_repository.clear_for_user(user.id)
    cancel_cart_jobs(user.telegram_id)
    await notify_admins(bot, session, order)
    try:
        await bot.send_message(
            user.telegram_id,
            f"🟢 Ваш заказ №{order.id} принят! Мы уже начинаем его обрабатывать. "
            "Отслеживайте статус в разделе «Мои заказы».",
        )
    except TelegramAPIError:
        pass
    return order
