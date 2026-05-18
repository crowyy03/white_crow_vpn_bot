import io
from datetime import datetime, timezone

import qrcode
from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import (
    disabled_actions,
    os_keyboard,
    profile_actions,
)
from src.bot.texts import (
    INSTRUCTION_PICK_OS,
    PLAN_DESC_FAMILY,
    PLAN_DESC_SOLO,
    PROFILE_ACTIVE,
    PROFILE_DISABLED,
    PROFILE_LOW_BALANCE,
    PROFILE_NO_VPN,
    PROFILE_TRIAL,
)
from src.config import get_settings
from src.db.models import User
from src.db.repos import TariffsRepo, UsersRepo

router = Router(name="profile")


def _plan_desc(plan_code: str) -> str:
    return PLAN_DESC_SOLO if plan_code == "solo" else PLAN_DESC_FAMILY


def _plan_devices(plan_code: str) -> str:
    return "1 устройство" if plan_code == "solo" else "5 устройств"


async def _render_profile(message: Message, user: User, session: AsyncSession) -> None:
    settings = get_settings()
    tariff = await TariffsRepo(session).get_by_code(user.plan)
    rate = tariff.daily_rate_kopecks if tariff else 700
    plan_name = tariff.name if tariff else "Solo"

    now = datetime.now(timezone.utc)
    if user.subscription_until and user.subscription_until > now:
        await message.answer(
            PROFILE_TRIAL.format(
                until=user.subscription_until.strftime("%d.%m.%Y"),
                plan_name=plan_name,
                rate=rate // 100,
            ),
            reply_markup=profile_actions(has_vpn=True, current_plan=user.plan),
            parse_mode="HTML",
        )
        return

    if not user.subscription_url:
        await message.answer(PROFILE_NO_VPN)
        return

    balance = user.balance_kopecks
    days = balance // rate if rate else 0

    if not user.is_active:
        await message.answer(
            PROFILE_DISABLED.format(plan_name=plan_name, devices=_plan_devices(user.plan)),
            reply_markup=disabled_actions(),
            parse_mode="HTML",
        )
        return

    if days < settings.low_balance_days_threshold:
        await message.answer(
            PROFILE_LOW_BALANCE.format(
                balance=balance // 100,
                days=days,
                rate=rate // 100,
                plan_name=plan_name,
                devices=_plan_devices(user.plan),
            ),
            reply_markup=profile_actions(has_vpn=True, current_plan=user.plan),
            parse_mode="HTML",
        )
        return

    await message.answer(
        PROFILE_ACTIVE.format(
            balance=balance // 100,
            days=days,
            rate=rate // 100,
            plan_name=plan_name,
            devices=_plan_devices(user.plan),
        ),
        reply_markup=profile_actions(has_vpn=True, current_plan=user.plan),
        parse_mode="HTML",
    )


async def show_profile(message: Message, session: AsyncSession, **_: object) -> None:
    user = await UsersRepo(session).get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer(PROFILE_NO_VPN)
        return
    await _render_profile(message, user, session)


@router.callback_query(F.data == "profile:show")
async def cb_show(call: CallbackQuery, session: AsyncSession) -> None:
    user = await UsersRepo(session).get_by_telegram_id(call.from_user.id)
    if user is None:
        await call.answer("Сначала нажми /start", show_alert=True)
        return
    await _render_profile(call.message, user, session)
    await call.answer()


@router.callback_query(F.data == "profile:copy")
async def on_copy(call: CallbackQuery, session: AsyncSession) -> None:
    user = await UsersRepo(session).get_by_telegram_id(call.from_user.id)
    if user is None or not user.subscription_url:
        await call.answer("Сначала активируй триал или пополни баланс", show_alert=True)
        return
    await call.message.answer(
        f"<code>{user.subscription_url}</code>\n\nНажми на ссылку выше, чтобы скопировать.",
        parse_mode="HTML",
    )
    await call.answer("Ссылка отправлена")


@router.callback_query(F.data == "profile:qr")
async def on_qr(call: CallbackQuery, session: AsyncSession) -> None:
    user = await UsersRepo(session).get_by_telegram_id(call.from_user.id)
    if user is None or not user.subscription_url:
        await call.answer("Сначала активируй триал или пополни баланс", show_alert=True)
        return
    img = qrcode.make(user.subscription_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    await call.message.answer_photo(
        BufferedInputFile(buf.read(), filename="subscription.png"),
        caption="QR-код подписки. Отсканируй в Happ.",
    )
    await call.answer()


@router.callback_query(F.data == "profile:howto")
async def on_howto(call: CallbackQuery) -> None:
    await call.message.answer(INSTRUCTION_PICK_OS, reply_markup=os_keyboard())
    await call.answer()
