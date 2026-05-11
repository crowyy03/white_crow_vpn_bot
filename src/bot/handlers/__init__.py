from aiogram import Router

from src.bot.handlers import admin, buy, menu, profile, referral, start, trial


def setup_routers() -> Router:
    root = Router()
    root.include_router(start.router)
    root.include_router(menu.router)
    root.include_router(buy.router)
    root.include_router(profile.router)
    root.include_router(trial.router)
    root.include_router(referral.router)
    root.include_router(admin.router)
    return root
