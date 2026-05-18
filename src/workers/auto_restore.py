from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.bot.texts import VPN_RESTORED_NOTIFICATION
from src.db.models import Tariff, User
from src.db.repos import UsersRepo
from src.services.remnawave import make_remnawave_client


async def _notify(bot: Bot, telegram_id: int, days: int, plan_name: str) -> None:
    try:
        await bot.send_message(
            telegram_id,
            VPN_RESTORED_NOTIFICATION.format(days=days, plan_name=plan_name),
            parse_mode="HTML",
        )
    except TelegramAPIError as e:
        logger.warning("auto_restore: notify {} failed: {}", telegram_id, e)


async def run_once(sessionmaker: async_sessionmaker, bot: Bot) -> None:
    async with sessionmaker() as session:
        result = await session.execute(
            select(User).where(
                User.is_active.is_(False),
                User.remnawave_uuid.is_not(None),
                User.subscription_url.is_not(None),
            )
        )
        users_list = list(result.scalars().all())
        if not users_list:
            await session.commit()
            return

        plan_codes = {u.plan for u in users_list}
        tariff_rows = await session.execute(
            select(Tariff).where(Tariff.code.in_(plan_codes))
        )
        tariffs = {t.code: t for t in tariff_rows.scalars().all()}

        users = UsersRepo(session)
        remna = make_remnawave_client()
        restored = 0

        for user in users_list:
            tariff = tariffs.get(user.plan)
            if tariff is None:
                continue
            if user.balance_kopecks < tariff.daily_rate_kopecks:
                continue
            try:
                await remna.enable_user(str(user.remnawave_uuid))
            except Exception as e:
                logger.exception("auto_restore: enable failed for {}: {}", user.id, e)
                continue
            await users.set_active(user.id, True)
            days = user.balance_kopecks // tariff.daily_rate_kopecks
            await _notify(bot, user.telegram_id, days, tariff.name)
            restored += 1

        await session.commit()
        if restored:
            logger.info("auto_restore: restored {} users", restored)
