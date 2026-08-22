from collections.abc import Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole
from app.services.order_tracking import STATUS_RANK, status_title

ORDERS_PAGE_SIZE = 5

STATUS_BUTTONS = (
    (OrderStatus.IN_PROGRESS.value, "✅ В работу", "✅ В работу"),
    (OrderStatus.PACKED.value, "📦 Собран", "✅ Собран"),
    (OrderStatus.SHIPPED.value, "🚚 Отправлен", "✅ Отправлен"),
    (OrderStatus.DONE.value, "🏁 Выполнен", "✅ Выполнен"),
)


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Добавить товар", callback_data="adm:add")
    builder.button(text="Заказы", callback_data="adm:orders:0")
    builder.adjust(1)
    return builder.as_markup()


def super_admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Создать инвайт-ссылку", callback_data="sadm:invite")
    builder.button(text="Список админов", callback_data="sadm:admins")
    builder.adjust(1)
    return builder.as_markup()


def orders_keyboard(orders: Sequence[Order], page: int, total_count: int) -> InlineKeyboardMarkup:
    total_pages = max(1, (total_count + ORDERS_PAGE_SIZE - 1) // ORDERS_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    builder = InlineKeyboardBuilder()
    for order in orders:
        builder.button(
            text=f"Заказ #{order.id} — {status_title(order.status)}",
            callback_data=f"adm:order:{order.id}",
        )
    builder.adjust(1)
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="« Назад", callback_data=f"adm:orders:{page - 1}"))
    if page + 1 < total_pages:
        nav.append(InlineKeyboardButton(text="Вперёд »", callback_data=f"adm:orders:{page + 1}"))
    if nav:
        builder.row(*nav)
    builder.row(InlineKeyboardButton(text="В админ-панель", callback_data="adm:home"))
    return builder.as_markup()


def order_status_keyboard(order_id: int, current_status: str, page: int = 0) -> InlineKeyboardMarkup:
    current_rank = STATUS_RANK.get(current_status, 0)
    builder = InlineKeyboardBuilder()
    row: list[InlineKeyboardButton] = []
    for status, idle_label, done_label in STATUS_BUTTONS:
        reached = STATUS_RANK[status] <= current_rank
        if reached:
            row.append(InlineKeyboardButton(text=done_label, callback_data="adm:noop"))
        else:
            row.append(InlineKeyboardButton(text=idle_label, callback_data=f"adm:st:{order_id}:{status}"))
        if len(row) == 2:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)
    builder.row(InlineKeyboardButton(text="К списку заказов", callback_data=f"adm:orders:{page}"))
    return builder.as_markup()


def order_details_keyboard(order: Order, page: int = 0) -> InlineKeyboardMarkup:
    return order_status_keyboard(order.id, order.status, page)


def admins_keyboard(admins: Sequence[User]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for admin in admins:
        label = f"@{admin.username}" if admin.username else str(admin.telegram_id)
        if admin.role == UserRole.SUPER_ADMIN.value:
            builder.button(text=f"{label} — супер-админ", callback_data="sadm:noop")
        else:
            builder.button(
                text=f"Снять права: {label}",
                callback_data=f"sadm:rm:{admin.id}",
            )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="Назад", callback_data="sadm:home"))
    return builder.as_markup()
