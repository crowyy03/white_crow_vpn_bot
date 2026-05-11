import asyncio
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.db.models import NotificationLog, User

CHECK_INTERVAL_SECONDS = 24 * 3600


async def _notify_expiring(sessionmaker: async_sessionmaker, bot: Bot, days: int, log_type: str) -> None:
    target_start = datetime.now(timezone.utc) + timedelta(days=days)
    target_end = target_start + timedelta(days=1)

    async with sessionmaker() as session:
        result = await session.execute(
            select(User).where(
                and_(
                    User.subscription_until >= target_start,
                    User.subscription_until < target_end,
                )
            )
        )
        candidates = list(result.scalars().all())

        for user in candidates:
            already = await session.execute(
                select(NotificationLog).where(
                    NotificationLog.user_id == user.id,
                    NotificationLog.type == log_type,
                )
            )
            if already.scalar_one_or_none():
                continue
            try:
                await bot.send_message(
                    user.telegram_id,
                    f"Подписка истекает через {days} дн. Продлить — в меню.",
                )
            except Exception as e:
                logger.warning("notify_expiring: failed for {}: {}", user.telegram_id, e)
                continue
            session.add(NotificationLog(user_id=user.id, type=log_type))
        await session.commit()


async def run(sessionmaker: async_sessionmaker, bot: Bot) -> None:
    while True:
        try:
            await _notify_expiring(sessionmaker, bot, 3, "expire_3d")
            await _notify_expiring(sessionmaker, bot, 1, "expire_1d")
        except Exception as e:
            logger.exception("notifications tick failed: {}", e)
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
