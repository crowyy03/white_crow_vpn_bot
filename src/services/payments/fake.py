from src.services.payments.base import PaymentResult


class FakeProvider:
    name = "fake"

    async def create_invoice(
        self,
        *,
        order_id: int,
        amount_kopecks: int,
        description: str,
    ) -> PaymentResult:
        return PaymentResult(
            payment_url=f"https://example.com/fake-pay/{order_id}",
            external_id=f"fake_{order_id}",
        )
