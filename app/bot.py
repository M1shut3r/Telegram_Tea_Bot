import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.database import DatabaseMiddleware, init_db
from app.handlers.admin import router as admin_router
from app.handlers.cart import router as cart_router
from app.handlers.catalog import router as catalog_router
from app.handlers.orders import router as orders_router
from app.handlers.start import router as start_router
from app.handlers.super_admin import router as super_admin_router
from app.services.cart_lifecycle import cart_scheduler, restore_cart_jobs


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    await init_db()
    bot = Bot(token=settings.bot_token, parse_mode="HTML")
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.update.middleware(DatabaseMiddleware())
    dispatcher.include_routers(
        start_router,
        orders_router,
        cart_router,
        catalog_router,
        admin_router,
        super_admin_router,
    )
    cart_scheduler.start()
    await restore_cart_jobs(bot)
    try:
        await dispatcher.start_polling(bot)
    finally:
        if cart_scheduler.running:
            cart_scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
