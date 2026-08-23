from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"timeout": 30},
    pool_pre_ping=True,
)
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def _add_missing_order_columns(connection: Any) -> None:
    result = await connection.execute(text("PRAGMA table_info(orders)"))
    existing = {row[1] for row in result.fetchall()}
    if "country" not in existing:
        await connection.execute(text("ALTER TABLE orders ADD COLUMN country VARCHAR(128) DEFAULT 'Россия'"))
    if "city" not in existing:
        await connection.execute(text("ALTER TABLE orders ADD COLUMN city VARCHAR(128) DEFAULT ''"))
    if "tracking_number" not in existing:
        await connection.execute(text("ALTER TABLE orders ADD COLUMN tracking_number VARCHAR(128)"))


async def init_db() -> None:
    from app.models import AdminInvite, Cart, Order, OrderItem, Product, User

    _ = (User, Product, Cart, Order, OrderItem, AdminInvite)
    async with engine.connect() as connection:
        await connection.execute(text("PRAGMA journal_mode=WAL"))
        await connection.execute(text("PRAGMA busy_timeout=8000"))
        await connection.execute(text("PRAGMA synchronous=NORMAL"))
        await connection.commit()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await _add_missing_order_columns(connection)


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with async_session_factory() as session:
            data["session"] = session
            result = await handler(event, data)
            await session.commit()
            return result
