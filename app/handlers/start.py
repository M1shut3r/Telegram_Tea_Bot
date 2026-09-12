from aiogram import Bot, F, Router
from aiogram.filters import CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.keyboards.user_kb import (
    CONTACT_SUPPORT_BUTTON,
    LEGACY_CONTACT_ADMIN_BUTTON,
    contact_support_keyboard,
    main_menu,
    subscribe_keyboard,
)
from app.models.user import User, UserRole
from app.repositories.users import UserRepository
from app.services.admin_manager import INVITE_PREFIX, activate_invite
from app.services.subscription import SubscriptionService
from app.services.support_contact import get_support_contact

router = Router()


async def resolve_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
) -> User:
    repository = UserRepository(session)
    return await repository.upsert(telegram_id, username, settings.super_admin_id)


async def has_shop_access(bot: Bot, user: User) -> bool:
    if user.role in {UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value}:
        return True
    service = SubscriptionService(bot, settings.channel_id)
    return await service.is_subscribed(user.telegram_id)


async def send_subscribe_gate(message: Message, bot: Bot) -> None:
    service = SubscriptionService(bot, settings.channel_id)
    url = await service.channel_url()
    await message.answer(
        "Чтобы пользоваться витриной, подпишитесь на наш канал и нажмите «Я подписался».",
        reply_markup=subscribe_keyboard(url),
    )


async def send_home(message: Message, user: User, text: str = "Добро пожаловать в чайную витрину.") -> None:
    await message.answer(text, reply_markup=main_menu(user.role))


@router.message(CommandStart())
async def handle_start(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    bot: Bot,
    state: FSMContext,
) -> None:
    await state.clear()
    if message.from_user is None:
        return
    user = await resolve_user(session, message.from_user.id, message.from_user.username)
    payload = command.args or ""
    if payload.startswith(INVITE_PREFIX):
        token = payload.removeprefix(INVITE_PREFIX)
        result = await activate_invite(session, token, user)
        messages = {
            "activated": "Инвайт принят. Вам выданы права администратора.",
            "already_staff": "Вы уже являетесь администратором.",
            "used": "Эта пригласительная ссылка уже использована.",
            "invalid": "Пригласительная ссылка недействительна.",
        }
        await message.answer(messages.get(result, messages["invalid"]))
        user = await resolve_user(session, message.from_user.id, message.from_user.username)
    await send_home(message, user)
    if not await has_shop_access(bot, user):
        await send_subscribe_gate(message, bot)


@router.message(
    StateFilter(default_state),
    F.text.in_({CONTACT_SUPPORT_BUTTON, LEGACY_CONTACT_ADMIN_BUTTON}),
)
async def handle_contact_support(message: Message, session: AsyncSession, bot: Bot) -> None:
    if message.from_user is None:
        return
    user = await resolve_user(session, message.from_user.id, message.from_user.username)
    if not await has_shop_access(bot, user):
        await send_subscribe_gate(message, bot)
        return
    contact = await get_support_contact(session)
    if not contact.is_set or contact.url is None:
        await message.answer("Контакт поддержки пока не назначен.")
        return
    await message.answer(
        "Нажмите кнопку ниже, чтобы написать в поддержку.",
        reply_markup=contact_support_keyboard(contact.url),
    )


@router.callback_query(F.data == "sub:check")
async def handle_subscription_check(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return
    user = await resolve_user(session, callback.from_user.id, callback.from_user.username)
    if not await has_shop_access(bot, user):
        await callback.answer("Подписка не найдена. Подпишитесь на канал и попробуйте снова.", show_alert=True)
        return
    await callback.answer("Доступ открыт.")
    await callback.message.answer("Спасибо за подписку!", reply_markup=main_menu(user.role))


@router.message(F.web_app_data)
async def handle_web_app_data(message: Message, session: AsyncSession, bot: Bot) -> None:
    if message.from_user is None or message.web_app_data is None:
        return
    user = await resolve_user(session, message.from_user.id, message.from_user.username)
    if not await has_shop_access(bot, user):
        await send_subscribe_gate(message, bot)
        return
    await send_home(message, user, "Данные витрины получены.")
