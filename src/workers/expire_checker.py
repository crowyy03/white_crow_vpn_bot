from datetime import datetime, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.db.models import User
from src.db.repos import UsersRepo
from src.services.remnawave import make_remnawave_client


TRIAL_EXPIRED_TEXT = (
    "🎁 Триал закончился.\n"
    "VPN временно отключён. Пополни баланс — и доступ включится автоматически.\n"
    "Solo: 7 ₽/сутки, Family: 14 ₽/сутки."
)


async def run_once(sessionmaker: async_sessionmaker, bot: Bot) -> None:
    remna = make_remnawave_client()
    now = datetime.now(timezone.utc)

    async with sessionmaker() as session:
        result = await session.execute(
            select(User).where(
                User.subscription_until.is_not(None),
                User.subscription_until < now,
                User.remnawave_uuid.is_not(None),
                User.is_active.is_(True),
            )
        )
        expired = list(result.scalars().all())
        users = UsersRepo(session)

        for user in expired:
            try:
                await remna.disable_user(str(user.remnawave_uuid))
            except Exception as e:
                logger.warning("expire_checker: disable failed for {}: {}", user.id, e)
                continue
            await users.set_active(user.id, False)
            await users.clear_trial_expiration(user.id)
            try:
                await bot.send_message(user.telegram_id, TRIAL_EXPIRED_TEXT)
            except TelegramAPIError as e:
                logger.warning("expire_checker: send to {} failed: {}", user.telegram_id, e)

        await session.commit()
