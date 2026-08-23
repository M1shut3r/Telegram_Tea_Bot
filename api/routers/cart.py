from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import BotDep, SessionDep, UserDep
from api.schemas import CartAddIn, CartOut, CartQuantityIn
from api.serializers import serialize_cart
from app.repositories.carts import CartRepository
from app.repositories.products import ProductRepository
from app.services.cart_lifecycle import cancel_cart_jobs, schedule_cart_jobs

router = APIRouter()


async def _active_cart(session: AsyncSession, user_id: int) -> CartOut:
    items = await CartRepository(session).get_with_products(user_id)
    active = [item for item in items if item.product is not None and item.product.is_active]
    return serialize_cart(list(active))


@router.get("", response_model=CartOut)
async def get_cart(session: SessionDep, user: UserDep) -> CartOut:
    return await _active_cart(session, user.id)


@router.post("/add", response_model=CartOut)
async def add_to_cart(payload: CartAddIn, session: SessionDep, user: UserDep, bot: BotDep) -> CartOut:
    product = await ProductRepository(session).get_by_id(payload.product_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар недоступен")
    repository = CartRepository(session)
    was_empty = await repository.count_items(user.id) == 0
    await repository.add_product(user.id, payload.product_id)
    if was_empty:
        schedule_cart_jobs(bot, user.telegram_id)
    return await _active_cart(session, user.id)


@router.post("/quantity", response_model=CartOut)
async def set_cart_quantity(payload: CartQuantityIn, session: SessionDep, user: UserDep) -> CartOut:
    repository = CartRepository(session)
    item = await repository.get_item(user.id, payload.product_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден в корзине")
    await repository.set_quantity(item.id, payload.quantity)
    cart = await _active_cart(session, user.id)
    if cart.count == 0:
        cancel_cart_jobs(user.telegram_id)
    return cart
