from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, Message

from app.models.product import Product
from app.services.photo_cache import read_cached_photo, store_cached_photo

PHOTO_UNAVAILABLE_NOTE = "<i>Фото временно недоступно.</i>"
_EXTENSIONS = {"image/png": "png", "image/webp": "webp"}


def is_not_modified(error: TelegramBadRequest) -> bool:
    return "message is not modified" in error.message


async def answer_product_card(
    message: Message,
    product: Product,
    caption: str,
    reply_markup: InlineKeyboardMarkup,
) -> Message:
    """Send a product card even when this bot cannot use the stored photo_id.

    A Telegram file_id belongs to the bot that received the file, so every product photo
    breaks after the shop switches to another bot token. Attempts, in order: the stored id;
    the copy cached by the Mini App photo proxy, uploaded again (the product keeps the new id,
    committed by DatabaseMiddleware); a text card without the photo.
    """
    try:
        return await message.answer_photo(photo=product.photo_id, caption=caption, reply_markup=reply_markup)
    except TelegramBadRequest:
        pass
    cached = read_cached_photo(product.photo_id)
    if cached is not None:
        content, media_type = cached
        extension = _EXTENSIONS.get(media_type, "jpg")
        upload = BufferedInputFile(content, filename=f"product-{product.id}.{extension}")
        try:
            sent = await message.answer_photo(photo=upload, caption=caption, reply_markup=reply_markup)
        except TelegramBadRequest:
            sent = None
        if sent is not None:
            if sent.photo:
                new_photo_id = sent.photo[-1].file_id
                store_cached_photo(new_photo_id, content, media_type)
                product.photo_id = new_photo_id
            return sent
    return await message.answer(f"{caption}\n\n{PHOTO_UNAVAILABLE_NOTE}", reply_markup=reply_markup)
