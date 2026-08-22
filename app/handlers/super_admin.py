from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.admin_kb import admins_keyboard, super_admin_keyboard
from app.keyboards.user_kb import SUPER_ADMIN_BUTTON
from app.models.user import User, UserRole
from app.repositories.users import UserRepository
from app.services.admin_manager import HasRole, build_invite_link, create_invite, revoke_admin

router = Router()
router.message.filter(HasRole(UserRole.SUPER_ADMIN.value))
router.callback_query.filter(HasRole(UserRole.SUPER_ADMIN.value))


@router.message(StateFilter(default_state), F.text == SUPER_ADMIN_BUTTON)
async def handle_super_admin_panel(message: Message) -> None:
    await message.answer("Управление командой", reply_markup=super_admin_keyboard())


@router.callback_query(F.data == "sadm:home")
async def handle_super_admin_home(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await callback.answer()
    await callback.message.edit_text("Управление командой", reply_markup=super_admin_keyboard())


@router.callback_query(F.data == "sadm:invite")
async def handle_create_invite(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
    staff_user: User,
) -> None:
    token = await create_invite(session, staff_user.id)
    link = await build_invite_link(bot, token)
    await callback.answer()
    if callback.message is None:
        return
    await callback.message.answer(
        "Инвайт-ссылка для нового администратора:\n"
        f"{link}\n\n"
        "Ссылка одноразовая. После перехода по ней пользователь получит роль admin."
    )


@router.callback_query(F.data == "sadm:admins")
async def handle_admins_list(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.message is None:
        await callback.answer()
        return
    admins = await UserRepository(session).list_by_roles(
        (UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value),
    )
    await callback.answer()
    await callback.message.edit_text(
        "Команда администраторов. Нажмите, чтобы снять права с обычного админа.",
        reply_markup=admins_keyboard(admins),
    )


@router.callback_query(F.data == "sadm:noop")
async def handle_super_admin_noop(callback: CallbackQuery) -> None:
    await callback.answer("Права супер-администратора снять нельзя.")


@router.callback_query(F.data.startswith("sadm:rm:"))
async def handle_revoke_admin(
    callback: CallbackQuery,
    session: AsyncSession,
    staff_user: User,
) -> None:
    if callback.data is None:
        await callback.answer()
        return
    target_id = int(callback.data.split(":")[2])
    result = await revoke_admin(session, target_id, staff_user)
    messages = {
        "revoked": "Права администратора сняты.",
        "missing": "Пользователь не найден.",
        "self": "Нельзя снять права с самого себя.",
        "forbidden": "Этого пользователя нельзя разжаловать.",
    }
    await callback.answer(messages.get(result, messages["forbidden"]), show_alert=True)
    if callback.message is None or result != "revoked":
        return
    admins = await UserRepository(session).list_by_roles(
        (UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value),
    )
    await callback.message.edit_reply_markup(reply_markup=admins_keyboard(admins))
