from collections.abc import Sequence

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.config import settings
from app.models.cart import Cart
from app.models.order import CANCELLABLE_ORDER_STATUSES, Order
from app.models.user import UserRole
from app.services.order_tracking import status_title

CATALOG_BUTTON = "Каталог"
CART_BUTTON = "Корзина"
MY_ORDERS_BUTTON = "📦 Мои заказы"
CONTACT_SUPPORT_BUTTON = "📞 Связаться с поддержкой"
LEGACY_CONTACT_ADMIN_BUTTON = "📞 Связаться с админом"
ADMIN_PANEL_BUTTON = "Админ-панель"
SUPER_ADMIN_BUTTON = "Супер-админ"
CANCEL_BUTTON = "Отмена"
WEBAPP_BUTTON = "🍵 Открыть витрину"
COUNTRY_RUSSIA = "Россия"
COUNTRY_RUSSIA_CODE = "RU"


def main_menu(role: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    webapp_url = settings.public_webapp_url
    if webapp_url is not None:
        builder.row(
            KeyboardButton(text=WEBAPP_BUTTON, web_app=WebAppInfo(url=webapp_url)),
        )
    builder.row(
        KeyboardButton(text=CATALOG_BUTTON),
        KeyboardButton(text=CART_BUTTON),
    )
    builder.row(KeyboardButton(text=MY_ORDERS_BUTTON))
    builder.row(KeyboardButton(text=CONTACT_SUPPORT_BUTTON))
    if role in {UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value}:
        builder.row(KeyboardButton(text=ADMIN_PANEL_BUTTON))
    if role == UserRole.SUPER_ADMIN.value:
        builder.row(KeyboardButton(text=SUPER_ADMIN_BUTTON))
    return builder.as_markup(resize_keyboard=True)


def cancel_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_BUTTON)]],
        resize_keyboard=True,
    )


def subscribe_keyboard(channel_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Подписаться на канал", url=channel_url)
    builder.button(text="Я подписался", callback_data="sub:check")
    webapp_url = settings.public_webapp_url
    if webapp_url is not None:
        builder.button(text=WEBAPP_BUTTON, web_app=WebAppInfo(url=webapp_url))
    builder.adjust(1)
    return builder.as_markup()


def contact_support_keyboard(url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Написать в поддержку", url=url)
    return builder.as_markup()


def country_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇷🇺 Россия", callback_data=f"checkout:country:{COUNTRY_RUSSIA_CODE}")
    builder.adjust(1)
    return builder.as_markup()


def carousel_keyboard(
    product_id: int,
    index: int,
    total: int,
    show_composition: bool,
) -> InlineKeyboardMarkup:
    prev_index = (index - 1) % total
    next_index = (index + 1) % total
    composition_flag = 0 if show_composition else 1
    composition_label = "Описание" if show_composition else "📖 Состав"
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="◀️ Предыдущий", callback_data=f"cat:go:{prev_index}:0"),
        InlineKeyboardButton(text="▶️ Следующий", callback_data=f"cat:go:{next_index}:0"),
    )
    builder.row(
        InlineKeyboardButton(
            text=composition_label,
            callback_data=f"cat:go:{index}:{composition_flag}",
        ),
        InlineKeyboardButton(text="🛒 В корзину", callback_data=f"cart:add:{product_id}"),
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад в меню", callback_data="cat:home"))
    return builder.as_markup()


def cart_keyboard(items: Sequence[Cart]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        title = item.product.name if item.product is not None else f"Товар #{item.product_id}"
        builder.row(
            InlineKeyboardButton(text="−", callback_data=f"cart:dec:{item.id}"),
            InlineKeyboardButton(
                text=f"{title} × {item.quantity}",
                callback_data=f"cart:noop:{item.id}",
            ),
            InlineKeyboardButton(text="+", callback_data=f"cart:inc:{item.id}"),
        )
    builder.row(InlineKeyboardButton(text="Оформить заказ", callback_data="cart:checkout"))
    builder.row(InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="cart:clear"))
    return builder.as_markup()


def my_orders_keyboard(orders: Sequence[Order]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for order in orders:
        builder.button(
            text=f"Заказ №{order.id} — {status_title(order.status)}",
            callback_data=f"usr:ord:{order.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def order_roadmap_keyboard(order: Order) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if order.status in CANCELLABLE_ORDER_STATUSES:
        builder.button(text="❌ Отменить заказ", callback_data=f"usr:cnl:{order.id}")
    builder.button(text="К списку заказов", callback_data="usr:ords")
    builder.adjust(1)
    return builder.as_markup()
