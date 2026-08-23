import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import MenuButtonWebApp, WebAppInfo

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
    if settings.public_webapp_url is None:
        logging.warning("WEBAPP_URL is empty or invalid. Mini App button is hidden until you set a real https:// URL.")
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
    webapp_url = settings.public_webapp_url
    if webapp_url is not None:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="Витрина", web_app=WebAppInfo(url=webapp_url)),
        )
    cart_scheduler.start()
    await restore_cart_jobs(bot)
    try:
        if settings.webapp_serve:
            import uvicorn

            from api.main import app as web_app

            web_app.state.bot = bot
            config = uvicorn.Config(
                web_app,
                host=settings.webapp_host,
                port=settings.webapp_port,
                log_level="info",
                loop="asyncio",
                timeout_keep_alive=75,
                timeout_graceful_shutdown=15,
                limit_concurrency=200,
            )
            server = uvicorn.Server(config)
            server.install_signal_handlers = False
            await asyncio.gather(dispatcher.start_polling(bot), server.serve())
        else:
            await dispatcher.start_polling(bot)
    finally:
        if cart_scheduler.running:
            cart_scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
