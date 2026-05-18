from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db.models import User
from src.db.repos import OrdersRepo, TariffsRepo, UsersRepo
from src.services.remnawave import make_remnawave_client


@dataclass
class TopupResult:
    telegram_id: int
    amount_kopecks: int
    new_balance_kopecks: int
    plan_code: str
    plan_name: str
    daily_rate_kopecks: int
    vpn_enabled: bool
    sub_url: str | None


async def _ensure_remnawave_user(
    session: AsyncSession, user: User, daily_rate_kopecks: int
) -> User:
    if user.remnawave_uuid and user.subscription_url:
        return user

    settings = get_settings()
    remna = make_remnawave_client()

    far_expire = datetime.now(timezone.utc) + timedelta(
        days=365 * settings.billing_far_future_years
    )
    rn_user = await remna.create_user(
        username=f"tg_{user.telegram_id}",
        expire_at=far_expire,
        traffic_limit_bytes=None,
        squad_uuid=settings.remnawave_default_squad_uuid,
        description=f"TG: @{user.username or '-'} (id {user.telegram_id})",
    )
    users = UsersRepo(session)
    await users.set_subscription(
        user.id,
        remnawave_uuid=rn_user.uuid,
        remnawave_short_uuid=rn_user.short_uuid,
        subscription_url=rn_user.subscription_url,
    )
    await users.clear_trial_expiration(user.id)
    await session.refresh(user)
    return user


async def process_topup(session: AsyncSession, order_id: int) -> TopupResult | None:
    orders = OrdersRepo(session)
    users = UsersRepo(session)
    tariffs = TariffsRepo(session)

    order = await orders.get(order_id)
    if order is None:
        logger.warning("process_topup: order {} not found", order_id)
        return None
    if order.status == "paid":
        logger.info("process_topup: order {} already paid", order_id)
        return None
    if order.kind != "topup":
        logger.warning("process_topup: order {} has kind={}", order_id, order.kind)
        return None

    user = await users.get_by_id(order.user_id)
    if user is None:
        logger.error("process_topup: user missing for order {}", order_id)
        return None

    tariff = await tariffs.get_by_code(user.plan)
    if tariff is None:
        logger.error("process_topup: tariff {} missing", user.plan)
        return None

    user = await _ensure_remnawave_user(session, user, tariff.daily_rate_kopecks)

    await users.add_balance(user.id, order.amount_kopecks)
    new_balance = user.balance_kopecks + order.amount_kopecks

    vpn_enabled = user.is_active
    if not user.is_active and new_balance >= tariff.daily_rate_kopecks:
        remna = make_remnawave_client()
        if user.remnawave_uuid:
            try:
                await remna.enable_user(str(user.remnawave_uuid))
                await users.set_active(user.id, True)
                vpn_enabled = True
            except Exception as e:
                logger.exception("enable_user failed for {}: {}", user.id, e)

    await orders.mark_paid(order.id)

    settings = get_settings()
    if user.referrer_id:
        bonus = order.amount_kopecks * settings.referral_percent // 100
        if bonus > 0:
            await users.add_balance(user.referrer_id, bonus)

    return TopupResult(
        telegram_id=user.telegram_id,
        amount_kopecks=order.amount_kopecks,
        new_balance_kopecks=new_balance,
        plan_code=tariff.code,
        plan_name=tariff.name,
        daily_rate_kopecks=tariff.daily_rate_kopecks,
        vpn_enabled=vpn_enabled,
        sub_url=user.subscription_url,
    )
