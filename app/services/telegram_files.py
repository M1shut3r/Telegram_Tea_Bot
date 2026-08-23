from time import time

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

_CACHE_TTL_SECONDS = 3_000.0
_cache: dict[str, tuple[str, float]] = {}


async def resolve_file_path(bot: Bot, file_id: str) -> str | None:
    cached = _cache.get(file_id)
    now = time()
    if cached is not None and cached[1] > now:
        return cached[0]
    try:
        telegram_file = await bot.get_file(file_id)
    except TelegramAPIError:
        return None
    if telegram_file.file_path is None:
        return None
    _cache[file_id] = (telegram_file.file_path, now + _CACHE_TTL_SECONDS)
    return telegram_file.file_path
