import base64
import hashlib
import json

import httpx

from src.config import get_settings
from src.services.payments.base import PaymentResult


class CryptomusProvider:
    name = "cryptomus"
    base_url = "https://api.cryptomus.com/v1"

    def __init__(self) -> None:
        s = get_settings()
        self.merchant = s.cryptomus_merchant_uuid
        self.api_key = s.cryptomus_api_key
        self.webhook_url = f"{s.webhook_base_url}/webhook/cryptomus"
        self.return_url = f"https://t.me/{s.bot_username}"

    def _sign(self, body_json: str) -> str:
        encoded = base64.b64encode(body_json.encode()).decode()
        return hashlib.md5((encoded + self.api_key).encode()).hexdigest()

    async def create_invoice(
        self,
        *,
        order_id: int,
        amount_kopecks: int,
        description: str,
    ) -> PaymentResult:
        amount_usd = f"{amount_kopecks / 100 / 100:.2f}"
        body = {
            "amount": amount_usd,
            "currency": "USD",
            "order_id": str(order_id),
            "url_callback": self.webhook_url,
            "url_return": self.return_url,
            "is_payment_multiple": False,
            "lifetime": 900,
        }
        body_json = json.dumps(body)
        headers = {
            "merchant": self.merchant,
            "sign": self._sign(body_json),
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=10.0) as c:
            resp = await c.post(
                f"{self.base_url}/payment", content=body_json, headers=headers
            )
            resp.raise_for_status()
            data = resp.json()["result"]
        return PaymentResult(
            payment_url=data["url"],
            external_id=data["uuid"],
        )
