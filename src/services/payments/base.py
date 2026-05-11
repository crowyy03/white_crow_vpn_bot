from dataclasses import dataclass
from typing import Protocol


@dataclass
class PaymentResult:
    payment_url: str
    external_id: str


class PaymentProvider(Protocol):
    name: str

    async def create_invoice(
        self,
        *,
        order_id: int,
        amount_kopecks: int,
        description: str,
    ) -> PaymentResult: ...
