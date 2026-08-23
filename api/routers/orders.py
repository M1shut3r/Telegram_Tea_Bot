from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status

from api.deps import BotDep, SessionDep, StaffDep, UserDep
from api.schemas import CheckoutIn, CheckoutOut, OrderDetailOut, OrderOut
from api.serializers import serialize_order, serialize_order_detail
from app.models.order import ACTIVE_ORDER_STATUSES, ARCHIVED_ORDER_STATUSES
from app.repositories.orders import OrderRepository
from app.services.order_management import OrderNotCancellableError, OrderNotFoundError, cancel_order
from app.services.ordering import EmptyCartError, place_order

router = APIRouter()

StatusFilter = Literal["active", "archived"]


def _statuses_for_filter(value: str | None) -> tuple[str, ...] | None:
    if value is None:
        return None
    if value == "active":
        return ACTIVE_ORDER_STATUSES
    if value == "archived":
        return ARCHIVED_ORDER_STATUSES
    return None


@router.get("", response_model=list[OrderOut])
@router.get("/my", response_model=list[OrderOut])
async def list_orders(
    session: SessionDep,
    user: UserDep,
    status_filter: Annotated[StatusFilter | None, Query(alias="status")] = None,
) -> list[OrderOut]:
    orders = await OrderRepository(session).list_for_user(
        user.id,
        limit=50,
        statuses=_statuses_for_filter(status_filter),
    )
    return [serialize_order(order) for order in orders]


@router.get("/admin", response_model=list[OrderOut])
async def list_admin_orders(
    session: SessionDep,
    user: StaffDep,
    status_filter: Annotated[StatusFilter | None, Query(alias="status")] = None,
) -> list[OrderOut]:
    repository = OrderRepository(session)
    if status_filter == "archived":
        orders = await repository.get_archived_orders(limit=50)
    else:
        orders = await repository.get_active_orders(limit=50)
    return [serialize_order(order) for order in orders]


@router.post("/{order_id}/cancel", response_model=OrderDetailOut)
async def cancel_my_order(
    order_id: int,
    session: SessionDep,
    user: UserDep,
    bot: BotDep,
) -> OrderDetailOut:
    repository = OrderRepository(session)
    order = await repository.get_for_user(order_id, user.id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    try:
        cancelled = await cancel_order(session, bot, order.id, "user")
    except OrderNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден") from error
    except OrderNotCancellableError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Заказ нельзя отменить",
        ) from error
    return serialize_order_detail(cancelled)


@router.get("/{order_id}", response_model=OrderDetailOut)
async def get_order(order_id: int, session: SessionDep, user: UserDep) -> OrderDetailOut:
    repository = OrderRepository(session)
    order = await repository.get_with_items(order_id)
    if order is None or order.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    return serialize_order_detail(order)


@router.post("/checkout", response_model=CheckoutOut)
async def checkout(payload: CheckoutIn, session: SessionDep, user: UserDep, bot: BotDep) -> CheckoutOut:
    try:
        order = await place_order(
            session=session,
            bot=bot,
            user=user,
            customer_name=payload.customer_name,
            phone=payload.phone,
            country=payload.country,
            city=payload.city,
            address=payload.address,
        )
    except EmptyCartError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Корзина пуста. Оформление невозможно.",
        ) from error
    return CheckoutOut(order=serialize_order(order))
