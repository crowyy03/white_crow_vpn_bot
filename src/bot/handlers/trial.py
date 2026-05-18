from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import connect_buttons
from src.bot.texts import TRIAL_GRANTED, TRIAL_USED
from src.config import get_settings
from src.db.repos import UsersRepo
from src.services.remnawave import make_remnawave_client

router = Router(name="trial")


async def _grant_trial(
    telegram_id: int,
    chat_message: Message,
    session: AsyncSession,
) -> None:
    settings = get_settings()
    repo = UsersRepo(session)
    user = await repo.get_by_telegram_id(telegram_id)
    if user is None:
        await chat_message.answer("Сначала нажми /start")
        return
    if user.trial_used:
        await chat_message.answer(TRIAL_USED)
        return

    expire_at = datetime.now(timezone.utc) + timedelta(days=settings.trial_days)
    traffic_bytes = settings.trial_traffic_gb * 1024 * 1024 * 1024

    remna = make_remnawave_client()
    rn_user = await remna.create_user(
        username=f"tg_{user.telegram_id}_trial",
        expire_at=expire_at,
        traffic_limit_bytes=traffic_bytes,
        squad_uuid=settings.remnawave_default_squad_uuid,
        description=f"trial TG: @{user.username or '-'} (id {user.telegram_id})",
    )
    await repo.set_subscription(
        user.id,
        remnawave_uuid=rn_user.uuid,
        remnawave_short_uuid=rn_user.short_uuid,
        subscription_url=rn_user.subscription_url,
        subscription_until=expire_at,
    )
    await repo.mark_trial_used(user.id)

    await chat_message.answer(
        TRIAL_GRANTED.format(
            until=expire_at.strftime("%d.%m.%Y"),
            sub_url=rn_user.subscription_url,
        ),
        reply_markup=connect_buttons(rn_user.subscription_url),
        parse_mode="HTML",
    )


async def grant_trial(message: Message, session: AsyncSession, **_: object) -> None:
    await _grant_trial(message.from_user.id, message, session)


@router.callback_query(F.data == "trial:start")
async def cb_trial(call: CallbackQuery, session: AsyncSession) -> None:
    await _grant_trial(call.from_user.id, call.message, session)
    await call.answer()
