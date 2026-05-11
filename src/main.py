import asyncio
import sys

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from loguru import logger

from src.bot.handlers import setup_routers
from src.bot.middlewares import DbSessionMiddleware
from src.config import get_settings
from src.db.session import dispose_engine, get_sessionmaker
from src.webhooks.api import create_app
from src.workers import expire_checker, notifications


def _setup_logging(level: str) -> None:
    logger.remove()
    logger.add(sys.stderr, level=level, enqueue=True)


async def _run_polling(dp: Dispatcher, bot: Bot) -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def _run_webhook_server(bot: Bot) -> None:
    app = create_app(bot)
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main() -> None:
    settings = get_settings()
    _setup_logging(settings.log_level)
    logger.info("Starting vpn-bot")

    storage = RedisStorage.from_url(settings.redis_url)
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher(storage=storage)

    sessionmaker = get_sessionmaker()
    dp.update.middleware(DbSessionMiddleware(sessionmaker))
    dp.include_router(setup_routers())

    tasks = [
        asyncio.create_task(_run_polling(dp, bot), name="polling"),
        asyncio.create_task(_run_webhook_server(bot), name="webhooks"),
        asyncio.create_task(expire_checker.run(sessionmaker, bot), name="expire_checker"),
        asyncio.create_task(notifications.run(sessionmaker, bot), name="notifier"),
    ]

    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
        for t in done:
            if t.exception():
                logger.error("Task {} crashed: {}", t.get_name(), t.exception())
        for t in pending:
            t.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
    finally:
        await bot.session.close()
        await storage.close()
        await dispose_engine()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down")
