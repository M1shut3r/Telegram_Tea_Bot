from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.start import send_home
from app.keyboards.admin_kb import (
    admins_keyboard,
    super_admin_keyboard,
    support_contact_keyboard,
    support_pick_keyboard,
)
from app.keyboards.user_kb import CANCEL_BUTTON, SUPER_ADMIN_BUTTON, cancel_menu
from app.models.user import User, UserRole
from app.repositories.users import UserRepository
from app.services.admin_manager import HasRole, build_invite_link, create_invite, revoke_admin
from app.services.support_contact import (
    SupportContact,
    clear_support_contact,
    extract_support_from_message,
    get_support_contact,
    set_support_contact,
)

router = Router()
router.message.filter(HasRole(UserRole.SUPER_ADMIN.value))
router.callback_query.filter(HasRole(UserRole.SUPER_ADMIN.value))


class SupportContactState(StatesGroup):
    waiting = State()


def support_screen_text(label: str) -> str:
    return f"Контакт для кнопки «Связаться с поддержкой».\n\nСейчас: {escape(label)}"


async def show_support_screen(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.message is None:
        return
    contact = await get_support_contact(session)
    text = support_screen_text(contact.label)
    markup = support_contact_keyboard(contact.is_set)
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=markup)


@router.message(StateFilter(default_state), F.text == SUPER_ADMIN_BUTTON)
async def handle_super_admin_panel(message: Message) -> None:
    await message.answer("Управление командой", reply_markup=super_admin_keyboard())


@router.callback_query(F.data == "sadm:home")
async def handle_super_admin_home(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await state.clear()
    await callback.answer()
    await callback.message.edit_text("Управление командой", reply_markup=super_admin_keyboard())


@router.callback_query(F.data == "sadm:invite")
async def handle_create_invite(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
    staff_user: User,
    state: FSMContext,
) -> None:
    await state.clear()
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
async def handle_admins_list(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await state.clear()
    admins = await UserRepository(session).list_by_roles(
        (UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value),
    )
    await callback.answer()
    await callback.message.edit_text(
        "Команда администраторов. Нажмите, чтобы снять права с обычного админа.",
        reply_markup=admins_keyboard(admins),
    )


@router.callback_query(F.data == "sadm:support")
async def handle_support_contact(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await state.clear()
    await callback.answer()
    await show_support_screen(callback, session)


@router.callback_query(F.data == "sadm:spick")
async def handle_support_pick(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await state.clear()
    admins = await UserRepository(session).list_by_roles(
        (UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value),
    )
    await callback.answer()
    if not admins:
        await callback.message.edit_text(
            "В команде пока никого нет. Укажите контакт вручную.",
            reply_markup=support_contact_keyboard(False),
        )
        return
    await callback.message.edit_text(
        "Выберите, кто будет отображаться в поддержке.",
        reply_markup=support_pick_keyboard(admins),
    )


@router.callback_query(F.data.startswith("sadm:sset:"))
async def handle_support_set_from_team(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer()
        return
    try:
        user_id = int(parts[2])
    except ValueError:
        await callback.answer()
        return
    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return
    await state.clear()
    contact = await set_support_contact(session, user.telegram_id, user.username)
    await callback.answer(f"Поддержка: {contact.label}")
    await show_support_screen(callback, session)


@router.callback_query(F.data == "sadm:smanual")
async def handle_support_manual_start(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await state.set_state(SupportContactState.waiting)
    await callback.answer()
    await callback.message.answer(
        "Отправьте @username, Telegram ID или перешлите сообщение человека, "
        "который должен отображаться в поддержке.\n"
        "Можно также отправить контакт Telegram.\n"
        "Чтобы отменить, нажмите «Отмена».",
        reply_markup=cancel_menu(),
    )


@router.callback_query(F.data == "sadm:sclear")
async def handle_support_clear(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    if callback.message is None:
        await callback.answer()
        return
    await state.clear()
    await clear_support_contact(session)
    await callback.answer("Контакт поддержки сброшен.")
    await show_support_screen(callback, session)


@router.message(SupportContactState.waiting, F.text == CANCEL_BUTTON)
async def handle_support_manual_cancel(
    message: Message,
    state: FSMContext,
    staff_user: User,
) -> None:
    await state.clear()
    await send_home(message, staff_user, "Назначение контакта поддержки отменено.")


@router.message(SupportContactState.waiting)
async def handle_support_manual_value(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    staff_user: User,
) -> None:
    parsed = extract_support_from_message(message)
    if parsed == "hidden":
        await message.answer("Этот пользователь скрыл аккаунт при пересылке. Отправьте @username или Telegram ID.")
        return
    if not isinstance(parsed, SupportContact):
        await message.answer("Отправьте @username, Telegram ID, контакт или перешлите сообщение этого человека.")
        return
    contact = await set_support_contact(session, parsed.telegram_id, parsed.username)
    await state.clear()
    await send_home(message, staff_user, f"Контакт поддержки обновлён: {contact.label}")


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
