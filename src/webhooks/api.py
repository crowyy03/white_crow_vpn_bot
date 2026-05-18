from contextlib import asynccontextmanager

from aiogram import Bot
from fastapi import FastAPI

from src.db.session import get_sessionmaker
from src.webhooks.cryptomus import router as cryptomus_router
from src.webhooks.lava import router as lava_router
from src.webhooks.paypalych import router as paypalych_router
from src.webhooks.yookassa import router as yookassa_router


def create_app(bot: Bot) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        _app.state.bot = bot
        _app.state.sessionmaker = get_sessionmaker()
        yield

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
    app.include_router(cryptomus_router)
    app.include_router(yookassa_router)
    app.include_router(paypalych_router)
    app.include_router(lava_router)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app
