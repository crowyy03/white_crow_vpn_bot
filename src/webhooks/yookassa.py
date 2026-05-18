from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from src.services.notifications import send_topup_success
from src.services.subscription import process_topup

router = APIRouter()


@router.post("/webhook/yookassa")
async def yookassa_webhook(request: Request) -> dict:
    payload = await request.json()
    event = payload.get("event")
    if event != "payment.succeeded":
        return {"ok": True}

    obj = payload.get("object") or {}
    metadata = obj.get("metadata") or {}
    try:
        order_id = int(metadata["order_id"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=400, detail="bad order_id")

    sessionmaker = request.app.state.sessionmaker
    bot = request.app.state.bot

    async with sessionmaker() as session:
        result = await process_topup(session, order_id)
        await session.commit()

    if result is not None:
        await send_topup_success(bot, result)

    logger.info("yookassa webhook processed order_id={}", order_id)
    return {"ok": True}
