from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, InputMediaPhoto, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.start import has_shop_access, resolve_user, send_home, send_subscribe_gate
from app.keyboards.user_kb import CATALOG_BUTTON, carousel_keyboard
from app.models.product import Product
from app.repositories.products import ProductRepository
from app.services.ordering import format_price
from app.services.product_photo import answer_product_card, is_not_modified

router = Router()


def product_caption(product: Product, show_composition: bool) -> str:
    name = escape(product.name)
    price = format_price(product.price)
    if show_composition:
        body = escape(product.composition)
        return f"<b>{name}</b>\n\n<i>Состав:</i>\n{body}\n\nЦена: {price}"
    body = escape(product.description)
    return f"<b>{name}</b>\n\n{body}\n\nЦена: {price}"


async def send_carousel_card(
    message: Message,
    product: Product,
    index: int,
    total: int,
    show_composition: bool = False,
) -> None:
    await answer_product_card(
        message,
        product,
        product_caption(product, show_composition),
        carousel_keyboard(product.id, index, total, show_composition),
    )


async def edit_carousel_card(
    callback: CallbackQuery,
    product: Product,
    index: int,
    total: int,
    show_composition: bool,
) -> None:
    message = callback.message
    if message is None:
        return
    caption = product_caption(product, show_composition)
    markup = carousel_keyboard(product.id, index, total, show_composition)
    current_photo = message.photo[-1].file_id if message.photo else None
    if current_photo is not None:
        current_caption = message.html_text or message.caption or ""
        try:
            if current_photo != product.photo_id:
                await message.edit_media(
                    media=InputMediaPhoto(media=product.photo_id, caption=caption, parse_mode="HTML"),
                    reply_markup=markup,
                )
            elif current_caption != caption:
                await message.edit_caption(caption=caption, reply_markup=markup)
            else:
                await message.edit_reply_markup(reply_markup=markup)
            return
        except TelegramBadRequest as error:
            if is_not_modified(error):
                return
    # A text card (its photo was unavailable) cannot be edited into a photo, and edit_media
    # fails when this bot cannot use the stored photo id. Replace the card instead.
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    await send_carousel_card(message, product, index, total, show_composition)


@router.message(StateFilter(default_state), F.text == CATALOG_BUTTON)
async def handle_catalog(
    message: Message,
    session: AsyncSession,
    bot: Bot,
) -> None:
    if message.from_user is None:
        return
    user = await resolve_user(session, message.from_user.id, message.from_user.username)
    if not await has_shop_access(bot, user):
        await send_subscribe_gate(message, bot)
        return
    products = list(await ProductRepository(session).list_active())
    if not products:
        await message.answer("Каталог пока пуст. Загляните позже.")
        return
    await send_carousel_card(message, products[0], 0, len(products))


@router.callback_query(F.data.startswith("cat:go:"))
async def handle_catalog_navigate(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
) -> None:
    await callback.answer()
    if callback.from_user is None or callback.data is None:
        return
    user = await resolve_user(session, callback.from_user.id, callback.from_user.username)
    if not await has_shop_access(bot, user):
        return
    parts = callback.data.split(":")
    index = int(parts[2])
    show_composition = parts[3] == "1"
    products = list(await ProductRepository(session).list_active())
    if not products:
        if callback.message is not None:
            try:
                await callback.message.edit_caption(caption="Каталог пока пуст. Загляните позже.")
            except TelegramBadRequest:
                return
        return
    total = len(products)
    index = index % total
    await edit_carousel_card(callback, products[index], index, total, show_composition)


@router.callback_query(F.data == "cat:home")
async def handle_catalog_home(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    await callback.answer()
    if callback.from_user is None or callback.message is None:
        return
    user = await resolve_user(session, callback.from_user.id, callback.from_user.username)
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await send_home(callback.message, user, "Главное меню")
