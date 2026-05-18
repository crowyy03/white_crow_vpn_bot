import asyncio
import sys

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from src.config import get_settings
from src.db.session import dispose_engine, get_sessionmaker
from src.workers import auto_restore, daily_billing, expire_checker


def _setup_logging(level: str) -> None:
    logger.remove()
    logger.add(sys.stderr, level=level, enqueue=True)


async def main() -> None:
    settings = get_settings()
    _setup_logging(settings.log_level)
    logger.info("Starting scheduler (tz={})", settings.tz)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    sessionmaker = get_sessionmaker()

    async def daily_job() -> None:
        try:
            await daily_billing.run_once(sessionmaker, bot)
        except Exception as e:
            logger.exception("daily_billing failed: {}", e)

    async def restore_job() -> None:
        try:
            await auto_restore.run_once(sessionmaker, bot)
        except Exception as e:
            logger.exception("auto_restore failed: {}", e)

    async def expire_job() -> None:
        try:
            await expire_checker.run_once(sessionmaker, bot)
        except Exception as e:
            logger.exception("expire_checker failed: {}", e)

    scheduler = AsyncIOScheduler(timezone=settings.tz)
    scheduler.add_job(daily_job, CronTrigger(hour=0, minute=0), id="daily_billing")
    scheduler.add_job(
        restore_job, IntervalTrigger(minutes=5), id="auto_restore", next_run_time=None
    )
    scheduler.add_job(
        expire_job, IntervalTrigger(minutes=30), id="expire_checker", next_run_time=None
    )

    scheduler.start()
    logger.info("Scheduler started, jobs: {}", [j.id for j in scheduler.get_jobs()])

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()
        await dispose_engine()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shutting down")
