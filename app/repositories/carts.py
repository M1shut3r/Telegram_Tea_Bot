from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart
from app.models.user import User
from app.repositories import BaseRepository


class CartRepository(BaseRepository[Cart]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Cart)

    async def get_with_products(self, user_id: int) -> Sequence[Cart]:
        statement = (
            select(Cart)
            .options(selectinload(Cart.product))
            .where(Cart.user_id == user_id)
            .order_by(Cart.created_at, Cart.id)
        )
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def get_item(self, user_id: int, product_id: int) -> Cart | None:
        statement = select(Cart).where(
            Cart.user_id == user_id,
            Cart.product_id == product_id,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def add_product(self, user_id: int, product_id: int) -> tuple[Cart, bool]:
        existing = await self.get_item(user_id, product_id)
        if existing is not None:
            await self.update_by_id(existing.id, quantity=existing.quantity + 1)
            updated = await self.get_by_id(existing.id)
            if updated is None:
                raise RuntimeError("Cart item was not found after update")
            return updated, False
        created = await self.create(user_id=user_id, product_id=product_id, quantity=1)
        return created, True

    async def set_quantity(self, cart_id: int, quantity: int) -> Cart | None:
        if quantity <= 0:
            await self.delete_by_id(cart_id)
            return None
        await self.update_by_id(cart_id, quantity=quantity)
        return await self.get_by_id(cart_id)

    async def increment(self, cart_id: int) -> Cart | None:
        item = await self.get_by_id(cart_id)
        if item is None:
            return None
        return await self.set_quantity(cart_id, item.quantity + 1)

    async def decrement(self, cart_id: int) -> Cart | None:
        item = await self.get_by_id(cart_id)
        if item is None:
            return None
        return await self.set_quantity(cart_id, item.quantity - 1)

    async def count_items(self, user_id: int) -> int:
        statement = select(func.coalesce(func.sum(Cart.quantity), 0)).where(Cart.user_id == user_id)
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    async def clear_for_user(self, user_id: int) -> None:
        statement = delete(Cart).where(Cart.user_id == user_id)
        await self._session.execute(statement)
        await self._session.flush()

    async def earliest_created_by_telegram(self) -> Sequence[tuple[int, datetime]]:
        statement = (
            select(User.telegram_id, func.min(Cart.created_at))
            .join(User, User.id == Cart.user_id)
            .group_by(User.telegram_id)
        )
        result = await self._session.execute(statement)
        return list(result.all())

    async def get_user_id_by_telegram(self, telegram_id: int) -> int | None:
        statement = select(User.id).where(User.telegram_id == telegram_id)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_telegram_id_by_user_id(self, user_id: int) -> int | None:
        statement = select(User.telegram_id).where(User.id == user_id)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()
