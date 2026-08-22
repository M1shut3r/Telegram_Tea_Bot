from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

ModelT = TypeVar("ModelT", bound=DeclarativeBase)


class BaseRepository(Generic[ModelT]):
    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self._session = session
        self._model = model

    async def get_by_id(self, entity_id: int) -> ModelT | None:
        return await self._session.get(self._model, entity_id)

    async def get_all(self) -> Sequence[ModelT]:
        result = await self._session.execute(select(self._model))
        return result.scalars().all()

    async def create(self, **values: Any) -> ModelT:
        statement = insert(self._model).values(**values)
        result = await self._session.execute(statement)
        await self._session.flush()
        entity_id = result.inserted_primary_key[0]
        entity = await self.get_by_id(int(entity_id))
        if entity is None:
            raise RuntimeError(f"{self._model.__name__} was not created")
        return entity

    async def update_by_id(self, entity_id: int, **values: Any) -> None:
        statement = update(self._model).where(self._model.id == entity_id).values(**values)
        await self._session.execute(statement)
        await self._session.flush()

    async def delete_by_id(self, entity_id: int) -> None:
        statement = delete(self._model).where(self._model.id == entity_id)
        await self._session.execute(statement)
        await self._session.flush()
