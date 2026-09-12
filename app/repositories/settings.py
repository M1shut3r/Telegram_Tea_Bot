from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shop_setting import ShopSetting


class ShopSettingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_value(self, key: str) -> str | None:
        entity = await self._session.get(ShopSetting, key)
        if entity is None:
            return None
        value = entity.value.strip()
        return value or None

    async def set_value(self, key: str, value: str) -> None:
        entity = await self._session.get(ShopSetting, key)
        if entity is None:
            self._session.add(ShopSetting(key=key, value=value))
        else:
            entity.value = value
        await self._session.flush()

    async def delete_value(self, key: str) -> None:
        entity = await self._session.get(ShopSetting, key)
        if entity is None:
            return
        await self._session.delete(entity)
        await self._session.flush()
