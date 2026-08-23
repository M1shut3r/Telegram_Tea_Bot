from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import Response

from api.deps import BotDep, SessionDep
from api.schemas import ProductOut
from api.serializers import serialize_product
from app.repositories.products import ProductRepository
from app.services.photo_cache import load_product_photo

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
async def get_product_photo(product_id: int, request: Request, session: SessionDep, bot: BotDep) -> Response:
    product = await ProductRepository(session).get_by_id(product_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")
    http = getattr(request.app.state, "http", None)
    if http is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Сервис фото недоступен")
    return await load_product_photo(bot, product.photo_id, http)
