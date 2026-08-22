from uuid import uuid4

from aiogram import Bot
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.users import InviteRepository, UserRepository

INVITE_PREFIX = "invite_"


class HasRole(BaseFilter):
    def __init__(self, *roles: str) -> None:
        self._roles = set(roles)

    async def __call__(
        self,
        event: Message | CallbackQuery,
        session: AsyncSession,
    ) -> bool | dict[str, User]:
        if event.from_user is None:
            return False
        repository = UserRepository(session)
        user = await repository.get_by_telegram_id(event.from_user.id)
        if user is None or user.role not in self._roles:
            return False
        return {"staff_user": user}


async def create_invite(session: AsyncSession, created_by: int) -> str:
    token = uuid4().hex
    repository = InviteRepository(session)
    await repository.create(token=token, created_by=created_by, is_used=False)
    return token


async def build_invite_link(bot: Bot, token: str) -> str:
    me = await bot.get_me()
    return f"https://t.me/{me.username}?start={INVITE_PREFIX}{token}"


async def activate_invite(session: AsyncSession, token: str, user: User) -> str:
    repository = InviteRepository(session)
    invite = await repository.get_by_token(token)
    if invite is None:
        return "invalid"
    if invite.is_used:
        return "used"
    if user.role in {UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value}:
        return "already_staff"
    user_repository = UserRepository(session)
    await user_repository.set_role(user.id, UserRole.ADMIN.value)
    await repository.mark_used(invite.id, user.id)
    user.role = UserRole.ADMIN.value
    return "activated"


async def revoke_admin(session: AsyncSession, target_user_id: int, actor: User) -> str:
    repository = UserRepository(session)
    target = await repository.get_by_id(target_user_id)
    if target is None:
        return "missing"
    if target.id == actor.id:
        return "self"
    if target.role != UserRole.ADMIN.value:
        return "forbidden"
    await repository.set_role(target.id, UserRole.USER.value)
    return "revoked"
