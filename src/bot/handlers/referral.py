from aiogram import Router
from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.texts import REFERRAL_INFO
from src.config import get_settings
from src.db.models import User
from src.db.repos import UsersRepo

router = Router(name="referral")


async def show_referral(message: Message, session: AsyncSession, **_: object) -> None:
    settings = get_settings()
    user = await UsersRepo(session).get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer("Сначала нажми /start")
        return

    result = await session.execute(
        select(func.count()).select_from(User).where(User.referrer_id == user.id)
    )
    count = result.scalar_one()

    link = f"https://t.me/{settings.bot_username}?start=ref_{user.telegram_id}"
    await message.answer(
        REFERRAL_INFO.format(
            link=link,
            count=count,
            balance=user.balance_kopecks // 100,
            percent=settings.referral_percent,
        ),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
