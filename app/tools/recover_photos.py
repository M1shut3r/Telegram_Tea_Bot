"""Check product photos after moving the shop to another bot and restore what can be restored.

Run from the project root with the virtualenv active, while the bot keeps running:

    python -m app.tools.recover_photos

Nothing in .env or the database changes. A Telegram file_id works only in the bot that
received the photo. For every active product the script checks the photo cache
(data/photos) and the current bot. If you enter the old bot token at the prompt, photos
the current bot cannot read are downloaded through the old bot into the cache. The Mini
App shows them right away, and the chat catalog uploads them to the new bot the first
time the product is opened.
"""

import asyncio
import mimetypes
from collections.abc import Sequence
from getpass import getpass

import aiohttp
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.utils.token import TokenValidationError

from app.config import settings
from app.database import async_session_factory
from app.models.product import Product
from app.repositories.products import ProductRepository
from app.services.photo_cache import read_cached_photo, store_cached_photo

CACHED = "фото есть"
WORKS = "фото работает"
RECOVERED = "фото восстановлено"
MISSING = "НЕТ ФОТО — загрузите заново в админке"


async def _can_read(bot: Bot, file_id: str) -> bool:
    try:
        await bot.get_file(file_id)
    except TelegramAPIError:
        return False
    return True


async def _download(bot: Bot, file_id: str) -> tuple[bytes, str] | None:
    try:
        telegram_file = await bot.get_file(file_id)
        if telegram_file.file_path is None:
            return None
        buffer = await bot.download_file(telegram_file.file_path)
    except (TelegramAPIError, aiohttp.ClientError, TimeoutError):
        return None
    if buffer is None:
        return None
    media_type = mimetypes.guess_type(telegram_file.file_path)[0] or "image/jpeg"
    return buffer.read(), media_type


async def check_products(
    products: Sequence[Product],
    current_bot: Bot,
    old_bot: Bot | None,
) -> list[tuple[Product, str]]:
    results: list[tuple[Product, str]] = []
    for product in products:
        if read_cached_photo(product.photo_id) is not None:
            status = CACHED
        elif await _can_read(current_bot, product.photo_id):
            status = WORKS
        else:
            photo = await _download(old_bot, product.photo_id) if old_bot is not None else None
            if photo is not None:
                store_cached_photo(product.photo_id, *photo)
                status = RECOVERED
            else:
                status = MISSING
        results.append((product, status))
    return results


def _ask_old_bot() -> Bot | None:
    print("Токен старого бота нужен, чтобы скачать фото, которые новый бот не видит.")
    print("Его можно взять в @BotFather: /mybots → старый бот → API Token.")
    raw = getpass("Токен старого бота (Enter — только проверить): ").strip()
    if not raw or raw == settings.bot_token:
        return None
    try:
        return Bot(token=raw)
    except TokenValidationError:
        print("Токен не похож на токен бота, продолжаю без него.")
        return None


async def main() -> None:
    old_bot = _ask_old_bot()
    current_bot = Bot(token=settings.bot_token)
    try:
        async with async_session_factory() as session:
            products = list(await ProductRepository(session).list_active())
        if not products:
            print("Активных товаров нет.")
            return
        results = await check_products(products, current_bot, old_bot)
    finally:
        await current_bot.session.close()
        if old_bot is not None:
            await old_bot.session.close()
    print()
    for product, status in results:
        print(f"#{product.id} {product.name} — {status}")
    missing = sum(1 for _, status in results if status == MISSING)
    print()
    print(f"Товаров: {len(results)}, без фото: {missing}.")
    if missing:
        print("Фото для них: Админ-панель → Редактировать товар → товар → Фото.")
        if old_bot is None:
            print("Или запустите скрипт ещё раз и введите токен старого бота.")


if __name__ == "__main__":
    asyncio.run(main())
