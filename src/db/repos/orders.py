from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Order

PENDING_TTL_MINUTES = 15


class OrdersRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_topup(
        self,
        *,
        user_id: int,
        amount_kopecks: int,
        payment_method: str,
    ) -> Order:
        order = Order(
            user_id=user_id,
            tariff_id=None,
            kind="topup",
            amount_kopecks=amount_kopecks,
            payment_method=payment_method,
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=PENDING_TTL_MINUTES),
        )
        self.session.add(order)
        await self.session.flush()
        return order

    async def get(self, order_id: int) -> Order | None:
        return await self.session.get(Order, order_id)

    async def mark_paid(
        self,
        order_id: int,
        payment_external_id: str | None = None,
    ) -> None:
        values: dict = {
            "status": "paid",
            "paid_at": datetime.now(timezone.utc),
        }
        if payment_external_id is not None:
            values["payment_external_id"] = payment_external_id
        await self.session.execute(
            update(Order).where(Order.id == order_id).values(**values)
        )

    async def set_payment_info(
        self, order_id: int, payment_url: str, payment_external_id: str
    ) -> None:
        await self.session.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(payment_url=payment_url, payment_external_id=payment_external_id)
        )

    async def set_external_id(self, order_id: int, payment_external_id: str) -> None:
        await self.session.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(payment_external_id=payment_external_id)
        )

    async def find_by_external(self, payment_external_id: str) -> Order | None:
        result = await self.session.execute(
            select(Order).where(Order.payment_external_id == payment_external_id)
        )
        return result.scalar_one_or_none()
