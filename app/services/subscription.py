from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError

_ACTIVE_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.CREATOR,
}


class SubscriptionService:
    def __init__(self, bot: Bot, channel_id: int) -> None:
        self._bot = bot
        self._channel_id = channel_id

    async def is_subscribed(self, telegram_id: int) -> bool:
        try:
            member = await self._bot.get_chat_member(self._channel_id, telegram_id)
        except TelegramAPIError:
            return False
        return member.status in _ACTIVE_STATUSES

    async def channel_url(self) -> str:
        try:
            chat = await self._bot.get_chat(self._channel_id)
        except TelegramAPIError:
            return "https://t.me"
        if chat.username:
            return f"https://t.me/{chat.username}"
        try:
            return await self._bot.export_chat_invite_link(self._channel_id)
        except TelegramAPIError:
            return "https://t.me"
