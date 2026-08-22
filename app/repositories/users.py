from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invite import AdminInvite
from app.models.user import User, UserRole
from app.repositories import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        statement = select(User).where(User.telegram_id == telegram_id)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        telegram_id: int,
        username: str | None,
        super_admin_id: int,
    ) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        default_role = UserRole.SUPER_ADMIN.value if telegram_id == super_admin_id else UserRole.USER.value
        if user is None:
            return await self.create(
                telegram_id=telegram_id,
                username=username,
                role=default_role,
            )
        updates: dict[str, str | None] = {}
        if user.username != username:
            updates["username"] = username
        if telegram_id == super_admin_id and user.role != UserRole.SUPER_ADMIN.value:
            updates["role"] = UserRole.SUPER_ADMIN.value
        if updates:
            await self.update_by_id(user.id, **updates)
            refreshed = await self.get_by_id(user.id)
            if refreshed is None:
                raise RuntimeError("User was not found after update")
            return refreshed
        return user

    async def list_by_roles(self, roles: Sequence[str]) -> Sequence[User]:
        statement = select(User).where(User.role.in_(roles)).order_by(User.id)
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def set_role(self, user_id: int, role: str) -> None:
        await self.update_by_id(user_id, role=role)


class InviteRepository(BaseRepository[AdminInvite]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AdminInvite)

    async def get_by_token(self, token: str) -> AdminInvite | None:
        statement = select(AdminInvite).where(AdminInvite.token == token)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def mark_used(self, invite_id: int, used_by: int) -> None:
        statement = update(AdminInvite).where(AdminInvite.id == invite_id).values(is_used=True, used_by=used_by)
        await self._session.execute(statement)
        await self._session.flush()
