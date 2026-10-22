import logging
from time import monotonic

from aiogram import Bot
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError, TelegramRetryAfter, TelegramServerError

logger = logging.getLogger(__name__)

_ACTIVE_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.CREATOR,
}
_STAFF_STATUSES = {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}
# Errors that say nothing about the channel setup; diagnose() re-raises them.
_TRANSIENT_ERRORS = (TelegramNetworkError, TelegramRetryAfter, TelegramServerError)
# CHANNEL_ID from Example.env. Seeing it at runtime means .env was never updated.
EXAMPLE_CHANNEL_ID = -1001234567890
_URL_CACHE_TTL_SECONDS = 600
_url_cache: dict[int, tuple[float, str]] = {}


def _normalize_channel_url(raw: str) -> str | None:
    value = raw.strip()
    if not value:
        return None
    if value.startswith("@"):
        return f"https://t.me/{value[1:]}"
    if value.startswith("t.me/"):
        return f"https://{value}"
    if value.startswith(("https://t.me/", "https://telegram.me/")):
        return value
    return None


class SubscriptionService:
    def __init__(self, bot: Bot, channel_id: int, channel_url: str = "") -> None:
        self._bot = bot
        self._channel_id = channel_id
        self._raw_url = channel_url.strip()
        self._configured_url = _normalize_channel_url(channel_url)

    async def is_subscribed(self, telegram_id: int) -> bool:
        try:
            member = await self._bot.get_chat_member(self._channel_id, telegram_id)
        except TelegramAPIError as error:
            logger.error("Subscription check failed for channel %s: %s", self._channel_id, error)
            return False
        if member.status == ChatMemberStatus.RESTRICTED:
            return bool(getattr(member, "is_member", False))
        return member.status in _ACTIVE_STATUSES

    async def channel_url(self) -> str | None:
        """Link for the «Подписаться» button, or None if the channel is unreachable.

        Never falls back to a generic https://t.me page: a wrong link is worse than none.
        """
        if self._configured_url is not None:
            return self._configured_url
        cached = _url_cache.get(self._channel_id)
        if cached is not None and monotonic() - cached[0] < _URL_CACHE_TTL_SECONDS:
            return cached[1]
        url = await self._resolve_url()
        if url is not None:
            _url_cache[self._channel_id] = (monotonic(), url)
        return url

    async def _resolve_url(self) -> str | None:
        try:
            chat = await self._bot.get_chat(self._channel_id)
        except TelegramAPIError as error:
            logger.error("Channel %s is unreachable: %s", self._channel_id, error)
            return None
        if chat.username:
            return f"https://t.me/{chat.username}"
        # Private channel. getChat already returns the bot's own invite link when the bot
        # may invite users. exportChatInviteLink is not used: it revokes the previous
        # primary link, so every /start used to break links shared elsewhere.
        if chat.invite_link:
            return chat.invite_link
        try:
            link = await self._bot.create_chat_invite_link(self._channel_id, name="Чайный бот")
        except TelegramAPIError as error:
            logger.error("Cannot create an invite link for channel %s: %s", self._channel_id, error)
            return None
        return link.invite_link

    async def diagnose(self) -> list[str]:
        """Human-readable problems with the channel setup; empty when everything works."""
        if self._channel_id == EXAMPLE_CHANNEL_ID:
            return [
                f"CHANNEL_ID={self._channel_id} — это пример из Example.env, а не ваш канал. "
                "Укажите в .env настоящий ID канала (-100…) и перезапустите бота."
            ]
        problems: list[str] = []
        if self._raw_url and self._configured_url is None:
            problems.append(
                f"CHANNEL_URL={self._raw_url} не похоже на ссылку Telegram и игнорируется. "
                "Нужно https://t.me/имя, @имя или https://t.me/+приглашение."
            )
        try:
            chat = await self._bot.get_chat(self._channel_id)
        except _TRANSIENT_ERRORS:
            raise
        except TelegramAPIError as error:
            problems.append(
                f"Бот не видит канал CHANNEL_ID={self._channel_id} ({error.message}). "
                "Проверьте ID в .env и что бот добавлен в канал администратором."
            )
            return problems
        title = chat.title or str(self._channel_id)
        if chat.type not in {ChatType.CHANNEL, ChatType.SUPERGROUP}:
            problems.append(f"CHANNEL_ID={self._channel_id} указывает на «{title}», а это не канал.")
        try:
            bot_member = await self._bot.get_chat_member(self._channel_id, self._bot.id)
        except _TRANSIENT_ERRORS:
            raise
        except TelegramAPIError as error:
            bot_member = None
            problems.append(f"Не удалось проверить права бота в «{title}» ({error.message}).")
        if bot_member is not None and bot_member.status not in _STAFF_STATUSES:
            problems.append(
                f"Бот не администратор канала «{title}», поэтому не видит подписчиков: "
                "проверка подписки не пропустит никого. Назначьте бота администратором."
            )
        if self._configured_url is None and not chat.username and not chat.invite_link:
            can_invite = bool(getattr(bot_member, "can_invite_users", False))
            if not can_invite:
                problems.append(
                    f"Канал «{title}» закрытый, а у бота нет права приглашать участников, "
                    "поэтому кнопка «Подписаться» не может получить ссылку. Дайте боту это право "
                    "или укажите ссылку в CHANNEL_URL в .env."
                )
        return problems
