import asyncio
from datetime import datetime, timezone

from aiogram import Bot
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.db.models import User
from src.services.remnawave import make_remnawave_client

CHECK_INTERVAL_SECONDS = 6 * 3600


async def _tick(sessionmaker: async_sessionmaker, bot: Bot) -> None:
    remna = make_remnawave_client()
    async with sessionmaker() as session:
        now = datetime.now(timezone.utc)
        result = await session.execute(
            select(User).where(
                User.subscription_until.is_not(None),
                User.subscription_until < now,
                User.remnawave_uuid.is_not(None),
            )
        )
        expired = list(result.scalars().all())

    for user in expired:
        try:
            await remna.disable_user(str(user.remnawave_uuid))
            await bot.send_message(
                user.telegram_id, "Подписка истекла. Продли в меню «💳 Купить подписку»."
            )
        except Exception as e:
            logger.warning("expire_checker: failed for {}: {}", user.telegram_id, e)


async def run(sessionmaker: async_sessionmaker, bot: Bot) -> None:
    while True:
        try:
            await _tick(sessionmaker, bot)
        except Exception as e:
            logger.exception("expire_checker tick failed: {}", e)
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
