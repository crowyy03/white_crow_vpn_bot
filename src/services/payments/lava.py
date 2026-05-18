import hashlib
import hmac

import httpx

from src.config import get_settings
from src.services.payments.base import PaymentResult


class LavaProvider:
    name = "lava"

    def __init__(self) -> None:
        s = get_settings()
        self.api_url = s.lava_api_url.rstrip("/")
        self.api_key = s.lava_api_key
        self.shop_id = s.lava_shop_id
        self.hook_url = f"{s.webhook_base_url}/webhook/lava"
        self.success_url = f"https://t.me/{s.bot_username}"
        self.fail_url = f"https://t.me/{s.bot_username}"

    async def create_invoice(
        self,
        *,
        order_id: int,
        amount_kopecks: int,
        description: str,
    ) -> PaymentResult:
        amount_rub = round(amount_kopecks / 100, 2)
        body = {
            "shopId": self.shop_id,
            "sum": amount_rub,
            "orderId": str(order_id),
            "hookUrl": self.hook_url,
            "successUrl": self.success_url,
            "failUrl": self.fail_url,
            "expire": 900,
            "comment": description,
        }
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=10.0) as c:
            resp = await c.post(
                f"{self.api_url}/business/invoice/create", json=body, headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
        result = data.get("data") or data.get("result") or data
        return PaymentResult(
            payment_url=result["url"],
            external_id=str(result.get("id") or result.get("invoiceId") or order_id),
        )


def verify_webhook_signature(amount: str, order_id: str, signature: str) -> bool:
    secret = get_settings().lava_secret
    if not secret or not signature:
        return False
    raw = f"{amount}:{order_id}:{secret}".encode()
    expected = hashlib.sha256(raw).hexdigest()
    return hmac.compare_digest(expected.lower(), signature.lower())
