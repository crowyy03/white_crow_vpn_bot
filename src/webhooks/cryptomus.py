import base64
import hashlib
import json

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from src.config import get_settings
from src.services.notifications import send_subscription_link
from src.services.subscription import process_payment

router = APIRouter()


def _verify_sign(data: dict, sign: str, api_key: str) -> bool:
    encoded = base64.b64encode(json.dumps(data).encode()).decode()
    expected = hashlib.md5((encoded + api_key).encode()).hexdigest()
    return sign == expected


@router.post("/webhook/cryptomus")
async def cryptomus_webhook(request: Request) -> dict:
    payload = await request.json()
    sign = payload.pop("sign", None)
    if not sign:
        raise HTTPException(status_code=400, detail="missing sign")

    settings = get_settings()
    if not _verify_sign(payload, sign, settings.cryptomus_api_key):
        raise HTTPException(status_code=403, detail="bad sign")

    status = payload.get("status")
    if status not in ("paid", "paid_over"):
        return {"ok": True}

    try:
        order_id = int(payload["order_id"])
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
            from src.db.repos import UsersRepo

            user = await UsersRepo(session).get_by_telegram_id(telegram_id)
        if user and user.subscription_url:
            await send_subscription_link(
                bot, telegram_id, user.subscription_url, new_expire.strftime("%d.%m.%Y")
            )

    logger.info("cryptomus webhook processed order_id={}", order_id)
    return {"ok": True}
