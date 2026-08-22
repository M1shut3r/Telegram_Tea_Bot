from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem, OrderStatus
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

    async def list_for_user(self, user_id: int, limit: int = 10) -> Sequence[Order]:
        statement = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc(), Order.id.desc())
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def get_for_user(self, order_id: int, user_id: int) -> Order | None:
        statement = select(Order).where(Order.id == order_id, Order.user_id == user_id)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def update_status(self, order_id: int, status: str) -> Order | None:
        await self.update_by_id(order_id, status=status)
        return await self.get_with_items(order_id)


class OrderItemRepository(BaseRepository[OrderItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, OrderItem)
