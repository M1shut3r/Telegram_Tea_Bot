from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import (
    ACTIVE_ORDER_STATUSES,
    ARCHIVED_ORDER_STATUSES,
    Order,
    OrderItem,
    OrderStatus,
)
from app.repositories import BaseRepository


class OrderRepository(BaseRepository[Order]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Order)

    async def create_with_items(
        self,
        user_id: int,
        customer_name: str,
        phone: str,
        country: str,
        city: str,
        address: str,
        items: Sequence[tuple[int, int, Decimal]],
        total_price: Decimal,
    ) -> Order:
        order = await self.create(
            user_id=user_id,
            customer_name=customer_name,
            phone=phone,
            country=country,
            city=city,
            address=address,
            total_price=total_price,
            status=OrderStatus.NEW.value,
        )
        for product_id, quantity, price_at_purchase in items:
            statement_values = {
                "order_id": order.id,
                "product_id": product_id,
                "quantity": quantity,
                "price_at_purchase": price_at_purchase,
            }
            item_repo = OrderItemRepository(self._session)
            await item_repo.create(**statement_values)
        created = await self.get_with_items(order.id)
        if created is None:
            raise RuntimeError("Order was not found after create")
        return created

    async def get_with_items(self, order_id: int) -> Order | None:
        statement = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.user),
            )
            .where(Order.id == order_id)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_recent(self, offset: int, limit: int) -> Sequence[Order]:
        statement = (
            select(Order)
            .options(selectinload(Order.user))
            .order_by(Order.created_at.desc(), Order.id.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def count_all(self) -> int:
        statement = select(func.count(Order.id))
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    async def _list_by_statuses(
        self,
        statuses: Sequence[str],
        offset: int,
        limit: int,
    ) -> Sequence[Order]:
        statement = (
            select(Order)
            .options(selectinload(Order.user))
            .where(Order.status.in_(list(statuses)))
            .order_by(Order.created_at.desc(), Order.id.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def _count_by_statuses(self, statuses: Sequence[str]) -> int:
        statement = select(func.count(Order.id)).where(Order.status.in_(list(statuses)))
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    async def get_active_orders(self, offset: int = 0, limit: int = 50) -> Sequence[Order]:
        return await self._list_by_statuses(ACTIVE_ORDER_STATUSES, offset, limit)

    async def get_archived_orders(self, offset: int = 0, limit: int = 50) -> Sequence[Order]:
        return await self._list_by_statuses(ARCHIVED_ORDER_STATUSES, offset, limit)

    async def count_active(self) -> int:
        return await self._count_by_statuses(ACTIVE_ORDER_STATUSES)

    async def count_archived(self) -> int:
        return await self._count_by_statuses(ARCHIVED_ORDER_STATUSES)

    async def list_for_user(
        self,
        user_id: int,
        limit: int = 10,
        statuses: Sequence[str] | None = None,
    ) -> Sequence[Order]:
        statement = select(Order).where(Order.user_id == user_id)
        if statuses is not None:
            statement = statement.where(Order.status.in_(list(statuses)))
        statement = statement.order_by(Order.created_at.desc(), Order.id.desc()).limit(limit)
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def get_for_user(self, order_id: int, user_id: int) -> Order | None:
        statement = select(Order).where(Order.id == order_id, Order.user_id == user_id)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        order_id: int,
        status: str,
        tracking_number: str | None = None,
    ) -> Order | None:
        values: dict[str, str] = {"status": status}
        if tracking_number is not None:
            values["tracking_number"] = tracking_number
        await self.update_by_id(order_id, **values)
        return await self.get_with_items(order_id)

    async def set_shipped(self, order_id: int, tracking_number: str) -> Order | None:
        return await self.update_status(
            order_id,
            OrderStatus.SHIPPED.value,
            tracking_number=tracking_number.strip(),
        )


class OrderItemRepository(BaseRepository[OrderItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, OrderItem)
