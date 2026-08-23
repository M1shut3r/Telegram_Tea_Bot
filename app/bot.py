import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import MenuButtonWebApp, WebAppInfo
from aiogram.utils.backoff import BackoffConfig

from app.config import settings
from app.database import DatabaseMiddleware, init_db
from app.handlers.admin import router as admin_router
from app.handlers.cart import router as cart_router
from app.handlers.catalog import router as catalog_router
from app.handlers.orders import router as orders_router
from app.handlers.start import router as start_router
from app.handlers.super_admin import router as super_admin_router
from app.services.cart_lifecycle import cart_scheduler, restore_cart_jobs

_SILENCED_LOGGERS = (
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
    "aiogram",
    "aiohttp",
    "aiohttp.access",
    "httpx",
    "httpcore",
    "sqlalchemy",
    "sqlalchemy.engine",
    "apscheduler",
    "asyncio",
)


def _configure_logging() -> str:
    level_name = settings.log_level.strip().upper()
    level = getattr(logging, level_name, logging.CRITICAL)
    logging.basicConfig(level=level, force=True)
    if level >= logging.CRITICAL:
        logging.disable(logging.CRITICAL)
    for name in _SILENCED_LOGGERS:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False
        if level >= logging.CRITICAL:
            logger.disabled = True
            logger.handlers.clear()
            logger.addHandler(logging.NullHandler())
    return "critical" if level >= logging.CRITICAL else level_name.lower()


def _telegram_session() -> AiohttpSession:
    session = AiohttpSession(timeout=35.0)
    session._connector_init.update(
        keepalive_timeout=20,
        enable_cleanup_closed=True,
        ttl_dns_cache=300,
        limit=100,
    )
    return session


async def _start_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    await dispatcher.start_polling(
        bot,
        polling_timeout=20,
        handle_as_tasks=True,
        close_bot_session=False,
        backoff_config=BackoffConfig(min_delay=0.2, max_delay=2.0, factor=1.3, jitter=0.1),
    )


async def main() -> None:
    log_level = _configure_logging()
    if settings.public_webapp_url is None and log_level != "critical":
        logging.warning("WEBAPP_URL is empty or invalid. Mini App button is hidden until you set a real https:// URL.")
    await init_db()
    bot = Bot(token=settings.bot_token, parse_mode="HTML", session=_telegram_session())
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
                log_level=log_level,
                access_log=False,
                loop="asyncio",
                timeout_keep_alive=75,
                timeout_graceful_shutdown=15,
                limit_concurrency=200,
            )
            server = uvicorn.Server(config)
            server.install_signal_handlers = False
            await asyncio.gather(_start_polling(dispatcher, bot), server.serve())
        else:
            await _start_polling(dispatcher, bot)
    finally:
        if cart_scheduler.running:
            cart_scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
