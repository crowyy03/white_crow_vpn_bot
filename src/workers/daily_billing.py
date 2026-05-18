from datetime import date, datetime, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.bot.texts import LOW_BALANCE_NOTIFICATION, VPN_DISABLED_NOTIFICATION
from src.config import get_settings
from src.db.models import Tariff, User
from src.db.repos import UsersRepo
from src.services.remnawave import make_remnawave_client


async def _send(bot: Bot, telegram_id: int, text: str, **kwargs) -> None:
    try:
        await bot.send_message(telegram_id, text, parse_mode="HTML", **kwargs)
    except TelegramAPIError as e:
        logger.warning("daily_billing: send to {} failed: {}", telegram_id, e)


def _plan_devices(plan_code: str) -> str:
    return "1 устройство" if plan_code == "solo" else "5 устройств"


async def _tick_user(
    session,
    bot: Bot,
    user: User,
    rate: int,
    plan_name: str,
    today: date,
) -> None:
    settings = get_settings()
    users = UsersRepo(session)
    remna = make_remnawave_client()

    if user.balance_kopecks >= rate:
        await users.deduct_balance(user.id, rate)
        await users.set_last_billed_on(user.id, today)
        new_balance = user.balance_kopecks - rate
        days_left = new_balance // rate if rate else 0
        if days_left < settings.low_balance_days_threshold:
            await _send(
                bot,
                user.telegram_id,
                LOW_BALANCE_NOTIFICATION.format(
                    days=days_left,
                    balance=new_balance // 100,
                    plan_name=plan_name,
                ),
            )
        return

    if user.is_active and user.remnawave_uuid:
        try:
            await remna.disable_user(str(user.remnawave_uuid))
        except Exception as e:
            logger.exception("daily_billing: disable failed for {}: {}", user.id, e)
            return
    await users.set_active(user.id, False)
    await users.set_last_billed_on(user.id, today)
    await _send(bot, user.telegram_id, VPN_DISABLED_NOTIFICATION)


async def run_once(sessionmaker: async_sessionmaker, bot: Bot) -> None:
    now = datetime.now(timezone.utc)
    today = now.date()

    async with sessionmaker() as session:
        result = await session.execute(
            select(User).where(
                User.subscription_url.is_not(None),
                User.is_active.is_(True),
                User.subscription_until.is_(None),
            )
        )
        candidates = list(result.scalars().all())

        if not candidates:
            await session.commit()
            return

        plan_codes = {u.plan for u in candidates}
        tariff_rows = await session.execute(
            select(Tariff).where(Tariff.code.in_(plan_codes))
        )
        tariffs = {t.code: t for t in tariff_rows.scalars().all()}

        billed = 0
        for user in candidates:
            if user.last_billed_on == today:
                continue
            tariff = tariffs.get(user.plan)
            if tariff is None:
                logger.warning("daily_billing: tariff {} missing", user.plan)
                continue
            try:
                await _tick_user(
                    session, bot, user, tariff.daily_rate_kopecks, tariff.name, today
                )
                billed += 1
            except Exception as e:
                logger.exception("daily_billing: tick {} failed: {}", user.id, e)

        await session.commit()
        logger.info("daily_billing: processed {} users", billed)
