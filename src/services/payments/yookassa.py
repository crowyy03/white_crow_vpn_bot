from uuid import uuid4

import httpx

from src.config import get_settings
from src.services.payments.base import PaymentResult


class YookassaProvider:
    name = "yookassa"
    base_url = "https://api.yookassa.ru/v3"

    def __init__(self) -> None:
        s = get_settings()
        self.shop_id = s.yookassa_shop_id
        self.secret_key = s.yookassa_secret_key
        self.return_url = f"https://t.me/{s.bot_username}"

    async def create_invoice(
        self,
        *,
        order_id: int,
        amount_kopecks: int,
        description: str,
    ) -> PaymentResult:
        amount_rub = f"{amount_kopecks / 100:.2f}"
        body = {
            "amount": {"value": amount_rub, "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": self.return_url},
            "capture": True,
            "description": description,
            "metadata": {"order_id": str(order_id)},
        }
        headers = {
            "Idempotence-Key": str(uuid4()),
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(
            timeout=10.0, auth=(self.shop_id, self.secret_key)
        ) as c:
            resp = await c.post(f"{self.base_url}/payments", json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return PaymentResult(
            payment_url=data["confirmation"]["confirmation_url"],
            external_id=data["id"],
        )
