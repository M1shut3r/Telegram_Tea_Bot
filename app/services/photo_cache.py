import asyncio
from hashlib import sha256
from pathlib import Path

import httpx
from aiogram import Bot
from fastapi import HTTPException, status
from fastapi.responses import FileResponse, Response

from app.config import settings
from app.services.telegram_files import resolve_file_path

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "photos"
_FETCH_LOCKS: dict[str, asyncio.Lock] = {}
_LOCKS_GUARD = asyncio.Lock()
_FETCH_LIMIT = asyncio.Semaphore(4)
_CACHE_HEADERS = {"Cache-Control": "public, max-age=86400"}


def _cache_paths(file_id: str) -> tuple[Path, Path]:
    key = sha256(file_id.encode("utf-8")).hexdigest()
    return _CACHE_DIR / key, _CACHE_DIR / f"{key}.type"


async def _lock_for(file_id: str) -> asyncio.Lock:
    async with _LOCKS_GUARD:
        lock = _FETCH_LOCKS.get(file_id)
        if lock is None:
            lock = asyncio.Lock()
            _FETCH_LOCKS[file_id] = lock
        return lock


def _read_cached(file_id: str) -> FileResponse | None:
    body_path, type_path = _cache_paths(file_id)
    if not body_path.is_file():
        return None
    media_type = "image/jpeg"
    if type_path.is_file():
        media_type = type_path.read_text(encoding="utf-8").strip() or media_type
    return FileResponse(body_path, media_type=media_type, headers=_CACHE_HEADERS)


def _write_cached(file_id: str, content: bytes, media_type: str) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    body_path, type_path = _cache_paths(file_id)
    tmp_path = body_path.with_suffix(".tmp")
    tmp_path.write_bytes(content)
    tmp_path.replace(body_path)
    type_path.write_text(media_type, encoding="utf-8")


async def load_product_photo(bot: Bot, photo_id: str, http: httpx.AsyncClient) -> Response:
    cached = _read_cached(photo_id)
    if cached is not None:
        return cached
    lock = await _lock_for(photo_id)
    async with lock:
        cached = _read_cached(photo_id)
        if cached is not None:
            return cached
        file_path = await resolve_file_path(bot, photo_id)
        if file_path is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фото недоступно")
        url = f"https://api.telegram.org/file/bot{settings.bot_token}/{file_path}"
        async with _FETCH_LIMIT:
            try:
                upstream = await http.get(url)
            except httpx.HTTPError as error:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Не удалось загрузить фото",
                ) from error
        if upstream.status_code != status.HTTP_200_OK:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фото недоступно")
        media_type = upstream.headers.get("content-type", "image/jpeg")
        _write_cached(photo_id, upstream.content, media_type)
        return Response(content=upstream.content, media_type=media_type, headers=_CACHE_HEADERS)
