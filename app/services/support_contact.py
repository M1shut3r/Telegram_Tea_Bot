import re
from dataclasses import dataclass

from aiogram.types import Contact, Message, MessageOriginHiddenUser, MessageOriginUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.settings import ShopSettingRepository
from app.repositories.users import UserRepository

SUPPORT_TELEGRAM_ID_KEY = "support_telegram_id"
SUPPORT_USERNAME_KEY = "support_username"
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{5,32}$")
USERNAME_PREFIXES = (
    "https://t.me/",
    "http://t.me/",
    "https://telegram.me/",
    "http://telegram.me/",
    "t.me/",
    "telegram.me/",
    "@",
)


@dataclass(slots=True)
class SupportContact:
    telegram_id: int | None
    username: str | None

    @property
    def is_set(self) -> bool:
        return self.telegram_id is not None or bool(self.username)

    @property
    def label(self) -> str:
        if self.username:
            return f"@{self.username}"
        if self.telegram_id is not None:
            return f"ID {self.telegram_id}"
        return "не назначен"

    @property
    def url(self) -> str | None:
        if self.username:
            return f"https://t.me/{self.username}"
        if self.telegram_id is not None:
            return f"tg://user?id={self.telegram_id}"
        return None


def parse_username(raw: str) -> str | None:
    text = raw.strip()
    lowered = text.lower()
    for prefix in USERNAME_PREFIXES:
        if lowered.startswith(prefix):
            text = text[len(prefix) :]
            break
    text = text.split("?", 1)[0].split("/", 1)[0].strip()
    if USERNAME_RE.fullmatch(text):
        return text
    return None


def parse_telegram_id(raw: str) -> int | None:
    text = raw.strip()
    if not text.isdigit():
        return None
    value = int(text)
    if value <= 0:
        return None
    return value


def extract_support_from_message(message: Message) -> SupportContact | str | None:
    if message.forward_from is not None:
        return SupportContact(telegram_id=message.forward_from.id, username=message.forward_from.username)
    origin = message.forward_origin
    if isinstance(origin, MessageOriginHiddenUser):
        return "hidden"
    if isinstance(origin, MessageOriginUser):
        sender = origin.sender_user
        return SupportContact(telegram_id=sender.id, username=sender.username)
    contact: Contact | None = message.contact
    if contact is not None and contact.user_id:
        return SupportContact(telegram_id=contact.user_id, username=None)
    raw = (message.text or "").strip()
    if not raw:
        return None
    telegram_id = parse_telegram_id(raw)
    if telegram_id is not None:
        return SupportContact(telegram_id=telegram_id, username=None)
    username = parse_username(raw)
    if username is not None:
        return SupportContact(telegram_id=None, username=username)
    return None


async def get_support_contact(session: AsyncSession) -> SupportContact:
    repository = ShopSettingRepository(session)
    raw_id = await repository.get_value(SUPPORT_TELEGRAM_ID_KEY)
    username = await repository.get_value(SUPPORT_USERNAME_KEY)
    telegram_id = int(raw_id) if raw_id is not None and raw_id.isdigit() else None
    if telegram_id is not None:
        user = await UserRepository(session).get_by_telegram_id(telegram_id)
        if user is not None and user.username:
            username = user.username
    return SupportContact(telegram_id=telegram_id, username=username)


async def set_support_contact(
    session: AsyncSession,
    telegram_id: int | None,
    username: str | None,
) -> SupportContact:
    repository = ShopSettingRepository(session)
    if telegram_id is not None:
        await repository.set_value(SUPPORT_TELEGRAM_ID_KEY, str(telegram_id))
        user = await UserRepository(session).get_by_telegram_id(telegram_id)
        if user is not None and user.username:
            username = user.username
    else:
        await repository.delete_value(SUPPORT_TELEGRAM_ID_KEY)
    if username:
        await repository.set_value(SUPPORT_USERNAME_KEY, username)
    else:
        await repository.delete_value(SUPPORT_USERNAME_KEY)
    return SupportContact(telegram_id=telegram_id, username=username)


async def clear_support_contact(session: AsyncSession) -> None:
    repository = ShopSettingRepository(session)
    await repository.delete_value(SUPPORT_TELEGRAM_ID_KEY)
    await repository.delete_value(SUPPORT_USERNAME_KEY)
