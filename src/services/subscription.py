from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db.repos import OrdersRepo, TariffsRepo, UsersRepo
from src.services.remnawave import make_remnawave_client


async def process_payment(session: AsyncSession, order_id: int) -> tuple[int, datetime] | None:
    orders = OrdersRepo(session)
    users = UsersRepo(session)
    tariffs = TariffsRepo(session)

    order = await orders.get(order_id)
    if order is None:
        logger.warning("process_payment: order {} not found", order_id)
        return None
    if order.status == "paid":
        logger.info("process_payment: order {} already paid", order_id)
        return None

    user = await users.get_by_id(order.user_id)
    tariff = await tariffs.get(order.tariff_id)
    if user is None or tariff is None:
        logger.error("process_payment: user/tariff missing for order {}", order_id)
        return None

    now = datetime.now(timezone.utc)
    base = user.subscription_until if user.subscription_until and user.subscription_until > now else now
    new_expire = base + timedelta(days=tariff.duration_days)

    settings = get_settings()
    remna = make_remnawave_client()

    if not user.remnawave_uuid:
        rn_user = await remna.create_user(
            username=f"tg_{user.telegram_id}",
            expire_at=new_expire,
            traffic_limit_bytes=tariff.traffic_limit_bytes,
            squad_uuid=settings.remnawave_default_squad_uuid,
            description=f"TG: @{user.username or '-'} (id {user.telegram_id})",
        )
        await users.set_subscription(
            user.id,
            remnawave_uuid=rn_user.uuid,
            remnawave_short_uuid=rn_user.short_uuid,
            subscription_url=rn_user.subscription_url,
            subscription_until=new_expire,
        )
    else:
        await remna.update_user_expire(str(user.remnawave_uuid), new_expire)
        await remna.enable_user(str(user.remnawave_uuid))
        await users.set_subscription(user.id, subscription_until=new_expire)

    await orders.mark_paid(order.id)

    if user.referrer_id:
        bonus = order.amount_kopecks * settings.referral_percent // 100
        await users.add_balance(user.referrer_id, bonus)

    return user.telegram_id, new_expire
