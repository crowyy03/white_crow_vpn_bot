import hashlib

import httpx

from src.config import get_settings
from src.services.payments.base import PaymentResult


class PaypalychProvider:
    name = "paypalych"

    def __init__(self) -> None:
        s = get_settings()
        self.api_url = s.paypalych_api_url.rstrip("/")
        self.token = s.paypalych_api_token
        self.shop_id = s.paypalych_shop_id
        self.success_url = f"{s.webhook_base_url}/webhook/paypalych/success"
        self.fail_url = f"{s.webhook_base_url}/webhook/paypalych/fail"

    async def create_invoice(
        self,
        *,
        order_id: int,
        amount_kopecks: int,
        description: str,
    ) -> PaymentResult:
        amount_rub = round(amount_kopecks / 100, 2)
        body = {
            "amount": amount_rub,
            "order_id": str(order_id),
            "description": description,
            "type": "normal",
            "shop_id": self.shop_id,
            "currency_in": "RUB",
            "success_url": self.success_url,
            "fail_url": self.fail_url,
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=10.0) as c:
            resp = await c.post(f"{self.api_url}/bill/create", json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return PaymentResult(
            payment_url=data["link_url"],
            external_id=str(data["bill_id"]),
        )


def verify_postback_signature(out_sum: str, inv_id: str, signature: str) -> bool:
    secret = get_settings().paypalych_api_token
    if not secret or not signature:
        return False
    raw = f"{out_sum}:{inv_id}:{secret}".encode()
    expected = hashlib.sha256(raw).hexdigest()
    return expected.lower() == signature.lower()
