from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from src.db.repos import UsersRepo
from src.services.notifications import send_subscription_link
from src.services.subscription import process_payment

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
        result = await process_payment(session, order_id)
        await session.commit()

    if result is not None:
        telegram_id, new_expire = result
        async with sessionmaker() as session:
            user = await UsersRepo(session).get_by_telegram_id(telegram_id)
        if user and user.subscription_url:
            await send_subscription_link(
                bot, telegram_id, user.subscription_url, new_expire.strftime("%d.%m.%Y")
            )

    logger.info("yookassa webhook processed order_id={}", order_id)
    return {"ok": True}
