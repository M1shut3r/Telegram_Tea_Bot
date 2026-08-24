from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Product)

    async def list_active(self) -> Sequence[Product]:
        statement = select(Product).where(Product.is_active.is_(True)).order_by(Product.id)
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def count_active(self) -> int:
        statement = select(func.count()).select_from(Product).where(Product.is_active.is_(True))
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    async def list_active_page(self, offset: int, limit: int) -> Sequence[Product]:
        statement = select(Product).where(Product.is_active.is_(True)).order_by(Product.id).offset(offset).limit(limit)
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def add_product(
        self,
        name: str,
        photo_id: str,
        description: str,
        composition: str,
        price: Decimal,
    ) -> Product:
        return await self.create(
            name=name,
            photo_id=photo_id,
            description=description,
            composition=composition,
            price=price,
            is_active=True,
        )

    async def update_fields(self, product_id: int, **values: Any) -> Product | None:
        product = await self.get_by_id(product_id)
        if product is None or not product.is_active:
            return None
        for key, value in values.items():
            setattr(product, key, value)
        await self._session.flush()
        return product

    async def deactivate(self, product_id: int) -> Product | None:
        return await self.update_fields(product_id, is_active=False)
