import logging
from collections.abc import AsyncGenerator
from typing import Annotated

from aiogram import Bot
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_factory
from app.models.user import User, UserRole
from app.repositories.users import UserRepository
from app.services.telegram_webapp import InvalidWebAppDataError, parse_webapp_user

logger = logging.getLogger(__name__)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_bot(request: Request) -> Bot:
    bot = getattr(request.app.state, "bot", None)
    if bot is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Бот недоступен")
    return bot


def _extract_init_data(request: Request, header_init_data: str, authorization: str) -> str:
    candidates = (
        getattr(request.state, "telegram_init_data", ""),
        header_init_data,
        authorization,
        request.headers.get("x-telegram-init-data", ""),
        request.query_params.get("_auth", ""),
    )
    for item in candidates:
        if item and str(item).strip():
            return str(item).strip()
    return ""


async def get_current_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    init_data: Annotated[str, Header(alias="X-Telegram-Init-Data")] = "",
    authorization: Annotated[str, Header(alias="Authorization")] = "",
    debug_telegram_id: Annotated[int | None, Header(alias="X-Debug-Telegram-Id")] = None,
) -> User:
    if settings.webapp_debug and debug_telegram_id is not None:
        return await UserRepository(session).upsert(
            debug_telegram_id,
            None,
            settings.super_admin_id,
        )
    payload = _extract_init_data(request, init_data, authorization)
    try:
        webapp_user = parse_webapp_user(payload, settings.bot_token)
    except InvalidWebAppDataError as error:
        logger.warning(
            "WebApp auth failed: %s has_payload=%s header_keys=%s",
            error.reason,
            bool(payload.strip()),
            sorted(request.headers.keys()),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительные данные Telegram",
        ) from error
    return await UserRepository(session).upsert(
        webapp_user.id,
        webapp_user.username,
        settings.super_admin_id,
    )


SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserDep = Annotated[User, Depends(get_current_user)]
BotDep = Annotated[Bot, Depends(get_bot)]


async def require_staff(user: UserDep) -> User:
    if user.role not in {UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return user


StaffDep = Annotated[User, Depends(require_staff)]
