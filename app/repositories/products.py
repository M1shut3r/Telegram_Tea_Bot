from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import select
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
