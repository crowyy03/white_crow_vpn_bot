from datetime import datetime, timezone

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.texts import ADMIN_ONLY
from src.config import get_settings
from src.db.models import Order, User

router = Router(name="admin")


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in get_settings().admin_ids_set


@router.message(Command("stats"))
async def cmd_stats(message: Message, session: AsyncSession) -> None:
    if not _is_admin(message.from_user.id):
        await message.answer(ADMIN_ONLY)
        return

    total_users = (await session.execute(select(func.count()).select_from(User))).scalar_one()
    now = datetime.now(timezone.utc)
    active_users = (
        await session.execute(
            select(func.count()).select_from(User).where(User.subscription_until > now)
        )
    ).scalar_one()
    revenue = (
        await session.execute(
            select(func.coalesce(func.sum(Order.amount_kopecks), 0)).where(Order.status == "paid")
        )
    ).scalar_one()

    await message.answer(
        f"📊 Статистика\n\n"
        f"Всего юзеров: <b>{total_users}</b>\n"
        f"С активной подпиской: <b>{active_users}</b>\n"
        f"Выручка за всё время: <b>{revenue // 100} ₽</b>",
        parse_mode="HTML",
    )


@router.message(Command("give"))
async def cmd_give(
    message: Message, command: CommandObject, session: AsyncSession
) -> None:
    if not _is_admin(message.from_user.id):
        await message.answer(ADMIN_ONLY)
        return
    await message.answer("Стаб: /give пока не реализован.")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        await message.answer(ADMIN_ONLY)
        return
    await message.answer("Стаб: /broadcast пока не реализован.")
