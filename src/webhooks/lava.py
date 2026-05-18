from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from src.services.notifications import send_topup_success
from src.services.payments.lava import verify_webhook_signature
from src.services.subscription import process_topup

router = APIRouter()


@router.post("/webhook/lava")
async def lava_webhook(request: Request) -> dict:
    payload = await request.json()

    order_id_raw = str(payload.get("orderId") or payload.get("order_id") or "")
    amount = str(payload.get("amount") or payload.get("sum") or "")
    signature = str(payload.get("signature") or "")
    status = (payload.get("status") or "").lower()

    if not order_id_raw:
        raise HTTPException(status_code=400, detail="missing orderId")

    if not verify_webhook_signature(amount, order_id_raw, signature):
        logger.warning("lava: bad signature for orderId={}", order_id_raw)
        raise HTTPException(status_code=403, detail="bad signature")

    if status and status not in ("success", "paid", "completed"):
        logger.info("lava webhook orderId={} status={} ignored", order_id_raw, status)
        return {"status": "ok"}

    try:
        order_id = int(order_id_raw)
    except ValueError:
        raise HTTPException(status_code=400, detail="bad orderId")

    sessionmaker = request.app.state.sessionmaker
    bot = request.app.state.bot

    async with sessionmaker() as session:
        result = await process_topup(session, order_id)
        await session.commit()

    if result is not None:
        await send_topup_success(bot, result)

    logger.info("lava webhook processed orderId={}", order_id)
    return {"status": "ok"}
