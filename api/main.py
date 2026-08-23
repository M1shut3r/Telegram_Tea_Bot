from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path

from aiogram import Bot
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from api.deps import get_current_user
from api.routers.cart import router as cart_router
from api.routers.orders import router as orders_router
from api.routers.products import router as products_router
from app.config import settings
from app.database import init_db
from app.services.cart_lifecycle import cart_scheduler

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
INDEX_FILE = FRONTEND_DIST / "index.html"


def _safe_frontend_file(asset_path: str) -> Path | None:
    candidate = (FRONTEND_DIST / asset_path).resolve()
    try:
        candidate.relative_to(FRONTEND_DIST.resolve())
    except ValueError:
        return None
    if candidate.is_file():
        return candidate
    return None


def extract_telegram_init_data(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    header_value = request.headers.get("x-telegram-init-data", "")
    query_value = request.query_params.get("_auth", "")
    for item in (header_value, authorization, query_value):
        if item and item.strip():
            return item.strip()
    return ""


class TelegramAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[StarletteResponse]],
    ) -> StarletteResponse:
        request.state.telegram_init_data = extract_telegram_init_data(request)
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    owns_bot = getattr(app.state, "bot", None) is None
    if owns_bot:
        app.state.bot = Bot(token=settings.bot_token, parse_mode="HTML")
        if not cart_scheduler.running:
            cart_scheduler.start()
    try:
        yield
    finally:
        if owns_bot:
            await app.state.bot.session.close()
            if cart_scheduler.running:
                cart_scheduler.shutdown(wait=False)


app = FastAPI(title="Tea Shop Mini App", lifespan=lifespan, redirect_slashes=False)
app.add_middleware(TelegramAuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(products_router, prefix="/api/products", tags=["products"])
app.include_router(cart_router, prefix="/api/cart", tags=["cart"])
app.include_router(orders_router, prefix="/api/orders", tags=["orders"])

FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    '<rect width="32" height="32" rx="8" fill="#0b0c10"/>'
    '<text x="16" y="22" text-anchor="middle" font-size="14" fill="#67e8c8">Ж</text>'
    "</svg>"
)


@app.get("/favicon.ico")
async def favicon() -> Response:
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")


def _index_response() -> FileResponse:
    if not INDEX_FILE.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mini App не собран")
    return FileResponse(INDEX_FILE)


@app.get("/webapp")
@app.get("/webapp/")
async def webapp_index() -> FileResponse:
    return _index_response()


@app.get("/webapp/{asset_path:path}")
async def webapp_asset(asset_path: str) -> FileResponse:
    existing = _safe_frontend_file(asset_path)
    if existing is not None:
        return FileResponse(existing)
    return _index_response()


__all__ = ("app", "get_current_user")
