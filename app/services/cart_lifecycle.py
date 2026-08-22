from datetime import UTC, datetime, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.repositories.carts import CartRepository

cart_scheduler = AsyncIOScheduler(timezone="UTC")

_REMINDER_2H = (
    "Вы собрали корзину с элитным чаем, но ещё не оформили заказ.\n"
    "Позиции ждут вас — завершите оформление, пока чай в наличии."
)
_REMINDER_12H = "Напоминаем: ваша корзина всё ещё не оформлена.\nЧерез 12 часов она будет очищена автоматически."
_CLEARED_24H = "Корзина очищена: заказ не был оформлен в течение суток.\nВы можете снова выбрать чай в каталоге."


def _reminder_job_id(telegram_id: int, hours: int) -> str:
    return f"cart_remind_{hours}h_{telegram_id}"


def _clear_job_id(telegram_id: int) -> str:
    return f"cart_clear_24h_{telegram_id}"


async def _cart_still_active(telegram_id: int) -> bool:
    async with async_session_factory() as session:
        repository = CartRepository(session)
        user_id = await repository.get_user_id_by_telegram(telegram_id)
        if user_id is None:
            return False
        return await repository.count_items(user_id) > 0


async def send_cart_reminder(bot: Bot, telegram_id: int, hours: int) -> None:
    if not await _cart_still_active(telegram_id):
        return
    text = _REMINDER_2H if hours == 2 else _REMINDER_12H
    try:
        await bot.send_message(telegram_id, text)
    except TelegramAPIError:
        return


async def clear_abandoned_cart(bot: Bot, telegram_id: int) -> None:
    async with async_session_factory() as session:
        repository = CartRepository(session)
        user_id = await repository.get_user_id_by_telegram(telegram_id)
        if user_id is None:
            return
        if await repository.count_items(user_id) == 0:
            return
        await repository.clear_for_user(user_id)
        await session.commit()
    try:
        await bot.send_message(telegram_id, _CLEARED_24H)
    except TelegramAPIError:
        return


def cancel_cart_jobs(telegram_id: int) -> None:
    for job_id in (
        _reminder_job_id(telegram_id, 2),
        _reminder_job_id(telegram_id, 12),
        _clear_job_id(telegram_id),
    ):
        job = cart_scheduler.get_job(job_id)
        if job is not None:
            job.remove()


async def cancel_cart_jobs_for_user(session: AsyncSession, user_id: int) -> None:
    telegram_id = await CartRepository(session).get_telegram_id_by_user_id(user_id)
    if telegram_id is None:
        return
    cancel_cart_jobs(telegram_id)


def _add_date_job(job_id: str, run_date: datetime, func: object, kwargs: dict[str, object]) -> None:
    if run_date <= datetime.now(UTC):
        return
    cart_scheduler.add_job(
        func,
        trigger="date",
        run_date=run_date,
        kwargs=kwargs,
        id=job_id,
        replace_existing=True,
        misfire_grace_time=300,
    )


def schedule_cart_jobs(bot: Bot, telegram_id: int) -> None:
    if cart_scheduler.get_job(_clear_job_id(telegram_id)) is not None:
        return
    started_at = datetime.now(UTC)
    _add_date_job(
        _reminder_job_id(telegram_id, 2),
        started_at + timedelta(hours=2),
        send_cart_reminder,
        {"bot": bot, "telegram_id": telegram_id, "hours": 2},
    )
    _add_date_job(
        _reminder_job_id(telegram_id, 12),
        started_at + timedelta(hours=12),
        send_cart_reminder,
        {"bot": bot, "telegram_id": telegram_id, "hours": 12},
    )
    _add_date_job(
        _clear_job_id(telegram_id),
        started_at + timedelta(hours=24),
        clear_abandoned_cart,
        {"bot": bot, "telegram_id": telegram_id},
    )


def _aware(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=UTC)
    return moment


async def restore_cart_jobs(bot: Bot) -> None:
    async with async_session_factory() as session:
        repository = CartRepository(session)
        rows = await repository.earliest_created_by_telegram()
    now = datetime.now(UTC)
    for telegram_id, created_at in rows:
        started_at = _aware(created_at)
        deadline_24 = started_at + timedelta(hours=24)
        if now >= deadline_24:
            await clear_abandoned_cart(bot, telegram_id)
            continue
        _add_date_job(
            _reminder_job_id(telegram_id, 2),
            started_at + timedelta(hours=2),
            send_cart_reminder,
            {"bot": bot, "telegram_id": telegram_id, "hours": 2},
        )
        _add_date_job(
            _reminder_job_id(telegram_id, 12),
            started_at + timedelta(hours=12),
            send_cart_reminder,
            {"bot": bot, "telegram_id": telegram_id, "hours": 12},
        )
        _add_date_job(
            _clear_job_id(telegram_id),
            deadline_24,
            clear_abandoned_cart,
            {"bot": bot, "telegram_id": telegram_id},
        )
