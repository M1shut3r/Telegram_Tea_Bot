import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from api.deps import BotDep, SessionDep
from api.schemas import ProductOut
from api.serializers import serialize_product
from app.config import settings
from app.repositories.products import ProductRepository
from app.services.telegram_files import resolve_file_path

router = APIRouter()


@router.get("", response_model=list[ProductOut])
async def list_products(session: SessionDep) -> list[ProductOut]:
    products = await ProductRepository(session).list_active()
    return [serialize_product(product) for product in products]


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, session: SessionDep) -> ProductOut:
    product = await ProductRepository(session).get_by_id(product_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")
    return serialize_product(product)


@router.get("/{product_id}/photo")
async def get_product_photo(product_id: int, session: SessionDep, bot: BotDep) -> Response:
    product = await ProductRepository(session).get_by_id(product_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")
    file_path = await resolve_file_path(bot, product.photo_id)
    if file_path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фото недоступно")
    url = f"https://api.telegram.org/file/bot{settings.bot_token}/{file_path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            upstream = await client.get(url)
        except httpx.HTTPError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Не удалось загрузить фото",
            ) from error
    if upstream.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фото недоступно")
    media_type = upstream.headers.get("content-type", "image/jpeg")
    return Response(
        content=upstream.content,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=3000"},
    )
